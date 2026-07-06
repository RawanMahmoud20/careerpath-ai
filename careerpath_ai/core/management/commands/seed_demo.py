"""
Seed demo careers, skills, and a sample roadmap for local development / testing.

Usage:
    python manage.py seed_demo
"""
import json

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from careers.models import Career, CareerSkill
from skills.models import Skill, UserSkill
from analysis.models import UserRoadmap
from dashboard.models import UserTaskProgress


class Command(BaseCommand):
    help = 'Seed demo careers, skills, and a sample roadmap.'

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        # ── Demo user ────────────────────────────────────────────────────────
        user, created = User.objects.get_or_create(
            email='demo@example.com',
            defaults={'full_name': 'Demo User'},
        )
        if created:
            user.set_password('demo12345')
            user.save()
            self.stdout.write('  Created demo user (demo@example.com / demo12345)')

        # ── Skills ───────────────────────────────────────────────────────────
        skills_data = [
            ('Python',             'Technical'),
            ('SQL',                'Technical'),
            ('Excel',              'Technical'),
            ('Data Visualization', 'Technical'),
            ('Communication',      'Soft'),
            ('Project Management', 'Soft'),
            ('React',              'Technical'),
            ('UI/UX Design',       'Design'),
            ('Figma',              'Design'),
            ('JavaScript',         'Technical'),
            ('Dart',               'Technical'),
            ('Flutter',            'Technical'),
        ]
        for name, category in skills_data:
            Skill.objects.get_or_create(name=name, defaults={'category': category})

        # ── Careers ──────────────────────────────────────────────────────────
        careers_data = [
            {
                'title':        'Data Analyst',
                'description':  'Turn raw data into actionable insights with SQL, dashboards, and business analysis.',
                'estimated_time': '12-16 weeks',
                'skills':       ['Python', 'SQL', 'Excel', 'Data Visualization', 'Communication'],
            },
            {
                'title':        'Frontend Developer',
                'description':  'Build polished, responsive web interfaces using modern JavaScript and React.',
                'estimated_time': '14-20 weeks',
                'skills':       ['JavaScript', 'React', 'UI/UX Design', 'Communication'],
            },
            {
                'title':        'UX Designer',
                'description':  'Design intuitive experiences and prototypes for products and apps.',
                'estimated_time': '10-14 weeks',
                'skills':       ['UI/UX Design', 'Figma', 'Communication', 'Project Management'],
            },
            {
                'title':        'Flutter Developer',
                'description':  'Build cross-platform mobile apps with Dart and the Flutter framework.',
                'estimated_time': '6 Months',
                'skills':       ['Dart', 'Flutter', 'UI/UX Design', 'JavaScript'],
            },
        ]
        for data in careers_data:
            career, _ = Career.objects.get_or_create(
                title=data['title'],
                defaults={
                    'description':    data['description'],
                    'estimated_time': data['estimated_time'],
                },
            )
            for skill_name in data['skills']:
                skill = Skill.objects.get(name=skill_name)
                CareerSkill.objects.get_or_create(
                    career=career, skill=skill, defaults={'priority': 'high'}
                )

        # ── Demo user skills ─────────────────────────────────────────────────
        user_skills = [
            ('Python',        'intermediate'),
            ('SQL',           'beginner'),
            ('Excel',         'intermediate'),
            ('Communication', 'advanced'),
        ]
        for name, level in user_skills:
            skill = Skill.objects.get(name=name)
            UserSkill.objects.get_or_create(
                user=user, skill=skill, defaults={'level': level}
            )

        # ── Sample roadmap for demo user ─────────────────────────────────────
        career = Career.objects.get(title='Data Analyst')
        roadmap_content = {
            'phases': [
                {
                    'title':       'Foundation',
                    'description': 'Build core data analysis fundamentals.',
                    'tasks': [
                        {
                            'ref':            'python-basics',
                            'title':          'Learn Python fundamentals',
                            'description':    'Practice variables, loops, and functions.',
                            'estimated_time': '2 weeks',
                        },
                        {
                            'ref':            'sql-fundamentals',
                            'title':          'Practice SQL joins',
                            'description':    'Write queries for data extraction.',
                            'estimated_time': '1 week',
                        },
                    ],
                },
                {
                    'title':       'Practical Skills',
                    'description': 'Apply your knowledge to real examples.',
                    'tasks': [
                        {
                            'ref':            'dashboard-project',
                            'title':          'Create a dashboard project',
                            'description':    'Build a simple dashboard with charts.',
                            'estimated_time': '2 weeks',
                        },
                        {
                            'ref':            'business-report',
                            'title':          'Write a business insight report',
                            'description':    'Translate data into recommendations.',
                            'estimated_time': '1 week',
                        },
                    ],
                },
            ]
        }

        UserRoadmap.objects.update_or_create(
            user=user,
            defaults={
                'career':          career,
                'readiness_score': 60,
                'roadmap_json':    json.dumps(roadmap_content),
            },
        )

        # ── Sample task progress ─────────────────────────────────────────────
        progress = [
            ('python-basics',     'completed'),
            ('sql-fundamentals',  'in_progress'),
            ('dashboard-project', 'not_started'),
            ('business-report',   'not_started'),
        ]
        for task_ref, status in progress:
            UserTaskProgress.objects.update_or_create(
                user=user, task_ref=task_ref, defaults={'status': status}
            )

        self.stdout.write(self.style.SUCCESS('✅ Demo data seeded successfully.'))
