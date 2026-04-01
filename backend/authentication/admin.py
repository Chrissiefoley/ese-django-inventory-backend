from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserInfo, Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'email', 'department', 'hire_date')
    search_fields = ('employee_id', 'full_name', 'email')
    list_filter = ('department', 'hire_date')


class UserInfoInline(admin.StackedInline):
    model = UserInfo
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserInfoInline,)
    list_display = ('username', 'email', 'role', 'is_staff_verified', 'is_active')
    list_filter = ('role', 'is_staff_verified', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'is_staff_verified')}),
    )
