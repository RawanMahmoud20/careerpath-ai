from django.contrib import admin
from django.urls import path, include
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
path('dashboard/', include('dashboard.urls')),path('roadmap/', include('roadmap.urls')),
    path('careers/', include('careers.urls')),
    
    path('analysis/', include('analysis.urls', namespace='analysis')),
    path('my-skills/', include('skills.urls')),
]