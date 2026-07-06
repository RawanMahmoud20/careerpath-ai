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

            # تجهيز مصفوفة المهام بالهيكلية المتوافقة مع الـ Template الجديد
            formatted_tasks = []
            for t in tasks:
                status = progress_map.get(t['ref'], 'not_started')
                formatted_tasks.append({
                    'task': {
                        'task_ref': t['ref'],
                        'title': t['title'],
                        'description': t.get('description', '')
                    },
                    'status': status
                })

            completed = sum(1 for t in tasks if progress_map.get(t['ref'], 'not_started') == 'completed')
            pct = int((completed / total) * 100) if total > 0 else 0

            phases_with_stats.append({
                'phase': {
                    'phase_number': len(phases_with_stats) + 1,
                    'title': phase.get('title', ''),
                    'description': phase.get('description', '')
                },
                'tasks': formatted_tasks,
                'completed': completed,
                'total': total,
                'pct': pct,
            })

    all_tasks = sum(p['total'] for p in phases_with_stats)
    all_done = sum(p['completed'] for p in phases_with_stats)
    overall_pct = int((all_done / all_tasks) * 100) if all_tasks > 0 else 0

    # جلب التوصية القادمة من الـ Plan أو وضع نص افتراضي ذكي
    next_step = "Focus on completing your current active tasks to bridge your skill gaps!"
    if plan and plan.target_career:
        next_step = f"Continue following your customized plan to unlock your potential as a {plan.target_career.title}."

    # تجهيز الـ Context ليتوافق بالملي مع التصميم الجديد
    context = {
        'career': plan.target_career if plan else None,
        'overall': overall_pct,
        'completed_tasks': all_done,
        'total_tasks': all_tasks,
        'phases_data': phases_with_stats,
        'next_step': next_step
    }
    return render(request, 'roadmap/roadmap.html', context)





@login_required
@require_POST
def update_task_progress(request):
    task_ref = request.POST.get('task_ref')
    status = request.POST.get('status')
    
    if not task_ref or not status:
        return JsonResponse({'ok': False, 'error': 'Missing data'}, status=400)
        
    # تحديث أو إنشاء حالة المهمة للمستخدم الحالي في الداتا بيز
    progress, created = UserTaskProgress.objects.update_or_create(
        user=request.user,
        task_ref=task_ref,
        defaults={'status': status}
    )
    
    return JsonResponse({'ok': True})