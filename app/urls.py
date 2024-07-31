from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    # /
    path('', views.HomeView.as_view(), name="index"),
    path('today', views.TodayView.as_view(), name="today"),
    path('latest', views.LatestView.as_view(), name="latest"),
    path('follow', views.FollowView.as_view(), name="follow"),
    path('new-title', views.NewTitleView.as_view(), name="new-title"),
    path('fav', views.FavView.as_view(), name="fav"),
    path('ldmv', views.LDMVViews.as_view(), name="ldmv"),
    path('fav_entry', views.FavEntryView.as_view(), name="fav-entry"),
    path('vote', views.VoteView.as_view(), name="vote"),
    path('<int:follow_id>/follow',
         views.FollowUserView.as_view(), name="follow-user"),
    path('<int:follow_id>/unfollow',
         views.UnFollowUserView.as_view(), name="unfollow-user"),
    # authentication pages
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    #
    path('<int:title_id>/title', views.TitleView.as_view(), name="title"),
    path('<int:title_id>/voted', views.VotedView.as_view(), name="most-voted"),
    path('<int:author_id>/profile',
         views.ProfileView.as_view(), name="profile"),
]
