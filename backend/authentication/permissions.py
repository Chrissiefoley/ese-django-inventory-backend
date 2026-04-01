from rest_framework.permissions import BasePermission


class IsVerifiedStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_staff_verified and
            request.user.role in ['staff', 'admin']
        )


class IsVerifiedAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_staff_verified and
            request.user.role == 'admin'
        )


class IsStaffVerified(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_staff_verified
        )
