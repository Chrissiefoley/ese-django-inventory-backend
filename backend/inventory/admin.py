from django.contrib import admin
from .models import Item


class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description', 'count', 'price')


admin.site.register(Item, ItemAdmin)
