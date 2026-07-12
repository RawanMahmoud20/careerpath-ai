import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from careers.models import CareerSkill, Career # تأكد من استيراد موديل Career
from skills.models import UserSkill
from .models import UserRoadmap, SkillGap
from .roadmap_generator import generate_and_save_roadmap # استدعاء ملف التوليد الذكي لجميناي

LEVEL_WEIGHTS = {
    'advanced':     1.0,
    'intermediate': 0.7,
    'beginner':     0.4,
}


@login_required
def skill_gap_analysis(request):
    user = request.user

    roadmap = UserRoadmap.objects.filter(user=user).select_related('career').first()

    career          = roadmap.career if roadmap else None
    perfect_matched = []
    skills_to_improve = []
    missing_skills  = []
    readiness       = roadmap.readiness_score if roadmap else 0
    ai_summary      = "Select a career goal first, then complete your skills profile!"

    if roadmap and career:
        ai_summary = (
            f"You are {readiness}% ready for {career.title}. "
            "Review the gaps below and follow your roadmap to close them!"
        )

        user_skills_dict = {
            us.skill.name: us
            for us in UserSkill.objects.filter(user=user).select_related('skill')
        }

        career_skills = CareerSkill.objects.filter(career=career).select_related('skill')
        total         = career_skills.count()
        score         = 0.0

        for cs in career_skills:
            name = cs.skill.name
            if name in user_skills_dict:
                us_obj = user_skills_dict[name]
                score += LEVEL_WEIGHTS.get(us_obj.level, 0.4)
                if us_obj.level == 'advanced':
                    perfect_matched.append(us_obj)
                else:
                    skills_to_improve.append(us_obj)
            else:
                SkillGap.objects.get_or_create(roadmap=roadmap, skill=cs.skill)
                missing_skills.append({'skill': cs.skill, 'priority': cs.priority})

        if total > 0:
            readiness = min(int((score / total) * 100), 100)
            roadmap.readiness_score = readiness
            roadmap.save(update_fields=['readiness_score'])

    context = {
        'career':           career,
        'ai_summary':       ai_summary,
        'perfect_matched':  perfect_matched,
        'skills_to_improve': skills_to_improve,
        'missing_skills':   missing_skills,
        'readiness':        readiness,
    }
    return render(request, 'analysis/skill_gap.html', context)

@login_required
@require_POST
def trigger_roadmap_generation(request):
    """
    🎯 مطورة: لو المستخدم يمتلك خطة توليد مسبقة لنفس الكارير الحالي (حتى لو Readiness أقل من 100%)،
    يتم توجيهه مباشرة دون مسح البيانات أو مناداة جميناي مجدداً.
    """
    user = request.user
    
    # 1. جلب الخطة الحالية المسجلة في قاعدة البيانات
    roadmap = UserRoadmap.objects.filter(user=user).select_related('career').first()
    
    # 2. تحديد الكارير المستهدف
    career = roadmap.career if roadmap else getattr(user, 'target_career', None)
    
    if not career:
        return redirect('dashboard')
        
    # 3. 🎯 الفحص الذكي والمنعي: 
    # لو الـ roadmap موجودة، ونفس الكارير المطلوب، وفيها json مولد مسبقاً ومخزن
    if roadmap and roadmap.career_id == career.id and roadmap.roadmap_json:
        # نقوم بالتحويل الفوري لصفحة الرودماب دون تصفير أو استدعاء جميناي
        return redirect('/roadmap/')
        
    # 4. إذا كان الكارير جديد تماماً أو لا يوجد JSON مسبق، نقوم بالتوليد لأول مرة
    try:
        generate_and_save_roadmap(user, career)
    except Exception as e:
        print(f"💥 Error triggered during Gemini roadmap generation: {e}")
        
    return redirect('/roadmap/')