import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from analysis.models import UserRoadmap
from careers.models import Career


class RoadmapViewTests(TestCase):
    def test_roadmap_page_renders_phases(self):
        User = get_user_model()
        user = User.objects.create_user(
            username='roadmap-user', email='roadmap@example.com', password='pass1234'
        )
        career = Career.objects.create(
            title='Data Analyst', description='Analyze data.', estimated_time='4 months'
        )

        UserRoadmap.objects.create(
            user=user,
            career=career,
            readiness_score=0,
            roadmap_json=json.dumps({
                'phases': [
                    {
                        'title':       'Foundation',
                        'description': 'Build your base.',
                        'tasks': [
                            {
                                'title':          'Learn SQL',
                                'description':    'Practice SQL basics.',
                                'estimated_time': '1 week',
                            }
                        ],
                    }
                ]
            }),
        )

        self.client.force_login(user)
        response = self.client.get('/roadmap/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Foundation')
        self.assertContains(response, 'Learn SQL')
