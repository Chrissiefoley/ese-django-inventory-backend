from django.contrib import admin
from .models import Item

# Register your models here.
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'quantity', 'price')

admin.site.register(Item, ItemAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantity', 'price', 'user', 'seat_no', 'created_at')