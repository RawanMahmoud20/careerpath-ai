from django.db import models
from django.contrib.auth import get_user_model
from careers.models import Career

User = get_user_model()

class CareerTransitionPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_career = models.ForeignKey(Career, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} → {self.target_career}"

class AIRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_career = models.ForeignKey(Career, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=50, default='roadmap')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} | {self.recommendation_type}"