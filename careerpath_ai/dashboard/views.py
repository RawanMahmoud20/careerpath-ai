import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from analysis.models import UserRoadmap # تأكد من استيراد الموديل الصحيح عندك
from dashboard.models import UserProfile, UserTaskProgress
from skills.models import Skill, UserSkill
from careers.models import Career, CareerSkill
from analysis.models import UserRoadmap, SkillGap
from analysis.roadmap_generator import generate_and_save_roadmap


@login_required
def dashboard(request):
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)

    try:
        user_roadmap = UserRoadmap.objects.select_related('career').get(user=user)
        target_career = user_roadmap.career
        readiness     = user_roadmap.readiness_score or 0
    except UserRoadmap.DoesNotExist:
        target_career = None
        readiness     = 0

    matched_count = 0
    missing_count = 0

    if target_career:
        user_skill_names = set(
            UserSkill.objects.filter(user=user).values_list('skill__name', flat=True)
        )
        req_skill_names = set(
            CareerSkill.objects.filter(career=target_career).values_list('skill__name', flat=True)
        )
        matched_count = len(user_skill_names & req_skill_names)
        missing_count = len(req_skill_names - user_skill_names)

    context = {
        'profile':       profile_obj,
        'target_career': target_career,
        'readiness':     readiness,
        'matched_count': matched_count,
        'missing_count': missing_count,
        'careers':       Career.objects.all(),
    }
    return render(request, 'dashboard/dashboard.html', context)
@login_required
def select_career(request, career_id):  # أو choose_career حسب اسم الـ view عندك
    if request.method == 'POST':
        try:
            career = get_object_or_404(Career, id=career_id)
            
            # 1️⃣ جلب جميع المهارات المتقدمة (Advanced) التي يمتلكها اليوزر حالياً
            from skills.models import UserSkill
            from careers.models import CareerSkill
            from dashboard.models import UserTaskProgress
            from analysis.models import UserRoadmap

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
            
            if not existing_roadmap or existing_roadmap.career_id != career.id:
                
                # حذف بيانات التتبع القديمة للكارير السابق
                UserTaskProgress.objects.filter(user=request.user).delete()
                
                if is_already_fully_qualified:
                    # 🎉 حالة خاصة: اليوزر جاهز 100% مسبقاً! نثبت السكور 100 فوراً بالداشبورد
                    completed_roadmap_json = {
                        "career": career.title,
                        "phases": [{"phase_number": 1, "phase_title": "Completed", "tasks": []}]
                    }
                    UserRoadmap.objects.update_or_create(
                        user=request.user,
                        defaults={
                            'career': career,
                            'roadmap_json': json.dumps(completed_roadmap_json),
                            'readiness_score': 100,  # 🔥 هان السر! ثبتناها 100% علطول بالداتابيز
                        }
                    )
                    messages.success(request, f"🎯 Outstanding! You are already 100% qualified for {career.title}.")
                else:
                    # اللوجيك العادي لو الكارير جديد واليوزر مش جاهز فيه لسا
                    UserRoadmap.objects.update_or_create(
                        user=request.user,
                        defaults={
                            'career': career,
                            'roadmap_json': '',     # تصفير النص للتوليد اليدوي لاحقاً
                            'readiness_score': 0,   # يبدأ من 0% لأنه بحاجة لتوليد مهام
                        }
                    )
                    messages.success(request, f"Target career switched to {career.title}. Go to Skill Gap to generate your roadmap!")
            else:
                messages.info(request, f"Current career is already set to {career.title}.")

            return redirect('/dashboard/')

        except Exception as e:
            messages.error(request, f"Error selecting career: {e}")

    return redirect('/dashboard/')
@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.full_name = request.POST.get('full_name', '')
        user.save()
        profile.current_field    = request.POST.get('current_field', '')
        profile.experience_level = request.POST.get('experience_level', 'beginner')
        profile.save()
        return redirect('/dashboard/')

    return render(request, 'dashboard/profile.html', {'profile': profile})


