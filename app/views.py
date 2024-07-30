from django.contrib.auth import authenticate, login, logout
from django.db.models import Max, Count, Q, F
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views import View
import random

from .models import Title, Entry, Author
from .forms import LoginForm, SignupForm


# Create your views here.
class HomeView(View):
    context = {}

    def get(self, request):
        HOME_ENTRY_COUNT = 10
        pk_max = Entry.objects.all().aggregate(pk_max=Max("pk"))['pk_max']
        if (pk_max):
            count = min(pk_max, HOME_ENTRY_COUNT)  # limit with pk and count
            random_list = random.sample(range(1, pk_max+1), count)
            entries = Entry.objects.filter(pk__in=random_list).order_by('?')
            self.context["entries"] = entries

        return render(request, 'home_page.html', self.context)


class TitleView(View):
    context = {}

    def get(self, request, title_id):
        title = Title.objects.get(pk=title_id)
        self.context['title'] = title
        title_entries = Entry.objects.filter(title=title)
        self.context['entries'] = title_entries.order_by('created_at')

        return render(request, 'title_page.html', self.context)


class FollowView(View):
    context = {}

    def get(self, request):
        if (not request.user.is_authenticated):
            return redirect('app:index')
        follows = Author.objects.filter(follow=request.user.id)
        print(follows)
        entries = Entry.objects.filter(author__in=follows)
        self.context['entries'] = entries.order_by('-created_at')

        return render(request, 'home_page.html', self.context)


class FavView(View):
    context = {}

    def get(self, request):
        if (not request.user.is_authenticated):
            return redirect('app:index')
        entries = Entry.objects.filter(authorsfavorites__author=request.user)
        self.context['entries'] = entries.order_by('-created_at')

        return render(request, 'home_page.html', self.context)


class VotedView(View):
    context = {}

    def get(self, request, title_id):
        title = Title.objects.get(pk=title_id)
        self.context['title'] = title
        entries = Entry.objects.filter(title=title).annotate(
            up_votes_count=Count('vote', filter=Q(vote__is_up=True)),
            down_votes_count=Count('vote', filter=Q(vote__is_up=False)),
        )
        entries = entries.annotate(
            vote_diff=F('up_votes_count') - F('down_votes_count'))
        self.context['entries'] = entries.order_by('-vote_diff')

        return render(request, 'title_page.html', self.context)


class TodayView(View):
    context = {}

    def get(self, request):
        titles = Title.objects.filter(created_at__day=timezone.now().day)
        self.context['titles'] = titles.order_by('-created_at')
        entries = Entry.objects.filter(created_at__day=timezone.now().day)
        self.context['entries'] = entries.order_by('-created_at')

        return render(request, 'today_page.html', self.context)


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
        author = Author.objects.get(pk=author_id)
        self.context['author'] = author
        user_entries = Entry.objects.filter(author=author)
        self.context['entries'] = user_entries.order_by('created_at')
        user_titles = Title.objects.filter(owner=author).order_by('created_at')
        self.context['titles'] = user_titles

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
