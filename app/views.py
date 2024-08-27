from django.db.models import Count, Q, F, Value, OuterRef
from django.db.models import Case, When, BooleanField, Subquery, IntegerField
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models.functions import Coalesce
from celery.result import AsyncResult

import random

from entry.models import Entry
from .models import Title, Author, Vote, Topic, Report
from .models import AuthorsFavorites, FollowTitle, FollowAuthor
from .forms import SettingsForm, TitleForm, ReportForm
from .forms import AINewEntryForm, AINewTitleForm, AINewEntriesLikeAnEntry
from .forms import NewTitleForm, NewTopicForm
from .constants import ORDER_CHOICES
from .ai_utils import AI, create_entry
from .search import search_titles, search_authors, search_topics
from .tasks import create_ai_title_task, create_random_entries_task


# user can choose random entry count max count is 50
class CacheHeaderMixin(object):
    cache_timeout = 60 * 60  # one hour
    # cache_timeout = 60 * 5

    def get_cache_timeout(self):
        return self.cache_timeout

    def dispatch(self, *args, **kwargs):
        return cache_page(self.get_cache_timeout())(super(
            CacheHeaderMixin, self).dispatch)(*args, **kwargs)


class AuthMixin(UserPassesTestMixin):
    def test_func(self):
        print("======HERE=======")
        return self.request.user.is_authenticated


class BaseView(View):
    context = {}
    ENTRY_COUNT = 10

    def get(self, request):
        # reset
        self.context['entries'] = None
        self.context['page_obj'] = None
        self.context['titles'] = None
        self.context['entries'] = None
        # last followers
        if request.user.is_authenticated:
            follows = FollowAuthor.objects.filter(
                follow=request.user).order_by('-follow_date')[:3]
            user_ids = follows.values_list('id', flat='anonymous')
            users = Author.objects.filter(pk__in=user_ids)
            self.context['last_follows'] = follows
            self.context['last_followers_count'] = users.count()
            self.get_entry_count(request)
            # last favs
            follow_title = FollowTitle.objects.filter(author=request.user)
            follow_title = follow_title.order_by('-last_seen')[:5]
            self.context['last_seen_titles'] = follow_title
            self.context['last_seen_count'] = follow_title.count()
        # topics
        self.context['topics'] = Topic.objects.all()

    def get_entry_count(self, request, is_title=True):
        if request.user.is_authenticated:
            if is_title:
                self.ENTRY_COUNT = int(request.user.title_entry_count)
            else:
                self.ENTRY_COUNT = int(request.user.random_entry_count)

    def get_is_fav_attr_entry(self, base_manager, user):
        return base_manager
        if (user.is_authenticated):
            uids = base_manager.values_list('uid', flat=True)
            fav_ids = AuthorsFavorites.objects.filter(
                entry_id__in=uids, author=user
                ).values_list('entry_id', flat=True)
            print("favs", fav_ids)
            return base_manager.annotate(
                is_fav=Case(
                    When(uid__in=fav_ids, then=Value(True)),
                    default=Value(False), output_field=BooleanField()))
        else:
            return base_manager

    def get_vote_counts_entry(self, base_manager):
        return base_manager
        up_votes_subquery = Vote.objects.filter(
            entry_id=OuterRef('uid'), is_up=True
            ).values('entry_id').annotate(
                count=Count('id')).values('count')
        down_votes_subquery = Vote.objects.filter(
            entry_id=OuterRef('uid'), is_up=False
            ).values('entry_id').annotate(
                count=Count('id')).values('count')

        return base_manager.annotate(
            up_votes_count=Coalesce(
                Subquery(up_votes_subquery, output_field=IntegerField()), 0),
            down_votes_count=Coalesce(
                Subquery(down_votes_subquery, output_field=IntegerField()), 0)
        )

    def get_fav_counts_entry(self, base_manager):
        fav_subquery = AuthorsFavorites.objects.filter(
            entry_id=OuterRef('uid')
            ).values('entry_id').annotate(
                count=Count('id')).values('count')
        return base_manager.annotate(
            fav_count=Coalesce(
                Subquery(fav_subquery, output_field=IntegerField()), 0))

    def set_pagination(self, base_manager, request):
        paginator = Paginator(base_manager, self.ENTRY_COUNT)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        self.context['page_obj'] = page_obj

    def set_entries_for_title_page(self, base_manager, request):
        self.get_entry_count(request)
        title_entries = self.get_is_fav_attr_entry(base_manager, request.user)
        title_entries = self.get_vote_counts_entry(title_entries)
        # title_entries = title_entries.order_by('created_at')
        self.set_pagination(title_entries, request)

        self.context['show_title'] = False
        return title_entries


