from django.contrib import admin
from .models import Skill, Career, CareerSkill, SelectedCareer


class CareerSkillInline(admin.TabularInline):
    model = CareerSkill
    extra = 1


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')
    search_fields = ('title',)
    inlines = [CareerSkillInline]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)


@admin.register(SelectedCareer)
class SelectedCareerAdmin(admin.ModelAdmin):
    list_display = ('user', 'career', 'chosen_at')
    search_fields = ('user__email', 'career__title')
