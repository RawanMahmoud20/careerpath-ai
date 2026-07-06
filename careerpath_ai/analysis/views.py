from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from careers.models import CareerSkill
from skills.models import UserSkill
from .models import UserRoadmap, SkillGap

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
                SkillGap.objects.get_or_create(roadmap=roadmap, skill_name=name)
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