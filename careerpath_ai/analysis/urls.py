from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.analysis_home, name='home'),
    path('skill-gap/<int:career_id>/', views.skill_gap_analysis, name='skill_gap'),
]