from django.db import models
from django.conf import settings

STATUS_CHOICES = [
    ('not_started', 'Not Started'),
    ('in_progress', 'In Progress'),
    ('completed',   'Completed'),
]

class UserTaskProgress(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_progress')
    task_ref     = models.CharField(max_length=200)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'task_ref')
        ordering = ['task_ref']

    def __str__(self):
        return f"{self.user.email} | {self.task_ref} | {self.status}"

class UserProfile(models.Model):
    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    current_field = models.CharField(max_length=150, blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='beginner')

    def __str__(self):
        return f"Profile: {self.user.email}"