from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
  
    full_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Full Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username