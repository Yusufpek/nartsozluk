from django.urls import path

from . import views
from app.views import NotFoundView

app_name = "entry"
urlpatterns = [
    path('fav', views.FavView.as_view(), name="fav"),
    path('<int:entry_id>/entry/', NotFoundView.as_view(), name='entry'),
    path('<uuid:entry_id>/entry/', views.EntryView.as_view(), name='entry'),
    path('fav_entry', views.FavEntryView.as_view(), name="fav-entry"),
    path('delete_entry', views.DeleteEntryView.as_view(), name="delete-entry"),
    path('<int:title_id>/new-entry',
         views.NewEntryView.as_view(), name="new-entry"),
    path('<uuid:entry_id>/edit-entry',
         views.EntryEditView.as_view(), name="edit-entry"),
    # follows
    path('vote', views.VoteView.as_view(), name="vote"),
]
