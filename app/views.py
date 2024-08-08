from django.contrib.auth import authenticate, login, logout
from django.db.models import Max, Count, Q, F, ExpressionWrapper, Value
from django.db.models import FloatField, Case, When, BooleanField
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views import View
import random

from .models import Title, Entry, Author, Vote, Topic, Report
from .models import AuthorsFavorites, FollowTitle, FollowAuthor
from .forms import LoginForm, SignupForm, SettingsForm
from .forms import EntryForm, TitleForm, ReportForm
from .constants import ORDER_CHOICES


# user can choose random entry count max count is 50
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
            user_ids = follows.values_list('user_id', flat='anonymous')
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
        if (user.is_authenticated):
            return base_manager.annotate(
                is_fav=Case(
                    When(authorsfavorites__author=user, then=Value(True)),
                    default=Value(False), output_field=BooleanField()))
        else:
            return base_manager

    def get_vote_counts_entry(self, base_manager):
        return base_manager.annotate(
            up_votes_count=Count('vote', filter=Q(vote__is_up=True)),
            down_votes_count=Count('vote', filter=Q(vote__is_up=False)),
        )

    def get_fav_counts_entry(self, base_manager):
        return base_manager.annotate(fav_count=Count('authorsfavorites'))

    def check_and_redirect_to_login(self, request):
        if not request.user.is_authenticated:
            return redirect('app:login')

    def set_pagination(self, base_manager, request):
        paginator = Paginator(base_manager, self.ENTRY_COUNT)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        self.context['page_obj'] = page_obj

    def set_entries_for_title_page(self, base_manager, request):
        self.get_entry_count(request)
        title_entries = self.get_is_fav_attr_entry(base_manager, request.user)
        title_entries = self.get_vote_counts_entry(title_entries)
        title_entries = title_entries.order_by('created_at')
        self.set_pagination(title_entries, request)

        self.context['show_title'] = False
        return title_entries

    def redirect_to_not_found(self, object):
        if not object:
            return redirect('app:not-found')


class HomeView(BaseView):
    def get(self, request):
        super().get(request)
        self.get_entry_count(request, is_title=False)

        pk_max = Entry.objects.all().aggregate(pk_max=Max("pk"))['pk_max']
        if (pk_max):
            count = min(pk_max, self.ENTRY_COUNT)  # limit with pk, count
            random_list = random.sample(range(1, pk_max+1), count)
            entries = Entry.objects.filter(pk__in=random_list)
            entries = self.get_is_fav_attr_entry(entries, request.user)
            entries = entries.order_by('?')
            self.context["entries"] = entries
        self.context['show_title'] = True
        return render(request, 'home_page.html', self.context)


class TitleView(BaseView):
    def get(self, request, title_id):
        super().get(request)

        title = Title.objects.filter(pk=title_id).first()
        self.redirect_to_not_found(title)

        self.context['title'] = title
        title_entries = Entry.objects.filter(title=title)
        title_entries = self.set_entries_for_title_page(title_entries, request)

        is_follow = False
        if request.user.is_authenticated:
            follow_title = FollowTitle.objects.filter(
                title=title, author=request.user).first()
            if follow_title:
                is_follow = True
                follow_title.save()  # update the last seen

        self.context['is_follow'] = is_follow
        self.context['order_choices'] = ORDER_CHOICES
        return render(request, 'title_page.html', self.context)


class LatestTitleView(TitleView):
    def get(self, request, title_id):
        super().get(request, title_id)
        title = self.context['title']
        title_entries = Entry.objects.filter(
            title=title, created_at__day=timezone.now().day)
        self.set_entries_for_title_page(title_entries, request)

        return render(request, 'title_page.html', self.context)