class HomeView(BaseView):
    def get(self, request):
        super().get(request)
        self.get_entry_count(request, is_title=False)

        # create_random_entries_task.delay_on_commit(10)

        if 'random_entries' in cache:
            entries = cache.get('random_entries')
            cache.delete('random_entries')
            print("entries")
        else:
            # TODO: delete entry got error here!
            ids = Entry.objects.values_list('uid', flat=True)
            max_count = len(ids)
            if (max_count):
                count = min(len(ids), self.ENTRY_COUNT)  # limit with pk, count
                count = min(max_count, count)  # limit with entry count
                if count == max_count:  # get all entries
                    entries = Entry.objects.all()
                else:
                    random_list = []
                    while len(random_list) < count:
                        id = random.choice(ids)
                        ids.remove(id)
                        random_list.append(id)
                    entries = Entry.objects.filter(pk__in=random_list).get()
                    print(entries)
                    print("----------------------------")
                # timeout - in seconds (5 minutes)
                cache.set('random_entries', entries, timeout=300)
            else:
                entries = None
        print(entries)
        if entries:
            entries = self.get_is_fav_attr_entry(entries, request.user)
            entries = entries.order_by('?')  # shuffle
            self.context["entries"] = entries
        self.context['show_title'] = True
        return render(request, 'home_page.html', self.context)


class TitleView(BaseView):
    def get(self, request, title_id):
        super().get(request)

        title = Title.objects.filter(pk=title_id).first()
        if not title:
            return redirect('app:not-found')

        self.context['title'] = title
        title_entries = Entry.objects.filter(title=title.text)
        title_entries = title_entries.order_by('created_at')
        title_entries = self.set_entries_for_title_page(title_entries, request)
        print("------------")
        print(title_entries)
        print("------------")

        is_follow = False
        if request.user.is_authenticated:
            follow_title = FollowTitle.objects.filter(
                title=title, author=request.user).first()
            if follow_title:
                is_follow = True
                follow_title.save()  # update the last seen

        self.context['is_follow'] = is_follow
        self.context['order_choices'] = ORDER_CHOICES
        self.context['before_entry_count'] = 0
        return render(request, 'title_page.html', self.context)


class LatestTitleView(TitleView):
    def get(self, request, title_id):
        super().get(request, title_id)
        title = self.context['title']
        title_entries = Entry.objects.filter(title=title)
        entries = title_entries.filter(created_at__day=timezone.now().day)
        before_entry_count = title_entries.filter(
            created_at__day__lt=timezone.now().day).count()
        self.set_entries_for_title_page(entries, request)
        self.context["before_entry_count"] = before_entry_count
        return render(request, 'title_page.html', self.context)


class FollowTitleView(AuthMixin, BaseView):
    def post(self, request):
        title_id = request.POST.get('title_id')
        user = request.user

        try:
            title = Title.objects.filter(pk=title_id).first()
            if not title:  # title check
                return JsonResponse(
                    {'success': False, 'error': "there is no title"})

            is_follow = False
            follow = FollowTitle.objects.filter(
                title=title, author=user).first()

            if follow:  # is follow check
                follow.delete()
            else:
                is_follow = True
                FollowTitle(title=title, author=user).save()
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': True, 'is_follow': is_follow})

    def get(self, request):
        super().get(request)

        follows = FollowTitle.objects.filter(author=request.user)
        title_ids = follows.values_list('title_id', flat=True)
        titles = Title.objects.filter(pk__in=title_ids)
        titles = titles.annotate(entries_count=Count(
            'entry',
            filter=Q(entry__created_at__gt=F('followtitle__last_seen')) &
            Q(followtitle__author=request.user),
            distinct=True))
        self.set_pagination(titles.order_by('-entries_count'), request)
        return render(request, 'followed_titles_page.html', self.context)


