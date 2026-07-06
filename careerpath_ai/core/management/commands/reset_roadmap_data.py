"""
Reset roadmap data while keeping users, careers, and skills.

Usage:
    python manage.py reset_roadmap_data
    python manage.py reset_roadmap_data --all   # also wipes UserTaskProgress
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Reset roadmap data (keeps users, careers, skills).'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true',
                            help='Also delete UserTaskProgress records.')

    def handle(self, *args, **options):
        from analysis.models import UserRoadmap, SkillGap
        from dashboard.models import UserTaskProgress

        counts = {}
        counts['SkillGap']    = SkillGap.objects.all().delete()[0]
        counts['UserRoadmap'] = UserRoadmap.objects.all().delete()[0]

        if options['all']:
            counts['UserTaskProgress'] = UserTaskProgress.objects.all().delete()[0]

        self.stdout.write(self.style.SUCCESS('✅ Roadmap data cleared:'))
        for model, count in counts.items():
            self.stdout.write(f'   • {model}: {count} rows deleted')
