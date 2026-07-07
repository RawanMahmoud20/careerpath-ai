from django.db import models
from skills.models import Skill

ICON_COLOR_CHOICES = [
    ('default', 'Indigo'),
    ('blue', 'Blue'),
    ('green', 'Green'),
    ('orange', 'Orange'),
    ('pink', 'Pink'),
]

class Career(models.Model):
    title           = models.CharField(max_length=150, unique=True)
    description     = models.TextField()
    required_skills = models.ManyToManyField(Skill, through='CareerSkill', related_name='careers')
    estimated_time  = models.CharField(max_length=50, default='6 Months')
    icon = models.CharField(max_length=30, default='bi-briefcase', blank=True)
    icon_color = models.CharField(max_length=10, choices=ICON_COLOR_CHOICES, default='default')
    def __str__(self):
        return self.title


class CareerSkill(models.Model):
    PRIORITY_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    career          = models.ForeignKey(Career, on_delete=models.CASCADE)
    skill           = models.ForeignKey(Skill, on_delete=models.CASCADE)
    is_transferable = models.BooleanField(default=False)
    priority        = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='high')

    class Meta:
        unique_together = ('career', 'skill')

    def __str__(self):
        return f"{self.career.title} | {self.skill.name} ({self.priority})"