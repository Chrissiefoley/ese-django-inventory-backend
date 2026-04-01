from django.db import models
from django.contrib.auth.models import AbstractUser


class Staff(models.Model):
    employee_id = models.CharField(max_length=20, primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    department = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Staff"

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


class User(AbstractUser):
    ROLES = (
        ('viewer', 'Viewer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )
    role = models.CharField(choices=ROLES, max_length=20, default='viewer')
    is_staff_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_info')
    employee_id = models.CharField(max_length=20, unique=True)
    contact_info = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(max_length=200, blank=True)

    def __str__(self):
        return self.user.username