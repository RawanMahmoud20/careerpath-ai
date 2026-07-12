import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from analysis.models import UserRoadmap, SkillGap
from dashboard.models import UserTaskProgress
from skills.models import Skill, UserSkill 


@login_required
def view_roadmap(request):
    user = request.user
    
    # 1. جلب الكارير النشط
    profile = getattr(user, 'user_profile', None) or getattr(user, 'profile', None)
    career = getattr(profile, 'target_career', None) if profile else None
    
    if not career:
        # fallback
        roadmap = UserRoadmap.objects.filter(user=user).first()
        career = roadmap.career if roadmap else None
    else:
        roadmap = UserRoadmap.objects.filter(user=user, career=career).first()
        
    phases_data = []
    total_tasks = 0
    completed_tasks = 0
    overall = 0
    
    if roadmap and roadmap.roadmap_json:
        try:
            # تحليل الـ JSON القادم من جميناي
            data = json.loads(roadmap.roadmap_json)
            phases_data = data.get('phases', [])
            
            # 🎯 جلب كافة المهارات التي أكملها المستخدم مسبقاً من قاعدة البيانات دفعة واحدة لتسريع الأداء
            user_progress_dict = {
                progress.task_ref: progress.status 
                for progress in UserTaskProgress.objects.filter(user=user)
            }
            
            # قراءة وربط الحالات الحقيقية من الداتابيز بالـ JSON المعروض
            for phase in phases_data:
                tasks = phase.get('tasks', [])
                total_tasks += len(tasks)
                
                phase_completed = 0
                for t in tasks:
                    ref_key = t.get('ref', '')
                    # 🎯 دمج الحالة المخزنة بالـ DB بداخل أوبجكت الـ JSON الحالي
                    db_status = user_progress_dict.get(ref_key, 'not_started')
                    t['status'] = db_status
                    
                    if db_status == 'completed':
                        completed_tasks += 1
                        phase_completed += 1
                
                # إرسال العداد الفعلي للمرحلة الحالية ليفهمه الـ Template والـ JS
                phase['completed'] = phase_completed
                phase['total'] = len(tasks)
                        
            if total_tasks > 0:
                overall = int((completed_tasks / total_tasks) * 100)
        except Exception as e:
            print(f"❌ Error parsing JSON in roadmap view: {e}")

    context = {
        'career': career,
        'roadmap': roadmap,
        'phases_data': phases_data,
        'total_tasks': total_tasks,      
        'completed_tasks': completed_tasks,
        'overall': overall,
        'readiness_score': roadmap.readiness_score if roadmap else 0,
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

    # 1. تحديث أو إنشاء حالة المهمة الحالية في جدول التقدم
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
            
            user_roadmap = UserRoadmap.objects.filter(user=user).first()
            if user_roadmap and user_roadmap.roadmap_json:
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
                        
                        # تحديث المستوى إلى advanced بشكل إجباري ومضمون
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