class FollowedTitleView(BaseView):
    def post(self, request):
        self.check_and_redirect_to_login(request)

        title_id = request.POST.get('title_id')
        user = request.user

        try:
            title = Title.objects.filter(pk=title_id).first()
            if not title:  # title check
                return JsonResponse(
                    {'success': False, 'error': "there is no title"})

            follow = FollowTitle.objects.filter(
                title=title, author=user).first()

            if follow:  # is follow check
                follow.delete()
            else:
                FollowTitle(title=title, author=user).save()
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': True})

    def get(self, request):
        self.check_and_redirect_to_login(request)
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


class FollowedTitleEntries(BaseView):
    def get(self, request, title_id):
        super().get(request)
        self.check_and_redirect_to_login(request)

        title = Title.objects.filter(pk=title_id).first()
        follow = FollowTitle.objects.filter(
            title=title, author=request.user).first()
        if title and follow:
            self.context['title'] = title
            entries = Entry.objects.filter(
                title=title, created_at__gt=follow.last_seen
                ).order_by('-created_at')
            follow.save()  # update last seen
            if entries.exists():
                self.set_entries_for_title_page(entries, request)
                return render(request, 'title_page.html', self.context)
            return redirect('app:title', title_id)  # no entry show all
        else:
            return render('app:not-found')


class FollowView(BaseView):
    context = {}

    def get(self, request):
        self.check_and_redirect_to_login(request)
        super().get(request)

        follows = FollowAuthor.objects.filter(user=request.user)
        author_ids = follows.values_list('follow_id', flat=True)
        query = int(request.GET.get('query', 1))

        if (query == 1):
            entries = Entry.objects.filter(author_id__in=author_ids)
        else:
            entries = Entry.objects.filter(
                authorsfavorites__author__in=author_ids)

        entries = entries.annotate(is_fav=Case(
                When(authorsfavorites__author=request.user, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()))
        self.context['entries'] = entries.order_by('-created_at')
        self.context['show_title'] = True

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'components/entries.html', self.context, request=request)
            return JsonResponse({'html': html})
        else:
            return render(request, 'follow_page.html', self.context)


class FavView(BaseView):
    context = {}

    def get(self, request):
        self.check_and_redirect_to_login(request)
        super().get(request)

        entries = Entry.objects.filter(
            authorsfavorites__author=request.user
            ).annotate(is_fav=Value(True, output_field=BooleanField()))
        self.context['entries'] = entries.order_by('-created_at')
        self.context['show_title'] = True

        return render(request, 'home_page.html', self.context)


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
        return render(request, 'title_page.html', self.context)


# pagination
class TodayView(BaseView):
    context = {}

    def get(self, request):
        super().get(request)

        titles = Title.objects.filter(created_at__day=timezone.now().day)
        titles = titles.order_by('-created_at')
        entries = Entry.objects.filter(
            created_at__day=timezone.now().day).order_by('-created_at')

        query = int(request.GET.get('query', 1))
        if query == 1:
            entries = self.get_is_fav_attr_entry(entries, request.user)
            self.set_pagination(entries, request)
        else:
            self.set_pagination(titles, request)

        self.context['show_title'] = True

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if query == 1:
                html = render_to_string(
                    'components/entries.html', self.context, request=request)
            else:
                html = render_to_string(
                    'components/titles.html', self.context, request=request)
            return JsonResponse({'html': html})
        return render(request, 'today_page.html', self.context)


class LDMVViews(BaseView):
    context = {}

    def get(self, request):
        super().get(request)
        LDMV_COUNT = 5
        yesterday = (timezone.now() - timezone.timedelta(days=1)).day
        entries = Entry.objects.filter(created_at__day=yesterday)
        entries = self.get_vote_counts_entry(entries)
        entries = self.get_fav_counts_entry(entries)
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
        titles = Title.objects.annotate(
            entries_count=Count(
                'entry',
                filter=Q(entry__created_at__day=timezone.now().day),
                distinc=True))
        titles = titles.order_by('-entries_count')[:25]
        self.set_pagination(titles, request)
        return render(request, 'latest_page.html', self.context)


