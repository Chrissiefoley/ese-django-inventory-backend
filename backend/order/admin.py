from django.contrib import admin
from .models import Order

# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantity', 'price', 'user', 'seat_no', 'created_at')


admin.site.register(Order, OrderAdmin)
