from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLES = (
        ('staff', 'Cabin crew'),
        ('passenger', 'Passenger'),
    )
    role = models.CharField(choices=ROLES, max_length=10)

    def __str__(self):
        return f"{self.username} ({self.role})"