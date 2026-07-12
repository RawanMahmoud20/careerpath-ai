from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    path('', views.career_list, name='list'),
    path('<int:career_id>/', views.career_detail, name='detail'),
    path('<int:career_id>/choose/', views.choose_career, name='choose'),
    path('search/', views.career_search_api, name='search_api'),

]
