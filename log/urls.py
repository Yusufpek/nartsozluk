from django.urls import path

from . import views

app_name = "log"
urlpatterns = [
    path('monitor-tasks', views.MonitorTasks.as_view(), name='monitor'),
]
