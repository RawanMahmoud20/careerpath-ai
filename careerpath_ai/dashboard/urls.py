from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard,name='home'),
    path('update-task/',views.update_task_status,  name='update_task'),
]