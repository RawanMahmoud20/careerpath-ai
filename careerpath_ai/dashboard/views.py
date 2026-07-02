from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from dashboard.models import UserTaskProgress, UserProfile


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
        

@login_required
def profile(request):
    """صفحة الملف الشخصي: تعرض/تعدّل الاسم والمجال ومستوى الخبرة."""
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # تحديث الاسم
        full_name = request.POST.get('full_name', '').strip()
        user.full_name = full_name
        user.save()

        # تحديث المجال الحالي ومستوى الخبرة
        profile_obj.current_field = request.POST.get('current_field', '').strip()
        profile_obj.experience_level = request.POST.get('experience_level', 'beginner')
        profile_obj.save()

        messages.success(request, 'Your profile has been updated.')
        return redirect('dashboard:profile')

    # المسار المختار (للعرض في القائمة الجانبية)
    plan = None
    try:
        from analysis.models import CareerTransitionPlan
        plan = CareerTransitionPlan.objects.filter(user=user).order_by('-created_at').first()
    except Exception:
        pass

    context = {
        'profile': profile_obj,
        'plan': plan,
    }
    return render(request, 'dashboard/profile.html', context)