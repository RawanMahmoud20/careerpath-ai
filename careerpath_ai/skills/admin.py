from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserSkill

# 1. تعريف الجدول المدمج للمهارات
class UserSkillInline(admin.TabularInline):
    model = UserSkill
    extra = 1
    fields = ('skill', 'level', 'added_at')
    readonly_fields = ('added_at',)

# 2. كلاس الـ Admin المطور الذي سيتم حقنه داخل اليوزر
class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserSkillInline]

# 3. كود صفحة المهارات المستقلة (بره) يضل زي ما هو
@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'level', 'added_at')
    list_filter = ('level', 'skill')
    search_fields = ('user__email', 'skill__name')