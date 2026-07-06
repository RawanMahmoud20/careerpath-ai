from django.contrib import admin
from .models import CareerTransitionPlan, PlanSkillGap, AIRecommendation

# 1. إنشاء جدول فرعي للفجوات ليظهر داخل صفحة الخطة
class PlanSkillGapInline(admin.TabularInline):
    model = PlanSkillGap
    extra = 0
    readonly_fields = ['skill_name']

# 2. تسجيل خطة الانتقال المهني (هنا فقط) وحشر الفجوات داخلها
@admin.register(CareerTransitionPlan)
class CareerTransitionPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_career', 'readiness_score', 'created_at')
    list_filter = ('target_career',)
    search_fields = ('user__email', 'target_career__title')
    inlines = [PlanSkillGapInline]

# 3. تسجيل توصيات الـ AI
@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'recommendation_type', 'created_at')
    list_filter = ('recommendation_type',)