class FollowedTitleEntries(AuthMixin, BaseView):
    def get(self, request, title_id):

        super().get(request)

        title = Title.objects.filter(pk=title_id).first()
        follow = FollowTitle.objects.filter(
            title=title, author=request.user).first()
        if title and follow:
            self.context['title'] = title
            title_entries = Entry.objects.filter(title=title)
            entries = title_entries.filter(
                created_at__gt=follow.last_seen).order_by('-created_at')
            before_entry_count = title_entries.count() - entries.count()
            self.context['before_entry_count'] = before_entry_count
            follow.save()  # update last seen
            if entries.exists():
                before_entry_count = title_entries.filter(
                    created_at__lte=follow.last_seen).count()
                self.set_entries_for_title_page(entries, request)
                self.context['before_entry_count'] = before_entry_count
                return render(request, 'title_page.html', self.context)
            return redirect('app:title', title_id)  # no entry show all
        else:
            return render('app:not-found')


class FollowView(AuthMixin, BaseView):
    def get(self, request):
        super().get(request)

        follows = FollowAuthor.objects.filter(user=request.user)
        author_ids = follows.values_list('follow_id', flat=True)
        query = int(request.GET.get('query', 1))

        if (query == 1):
            entries = Entry.objects.filter(author_id__in=author_ids)
        else:
            favs = AuthorsFavorites.objects.filter(
                author__in=author_ids).values_list('entry_id', flat=True)
            entries = Entry.objects.filter(uid__in=favs)

        entries = self.get_is_fav_attr_entry(entries, request.user)

        self.context['entries'] = entries.order_by('-created_at')
        self.context['show_title'] = True

        # ajax request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'components/entries.html', self.context, request=request)
            return JsonResponse({'html': html})
        else:
            return render(request, 'follow_page.html', self.context)


class OrderView(BaseView):
    context = {}

    def get(self, request, title_id, query):
        super().get(request)

        title = Title.objects.get(pk=title_id)
        self.context['title'] = title
        title_entries = Entry.objects.filter(title=title)
        title_entries = self.get_fav_counts_entry(title_entries)
        title_entries = self.set_entries_for_title_page(title_entries, request)

        if (query == 1):  # order by vote
            title_entries = title_entries.annotate(
                vote_diff=(F('up_votes_count') - F('down_votes_count')))
            title_entries = title_entries.order_by('-vote_diff')
        elif (query == 2):  # order by fav
            title_entries = title_entries.order_by('-fav_count')
        elif (query == 3):  # order by created at - first
            title_entries = title_entries.order_by('created_at')
        elif (query == 4):  # order by created at - last
            title_entries = title_entries.order_by('-created_at')
        else:
            title_entries = title_entries.order_by('?')

        self.context['order_choices'] = ORDER_CHOICES
        self.context['selected_choice'] = ORDER_CHOICES[query-1]
        self.set_pagination(title_entries, request)
        return render(request, 'title_page.html', self.context)


# pagination
class TodayView(BaseView):
    def get(self, request):
        super().get(request)

        query = int(request.GET.get('query', 1))

        if query == 1:
            entries = Entry.objects.filter(
                created_at__day=timezone.now().day).order_by('-pk')
            entries = self.get_is_fav_attr_entry(entries, request.user)
            self.set_pagination(entries, request)
        else:
            titles = Title.objects.filter(created_at__day=timezone.now().day)
            titles = titles.order_by('-created_at')
            self.set_pagination(titles, request)

        self.context['show_title'] = True
        self.context['is_entries'] = (query == 1)

        # ajax request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if query == 1:
                html = render_to_string(
                    'components/paginated_entries.html',
                    self.context,
                    request=request)
                return JsonResponse({'html': html, 'page': 1})
            else:
                html = render_to_string(
                    'components/paginated_titles.html',
                    self.context,
                    request=request)
                return JsonResponse({'html': html, 'page': 2})
        print('is_entries:', self.context['is_entries'])
        return render(request, 'today_page.html', self.context)


