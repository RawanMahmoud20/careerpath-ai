import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from dashboard.models import UserTaskProgress, UserProfile


@login_required
def roadmap(request):
    user = request.user
    plan = None
    ai_roadmap = None

    try:
        from analysis.models import CareerTransitionPlan, AIRecommendation
        plan = CareerTransitionPlan.objects.filter(user=user).order_by('-created_at').first()

        if plan:
            ai_rec = AIRecommendation.objects.filter(
                user=user,
                target_career=plan.target_career,
                recommendation_type='roadmap'
            ).order_by('-created_at').first()

            if ai_rec:
                try:
                    ai_roadmap = json.loads(ai_rec.content)
                except Exception:
                    ai_roadmap = None
    except Exception:
        pass

    progress_qs = UserTaskProgress.objects.filter(user=user)
    progress_map = {p.task_ref: p.status for p in progress_qs}

    phases_with_stats = []
    if ai_roadmap and 'phases' in ai_roadmap:
        for phase in ai_roadmap['phases']:
            tasks = phase.get('tasks', [])
            total = len(tasks)

            for t in tasks:
                t['status'] = progress_map.get(t['ref'], 'not_started')

            completed = sum(1 for t in tasks if t['status'] == 'completed')
            pct = int((completed / total) * 100) if total > 0 else 0

            phases_with_stats.append({
                **phase,
                'tasks': tasks,
                'completed': completed,
                'total': total,
                'pct': pct,
            })

    all_tasks = sum(p['total'] for p in phases_with_stats)
    all_done = sum(p['completed'] for p in phases_with_stats)
    overall_pct = int((all_done / all_tasks) * 100) if all_tasks > 0 else 0

    context = {
        'plan': plan,
        'phases': phases_with_stats,
        'overall_pct': overall_pct,
        'all_done': all_done,
        'all_tasks': all_tasks,
    }
    return render(request, 'roadmap/roadmap.html', context)


@login_required
def skills_selection(request):
    """Display the skill selection page for the user"""
    return render(request, 'roadmap/skills_selection.html')


@login_required
@require_POST
def save_skills(request):
    try:
        data = json.loads(request.body)
        selected_skills = data.get('skills', [])

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.skills = selected_skills
        profile.save()

        return JsonResponse({
            'success': True,
            'redirect_url': '/roadmap/'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})