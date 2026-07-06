from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
 path('', views.dashboard, name='home'),
path('select-career/<int:career_id>/', views.select_career, name='select_career'),
path('profile/', views.profile_view, name='profile'),]