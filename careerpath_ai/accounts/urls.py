from django.urls import path
from .views import register_view, EmailLoginView, logout_view

# No app_name namespace, so names are referenced directly as
# 'login', 'register', 'logout' (matches Django's LOGIN_URL convention).
urlpatterns = [
    path("login/", EmailLoginView.as_view(), name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
]
