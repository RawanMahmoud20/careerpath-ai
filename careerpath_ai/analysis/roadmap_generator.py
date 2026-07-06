"""
Gemini-powered roadmap generator.
Saves results to analysis.models.UserRoadmap.
"""
import json
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from careers.models import Career
from skills.models import UserSkill
from .models import UserRoadmap

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
- Every task must have title, description, estimated_time
- Return ONLY valid JSON parseable by json.loads()"""


def _user_prompt(career_title: str, user_skills: list[str]) -> str:
    skills_str = ", ".join(user_skills) if user_skills else "No prior skills"
    return (
        f"Create a learning roadmap for: {career_title}\n\n"
        f"User's current skills: {skills_str}\n\n"
        "Generate a practical, step-by-step roadmap. Return ONLY the JSON object."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Gemini call
# ──────────────────────────────────────────────────────────────────────────────

def _call_gemini(career_title: str, user_skills: list[str]) -> dict:
    """Call Gemini API. Returns parsed roadmap dict, or raises on failure."""
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        raise ImproperlyConfigured('GEMINI_API_KEY is not set in settings / .env')

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=SYSTEM_PROMPT,
    )

    response = model.generate_content(_user_prompt(career_title, user_skills))
    raw = getattr(response, 'text', '') or ''

    # Strip markdown code fences if Gemini wraps the JSON
    raw = raw.strip()
    if raw.startswith('```'):
        lines = raw.splitlines()
        raw = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

    roadmap = json.loads(raw)

    if not isinstance(roadmap.get('phases'), list) or not roadmap['phases']:
        raise ValueError('Gemini response has no phases list')

    return roadmap


def _fallback_roadmap(career_title: str) -> dict:
    """Static fallback used ONLY when Gemini fails."""
    return {
        'phases': [
            {
                'title': f'Foundations of {career_title}',
                'description': f'Build core knowledge required for {career_title}.',
                'tasks': [
                    {
                        'title': 'Study core concepts',
                        'description': f'Learn the fundamental concepts that every {career_title} must know.',
                        'estimated_time': '2 weeks',
                    },
                    {
                        'title': 'Set up your environment',
                        'description': 'Install and configure the tools and software you will use daily.',
                        'estimated_time': '3 days',
                    },
                ],
            },
            {
                'title': 'Hands-on Practice',
                'description': 'Apply what you have learned through guided exercises.',
                'tasks': [
                    {
                        'title': 'Complete beginner exercises',
                        'description': 'Work through structured exercises to solidify your understanding.',
                        'estimated_time': '2 weeks',
                    },
                    {
                        'title': 'Build a mini project',
                        'description': f'Create a small project that showcases basic {career_title} skills.',
                        'estimated_time': '1 week',
                    },
                ],
            },
            {
                'title': 'Portfolio & Job Readiness',
                'description': 'Prepare yourself for interviews and real-world work.',
                'tasks': [
                    {
                        'title': 'Build a portfolio project',
                        'description': 'Create a polished project you can show to employers.',
                        'estimated_time': '3 weeks',
                    },
                    {
                        'title': 'Practice interview questions',
                        'description': f'Review common {career_title} interview questions and practice answering them.',
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
    Saves the result to UserRoadmap (upsert — one row per user).
    Returns the roadmap dict.
    """
    if not career or not career.title:
        raise ValueError('Career must have a title.')

    user_skills = list(
        UserSkill.objects.filter(user=user)
        .select_related('skill')
        .values_list('skill__name', flat=True)
    )

    # Try Gemini first, fall back gracefully
    try:
        roadmap = _call_gemini(career.title, user_skills)
        logger.info('Gemini roadmap generated for %s → %s', user.email, career.title)
    except Exception as exc:
        logger.error('Gemini failed for %s → %s: %s', user.email, career.title, exc, exc_info=True)
        roadmap = _fallback_roadmap(career.title)
        logger.warning('Using fallback roadmap for %s → %s', user.email, career.title)

    # Upsert: one row per user, always pointing to the current career
    UserRoadmap.objects.update_or_create(
        user=user,
        defaults={
            'career': career,
            'roadmap_json': json.dumps(roadmap),
            'readiness_score': 0,
        },
    )

    return roadmap