class LDMVViews(CacheHeaderMixin, BaseView):
    context = {}

    def get(self, request):
        super().get(request)
        LDMV_COUNT = 5
        yesterday = (timezone.now() - timezone.timedelta(days=1)).day
        entries = Entry.objects.filter(created_at__day=yesterday)
        entries = self.get_vote_counts_entry(entries)
        entries = self.get_fav_counts_entry(entries)
        entries = self.get_is_fav_attr_entry(entries, request.user)
        entries = entries.annotate(
            vote_point=(
                (F('up_votes_count') * 5) +
                (F('down_votes_count') * -1) +
                (F('fav_count') * 2)))
        self.context['entries'] = entries.order_by('-vote_point')[:LDMV_COUNT]
        self.context['show_title'] = True
        return render(request, 'home_page.html', self.context)


# pagination
class LatestView(BaseView):
    def get(self, request):
        super().get(request)
        titles = Title.objects.all()
        title_entry_counts = {}
        for title in titles:
            count = Entry.objects.filter(title=title.text).count()
            title_entry_counts[title] = count

        sorted_count = sorted(
            title_entry_counts.items(),
            key=lambda x: x[1],
            reverse=True)
        latest_titles = [title for title, count in sorted_count[:25]]
        self.context['title_entry_counts'] = title_entry_counts
        self.set_pagination(latest_titles, request)
        return render(request, 'latest_page.html', self.context)


class ProfileView(BaseView):
    def get(self, request, author_id, query=0):
        super().get(request)

        # distinct=True meaning is each unique row is only counted once.
        print("here :)")

        author = Author.objects.filter(pk=author_id).first()
        if not author:
            return redirect('app:not-found')

        print("db fetch user stats")
        author.entry_count = Entry.objects.filter(author=author).count()
        author.title_count = Title.objects.filter(owner=author).count()
        author.follower_count = FollowAuthor.objects.filter(
            follow=author).count()
        entry_ids = Entry.objects.filter(
            author=author).values_list('uid', flat=True)
        author.vote_count = Vote.objects.filter(
            entry_id__in=entry_ids).count()
        author.up_vote_count = Vote.objects.filter(
            entry_id__in=entry_ids,
            is_up=True).count()
        author.save()
        vote_ratio = 0
        if author.vote_count:
            vote_ratio = author.up_vote_count * 100 / author.vote_count
        self.context['vote_ratio'] = "{:.2f}".format(vote_ratio)

        self.context['author'] = author

        follow = 0  # can follow
        if (not request.user.is_authenticated):
            follow = -1  # there is no user logged in
        elif (request.user == author):
            follow = 1  # same person
        else:
            follow_author = FollowAuthor.objects.filter(
                user=request.user, follow=author).first()
            if follow_author:  # exist check
                self.context['follow_date'] = follow_author.follow_date
                follow = 2  # already follower
            else:
                follow = 0  # can follow
        self.context['follow'] = follow

        query = int(query)
        if query == 1:
            user_entries = Entry.objects.filter(author=author)
            user_entries = self.get_is_fav_attr_entry(
                user_entries, request.user).order_by('-pk')
            self.set_pagination(user_entries, request)
        elif query == 2:
            user_titles = Title.objects.filter(
                owner=author).order_by('-pk')
            self.set_pagination(user_titles, request)
        elif query == 3:
            follows = FollowAuthor.objects.filter(follow=author)
            follower_ids = follows.values_list('user_id', flat=True)
            followers = Author.objects.filter(pk__in=follower_ids)
            followers = followers.order_by("username")
            self.set_pagination(followers, request)
        else:
            self.context['page_obj'] = None
        self.context['show_title'] = True
        self.context['query'] = query

        return render(request, 'profile_page.html', self.context)


class FollowUserView(AuthMixin, BaseView):
    def get(self, request, follow_id):
        follow = Author.objects.filter(pk=follow_id).first()
        if follow:
            FollowAuthor(user=request.user, follow=follow).save()
            return redirect('app:profile', follow_id)
        else:
            return redirect('app:index')


class UnFollowUserView(View):
    def get(self, request, follow_id):
        follow = Author.objects.filter(pk=follow_id).first()
        if not follow:
            return redirect('app:not-found')

        follow_author = FollowAuthor.objects.filter(
            user=request.user, follow=follow).first()
        if follow_author:
            follow_author.delete()

        return redirect('app:profile', follow_id)


