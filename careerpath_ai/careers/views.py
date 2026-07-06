from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Career
from analysis.models import UserRoadmap
from analysis.roadmap_generator import generate_and_save_roadmap


def career_detail(request, career_id):
    """Show detailed information about a specific career path."""
    career = get_object_or_404(Career.objects.prefetch_related('required_skills'), id=career_id)
    return render(request, 'careers/career_detail.html', {'career': career})


@login_required
def career_list(request):
    careers = Career.objects.all().prefetch_related('required_skills')

    # Which career (if any) has the user already selected?
    try:
        selected_id = UserRoadmap.objects.get(user=request.user).career_id
    except UserRoadmap.DoesNotExist:
        selected_id = None

    return render(request, 'careers/careers.html', {
        'careers':     careers,
        'selected_id': selected_id,
    })


@login_required
@require_POST
def choose_career(request, career_id):
    career = get_object_or_404(Career, id=career_id)

    try:
        generate_and_save_roadmap(request.user, career)
        messages.success(
            request,
            f'Your target career is now: {career.title} and your roadmap has been generated.',
        )
    except Exception as e:
        messages.warning(request, f'Career selected, but roadmap generation failed: {e}')

    return redirect('dashboard:home')
