from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import RegisterForm, EmailLoginForm


def register_view(request):
    """Create a new account, then log the user in."""
    if request.user.is_authenticated:
        return redirect("landing")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("dashboard:home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


class EmailLoginView(LoginView):
    """Login using email + password."""
    template_name = "accounts/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect("landing")
