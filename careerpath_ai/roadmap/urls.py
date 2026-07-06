from django.urls import path
from . import views

app_name = 'roadmap'

urlpatterns = [
    path('', views.roadmap, name='home'),
 
    path('update-progress/', views.update_task_progress, name='update_progress'),
]