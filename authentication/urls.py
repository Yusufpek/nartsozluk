from django.urls import path

from . import views

app_name = "authentication"
urlpatterns = [
    # authentication pages
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
