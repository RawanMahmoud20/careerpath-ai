import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from analysis.models import UserRoadmap
from dashboard.models import UserTaskProgress


@login_required
def roadmap(request):
    user = request.user

    try:
        user_roadmap = UserRoadmap.objects.select_related('career').get(user=user)
    except UserRoadmap.DoesNotExist:
        # User hasn't chosen a career yet
        context = {
            'career':          None,
            'overall':         0,
            'completed_tasks': 0,
            'total_tasks':     0,
            'phases_data':     [],
            'next_step':       "Choose a career goal to generate your personalised roadmap!",
        }
        return render(request, 'roadmap/roadmap.html', context)

    # Parse the stored JSON
    try:
        ai_roadmap = json.loads(user_roadmap.roadmap_json)
    except (json.JSONDecodeError, TypeError):
        ai_roadmap = {'phases': []}

    # Load progress for this user
    progress_map = {
        p.task_ref: p.status
        for p in UserTaskProgress.objects.filter(user=user)
    }

    phases_data = []
    for phase in ai_roadmap.get('phases', []):
        tasks = phase.get('tasks', [])
        total = len(tasks)
        phase_title_slug = phase.get('title', 'phase').lower().replace(' ', '-')

        formatted_tasks = []
        for idx, t in enumerate(tasks):
            task_ref = t.get('ref') or f"{phase_title_slug}-{idx + 1}"
            formatted_tasks.append({
                'task': {
                    'task_ref':    task_ref,
                    'title':       t.get('title', f'Task {idx + 1}'),
                    'description': t.get('description', ''),
                },
                'status': progress_map.get(task_ref, 'not_started'),
            })

        completed = sum(1 for t in formatted_tasks if t['status'] == 'completed')
        pct = int((completed / total) * 100) if total > 0 else 0

        phases_data.append({
            'phase': {
                'phase_number': len(phases_data) + 1,
                'title':        phase.get('title', ''),
                'description':  phase.get('description', ''),
            },
            'tasks':     formatted_tasks,
            'completed': completed,
            'total':     total,
            'pct':       pct,
        })

    all_tasks = sum(p['total'] for p in phases_data)
    all_done  = sum(p['completed'] for p in phases_data)
    overall   = int((all_done / all_tasks) * 100) if all_tasks > 0 else 0

    career = user_roadmap.career
    context = {
        'career':          career,
        'overall':         overall,
        'completed_tasks': all_done,
        'total_tasks':     all_tasks,
        'phases_data':     phases_data,
        'next_step':       (
            f"Continue your journey to become a {career.title}. "
            "Complete each phase task by task!"
        ),
    }
    return render(request, 'roadmap/roadmap.html', context)


@login_required
@require_POST
def update_task_progress(request):
    task_ref = request.POST.get('task_ref')
    status   = request.POST.get('status')

    if not task_ref or not status:
        return JsonResponse({'ok': False, 'error': 'Missing data'}, status=400)

    UserTaskProgress.objects.update_or_create(
        user=request.user,
        task_ref=task_ref,
        defaults={'status': status},
    )
    return JsonResponse({'ok': True})