class NewTitleView(AuthMixin, BaseView):
    form = TitleForm()

    def post(self, request):

        form = TitleForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['title']
            topic = form.cleaned_data['topic']
            entry_content = form.cleaned_data['entry_content']
            title = Title(text=text, topic=topic, owner=request.user)
            title.save()
            entry = Entry(
                content=entry_content,
                author=request.user.username,
                title=title.text)
            entry.save()
            return redirect('app:index')
        else:
            self.context['form'] = form
            return render(request, 'new_title_page.html', self.context)

    def get(self, request):
        super().get(request)

        form = TitleForm()
        self.context['form'] = form
        return render(request, 'new_title_page.html', self.context)


class TopicView(BaseView):
    def get(self, request, topic_id):
        super().get(request)
        topic = Topic.objects.filter(pk=topic_id).first()
        if not topic:
            return redirect('app:not-found')

        titles = Title.objects.filter(topic=topic)
        self.context['topic'] = topic
        self.context['titles'] = titles
        return render(request, 'topic_title_page.html', self.context)


class NotFoundView(View):
    context = {}

    def get(self, request):
        return render(request, '404.html', self.context)


class SettingsView(AuthMixin, BaseView):
    form = SettingsForm()

    def post(self, request):
        form = SettingsForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.cleaned_data['profile_image']
            title_entry_count = form.cleaned_data['title_entry_count']
            random_entry_count = form.cleaned_data['random_entry_count']
            # check img is new
            if (request.user.profile_image != img and img != 'default.jpg'):
                request.user.profile_image = img
            request.user.title_entry_count = title_entry_count
            request.user.random_entry_count = random_entry_count
            request.user.save()
            return redirect('app:profile', request.user.id)
        self.context['form'] = form
        return render(request, 'settings_page.html', self.context)

    def get(self, request):
        super().get(request)

        initial = {
            'random_entry_count': request.user.random_entry_count,
            'title_entry_count': request.user.title_entry_count,
            'profile_image': request.user.profile_image
        }
        form = SettingsForm(initial=initial)
        self.context['form'] = form
        return render(request, 'settings_page.html', self.context)


class SearchView(View):
    def get(self, request):
        query = request.GET.get('query')
        result_data = []
        if query:
            topics = search_topics(query)
            titles = search_titles(query)
            authors = search_authors(query)
            if not titles:
                titles = Title.objects.filter(text__istartswith=query)
            if not authors:
                authors = Author.objects.filter(username__istartswith=query)
            for topic in topics:
                result_data.append(
                    {
                        'id': topic.id,
                        'text': topic.text,
                        'category': 0
                    }
                )
            for title in titles:
                result_data.append(
                    {
                        'id': title.id,
                        'text': title.text,
                        'category': 1
                    }
                )
            for author in authors:
                result_data.append(
                    {
                        'id': author.id,
                        'text': author.username,
                        'category': 2
                    }
                )
            result_data = sorted(result_data, key=lambda d: d['text'])

        return JsonResponse({'status': True, 'data': result_data})


class ReportView(AuthMixin, BaseView):
    def post(self, request, entry_id):
        entry = Entry.objects.filter(uid=entry_id).first()
        if not entry:
            return redirect('app:not-found')
        self.context['entry'] = entry

        form = ReportForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            report = Report(description=text,
                            entry_id=entry.uid,
                            user=request.user)
            report.save()
            return redirect('app:index')
        else:
            self.context['form'] = form
            return render(request, 'add_report_page.html', self.context)

    def get(self, request, entry_id):
        super().get(request)

        entry = Entry.objects.filter(uid=entry_id).first()
        if not entry:
            return redirect('app:not-found')
        self.context['entry'] = entry

        form = ReportForm()
        self.context['form'] = form
        return render(request, 'add_report_page.html', self.context)


class AllReportsView(BaseView):
    def get(self, request):
        super().get(request)
        if not request.user.is_staff:
            return redirect('authentication:login')
        reports = Report.objects.order_by('date')
        self.set_pagination(reports, request)
        return render(request, 'all_reports_page.html', self.context)


