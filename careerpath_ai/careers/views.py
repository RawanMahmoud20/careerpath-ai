from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q

from .models import Career
from skills.models import UserSkill
from careers.models import  CareerSkill
from analysis.models import UserRoadmap
from dashboard.models import UserTaskProgress
from analysis.models import UserRoadmap
from analysis.roadmap_generator import generate_and_save_roadmap

from dashboard.models import UserTaskProgress
from analysis.models import UserRoadmap
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
        # 1️⃣ جلب جميع المهارات المتقدمة (Advanced) التي يمتلكها اليوزر حالياً
        advanced_user_skills = list(
            UserSkill.objects.filter(user=request.user, level='advanced')
            .select_related('skill')
            .values_list('skill__id', flat=True)
        )

        # 2️⃣ جلب المهارات المطلوبة للكارير المختار
        career_skills = CareerSkill.objects.filter(career=career).select_related('skill')
        career_skill_ids = [cs.skill.id for cs in career_skills]

        # 3️⃣ الفحص الذكي: هل اليوزر يمتلك كافة مهارات هذا الكارير بمستوى Advanced مسبقاً؟
        is_already_fully_qualified = all(sk_id in advanced_user_skills for sk_id in career_skill_ids) if career_skill_ids else False

        existing_roadmap = UserRoadmap.objects.filter(user=request.user).first()
        
        # لو اليوزر اختار كارير جديد تماماً أو لسا ما عنده خطة من أصلو
        if not existing_roadmap or existing_roadmap.career_id != career.id:
            
            print(f"\n🔄 [CAREER CHANGED FROM CAREERS PAGE] Switched to: '{career.title}'")
            
            # القضاء على التقدم القديم للكارير السابق
            deleted_progress, _ = UserTaskProgress.objects.filter(user=request.user).delete()
            print(f"🧹 Cleaned up {deleted_progress} old tasks from UserTaskProgress.")
            
            if is_already_fully_qualified:
                # 🎉 حالة خاصة: اليوزر جاهز 100% مسبقاً! نثبت السكور 100 فوراً بالداتابيز لتظهر بالداشبورد
                completed_roadmap_json = {
                    "career": career.title,
                    "phases": [{"phase_number": 1, "phase_title": "Completed", "tasks": []}]
                }
                UserRoadmap.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'career': career,
                        'roadmap_json': json.dumps(completed_roadmap_json),
                        'readiness_score': 100,  # 🔥 هان السر! بتظهر 100% علطول بالداشبورد والـ Roadmap
                    }
                )
                print(f"✅ UserRoadmap marked as 100% qualified directly.\n")
                messages.success(request, f"🎯 Outstanding! You are already 100% qualified for {career.title}.")
            else:
                # اللوجيك العادي لو الكارير جديد واليوزر مش جاهز فيه لسا ومحتاج توليد
                UserRoadmap.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'career': career,
                        'roadmap_json': '',     # تصفير النص للتوليد اليدوي لاحقاً في صفحة الـ Skill Gap
                        'readiness_score': 0,   # يبدأ من 0%
                    }
                )
                print(f"✅ UserRoadmap wiped and updated. Ready for manual AI generation via Skill Gap.\n")
                messages.success(
                    request,
                    f"Target career switched to {career.title}. Review your skill gaps and generate your roadmap!",
                )
        else:
            # لو اختار نفس الكارير الحالي من صفحة الـ Careers، تظل بياناته كما هي دون أي تصفير أو توليد
            messages.info(request, f"Current career is already set to {career.title}.")

    except Exception as e:
        messages.error(request, f"Error selecting career from Careers page: {e}")

    return redirect('/careers/')


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
