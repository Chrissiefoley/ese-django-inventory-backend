from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdminUser()]
        return [IsAdminUser()]

