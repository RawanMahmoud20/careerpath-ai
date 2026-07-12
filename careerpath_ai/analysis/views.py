import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from careers.models import CareerSkill, Career 
from skills.models import UserSkill
from .models import UserRoadmap, SkillGap
from .roadmap_generator import generate_and_save_roadmap 

LEVEL_WEIGHTS = {
    'advanced':     1.0,
    'intermediate': 0.7,
    'beginner':     0.4,
}
@login_required
def skill_gap_analysis(request):
    user = request.user

    print("========================================")
    print(f"🕵️‍♂️ DEBUG SKILL GAP FOR USER: {user.email}")
    
    # 1. 🎯 جلب الكارير الحالي المختار من بروفايل المستخدم
    profile = getattr(user, 'user_profile', None) or getattr(user, 'profile', None)
    career = None
    if profile and hasattr(profile, 'target_career') and profile.target_career:
        career = profile.target_career
    else:
        roadmap_fallback = UserRoadmap.objects.filter(user=user).select_related('career').first()
        if roadmap_fallback:
            career = roadmap_fallback.career

    print(f"🔍 DEBUG: Unified Extracted Career -> {career}")

    if not career:
        return redirect('/dashboard/')

    # 2. 🎯 جلب الـ roadmap الحالي لليوزر أو إنشاؤه تلقائياً لو تم تصفيره
    roadmap, created = UserRoadmap.objects.get_or_create(
        user=user,
        defaults={'career': career, 'readiness_score': 0, 'roadmap_json': ''}
    )

    # فحص محتوى الـ JSON الفعّال لمنع التداخل
    is_json_valid_for_this_career = False
    if roadmap and roadmap.roadmap_json and len(roadmap.roadmap_json) > 150:
        try:
            json_text = roadmap.roadmap_json.lower()
            if career.title.lower() in json_text:
                is_json_valid_for_this_career = True
        except Exception:
            pass

    perfect_matched = []
    skills_to_improve = []
    missing_skills  = []
    
    # 🎯 إرجاع لوجيك الحساب الأصلي والصحيح 100% بناءً على الـ CareerSkill والـ LEVEL_WEIGHTS
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

    # تأمين الحساب لمنع الـ DivisionByZero أو الفراغات بالمتصفح
    if total > 0:
        readiness = min(int((score / total) * 100), 100)
    else:
        readiness = 0

    # حفظ السكور الجديد بالداتابيز
    roadmap.readiness_score = readiness
    roadmap.save(update_fields=['readiness_score'])

    # 🎯 صياغة نص الـ AI Summary ديناميكياً بعد انتهاء عملية الحساب
    if readiness == 100:
        ai_summary = f"You are 100% ready for {career.title}! Outstanding achievement! You have mastered all required technical benchmarks for this role."
    else:
        ai_summary = f"You are {readiness}% ready for {career.title}. Review the gaps below and follow your roadmap to close them!"

    # 3. 🛡️ الفحص الموجه للـ HTML لتحديد ظهور الأزرار
    has_valid_roadmap = False
    if roadmap and roadmap.roadmap_json and len(roadmap.roadmap_json) > 150 and is_json_valid_for_this_career:
        has_valid_roadmap = True

    context = {
        'career':            career,
        'roadmap':           roadmap,
        'has_valid_roadmap':  has_valid_roadmap,
        'ai_summary':        ai_summary,
        'perfect_matched':   perfect_matched,
        'skills_to_improve':  skills_to_improve,
        'missing_skills':    missing_skills,
        'readiness':         readiness,
    }
    return render(request, 'analysis/skill_gap.html', context)
@login_required
@require_POST
def trigger_roadmap_generation(request):
    print("========================================")
    print("🔥 BOOM! trigger_roadmap_generation called successfully!")
    print("========================================")
    
    user = request.user
    
    # 1. تحديد الكارير المستهدف النشط حالياً بنفس الطريقة
    profile = getattr(user, 'user_profile', None) or getattr(user, 'profile', None)
    career = None
    if profile and hasattr(profile, 'target_career') and profile.target_career:
        career = profile.target_career
    else:
        roadmap_fallback = UserRoadmap.objects.filter(user=user).select_related('career').first()
        if roadmap_fallback:
            career = roadmap_fallback.career
    
    # 2. جلب الـ Roadmap المرتبط بهذا الكارير
    roadmap = None
    if career:
        roadmap = UserRoadmap.objects.filter(user=user, career=career).first()
    
    print(f"DEBUG: Found Career -> {career}")
    print(f"DEBUG: Found Roadmap Object -> {roadmap}")

    if not career:
        print("❌ DEBUG: No career found for user! Redirecting to dashboard...")
        return redirect('dashboard')
        
    # 3. 🛡️ الفحص المنعي المطور: لو النص موجود وطويل فعلاً (صحيح) اذهب للرودماب مباشرة
   # 3. الفحص المنعي: لا تقبل بالتحويل إلا لو الرودماب تابعة للكارير الحالي فعلياً وطويلة
    if roadmap and roadmap.career == career and roadmap.roadmap_json and len(roadmap.roadmap_json) > 150:
        print("🟢 DEBUG: Valid roadmap JSON exists for THIS career. Redirecting Directly...")
        return redirect('/roadmap/')
    
    # 4. إذا كانت الرودماب تابعة لكارير تاني أو النص تالف، امسحها وصفرها عشان جميناي يبني صح
    if roadmap:
        print("⚠️ DEBUG: Career mismatch or corrupted data. Resetting row for clean generation...")
        roadmap.career = career # إجبار تعديل الكارير للجدول
        roadmap.roadmap_json = ""
        roadmap.save()
        
    # 5. الاستدعاء الفعلي لجميناي لبناء الخطة
    try:
        print("🧠 Gemini generation started... Please wait...")
        generate_and_save_roadmap(user, career)
        print("✅ Gemini generation finished successfully!")
    except Exception as e:
        print("💥💥💥 ERROR INSIDE GEMINI GENERATION:")
        import traceback
        traceback.print_exc() 
        
    return redirect('/roadmap/')