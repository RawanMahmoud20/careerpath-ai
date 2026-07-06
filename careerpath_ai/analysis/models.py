from django.db import models
from django.contrib.auth import get_user_model
from careers.models import Career

User = get_user_model()


class UserRoadmap(models.Model):
    """
    Single source of truth for a user's career roadmap.
    Replaces the old CareerTransitionPlan + AIRecommendation pair.

    - One row per user (OneToOne).
    - When the user switches careers the row is simply updated in place.
    - roadmap_json stores the JSON blob (phases / tasks) produced by Gemini.
    - readiness_score is updated by the Skill-Gap analysis page.
    """
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='roadmap')
    career          = models.ForeignKey(Career, on_delete=models.CASCADE, related_name='roadmaps')
    readiness_score = models.IntegerField(default=0)
    roadmap_json    = models.TextField(default='{}')
    generated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} → {self.career.title}"


class SkillGap(models.Model):
    """Tracks which skills a user is missing for their target career."""
    roadmap    = models.ForeignKey(UserRoadmap, on_delete=models.CASCADE, related_name='skill_gaps')
    skill_name = models.CharField(max_length=100)
    is_mastered = models.BooleanField(default=False)

    class Meta:
        unique_together = ('roadmap', 'skill_name')

    def __str__(self):
        return f"{self.roadmap.career.title} → {self.skill_name}"