class ProfileView(BaseView):
    def get(self, request, author_id, query=0):
        super().get(request)

        # distinct=True meaning is each unique row is only counted once.
        author = Author.objects.filter(
            pk=author_id
        ).annotate(
            entry_count=Count('entry', distinct=True),
            title_count=Count('title', distinct=True),
            follower_count=Count('followers', distinct=True),
            total_votes=Count('entry__vote', distinct=True),
            up_votes=Count('entry__vote',
                           filter=Q(entry__vote__is_up=True), distinct=True),
            ).annotate(
                upvote_ratio=ExpressionWrapper(
                    (F('up_votes') * 100 / F('total_votes')),
                    output_field=FloatField())).first()
        self.redirect_to_not_found(author)

        if author.total_votes == 0:
            author.upvote_ratio = 0
        self.context['author'] = author

        follow = 0  # can follow
        if (not request.user.is_authenticated):
            follow = -1  # there is no user logged in
        elif (request.user == author):
            follow = 1  # same person
        else:
            try:
                follow_author = FollowAuthor.objects.get(
                    user=request.user, follow=author)
                self.context['follow_date'] = follow_author.follow_date
                follow = 2  # already follower
            except FollowAuthor.DoesNotExist:
                follow = 0
        self.context['follow'] = follow

        query = int(query)
        if query == 1:
            user_entries = Entry.objects.filter(author=author)
            user_entries = self.get_is_fav_attr_entry(
                user_entries, request.user).order_by(
                    '-created_at')
            self.set_pagination(user_entries, request)
        elif query == 2:
            user_titles = Title.objects.filter(
                owner=author).order_by('created_at')
            self.set_pagination(user_titles, request)
        elif query == 3:
            follows = FollowAuthor.objects.filter(follow=author)
            follower_ids = follows.values_list('user_id', flat=True)
            followers = Author.objects.filter(pk__in=follower_ids)
            self.set_pagination(followers, request)
        else:
            self.context['page_obj'] = None
        self.context['show_title'] = True
        self.context['query'] = query

        return render(request, 'profile_page.html', self.context)


class SignupView(View):
    form = SignupForm()

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            if (request.user.is_authenticated):
                logout(request)
            # form auto hash the password but authenticated wants to raw pass
            author = form.save(commit=False)
            password = form.cleaned_data['password1']
            author.save()
            user = authenticate(request,
                                username=author.username,
                                password=password)
            if user:
                login(request, user)
            return redirect('app:index')
        else:
            form = SignupForm(request.POST)
            return render(request, 'signup_page.html', {'form': form})

    def get(self, request):
        form = SignupForm()
        return render(request, 'signup_page.html', {'form': form})


