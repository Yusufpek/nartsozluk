from django.urls import path

from . import views

app_name = "entry_log"
urlpatterns = [
    path('logs', views.EntryLogView.as_view(), name='logs'),
    path('summary', views.EntryLogView.as_view(), name='summary'),
]
