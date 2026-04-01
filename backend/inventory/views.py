from rest_framework import viewsets
from authentication.permissions import IsStaffVerified
from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(viewsets.ModelViewSet):

    serializer_class = ItemSerializer
    queryset = Item.objects.all()

    def get_permissions(self):
        # All staff-verified users can view AND edit inventory
        return [IsStaffVerified()]
