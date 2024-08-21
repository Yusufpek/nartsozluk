from django.views import View

from .models import Entry
from app.views import AuthMixin
from app.models import Vote, AuthorsFavorites
from django.http import JsonResponse


# Create your views here.
class VoteView(View):
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


class FavEntryView(View):
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


class DeleteEntryView(AuthMixin, View):
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
