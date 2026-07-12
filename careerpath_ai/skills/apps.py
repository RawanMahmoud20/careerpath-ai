from django.apps import AppConfig

class SkillsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'skills' # تأكد أن الاسم يطابق اسم تطبيق المهارات عندك

    def ready(self):
        # هان بنضمن إن جانقو شحن كل الموديلات أولاً قبل التعديل
        from django.contrib import admin
        from django.contrib.auth.models import User
        from .admin import CustomUserAdmin

        try:
            # نلغي تسجيل اليوزر القديم بأمان
            admin.site.unregister(User)
        except admin.exceptions.NotRegistered:
            pass
        
        # نسجل اليوزر الجديد ومعه جدول المهارات المدمج فوراً!
        admin.site.register(User, CustomUserAdmin)