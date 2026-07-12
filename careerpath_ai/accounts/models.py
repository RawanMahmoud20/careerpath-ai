from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random


class User(AbstractUser):
    full_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Full Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    def generate(self):
        self.code = str(random.randint(100000, 999999))
        self.attempts = 0
        self.save()
        return self.code

    def is_valid(self):
        """OTP is valid for 10 minutes."""
        return timezone.now() < self.created_at + timezone.timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.user.email}"