from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from dashboard.models import UserTaskProgress


@login_required
def dashboard(request):
    user = request.user

    plan = None
    latest_ai = None

    try:
        from analysis.models import CareerTransitionPlan, AIRecommendation
        plan = CareerTransitionPlan.objects.filter(user=user).order_by('-created_at').first()
        latest_ai = AIRecommendation.objects.filter(user=user).order_by('-created_at').first()
    except Exception:
        pass

    all_progress    = UserTaskProgress.objects.filter(user=user)
    total_tasks     = all_progress.count()
    completed_tasks = all_progress.filter(status='completed').count()
    inprog_tasks    = all_progress.filter(status='in_progress').count()
    progress_pct    = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    context = {
        'plan':            plan,
        'latest_ai':       latest_ai,
        'total_tasks':     total_tasks,
        'completed_tasks': completed_tasks,
        'inprog_tasks':    inprog_tasks,
        'progress_pct':    progress_pct,
        'all_progress': all_progress, 
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
@require_POST
def update_task_status(request):
    try:
        data     = json.loads(request.body)
        task_ref = data.get('task_ref')
        status   = data.get('status')

        if not task_ref or status not in ['not_started', 'in_progress', 'completed']:
            return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

        obj, _ = UserTaskProgress.objects.get_or_create(
            user=request.user,
            task_ref=task_ref,
        )
        obj.status = status
        obj.save()

        return JsonResponse({'success': True, 'status': obj.status})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)