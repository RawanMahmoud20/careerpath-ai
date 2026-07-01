from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Career, SelectedCareer


@login_required
def career_list(request):
    """تعرض كل المسارات المهنية المتاحة، وتحدّد أي واحد مختار حالياً."""
    careers = Career.objects.all().prefetch_related('required_skills')

    # المسار المختار حالياً للمستخدم (إن وُجد)
    selected = SelectedCareer.objects.filter(user=request.user).first()
    selected_id = selected.career_id if selected else None

    context = {
        'careers': careers,
        'selected_id': selected_id,
    }
    return render(request, 'careers/careers.html', context)


@login_required
@require_POST
def choose_career(request, career_id):
    """يختار المستخدم مساراً مهنياً كهدف حالي."""
    career = get_object_or_404(Career, id=career_id)

    # update_or_create: لو عنده مسار سابق يحدّثه، وإلا ينشئ جديد
    SelectedCareer.objects.update_or_create(
        user=request.user,
        defaults={'career': career},
    )

    messages.success(request, f'Your target career is now: {career.title}')
    return redirect('dashboard:home')
