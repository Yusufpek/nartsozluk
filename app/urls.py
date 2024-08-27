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
    path('ldmv', views.LDMVViews.as_view(), name="ldmv"),
    # follows
    path('<int:follow_id>/follow',
         views.FollowUserView.as_view(), name="follow-user"),
    path('<int:follow_id>/unfollow',
         views.UnFollowUserView.as_view(), name="unfollow-user"),
    # title pages
    path('<int:title_id>/latest',
         views.LatestTitleView.as_view(), name="latest-title"),
    path('followed-titles',
         views.FollowTitleView.as_view(), name="followed-title"),
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
    path('<uuid:entry_id>/report/', views.ReportView.as_view(), name="report"),
    path('all-reports', views.AllReportsView.as_view(), name="all-reports"),
    path('report-delete',
         views.ReportDeleteView.as_view(), name="report-delete"),
    path('<int:query>/ai-view', views.AIView.as_view(), name='ai-bot'),
    path('spammer', views.SpammerView.as_view(), name='spammer'),
    path('new-topic', views.NewTopicView.as_view(), name='new-topic'),
    path('not-found', views.NotFoundView.as_view(), name='not-found')
]
