from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View

from .forms import LoginForm, SignupForm
from .utils import send_register_email, send_delete_account_email
from .tasks import my_task


class SignupView(View):
    form = SignupForm()

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            if (request.user.is_authenticated):
                logout(request)
            # form auto hash the password but authenticated wants to raw pass
            author = form.save(commit=False)
            password = form.cleaned_data['password1']
            author.save()
            user = authenticate(request,
                                username=author.username,
                                password=password)
            if user:
                login(request, user)
                my_task.delay_on_commit(1, 2)
                send_register_email(author.username, author.email)
                return redirect('app:index')
            return render(request, 'signup_page.html', {'form': form})
        else:
            form = SignupForm(request.POST)
            return render(request, 'signup_page.html', {'form': form})

    def get(self, request):
        form = SignupForm()
        return render(request, 'signup_page.html', {'form': form})


class LoginView(View):
    form = LoginForm()

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                next = request.GET.get("next")
                if next:
                    return redirect(next)
                return redirect('app:index')
            else:
                message = 'login error, username or password is incorrect.'
                messages.warning(request, message)
                return render(request, 'login_page.html', {'form': form})
        else:
            return render(request, 'login_page.html', {'form': form})

    def get(self, request):
        form = LoginForm()
        return render(request, 'login_page.html', {'form': form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('authentication:login')


class DeleteAccountView(View):
    def get(self, request):
        author = request.user
        name = author.username
        email = author.email
        send_delete_account_email(name, email)
        author.delete()
        return redirect('authentication:signup')
