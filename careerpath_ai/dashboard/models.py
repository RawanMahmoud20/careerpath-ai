from django.db import models
from django.conf import settings

STATUS_CHOICES = [
    ('not_started', 'Not Started'),
    ('in_progress', 'In Progress'),
    ('completed',   'Completed'),
]

class UserTaskProgress(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_progress')
    task_ref     = models.CharField(max_length=200)   # e.g. "data_analyst_phase1_task2"
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'task_ref')
        ordering = ['task_ref']

    def __str__(self):
        return f"{self.user.email} | {self.task_ref} | {self.status}"