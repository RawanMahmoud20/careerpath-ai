from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Skill
from .models import UserSkill
from dashboard.models import UserTaskProgress
@login_required
def manage_skills_view(request):
    user = request.user
    user_skills = UserSkill.objects.filter(user=user).select_related('skill').order_by('skill__category')
    already_added_ids = user_skills.values_list('skill_id', flat=True)
    
    available_skills = Skill.objects.exclude(id__in=already_added_ids)
    
    categories = Skill.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct()
    
    context = {
        'user_skills': user_skills,
        'all_skills': available_skills,
        'categories': categories, # تم تمرير الأقسام هان
    }
    return render(request, 'skills/manage_skills.html', context)
@login_required
def add_user_skill(request):  # تأكد أن اسم الدالة يطابق الاسم المربوط بـ add_skill في urls.py
    if request.method == 'POST':
        skill_id = request.POST.get('skill_id')
        
        # 🎯 التقاط اسم الحقل بالظبط كما هو مبعوث من الـ HTML: current_level
        level = request.POST.get('current_level') or 'beginner'
        
        if skill_id:
            skill_obj = get_object_or_404(Skill, id=skill_id)
            
            # 🎯 التحديث الإجباري للمستوى لمنع بقائه beginner دائماً
            UserSkill.objects.update_or_create(
                user=request.user,
                skill=skill_obj,
                defaults={'level': level}
            )
    return redirect('skills:manage_skills')



@login_required
def remove_user_skill(request, skill_id):
    if request.method == 'POST':
        user_skill = get_object_or_404(UserSkill, user=request.user, skill_id=skill_id)
        
        # 1. 🔍 استخراج اسم المهارة الأصلي لتحويله لـ prefix (مثل: "Python" بتصير "python")
        skill_name = user_skill.skill.name.lower()
        print(f"\n🧹 [SKILL DELETION TRIGGERED] User is removing: '{skill_name}'")
        
        # 2. ⚡ الحماية الحديدية: حذف كافة تكات التقدم بجدول الـ UserTaskProgress اللي بتبدأ باسم المهارة
        deleted_count, _ = UserTaskProgress.objects.filter(
            user=request.user,
            task_ref__istartswith=f"{skill_name}-"
        ).delete()
        
        print(f"✅ Cleaned up {deleted_count} stale tasks from UserTaskProgress for '{skill_name}'")
        
        # 3. حذف المهارة من حساب اليوزر
        user_skill.delete()
        print(f"🔥 Skill row deleted from UserSkill successfully.\n")
        
    return redirect('skills:manage_skills')