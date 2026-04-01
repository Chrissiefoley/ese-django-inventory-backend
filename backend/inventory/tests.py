from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import Item
from authentication.models import Staff

User = get_user_model()


class InventoryItemTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()

        Staff.objects.create(
            employee_id='EMP001',
            full_name='Test Staff',
            email='staff@test.com',
            department='Operations'
        )

        self.user = User.objects.create_user(
            username='EMP001',
            email='staff@test.com',
            password='TestPass123',
            role='staff',
            is_staff_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_create_inventory_item(self):
        payload = {
            'name': 'Test Product',
            'description': 'Test Description',
            'category': 'Test',
            'count': 50,
            'price': '19.99'
        }
        response = self.client.post('/api/items/', payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.first()
        self.assertEqual(item.name, 'Test Product')
        self.assertEqual(item.count, 50)

    def test_view_inventory_items(self):
        Item.objects.create(
            name='Item 1',
            description='Description 1',
            category='Category A',
            count=30,
            price='10.00'
        )
        Item.objects.create(
            name='Item 2',
            description='Description 2',
            category='Category B',
            count=20,
            price='15.00'
        )

        response = self.client.get('/api/items/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Item 1')
        self.assertEqual(response.data[1]['name'], 'Item 2')

    def test_update_inventory_item_stock(self):
        item = Item.objects.create(
            name='Test Item',
            description='Test',
            category='Test',
            count=50,
            price='10.00'
        )

        payload = {'count': 25}
        response = self.client.patch(f'/api/items/{item.id}/', payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.count, 25)

    def test_delete_inventory_item(self):
        item = Item.objects.create(
            name='Item to Delete',
            description='Test',
            category='Test',
            count=10,
            price='5.00'
        )

        response = self.client.delete(f'/api/items/{item.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Item.objects.count(), 0)