class LoginView(View):
    form = LoginForm()

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('app:index')
            else:
                message = 'login error, username or password is incorrect.'
                messages.warning(request, message)
                return render(request, 'login_page.html', {'form': form})
        else:
            return render(request, 'login_page.html', {'form': form})

    def get(self, request):
        form = LoginForm()
        return render(request, 'login_page.html', {'form': form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('app:login')


class FollowUserView(View):
    def get(self, request, follow_id):
        try:
            follow = Author.objects.get(pk=follow_id)
            FollowAuthor(user=request.user, follow=follow).save()
            return redirect('app:profile', follow_id)
        except Author.DoesNotExist:
            return redirect('app:index')


class UnFollowUserView(View):
    def get(self, request, follow_id):
        try:
            follow = Author.objects.get(pk=follow_id)
            follow_author = FollowAuthor.objects.get(
                user=request.user, follow=follow)
            follow_author.delete()
            return redirect('app:profile', follow_id)
        except Author.DoesNotExist:
            return redirect('app:index')
        except FollowAuthor.DoesNotExist:
            return redirect('app:profile', follow_id)


class VoteView(View):
    def post(self, request):
        entry_id = request.POST.get('entry_id')
        vote_is_up = request.POST.get('is_up') == '1'
        vote = Vote.objects.filter(entry_id=entry_id, voter=request.user)
        vote = vote.first()
        if vote:
            if (not vote.is_up) and vote_is_up:
                vote.is_up = True
                vote.save()
            elif vote.is_up and (not vote_is_up):
                vote.is_up = False
                vote.save()
        else:
            vote = Vote(
                entry_id=entry_id, voter=request.user, is_up=vote_is_up)
        vote.save()
        up_votes_count = Vote.objects.filter(
            entry_id=entry_id, is_up=True).count()
        down_votes_count = Vote.objects.filter(
            entry_id=entry_id, is_up=False).count()

        return JsonResponse({
            'success': True,
            'up_votes_count': up_votes_count,
            'down_votes_count': down_votes_count,
        })


class FavEntryView(View):
    def post(self, request):
        entry_id = request.POST.get('entry_id')
        user = request.user
        try:
            favorite = AuthorsFavorites.objects.filter(
                entry_id=entry_id, author=user).first()
            if favorite:
                favorite.delete()
                is_favorite = False
            else:
                AuthorsFavorites(entry_id=entry_id, author=user).save()
                is_favorite = True
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': True, 'is_favorite': is_favorite})


class NewTitleView(BaseView):
    form = TitleForm()

    def post(self, request):
        self.check_and_redirect_to_login(request)

        form = TitleForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['title']
            topic = form.cleaned_data['topic']
            entry_content = form.cleaned_data['entry_content']
            title = Title(text=text, topic=topic, owner=request.user)
            title.save()
            entry = Entry(
                content=entry_content, author=request.user, title=title)
            entry.save()
            return redirect('app:index')
        else:
            return render(request, 'new_title_page.html', {'form': form})

    def get(self, request):
        super().get(request)
        form = TitleForm()
        return render(request, 'new_title_page.html', {'form': form})


class TopicView(BaseView):
    context = {}

    def get(self, request, topic_id):
        super().get(request)
        topic = Topic.objects.filter(pk=topic_id).first()
        self.redirect_to_not_found(topic)

        titles = Title.objects.filter(topic=topic)
        self.context['topic'] = topic
        self.context['titles'] = titles
        return render(request, 'topic_title_page.html', self.context)


class NewEntryView(BaseView):

    def get(self, request, title_id):
        super().get(request)
        title = Title.objects.filter(pk=title_id).first()
        if not title:
            return redirect('app:index')

        form = EntryForm(request.POST)
        return render(request, 'new_entry_page.html', {
            'form': form,
            'title': title
            })

    def post(self, request, title_id):
        self.check_and_redirect_to_login(request)

        title = Title.objects.filter(pk=title_id).first()  # check title
        if not title:
            return redirect('app:index')

        form = EntryForm(request.POST)
        if form.is_valid():
            entry_content = form.cleaned_data['content']
            entry = Entry.objects.filter(
                author=request.user,
                title=title,
                content__contains=entry_content).first()
            if entry:
                message = 'you already wrote like this.'
                messages.warning(request, message)
                return render(request, 'new_entry_page.html', {'form': form})
            else:
                Entry(
                    content=entry_content,
                    author=request.user,
                    title=title).save()
                return redirect('app:title', title_id)
        return render(request, 'new_entry_page.html', {
                    'form': form,
                    'title': title
                    })


class DeleteEntryView(BaseView):
    def post(self, request):
        self.check_and_redirect_to_login(request)
        super().get(request)

        entry_id = request.POST.get('entry_id')
        if request.user.is_staff:
            entry = Entry.objects.filter(pk=entry_id).first()
        else:
            entry = Entry.objects.filter(
                pk=entry_id, author=request.user).first()
        if entry:
            entry.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'Entry does not exist, or the author is not valid'})


