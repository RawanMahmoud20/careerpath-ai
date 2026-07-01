from django.urls import path
from . import views

app_name = 'roadmap'

urlpatterns = [
    path('', views.roadmap, name='home'),
    path('skills/', views.skills_selection, name='skills_selection'),
    path('skills/save/', views.save_skills, name='save_skills'),
]