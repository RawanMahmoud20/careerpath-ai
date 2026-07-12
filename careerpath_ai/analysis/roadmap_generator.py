"""
Gemini-powered roadmap generator.
Saves results to analysis.models.UserRoadmap.
"""
import json
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from careers.models import Career, CareerSkill
from skills.models import UserSkill
from analysis.models import UserRoadmap, SkillGap  
from dashboard.models import UserTaskProgress     

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a career development expert. Generate a structured learning roadmap.

YOU MUST RESPOND ONLY WITH A VALID JSON OBJECT. No text before or after the JSON.

Use EXACTLY this structure:
{
  "phases": [
    {
      "title": "Phase Title",
      "description": "Phase description",
      "tasks": [
        {
          "ref": "skillname-task-number (CRITICAL REQUIREMENT: This field must be strictly lowercase, use hyphens, and start EXACTLY with the missing skill name slug, e.g., 'flutter-task-1', 'flutter-task-2', or 'figma-task-1'). If a task does not directly map to a specific missing skill, use 'general-task-x'",
          "title": "Task Title",
          "description": "Task description",
          "estimated_time": "e.g. 2 weeks"
        }
      ]
    }
  ]
}

Rules:
- 3-5 phases, each with 2-4 tasks
- Logical beginner-to-advanced progression
- Every task must have ref, title, description, estimated_time
- CRITICAL: The "ref" prefix must start strictly with the exact missing skill name in lowercase so our tracker can parse it.
- Return ONLY valid JSON parseable by json.loads()"""


def _user_prompt(career_title: str, missing_skills: list[str]) -> str:
    skills_str = ", ".join(missing_skills) if missing_skills else "general concepts"
    return (
        f"Create a learning roadmap for target career: {career_title}\n\n"
        f"The user is MISSING the following skills which you MUST build the tasks and 'ref' field prefixes around: {skills_str}\n\n"
        "Generate a practical, step-by-step roadmap. Ensure every task has the correct 'ref' prefix based on the skill it teaches. Return ONLY the JSON object."
    )

# ──────────────────────────────────────────────────────────────────────────────
# Gemini call
# ──────────────────────────────────────────────────────────────────────────────
def _call_gemini(career_title: str, missing_skills: list[str]) -> dict:
    """Call the modern Gemini API using google-genai SDK cleanly."""
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        raise ImproperlyConfigured('GEMINI_API_KEY is not set in settings / .env')

    # الاستيراد النظيف من المكتبة الجديدة حصراً 
    from google import genai
    from google.genai import types

    # إنشاء العميل النقي
    client = genai.Client(api_key=api_key)
    
    full_prompt = f"{SYSTEM_PROMPT}\n\nTask instructions:\n" + _user_prompt(career_title, missing_skills)

    # 🎯 إعداد الـ Schema الصارمة لإجبار جميناي على الالتزام بالقالب ومنع الهلوسة خارج الـ JSON
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.1,  # خفض الحرارة لمنع الشطحات والنصوص العشوائية
        response_schema={
            "type": "OBJECT",
            "properties": {
                "phases": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "title": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "tasks": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "ref": {"type": "STRING"},
                                        "title": {"type": "STRING"},
                                        "description": {"type": "STRING"},
                                        "estimated_time": {"type": "STRING"}
                                    },
                                    "required": ["ref", "title", "description", "estimated_time"]
                                }
                            }
                        },
                        "required": ["title", "description", "tasks"]
                    }
                }
            },
            "required": ["phases"]
        }
    )

    # 🎯 الموديل الرسمي المستقر والمجاني كلياً حالياً للمشاريع الجديدة
    response = client.models.generate_content(
        model='gemini-3.5-flash', 
        contents=full_prompt,
        config=config,
    )
    
    raw = response.text or ''
    raw = raw.strip()

    if raw.startswith('```'):
        lines = raw.splitlines()
        raw = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

    try:
        roadmap = json.loads(raw)
    except json.JSONDecodeError as je:
        print(f"❌ [Gemini Modern JSON Error] Raw Text was: {raw}")
        raise je

    return roadmap

def _fallback_roadmap(career_title: str, missing_skills: list[str]) -> dict:
    """Static fallback used ONLY when Gemini fails, now dynamically matching missing skills."""
    # نأخذ أول مهارة مفقودة إذا وجدت كبادئة احتياطية، وإلا نستخدم اسم الكارير
    primary_skill = missing_skills[0].lower() if missing_skills else career_title.lower().replace(' ', '-')
    
    return {
        'phases': [
            {
                'title': f'Foundations of {career_title}',
                'description': f'Build core knowledge required for {career_title}.',
                'tasks': [
                    {
                        'ref': f'{primary_skill}-task-1',
                        'title': 'Study core concepts',
                        'description': f'Learn the fundamental concepts that every {career_title} must know.',
                        'estimated_time': '2 weeks',
                    },
                    {
                        'ref': f'{primary_skill}-task-2',
                        'title': 'Set up your environment',
                        'description': 'Install and configure the tools and software you will use daily.',
                        'estimated_time': '3 days',
                    },
                ],
            },
            {
                'title': 'Hands-on Practice & Mini Projects',
                'description': 'Apply what you have learned through guided exercises.',
                'tasks': [
                    {
                        'ref': f'{primary_skill}-task-3',
                        'title': 'Complete beginner exercises',
                        'description': 'Work through structured exercises to solidify your understanding.',
                        'estimated_time': '2 weeks',
                    },
                    {
                        'ref': f'{primary_skill}-task-4',
                        'title': 'Build a mini project',
                        'description': f'Create a small project that showcases basic {career_title} skills.',
                        'estimated_time': '1 week',
                    },
                ],
            },
        ]
    }

# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────
def generate_and_save_roadmap(user, career: Career) -> dict:
    """
    Generate (or regenerate) an AI roadmap for *user* targeting *career*.
    🎯 Feature 1: Prevents regeneration if currently active career is 100% ready.
    🎯 Feature 2: If switching back to a career where the user already has ALL required skills 
                 at 'advanced' level, it restores the 100% status immediately without calling Gemini or resetting.
    """
    if not career or not career.title:
        raise ValueError('Career must have a title.')

    # 1️⃣ جلب جميع المهارات المتقدمة (Advanced) التي يمتلكها اليوزر حالياً
    advanced_user_skills = list(
        UserSkill.objects.filter(user=user, level='advanced')
        .select_related('skill')
        .values_list('skill__id', flat=True)
    )

    # 2️⃣ جلب المهارات المطلوبة للكارير الجديد الذي تم الضغط عليه
    career_skills = CareerSkill.objects.filter(career=career).select_related('skill')
    career_skill_ids = [cs.skill.id for cs in career_skills]

    # 3️⃣ الفحص الذكي: هل اليوزر يمتلك كافة مهارات هذا الكارير بمستوى Advanced مسبقاً؟
    is_already_fully_qualified = all(sk_id in advanced_user_skills for sk_id in career_skill_ids) if career_skill_ids else False

    if is_already_fully_qualified:
        # 🎉 اليوزر جاهز 100% مسبقاً لهذا الكارير! نقوم بإعادة بناء الحالة فوراً بدون تصفير أو مناداة جميناي
        logger.info(f"User {user.email} is already 100% qualified for {career.title}. Restoring state.")
        
        # نقوم بإنشاء/تحديث الـ Roadmap لتصبح 100% مع JSON افتراضي نظيف (لأنه لا يحتاج لتاسكات)
        completed_roadmap_json = {
            "career": career.title,
            "phases": [{"phase_number": 1, "phase_title": "Completed", "tasks": []}]
        }
        
        UserRoadmap.objects.update_or_create(
            user=user,
            defaults={
                'career': career,
                'roadmap_json': json.dumps(completed_roadmap_json),
                'readiness_score': 100, 
            },
        )
        return completed_roadmap_json

    # 4️⃣ اللوجيك العادي في حال الكارير جديد واليوزر مش جاهز فيه 100%:
    existing_roadmap = UserRoadmap.objects.filter(user=user).first()
    
    if existing_roadmap:
        # منع التوليد إذا حاول إعادة توليد نفس الكارير الحالي الجاهز فيه 100%
        if existing_roadmap.readiness_score == 100 and existing_roadmap.career_id == career.id:
            raise ValueError(
                f"🎯 Congratulations! You have already achieved 100% job readiness for the {existing_roadmap.career.title} path. "
                f"Regeneration is disabled because you are completely ready for the job market!"
            )

        # حذف بيانات التتبع القديمة فقط لو الكارير مختلف واليوزر مش جاهز فيه 100%
        if existing_roadmap.career_id != career.id:
            SkillGap.objects.filter(roadmap=existing_roadmap).delete()
            UserTaskProgress.objects.filter(user=user).delete()
            logger.info(f"Cleared old tracking data due to career switch to: {career.title}")

    # 5️⃣ تحديد المهارات المفقودة (المتبقية) للكارير الجديد لبناء البرومبت
    all_user_skills = list(
        UserSkill.objects.filter(user=user)
        .select_related('skill')
        .values_list('skill__name', flat=True)
    )
    missing_skills = [cs.skill.name for cs in career_skills if cs.skill.name not in all_user_skills]

    # 6️⃣ استدعاء الـ AI لبناء الخطة للمهارات المفقودة
    try:
        roadmap = _call_gemini(career.title, missing_skills)
        logger.info('Gemini roadmap generated successfully.')
    except Exception as exc:
        logger.error('Gemini execution failed: %s. Falling back to structured default.', exc)
        roadmap = _fallback_roadmap(career.title, missing_skills)

    # 7️⃣ حفظ البيانات للكارير الجديد مع سكور 0 لتبدأ رحلة التعلم فيه
    UserRoadmap.objects.update_or_create(
        user=user,
        defaults={
            'career': career,
            'roadmap_json': json.dumps(roadmap),
            'readiness_score': 0, 
        },
    )

    return roadmap