from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=100)
    count = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(max_length=500, blank=True, default='')

    def __str__(self):
        return self.name
