from django.contrib import admin
from .models import UserRoadmap, SkillGap


class SkillGapInline(admin.TabularInline):
    model = SkillGap
    extra = 0
    readonly_fields = ['skill_name', 'is_mastered']


@admin.register(UserRoadmap)
class UserRoadmapAdmin(admin.ModelAdmin):
    list_display  = ('user', 'career', 'readiness_score', 'generated_at')
    list_filter   = ('career',)
    search_fields = ('user__email', 'career__title')
    readonly_fields = ('generated_at',)
    inlines = [SkillGapInline]