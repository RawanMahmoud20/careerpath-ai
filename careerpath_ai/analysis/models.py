from django.db import models
from django.contrib.auth import get_user_model
from careers.models import Career

User = get_user_model()

class CareerTransitionPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_career = models.ForeignKey(Career, on_delete=models.CASCADE)
    # حقل تخزين نسبة الجاهزية الإجمالية للمستخدم
    readiness_score = models.IntegerField(default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # الكود القديم كان: return f"{self.user.username} -> {self.target_career.title}"
        # الكود الجديد لحذف الاسم تماماً:
        if self.target_career:
            return f"Plan for {self.target_career.title}"
        return f"Plan #{self.id}"

# الجدول الجديد والذكي لتخزين فجوة المهارات لكل مستخدم وخطة
class PlanSkillGap(models.Model):
    plan = models.ForeignKey(CareerTransitionPlan, on_delete=models.CASCADE, related_name='gaps')
    skill_name = models.CharField(max_length=100) 
    is_mastered = models.BooleanField(default=False)

    def __str__(self):
        target = self.plan.target_career.title if self.plan.target_career else "No Career"
        return f"{target} -> {self.skill_name}"

class AIRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_career = models.ForeignKey(Career, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=50, default='roadmap')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} | {self.recommendation_type}"