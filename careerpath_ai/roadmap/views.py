import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from analysis.models import UserRoadmap, SkillGap
from dashboard.models import UserTaskProgress
from skills.models import Skill, UserSkill 


@login_required
def roadmap(request):
    user = request.user

    try:
        user_roadmap = UserRoadmap.objects.select_related('career').get(user=user)
    except UserRoadmap.DoesNotExist:
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
    user = request.user
    task_ref = request.POST.get('task_ref')
    status   = request.POST.get('status')

    # 📝 جملة طباعة لمراقبة الضغط بالترمينال
    print("\n" + "="*50)
    print(f"🚀 [CHECKBOX CLICKED] Task Ref: '{task_ref}' | Status: '{status}'")
    print("="*50)

    if not task_ref or not status:
        return JsonResponse({'ok': False, 'error': 'Missing data'}, status=400)

    # 1. تحديث أو إنشاء حالة المهمة الحالية
    UserTaskProgress.objects.update_or_create(
        user=user,
        task_ref=task_ref,
        defaults={'status': status},
    )

    # 2. فحص اكتمال المهارة التابعة للمهمة إذا تم تحديدها كـ completed
    if status == 'completed':
        try:
            # قص البادئة (مثال: من "flutter-task-1" نأخذ "flutter")
            skill_prefix = task_ref.split('-')[0]
            print(f"🔍 Skill Prefix Extracted: '{skill_prefix}'")
            
            user_roadmap = UserRoadmap.objects.get(user=user)
            ai_roadmap = json.loads(user_roadmap.roadmap_json)
            
            # أ) حساب عدد المهام الكلية في الـ JSON التي تبدأ بنفس اسم المهارة
            total_skill_tasks = 0
            for phase in ai_roadmap.get('phases', []):
                for task in phase.get('tasks', []):
                    ref = task.get('ref', '')
                    if ref.lower().startswith(f"{skill_prefix.lower()}-"):
                        total_skill_tasks += 1

            print(f"📊 [Total Tasks in JSON] for '{skill_prefix}': {total_skill_tasks}")

            # b) حساب عدد المهام التي أكملها المستخدم بالفعل في قاعدة البيانات وتخص المهارة
            completed_skill_tasks = UserTaskProgress.objects.filter(
                user=user,
                task_ref__istartswith=f"{skill_prefix}-",
                status='completed'
            ).count()

            print(f"✅ [Completed Tasks in DB] for '{skill_prefix}': {completed_skill_tasks}")

            # ج) إذا تساوى العددين، المهارة اكتملت بالكامل!
            if total_skill_tasks > 0 and completed_skill_tasks == total_skill_tasks:
                print(f"🎉 All tasks for '{skill_prefix}' are done! Upgrading skill...")
                
                # البحث عن المهارة الأصلية في السيستم
                skill_obj = Skill.objects.filter(name__icontains=skill_prefix).first()
                print(f"🎯 Found Skill Object: {skill_obj}")
                
                if skill_obj:
                    # تحديث الـ SkillGap الجديد باستخدام الـ ForeignKey
                    SkillGap.objects.filter(roadmap=user_roadmap, skill=skill_obj).update(is_mastered=True)
                    
                    # 🎯 التعديل الجوهري: تحديث المستوى إلى advanced بشكل إجباري ومضمون
                    user_skill, created = UserSkill.objects.update_or_create(
                        user=user,
                        skill=skill_obj,
                        defaults={'level': 'advanced'}
                    )
                    print(f"🔥 SUCCESS: '{skill_obj.name}' updated to ADVANCED! (Created row: {created})")
            else:
                print(f"⏳ Progress: {completed_skill_tasks}/{total_skill_tasks} tasks done for '{skill_prefix}'. Not advanced yet.")

        except Exception as e:
            print(f"💥 Error in calculation: {e}")
            import traceback
            traceback.print_exc()

    print("="*50 + "\n")
    return JsonResponse({'ok': True})