from django.db import models
from django.conf import settings

from django.db import models
from django.conf import settings
# استيراد الـ Skill من تطبيقها الجديد
from skills.models import Skill 

class Career(models.Model):
    title = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, through='CareerSkill', related_name='careers')
    estimated_time = models.CharField(max_length=50, default="6 Months")

    def __str__(self):
        return self.title

class CareerSkill(models.Model):
    PRIORITY_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    is_transferable = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='high')

    class Meta:
        unique_together = ('career', 'skill')

    def __str__(self):
        return f"{self.career.title} | {self.skill.name} ({self.priority})"
class SelectedCareer(models.Model):
    user   = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='selected_career',
    )
    career = models.ForeignKey(Career, on_delete=models.CASCADE, related_name='chosen_by')
    chosen_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} → {self.career.title}"
