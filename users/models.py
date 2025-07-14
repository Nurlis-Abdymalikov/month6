from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from users.managers import CustomUserManager
from django.utils import timezone
from datetime import date

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    birthday = models.DateField(null=True, blank=True)

    objects = CustomUserManager()

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email or ""



class ConfirmationCode(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='confirmation_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Код подтверждения для {self.user.username}"