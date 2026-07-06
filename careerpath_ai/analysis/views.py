from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dashboard.models import UserProfile
from careers.models import Career, CareerSkill 

# استيراد المهارات وموديل مهارات المستخدم من تطبيقها الجديد
from skills.models import Skill, UserSkill 
from .models import CareerTransitionPlan, PlanSkillGap, AIRecommendation

# 🎯 قاموس الأوزان الذكية لحساب نسبة الجاهزية بدقة هندسية
LEVEL_WEIGHTS = {
    'advanced': 1.0,     # المهارة المتقدمة تضاف للحسبة بكامل وزنها
    'intermediate': 0.7,  # المهارة المتوسطة تعطي جاهزية جزئية بنسبة 70%
    'beginner': 0.4      # المهارة المبتدئة تعطي جاهزية أولية بنسبة 40%
}
@login_required
def skill_gap_analysis(request):
    user = request.user
    
    plan = CareerTransitionPlan.objects.filter(user=user).order_by('-created_at').first()
    ai_rec = AIRecommendation.objects.filter(user=user, recommendation_type='roadmap').order_by('-created_at').first()
    ai_summary = ai_rec.content if ai_rec else "Our AI has completed the analysis. Explore your roadmap to bridge your level gaps!"
    
    career = None
    perfect_matched = []     # ✅ المهارات المكتملة تماماً (Advanced)
    skills_to_improve = []   # ⚠️ مهارات يمتلكها ولكن تحتاج لتطوير المستوى
    missing_skills = []      # ❌ مهارات مفقودة تماماً
    readiness = 0
    
    if plan and plan.target_career:
        career = plan.target_career
        
        # جلب مهارات المستخدم الحالية كموجز: { اسم_المهارة: الكائن بالكامل لقراءة المستوى والاسم }
        user_skills_dict = {
            us.skill.name: us 
            for us in UserSkill.objects.filter(user=user).select_related('skill')
        }
        
        career_skills = CareerSkill.objects.filter(career=career).select_related('skill')        
        total_skills_count = career_skills.count()
        total_score = 0.0
        
        for cs in career_skills:
            skill_name = cs.skill.name
            
            if skill_name in user_skills_dict:
                user_skill_obj = user_skills_dict[skill_name]
                current_level = user_skill_obj.level
                
                # إضافة الوزن التراكمي للحسبة
                total_score += LEVEL_WEIGHTS.get(current_level, 0.4)
                
                # التصنيف الهندسي بناءً على المستوى
                if current_level == 'advanced':
                    perfect_matched.append(user_skill_obj)
                else:
                    skills_to_improve.append(user_skill_obj)
            else:
                # مهارة مفقودة تماماً
                PlanSkillGap.objects.get_or_create(plan=plan, skill_name=skill_name)
                missing_skills.append({'skill': cs.skill, 'priority': cs.priority})
        
        if total_skills_count > 0:
            readiness = int((total_score / total_skills_count) * 100)
            if readiness > 100: readiness = 100
                
            plan.readiness_score = readiness
            plan.save()
            
    context = {
        'career': career,
        'ai_summary': ai_summary,
        'perfect_matched': perfect_matched,
        'skills_to_improve': skills_to_improve,
        'missing_skills': missing_skills,
        'readiness': readiness,
    }
    return render(request, 'analysis/skill_gap.html', context)