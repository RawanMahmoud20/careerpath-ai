from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q

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


@login_required
def career_search_api(request):
    """
    Live-search API endpoint.
    Returns careers matching the query as JSON (used by the Fetch API on the careers page).
    Matches on career title, description, or required skill names.
    """
    query = request.GET.get('q', '').strip()

    careers = Career.objects.all().prefetch_related('required_skills')

    if query:
        careers = careers.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(required_skills__name__icontains=query)
        ).distinct()

    # Which career has the user already selected?
    try:
        selected_id = UserRoadmap.objects.get(user=request.user).career_id
    except UserRoadmap.DoesNotExist:
        selected_id = None

    results = []
    for career in careers:
        results.append({
            'id': career.id,
            'title': career.title,
            'description': career.description,
            'estimated_time': career.estimated_time,
            'icon': career.icon,
            'icon_color': career.icon_color,
            'skills': [s.name for s in career.required_skills.all()[:4]],
            'is_selected': career.id == selected_id,
        })

    return JsonResponse({
        'query': query,
        'count': len(results),
        'careers': results,
    })
