from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from dashboard.models import UserProfile, UserTaskProgress
from skills.models import UserSkill
from careers.models import Career
from analysis.models import UserRoadmap
from analysis.roadmap_generator import generate_and_save_roadmap


@login_required
def dashboard(request):
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)

    # Single query — one row per user, no ambiguity
    try:
        user_roadmap = UserRoadmap.objects.select_related('career').get(user=user)
        target_career = user_roadmap.career
        readiness     = user_roadmap.readiness_score or 0
    except UserRoadmap.DoesNotExist:
        target_career = None
        readiness     = 0

    matched_count = 0
    missing_count = 0

    if target_career:
        user_skill_names = set(
            UserSkill.objects.filter(user=user).values_list('skill__name', flat=True)
        )
        req_skill_names = set(
            target_career.required_skills.values_list('name', flat=True)
        )
        matched_count = len(user_skill_names & req_skill_names)
        missing_count = len(req_skill_names - user_skill_names)

    context = {
        'profile':       profile_obj,
        'target_career': target_career,
        'readiness':     readiness,
        'matched_count': matched_count,
        'missing_count': missing_count,
        'careers':       Career.objects.all(),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def select_career(request, career_id):
    if request.method == 'POST':
        try:
            career = get_object_or_404(Career, id=career_id)
            generate_and_save_roadmap(request.user, career)
            messages.success(
                request,
                f"Career set to {career.title} — your roadmap has been generated!",
            )
        except Exception as e:
            messages.error(request, f"Error selecting career: {e}")

    return redirect('/dashboard/')


@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.full_name = request.POST.get('full_name', '')
        user.save()
        profile.current_field    = request.POST.get('current_field', '')
        profile.experience_level = request.POST.get('experience_level', 'beginner')
        profile.save()
        return redirect('dashboard:profile')

    return render(request, 'dashboard/profile.html', {'profile': profile})