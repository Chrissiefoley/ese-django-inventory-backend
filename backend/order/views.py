from django.shortcuts import render

# Create your views here.
class OrderViewSet(viewsets.ModelViewSet):

    serializer_class = OrderSerializer
    queryset = Item.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdminUser()]
        return [IsAdminUser()]

