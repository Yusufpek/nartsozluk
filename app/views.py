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

from .models import Title, Entry, Author, FollowAuthor, Vote, AuthorsFavorites
from .forms import LoginForm, SignupForm, TitleForm, EntryForm
from .constants import ORDER_CHOICES


# user can choose random entry count max count is 50
class HomeView(View):
    context = {}

    def get(self, request):
        HOME_ENTRY_COUNT = 10
        if request.user.is_authenticated:
            HOME_ENTRY_COUNT = request.user.random_entry_count
        pk_max = Entry.objects.all().aggregate(pk_max=Max("pk"))['pk_max']
        if (pk_max):
            count = min(pk_max, HOME_ENTRY_COUNT)  # limit with pk and count
            random_list = random.sample(range(1, pk_max+1), count)
            if request.user.is_authenticated:
                entries = Entry.objects.annotate(
                    is_fav=Case(When(
                        authorsfavorites__author=request.user,
                        then=Value(True)),
                        default=Value(False), output_field=BooleanField())
                    ).filter(pk__in=random_list).order_by('?')
            else:
                entries = Entry.objects.filter(
                    pk__in=random_list).order_by('?')
            self.context["entries"] = entries
        self.context['show_title'] = True
        return render(request, 'home_page.html', self.context)


class TitleView(View):
    context = {}

    def get(self, request, title_id):
        ENTRY_COUNT = 10
        if request.user.is_authenticated:
            ENTRY_COUNT = request.user.title_entry_count

        title = Title.objects.get(pk=title_id)
        self.context['title'] = title
        title_entries = Entry.objects.filter(title=title)
        if request.user.is_authenticated:
            title_entries = title_entries.annotate(
                is_fav=Case(
                    When(authorsfavorites__author=request.user,
                         then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()),
                up_votes_count=Count('vote', filter=Q(vote__is_up=True)),
                down_votes_count=Count('vote', filter=Q(vote__is_up=False)),
            )
        title_entries = title_entries.order_by('created_at')
        paginator = Paginator(title_entries, ENTRY_COUNT)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        self.context['page_obj'] = page_obj
        self.context['show_title'] = False
        self.context['order_choices'] = ORDER_CHOICES
        return render(request, 'title_page.html', self.context)


class FollowView(View):
    context = {}

    def get(self, request):
        if (not request.user.is_authenticated):
            return redirect('app:index')

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


class FavView(View):
    context = {}

    def get(self, request):
        if (not request.user.is_authenticated):
            return redirect('app:index')
        entries = Entry.objects.filter(
            authorsfavorites__author=request.user
            ).annotate(is_fav=Value(True, output_field=BooleanField()))
        self.context['entries'] = entries.order_by('-created_at')
        self.context['show_title'] = True

        return render(request, 'home_page.html', self.context)


class OrderView(View):
    context = {}

    def get(self, request, title_id, query):
        ENTRY_COUNT = 10
        if request.user.is_authenticated:
            ENTRY_COUNT = request.user.title_entry_count

        title = Title.objects.get(pk=title_id)
        self.context['title'] = title
        title_entries = Entry.objects.filter(
            title=title
        ).annotate(
            is_fav=Case(
                When(authorsfavorites__author=request.user, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()),
            up_votes_count=Count('vote', filter=Q(vote__is_up=True)),
            down_votes_count=Count('vote', filter=Q(vote__is_up=False)),
            fav_count=Count('authorsfavorites')
        )

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

        paginator = Paginator(title_entries, ENTRY_COUNT)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        self.context['page_obj'] = page_obj
        self.context['show_title'] = False
        self.context['order_choices'] = ORDER_CHOICES
        self.context['selected_choice'] = ORDER_CHOICES[query-1]
        return render(request, 'title_page.html', self.context)


# pagination
class TodayView(View):
    context = {}

    def get(self, request):
        ENTRY_COUNT = 10
        if request.user.is_authenticated:
            ENTRY_COUNT = request.user.title_entry_count

        titles = Title.objects.filter(created_at__day=timezone.now().day)
        self.context['titles'] = titles.order_by('-created_at')
        entries = Entry.objects.filter(
            created_at__day=timezone.now().day).order_by('-created_at')

        paginator = Paginator(entries, ENTRY_COUNT)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        self.context['page_obj'] = page_obj
        self.context['entries'] = entries
        self.context['show_title'] = True
        return render(request, 'today_page.html', self.context)


class LDMVViews(View):
    context = {}

    def get(self, request):
        LDMV_COUNT = 5
        yesterday = (timezone.now() - timezone.timedelta(days=1)).day
        entries = Entry.objects.filter(created_at__day=yesterday).annotate(
            up_votes_count=Count('vote', filter=Q(vote__is_up=True)),
            down_votes_count=Count('vote', filter=Q(vote__is_up=False)),
            fav_count=Count('authorsfavorites'),
        )
        entries = entries.annotate(
            vote_point=(
                (F('up_votes_count') * 5) +
                (F('down_votes_count') * -1) +
                (F('fav_count') * 2)))
        self.context['entries'] = entries.order_by('-vote_point')[:LDMV_COUNT]
        self.context['show_title'] = True
        return render(request, 'home_page.html', self.context)


# pagination
class LatestView(View):
    context = {}

    def get(self, request):
        count = Count(
            'entry',
            filter=Q(created_at__day=timezone.now().day))
        titles = Title.objects.annotate(todays_entries_count=count)
        self.context['titles'] = titles.order_by('-todays_entries_count')[:25]
        return render(request, 'latest_page.html', self.context)


class ProfileView(View):
    context = {}

    def get(self, request, author_id):
        # distinct=True meaning is each unique row is only counted once.
        author = Author.objects.annotate(
            follower_count=Count('followers', distinct=True),
            total_votes=Count('entry__vote', distinct=True),
            up_votes=Count('entry__vote', filter=Q(entry__vote__is_up=True)),
            ).annotate(
                upvote_ratio=ExpressionWrapper(
                    (F('up_votes') * 100 / F('total_votes')),
                    output_field=FloatField())).get(pk=author_id)
        if author.total_votes == 0:
            author.upvote_ratio = 0
        self.context['author'] = author
        user_entries = Entry.objects.filter(author=author)
        self.context['entries'] = user_entries.order_by('created_at')
        user_titles = Title.objects.filter(owner=author).order_by('created_at')
        self.context['titles'] = user_titles
        follow = 0  # can follow
        if (request.user == author):
            follow = 1  # same person
        else:
            try:
                followAuthor = FollowAuthor.objects.get(
                    user=request.user, follow=author)
                self.context['follow_date'] = followAuthor.follow_date
                follow = 2  # already follower
            except FollowAuthor.DoesNotExist:
                follow = 0
        self.context['follow'] = follow
        self.context['show_title'] = True
        return render(request, 'profile_page.html', self.context)


class SignupView(View):
    form = SignupForm()

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            if (request.user.is_authenticated):
                logout(request)
            author = form.save(commit=False)
            author.save()
            user = authenticate(request,
                                username=author.username,
                                password=author.password)
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


class NewTitleView(View):
    form = TitleForm()

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('app:login')

        form = TitleForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
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
        form = TitleForm()
        return render(request, 'new_title_page.html', {'form': form})


class TopicView(View):
    context = {}

    def get(self, request, topic_id):
        titles = Title.objects.filter(topic_id=topic_id)
        self.context['titles'] = titles
        return render(request, 'latest_page.html', self.context)


class NewEntryView(View):

    def get(self, request, title_id):
        title = Title.objects.filter(pk=title_id).first()
        if not title:
            return redirect('app:index')
        
        form = EntryForm(request.POST)
        return render(request, 'new_entry_page.html', {
            'form': form,
            'title': title
            })

    def post(self, request, title_id):
        if not request.user.is_authenticated:  # check user
            return redirect('app:index')

        title = Title.objects.filter(pk=title_id).first()  # check title
        if not title:
            return redirect('app:index')

        form = EntryForm()
        return render(request, 'new_entry_page.html', {
                    'form': form,
                    'title': title
                    })
