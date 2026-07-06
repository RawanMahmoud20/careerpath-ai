from django.db import models
from django.conf import settings

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True) # Technical, Soft Skill

    def __str__(self):
        return self.name

class UserSkill(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='users_possessed')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'skill')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.email} | {self.skill.name} ({self.level})"