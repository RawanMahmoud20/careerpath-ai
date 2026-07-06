from django.urls import path
from . import views

app_name = 'skills'

urlpatterns = [
    path('', views.manage_skills_view, name='manage_skills'),
    path('add/', views.add_user_skill, name='add_skill'),
    path('remove/<int:skill_id>/', views.remove_user_skill, name='remove_skill'),
]