class ReportDeleteView(BaseView):
    def post(self, request):
        # check user
        if not request.user.is_staff:
            return redirect('authentication:login')

        super().get(request)

        report_id = request.POST.get('report_id')
        query = int(request.POST.get('query'))
        report = Report.objects.filter(pk=report_id).first()

        if report:
            if query == 0:
                report.delete()
            elif query == 1:
                report.entry.delete()
            elif query == 2:
                author = report.entry.author.delete()
                report.entry.delete()
                author.delete()
            else:
                return JsonResponse(
                    {'success': False, 'error': 'incorrect qeury'})
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'report does not exist'})


class AIView(BaseView):
    def get(self, request, query):
        if request.user.username != 'bot':
            return redirect('authentication:login')
        super().get(request)

        if query == 0:  # new title and entries
            form = AINewTitleForm()
        elif query == 1:  # new entries to existing tile
            form = AINewEntryForm()
        elif query == 2:  # new entries to given entry tilte and style
            form = AINewEntriesLikeAnEntry()
        self.context['form'] = form
        self.context['query'] = query

        return render(request, 'ai_page.html', self.context)

    def post(self, request, query):
        if request.user.username != 'bot':
            return redirect('authentication:login')

        ai = AI()
        if query == 0:  # new title and entries
            self.context['title'] = None
            form = AINewTitleForm(request.POST)
            if form.is_valid():
                title_count = form.cleaned_data['title_count']
                entry_count = form.cleaned_data['entry_per_title_count']
                print('task')
                create_ai_title_task.delay_on_commit(
                    title_count,
                    entry_count)
            else:
                self.context['form'] = form
                return render(request, 'ai_page.html', self.context)
        elif query == 1:  # new entries to existing title
            form = AINewEntryForm(request.POST)
            if form.is_valid():
                form_title = form.cleaned_data['title_id']
                entry_count = form.cleaned_data['entry_count']
                title = Title.objects.filter(pk=form_title).first()
                if title:
                    entry_res = ai.get_new_entries_to_title(
                            title, entry_count)
                    for res in entry_res:
                        create_entry(res, request.user, title)
            else:
                self.context['form'] = form
                return render(request, 'ai_page.html', self.context)
        elif query == 2:
            form = AINewEntriesLikeAnEntry(request.POST)
            self.context['form'] = form
            if form.is_valid():
                entry_id = form.cleaned_data['entry_id']
                form_title = form.cleaned_data['title_id']
                entry_count = form.cleaned_data['entry_count']
                entry = Entry.objects.filter(uid=entry_id).first()
                title = Title.objects.filter(pk=form_title).first()
                if title and entry:
                    entry_res = ai.get_entries_like_an_entry(
                        title, entry, entry_count)
                    for res in entry_res:
                        create_entry(res, request.user, title)
            else:
                return render(request, 'ai_page.html', self.context)
        return redirect('app:today')


class SpammerView(AuthMixin, BaseView):
    def get(self, request):
        if request.user.username != 'bot':
            return redirect('authentication:login')
        super().get(request)
        form = NewTitleForm()
        self.context['form'] = form

        return render(request, 'spam_page.html', self.context)

    def post(self, request):
        if request.user.username != 'bot':
            return redirect('authentication:login')

        form = NewTitleForm(request.POST)
        if form.is_valid():
            title_count = form.cleaned_data['title_count']
            entry_count = form.cleaned_data['entry_per_title_count']
            print('task')
            res = create_random_entries_task.delay(
                title_count,
                entry_count)
            result = AsyncResult(res.id)
            print("state:", result.state)
        else:
            self.context['form'] = form
            return render(request, 'ai_page.html', self.context)
        return redirect('app:today')


class NewTopicView(AuthMixin, BaseView):
    def get(self, request):
        if not request.user.is_staff:
            return redirect('login')
        super().get(request)

        form = NewTopicForm()
        self.context['form'] = form
        return render(request, 'new_topic_page.html', self.context)

    def post(self, request):
        if not request.user.is_staff:
            return redirect('login')

        form = NewTopicForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            topic = Topic(text=text, created_by=request.user)
            topic.save()
            return redirect('app:index')
        else:
            self.context['form'] = form
            return render(request, 'new_topic_page.html', self.context)
