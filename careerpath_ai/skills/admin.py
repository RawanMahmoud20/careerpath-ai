from django.contrib import admin
from .models import UserSkill

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'level', 'added_at')
    list_filter = ('level', 'skill')
    search_fields = ('user__email', 'skill__name')