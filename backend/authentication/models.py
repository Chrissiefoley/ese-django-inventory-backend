from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    )
    role = models.CharField(choices=ROLES, max_length=20, default='staff')

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_info')
    employee_id = models.CharField(max_length=20, unique=True)
    contact_info = models.CharField(max_length=20)
    avatar = models.URLField(max_length=200, blank=True)

    def __str__(self):
        return self.user.username