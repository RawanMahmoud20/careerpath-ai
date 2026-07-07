from django.contrib import admin
from .models import Career, CareerSkill


class CareerSkillInline(admin.TabularInline):
    model = CareerSkill
    extra = 1


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ('icon', 'title', 'estimated_time')
    inlines = [CareerSkillInline]


@admin.register(CareerSkill)
class CareerSkillAdmin(admin.ModelAdmin):
    list_display = ('career', 'skill', 'priority', 'is_transferable')