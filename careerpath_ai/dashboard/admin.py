from django.contrib import admin
from .models import UserProfile

# تسجيل موديل الملف الشخصي ليظهر في لوحة التحكم
admin.site.register(UserProfile)