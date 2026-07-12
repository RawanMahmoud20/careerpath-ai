from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserSkill, Skill

# 1. تسجيل جدول المهارات الرئيسي
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)  # 👈 اكتفينا بحقل الاسم المضمون لتجنب أي تعارض
    search_fields = ('name',)

# 2. تعريف الجدول المدمج للمهارات داخل صفحة المستخدم
class UserSkillInline(admin.TabularInline):
    model = UserSkill
    extra = 1
    fields = ('skill', 'level', 'added_at')
    readonly_fields = ('added_at',)

# 3. كلاس الـ Admin المطور لحقن الجدول المدمج داخل اليوزر
class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserSkillInline]

# 4. تسجيل صفحة المهارات المستقلة للمستخدمين باستخدام المزخرف فقط
@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'level', 'added_at')
    list_filter = ('level', 'skill')
    search_fields = ('user__email', 'skill__name')

# 🛑 ملاحظة: تأكد أنه لا يوجد أي سطر admin.site.register(UserSkill) إضافي هنا في نهاية الملف.