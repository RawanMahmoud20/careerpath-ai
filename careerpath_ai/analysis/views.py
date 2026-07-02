import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from careers.models import Career, CareerSkill
from analysis.models import CareerTransitionPlan, AIRecommendation
from dashboard.models import UserProfile


@login_required
def skill_gap_analysis(request, career_id):
    user = request.user
    career = get_object_or_404(Career, id=career_id)

    try:
        profile = UserProfile.objects.get(user=user)
        user_skills = set(profile.skills)
    except UserProfile.DoesNotExist:
        user_skills = set()

    required_skills = set(
        CareerSkill.objects.filter(career=career)
        .values_list('skill__name', flat=True)
    )

    missing_skills = required_skills - user_skills
    matched_skills = required_skills & user_skills
    match_pct = int((len(matched_skills) / len(required_skills)) * 100) if required_skills else 0

    plan, _ = CareerTransitionPlan.objects.get_or_create(
        user=user,
        target_career=career
    )

    context = {
        'career': career,
        'matched_skills': list(matched_skills),
        'missing_skills': list(missing_skills),
        'match_pct': match_pct,
        'plan': plan,
    }
    return render(request, 'analysis/skill_gap.html', context)


@login_required
def analysis_home(request):
    careers = Career.objects.all()
    return render(request, 'analysis/analysis_home.html', {'careers': careers})