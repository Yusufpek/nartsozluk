from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    # main pages
    path('', views.HomeView.as_view(), name="index"),
    path('today', views.TodayView.as_view(), name="today"),
    path('latest', views.LatestView.as_view(), name="latest"),
    path('follow', views.FollowView.as_view(), name="follow"),
    path('new-title', views.NewTitleView.as_view(), name="new-title"),
    path('fav', views.FavView.as_view(), name="fav"),
    path('ldmv', views.LDMVViews.as_view(), name="ldmv"),
    # entry pages
    path('<int:entry_id>/entry/', views.EntryView.as_view(), name='entry'),
    path('fav_entry', views.FavEntryView.as_view(), name="fav-entry"),
    path('delete_entry', views.DeleteEntryView.as_view(), name="delete-entry"),
    path('<int:title_id>/new-entry',
         views.NewEntryView.as_view(), name="new-entry"),
    path('<int:entry_id>/edit-entry',
         views.EntryEditView.as_view(), name="edit-entry"),
    # follows
    path('vote', views.VoteView.as_view(), name="vote"),
    path('<int:follow_id>/follow',
         views.FollowUserView.as_view(), name="follow-user"),
    path('<int:follow_id>/unfollow',
         views.UnFollowUserView.as_view(), name="unfollow-user"),
    # authentication pages
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # title pages
    path('followed-titles',
         views.FollowedTitleView.as_view(), name="followed-title"),
    path('<int:title_id>/followed-title-entries',
         views.FollowedTitleEntries.as_view(), name="followed-title-entries"),
    path('<int:title_id>/title', views.TitleView.as_view(), name="title"),
    path('<int:title_id>/order/<int:query>',
         views.OrderView.as_view(), name="order"),
    path('<int:topic_id>/topic', views.TopicView.as_view(), name='topic'),
    # user profile pages
    path('<int:author_id>/profile',
         views.ProfileView.as_view(), name="profile"),
    path('<int:author_id>/profile/<int:query>',
         views.ProfileView.as_view(), name="profile"),
    path('settings/',
         views.SettingsView.as_view(), name='settings'),
    path('search', views.SearchView.as_view(), name='search'),
    path('not-found', views.NotFoundView.as_view(), name='not-found')
]
