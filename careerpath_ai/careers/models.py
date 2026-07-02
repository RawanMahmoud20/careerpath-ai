from django.db import models
from django.conf import settings

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True) # مثل: Technical, Soft Skill

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name

# 2. Careers)
class Career(models.Model):
    title = models.CharField(max_length=150, unique=True) # مثل: Data Analyst
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, through='CareerSkill', related_name='careers')

    def __str__(self):
        return self.title

class CareerSkill(models.Model):
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    is_transferable = models.BooleanField(default=False) # هل تعتبر مهارة قابلة للانتقال؟

    class Meta:
        unique_together = ('career', 'skill')


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
