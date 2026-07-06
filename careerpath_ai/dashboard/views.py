from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from dashboard.models import UserProfile, UserTaskProgress
from skills.models import UserSkill

try:
    from analysis.models import CareerTransitionPlan, Career
except ImportError:
    from careers.models import Career
    from analysis.models import CareerTransitionPlan
    
@login_required
def dashboard(request):
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    
    plan = CareerTransitionPlan.objects.filter(user=user).order_by('-created_at').first()
    
    target_career = None
    readiness = 0
    matched_count = 0
    missing_count = 0
    
    if plan:
        target_career = plan.target_career
        readiness = getattr(plan, 'readiness_score', 0) or 0
        
        # 🟢 التعديل الجوهري: جلب أسماء المهارات من جدول اليوزر الجديد
        user_skills = set(UserSkill.objects.filter(user=user).values_list('skill__name', flat=True))
        
        if hasattr(target_career, 'required_skills'):
            try:
                req_skills_set = set(target_career.required_skills.values_list('name', flat=True))
            except Exception:
                req_skills_set = set(getattr(target_career, 'required_skills', []))
                
            matched_skills = user_skills.intersection(req_skills_set)
            missing_skills = req_skills_set.difference(user_skills)
            
            matched_count = len(matched_skills)
            missing_count = len(missing_skills)
    
    careers = Career.objects.all()
    
    context = {
        'profile': profile_obj,
        'target_career': target_career,
        'readiness': readiness,
        'matched_count': matched_count,
        'missing_count': missing_count,
        'careers': careers,
    }
    return render(request, 'dashboard/dashboard.html', context)
@login_required
def select_career(request, career_id):
    if request.method == 'POST':
        try:
            from analysis.models import CareerTransitionPlan, Career
            career = get_object_or_404(Career, id=career_id)
            
            # الفحص العادي والتحديث المباشر بدون تمرير readiness_score لمنع الكراش
            plan_queryset = CareerTransitionPlan.objects.filter(user=request.user)
            
            if plan_queryset.exists():
                # إذا كانت الخطة موجودة مسبقاً، نقوم بتحديث الكارير فقط
                plan = plan_queryset.first()
                plan.target_career = career
                plan.save()
            else:
                # إذا لم تكن موجودة، نقوم بإنشائها وتمرير الحقول الأساسية المؤكدة فقط
                CareerTransitionPlan.objects.create(
                    user=request.user,
                    target_career=career
                )
            
            messages.success(request, f"Successfully selected {career.title} as your target career path!")
        except Exception as e:
            messages.error(request, f"Error selecting career: {str(e)}")
            
    return redirect('/dashboard/')
@login_required
def profile_view(request):
    user = request.user
    
    # جلب أو إنشاء ملف اليوزر الأساسي
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # استقبال البيانات الأساسية من الفورم وحفظها
        user.full_name = request.POST.get('full_name', '')
        user.save()
        profile.current_field = request.POST.get('current_field', '')
        profile.experience_level = request.POST.get('experience_level', 'beginner')
        profile.save()
        return redirect('dashboard:profile')        
    context = {
        'profile': profile,
    }
    return render(request, 'dashboard/profile.html', context)