from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from authentication.permissions import IsVerifiedStaff, IsStaffVerified
from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):

    serializer_class = ItemSerializer
    queryset = Item.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsStaffVerified()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsVerifiedStaff()]
        return [IsAuthenticated()]

