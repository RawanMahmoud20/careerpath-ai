from django.contrib import admin
from .models import Career, CareerSkill
from skills.models import Skill

# 1. إنشاء الجدول الفرعي للمهارات ليتم حشوه داخل الكارير
class CareerSkillInline(admin.TabularInline):
    model = CareerSkill
    extra = 1  # عدد الأسطر الفارغة الجاهزة للإضافة الفورية
    autocomplete_fields = ['skill']  # تفعيل البحث السريع عن المهارة

# 2. تسجيل الكارير (مرة واحدة فقط هنا) مع حشر المهارات جواته
@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ('title', 'estimated_time')
    search_fields = ('title',)
    inlines = [CareerSkillInline]

# 3. تسجيل المهارة العامة وتفعيل الـ search_fields فيها عشان الـ autocomplete يشتغل بدون مشاكل
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ['name']  # مُهم جداً لـ autocomplete_fields