# ──────────────────────────────────────────────────────────────────────────────
# 🎯 إدراج الفيو المسؤول عن معالجة الـ Checkbox للـ Tasks وتحديث الـ Skills
# ──────────────────────────────────────────────────────────────────────────────
@login_required
@require_POST
def update_task_progress(request):
    user = request.user
    task_ref = request.POST.get('task_ref')
    status   = request.POST.get('status')

    print("\n" + "="*50)
    print(f"🚀 [CHECKBOX CLICKED] User: {user.email}")
    print(f"📦 Task Ref: '{task_ref}' | Status Sent: '{status}'")
    print("="*50)

    if not task_ref or not status:
        print("❌ Missing task_ref or status in POST data")
        return JsonResponse({'ok': False, 'error': 'Missing data'}, status=400)

    # 1. تحديث أو إنشاء حالة تقدم المهمة
    progress_obj, created = UserTaskProgress.objects.update_or_create(
        user=user,
        task_ref=task_ref,
        defaults={'status': status},
    )
    print(f"💾 UserTaskProgress row - Created: {created} | Current Status: {progress_obj.status}")

    # 2. اللوجيك الذكي عند اكتمال التاسك
    if status == 'completed':
        try:
            # استخراج الـ prefix (مثال: من 'python-task-1' يستخرج 'python')
            skill_prefix = task_ref.split('-')[0].lower()
            print(f"🔍 Extracted Skill Prefix: '{skill_prefix}'")
            
            user_roadmap = UserRoadmap.objects.get(user=user)
            ai_roadmap = json.loads(user_roadmap.roadmap_json)
            
            # أ) حساب إجمالي المهام في الـ JSON التي تبدأ بنفس اسم المهارة
            total_skill_tasks = 0
            for phase in ai_roadmap.get('phases', []):
                for task in phase.get('tasks', []):
                    ref = task.get('ref', '')
                    if ref.lower().startswith(f"{skill_prefix}-"):
                        total_skill_tasks += 1

            print(f"📊 [JSON Analysis] Total tasks found for '{skill_prefix}': {total_skill_tasks}")

            # ب) حساب المهام المكتملة في قاعدة البيانات لهذه المهارة
            completed_skill_tasks = UserTaskProgress.objects.filter(
                user=user,
                task_ref__istartswith=f"{skill_prefix}-",
                status='completed'
            ).count()

            print(f"✅ [DB Analysis] Completed tasks found in DB for '{skill_prefix}': {completed_skill_tasks}")

            # ج) الفحص والمقارنة
            if total_skill_tasks > 0 and completed_skill_tasks == total_skill_tasks:
                print(f"🎉 SUCCESS! Total matches Completed ({completed_skill_tasks} == {total_skill_tasks})")
                
                # البحث عن المهارة في جدول المهارات
                skill_obj = Skill.objects.filter(name__icontains=skill_prefix).first()
                print(f"🎯 Matching Skill Object found in DB: {skill_obj}")
                
                if skill_obj:
                    # تحديث الفجوة
                    gaps_updated = SkillGap.objects.filter(roadmap=user_roadmap, skill=skill_obj).update(is_mastered=True)
                    print(f"🔄 SkillGap Rows updated to mastered: {gaps_updated}")
                    
                    # التحديث الإجباري للمستوى إلى advanced
                    user_skill, skill_created = UserSkill.objects.update_or_create(
                        user=user,
                        skill=skill_obj,
                        defaults={'level': 'advanced'}
                    )
                    print(f"🔥 UserSkill Updated/Created! - Created: {skill_created} | Final Level: {user_skill.level}")
            else:
                print(f"⏳ Not yet completed. Need {total_skill_tasks}, but have {completed_skill_tasks}")

        except Exception as e:
            print(f"💥 Exception crashed inside status=='completed': {e}")
            import traceback
            traceback.print_exc()

    print("="*50 + "\n")
    return JsonResponse({'ok': True})