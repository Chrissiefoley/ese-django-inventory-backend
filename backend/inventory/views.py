from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import Item, Order
from .serializers import ItemSerializer, OrderSerializer


class ItemViewSet(viewsets.ModelViewSet):

    serializer_class = ItemSerializer
    queryset = Item.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

