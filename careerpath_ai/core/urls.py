from django.urls import path
from .views import landing

# No app_name namespace: landing is referenced simply as {% url 'landing' %}
urlpatterns = [
    path("", landing, name="landing"),
]
