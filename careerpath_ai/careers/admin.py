from django.contrib import admin
from .models import Career, CareerSkill


class CareerSkillInline(admin.TabularInline):
    model = CareerSkill
    extra = 1


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ( 'title','description', 'estimated_time')
    inlines = [CareerSkillInline]


@admin.register(CareerSkill)
class CareerSkillAdmin(admin.ModelAdmin):
    list_display = ('career', 'skill', 'priority', 'is_transferable')
    
    # 1️⃣ إضافة فلاتر جانبية على اليمين للوظيفة والأولوية والمهارات التبادلية
    list_filter = ('career', 'priority', 'is_transferable')
    
    # 2️⃣ إضافة صندوق بحث علوي يبحث باسم الوظيفة أو اسم المهارة
    search_fields = ('career__title', 'skill__name')
    
    # 3️⃣ ترتيب الجدول تلقائياً حسب الوظيفة ثم الأولوية عشان تمنع العشوائية البصرية
    ordering = ('career', '-priority')