from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
 path('', views.skill_gap_analysis, name='skill_gap'),
]