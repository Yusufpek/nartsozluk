from django.shortcuts import render, redirect
from django.db.models import BooleanField, Value
from django.http import JsonResponse
from django.contrib import messages

from app.views import AuthMixin, BaseView
from app.models import Title, AuthorsFavorites, Vote
from .forms import EntryForm
from .models import Entry


class NewEntryView(AuthMixin, BaseView):
    def get(self, request, title_id):
        super().get(request)

        title = Title.objects.filter(pk=title_id).first()
        if not title:
            return redirect('app:index')

        form = EntryForm()
        self.context['title'] = title
        self.context['form'] = form
        return render(request, 'new_entry_page.html', self.context)

    def post(self, request, title_id):
        title = Title.objects.filter(pk=title_id).first()  # check title
        if not title:
            return redirect('app:index')

        self.context['title'] = title

        form = EntryForm(request.POST)
        self.context['form'] = form

        if form.is_valid():
            entry_content = form.cleaned_data['content']
            entry = Entry.objects.filter(
                author=request.user,
                title=title,
                content__contains=entry_content).first()
            if entry:
                message = 'you already wrote like this.'
                messages.warning(request, message)
                return render(request, 'new_entry_page.html', self.context)
            else:
                Entry(
                    content=entry_content,
                    author=request.user,
                    title=title).save()
                return redirect('app:title', title_id)
        return render(request, 'new_entry_page.html', self.context)


class EntryEditView(AuthMixin, BaseView):
    def get(self, request, entry_id):
        super().get(request)

        entry = Entry.objects.filter(uid=entry_id).first()
        if not entry:
            return redirect('app:not-found')

        if request.user != entry.author:
            return redirect('authentication:login')

        form = EntryForm(initial={'content': entry.content})
        self.context['form'] = form
        self.context['title'] = entry.title
        return render(request, 'new_entry_page.html', self.context)

    def post(self, request, entry_id):
        form = EntryForm(request.POST)
        if form.is_valid():
            entry_content = form.cleaned_data['content']
            entry = Entry.objects.filter(
                uid=entry_id, author=request.user).first()
            if not entry:
                return redirect('app:not-found')
            else:
                entry.content = entry_content
                entry.save()
                return redirect('app:title', entry.title.id)
        self.context['form'] = form
        self.context['title'] = entry.title
        return render(request, 'new_entry_page.html', self.context)


class EntryView(BaseView):
    context = {}

    def get(self, request, entry_id):
        super().get(request)

        entry = Entry.objects.filter(uid=entry_id)
        if not entry:
            return redirect('app:not-found')

        entry = self.get_is_fav_attr_entry(entry, request.user)
        entry = self.get_vote_counts_entry(entry)
        self.context["entries"] = [entry.first()]
        self.context['show_title'] = True
        return render(request, 'home_page.html', self.context)


class FavView(AuthMixin, BaseView):
    def get(self, request):
        super().get(request)
        favs = AuthorsFavorites.objects.filter(
            author=request.user).values_list('entry_id')
        entries = Entry.objects.filter(uid__in=favs).annotate(
            is_fav=Value(True, output_field=BooleanField()))
        self.context['entries'] = entries.order_by('-created_at')
        self.context['show_title'] = True

        return render(request, 'home_page.html', self.context)


class VoteView(BaseView):
    def post(self, request):
        entry_id = request.POST.get('entry_id')
        vote_is_up = request.POST.get('is_up') == '1'
        vote = Vote.objects.filter(entry_id=entry_id, voter=request.user)
        vote = vote.first()
        if vote:  # check is there a given vote
            # it is up vote but user gave down vote before
            if (not vote.is_up) and vote_is_up:
                vote.is_up = True
            # it is down vote but user gave up vote before
            elif vote.is_up and (not vote_is_up):
                vote.is_up = False
        else:   # create vote
            vote = Vote(
                entry_id=entry_id, voter=request.user, is_up=vote_is_up)
        vote.save()

        # get vote counts again for render
        up_votes_count = Vote.objects.filter(
            entry_id=entry_id, is_up=True).count()
        down_votes_count = Vote.objects.filter(
            entry_id=entry_id, is_up=False).count()

        return JsonResponse({
            'success': True,
            'up_votes_count': up_votes_count,
            'down_votes_count': down_votes_count,
        })


class FavEntryView(BaseView):
    def post(self, request):
        entry_id = request.POST.get('entry_id')
        user = request.user
        try:
            favorite = AuthorsFavorites.objects.filter(
                entry_id=entry_id, author=user).first()
            if favorite:  # if it is added to favorite
                favorite.delete()  # delete it
                is_favorite = False
            else:  # if it is not favorite create favorite object
                AuthorsFavorites(entry_id=entry_id, author=user).save()
                is_favorite = True
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': True, 'is_favorite': is_favorite})


class DeleteEntryView(AuthMixin, BaseView):
    def post(self, request):
        super().get(request)

        entry_id = request.POST.get('entry_id')
        if request.user.is_staff:
            entry = Entry.objects.filter(uid=entry_id).first()
        else:
            entry = Entry.objects.filter(
                uid=entry_id, author=request.user).first()

        if entry:
            entry.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'error': 'Entry does not exist, or the author is not valid'})
