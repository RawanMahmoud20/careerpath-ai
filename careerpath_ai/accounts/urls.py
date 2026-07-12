from django.urls import path
from .views import register_view, login_view, logout_view, verify_otp_view, cancel_registration_view

urlpatterns = [
    path('signup/', register_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('cancel-registration/', cancel_registration_view, name='cancel_registration'),
]
