from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from dashboard.models import UserTaskProgress


@login_required
def roadmap(request):
    user = request.user
    plan = None
    ai_roadmap = None

    try:
        from apps.analysis.models import CareerTransitionPlan, AIRecommendation
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
            completed = sum(1 for t in tasks if progress_map.get(t['ref']) == 'completed')
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
        'progress_map': progress_map,
        'overall_pct': overall_pct,
        'all_done': all_done,
        'all_tasks': all_tasks,
    }
    return render(request, 'roadmap/roadmap.html', context)