class EntryEditView(BaseView):
    def get(self, request, entry_id):
        super().get(request)

        entry = Entry.objects.filter(pk=entry_id).first()
        if not entry:
            return redirect('app:index')

        form = EntryForm(initial={'content': entry.content})
        return render(request, 'new_entry_page.html', {
            'form': form, 'title': entry.title})

    def post(self, request, entry_id):
        self.check_and_redirect_to_login(request)

        form = EntryForm(request.POST)
        if form.is_valid():
            entry_content = form.cleaned_data['content']
            entry = Entry.objects.filter(
                pk=entry_id, author=request.user).first()
            if not entry:
                message = 'you already wrote like this.'
                messages.warning(request, message)
                return render(request, 'new_entry_page.html', {'form': form})
            else:
                entry.content = entry_content
                entry.save()
                return redirect('app:title', entry.title.id)
        return render(request, 'new_entry_page.html',
                      {'form': form, 'title': entry.title})


class EntryView(BaseView):
    context = {}

    def get(self, request, entry_id):
        super().get(request)

        entry = Entry.objects.filter(pk=entry_id)
        self.redirect_to_not_found(entry)
        entry = self.get_is_fav_attr_entry(entry, request.user)
        entry = self.get_vote_counts_entry(entry)
        self.context["entries"] = [entry.first()]
        self.context['show_title'] = True
        return render(request, 'home_page.html', self.context)


class NotFoundView(View):
    context = {}

    def get(self, request):
        return render(request, 'not_found_page.html', self.context)


class SettingsView(BaseView):
    context = {}
    form = SettingsForm()

    def post(self, request):
        self.check_and_redirect_to_login(request)
        form = SettingsForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.cleaned_data['profile_image']
            title_entry_count = form.cleaned_data['title_entry_count']
            random_entry_count = form.cleaned_data['random_entry_count']
            if (request.user.profile_image != img and img != 'default.jpg'):
                request.user.profile_image = img
            request.user.title_entry_count = title_entry_count
            request.user.random_entry_count = random_entry_count
            request.user.save()
            return redirect('app:profile', request.user.id)
        return render(request, 'settings_page.html', {'form': form})

    def get(self, request):
        self.check_and_redirect_to_login(request)
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
            titles = Title.objects.filter(text__startswith=query)
            for title in titles:
                result_data.append(
                    {
                        'id': title.id,
                        'text': title.text,
                        'is_title': True
                    }
                )
            authors = Author.objects.filter(username__startswith=query)
            for author in authors:
                result_data.append(
                    {
                        'id': author.id,
                        'text': author.username,
                        'is_title': False
                    }
                )
            result_data = sorted(result_data, key=lambda d: d['text'])

        return JsonResponse({'status': True, 'data': result_data})


class ReportView(BaseView):
    def post(self, request, entry_id):
        self.check_and_redirect_to_login(request)

        entry = Entry.objects.filter(pk=entry_id).first()
        self.redirect_to_not_found(entry)
        self.context['entry'] = entry

        form = ReportForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            report = Report(description=text, entry=entry, user=request.user)
            report.save()
            return redirect('app:index')
        else:
            return render(request, 'add_report_page.html', {'form': form})

    def get(self, request, entry_id):
        super().get(request)
        print("getttt")
        self.check_and_redirect_to_login(request)

        entry = Entry.objects.filter(pk=entry_id).first()
        self.redirect_to_not_found(entry)
        self.context['entry'] = entry

        form = ReportForm()
        self.context['form'] = form
        return render(request, 'add_report_page.html', self.context)


class SeeReportsView(BaseView):
    def get(self, request):
        super().get(request)
        self.redirect_to_not_found(request.user.is_staff)
        reports = Report.objects.order_by('date')
        self.set_pagination(reports, request)
        return render(request, 'all_reports_page.html', self.context)


class ReportDeleteView(BaseView):
    def post(self, request):
        # check user
        self.redirect_to_not_found(request.user.is_staff)
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
                report.entry.author.delete()
            else:
                return JsonResponse(
                    {'success': False, 'error': 'incorrect qeury'})
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'report does not exist'})
