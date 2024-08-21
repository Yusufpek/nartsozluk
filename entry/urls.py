from django.urls import path

from . import views

app_name = "entry"
urlpatterns = [
    path('vote', views.VoteView.as_view(), name="vote"),
    path('fav_entry', views.FavEntryView.as_view(), name="fav-entry"),
    path('delete_entry', views.DeleteEntryView.as_view(), name="delete-entry"),

]
