from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Item
from authentication.models import UserInfo

User = get_user_model()


class ItemModelTestCase(TestCase):

    def setUp(self):
        self.item = Item.objects.create(
            name='Test Item',
            description='A test item description',
            category='Test Category',
            count=10,
            price=99.99
        )

    def test_item_creation(self):
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(self.item.name, 'Test Item')
        self.assertEqual(self.item.description, 'A test item description')
        self.assertEqual(self.item.category, 'Test Category')
        self.assertEqual(self.item.count, 10)
        self.assertEqual(float(self.item.price), 99.99)

    def test_item_string_representation(self):

        self.assertEqual(str(self.item), 'Test Item')


class ItemListTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/items/'

        Item.objects.create(
            name='Item 1',
            description='Description 1',
            category='Category A',
            count=10,
            price=10.00
        )
        Item.objects.create(
            name='Item 2',
            description='Description 2',
            category='Category B',
            count=20,
            price=20.00
        )

    def test_list_items_unauthenticated(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_items_returns_all_fields(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data[0]
        self.assertIn('id', item)
        self.assertIn('name', item)
        self.assertIn('description', item)
        self.assertIn('category', item)
        self.assertIn('count', item)
        self.assertIn('price', item)

    def test_list_items_empty(self):

        Item.objects.all().delete()
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ItemRetrieveTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.item = Item.objects.create(
            name='Retrieve Test Item',
            description='Test description',
            category='Test Category',
            count=5,
            price=15.99
        )
        self.detail_url = f'/api/items/{self.item.id}/'

    def test_retrieve_item_unauthenticated(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Test Item')
        self.assertEqual(response.data['count'], 5)


class ItemCreateTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.create_url = '/api/items/'

        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            role='admin',
            is_staff=True
        )
        UserInfo.objects.create(
            user=self.admin_user,
            employee_id='ADMIN001',
            contact_info='admin@test.com'
        )

        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass',
            role='staff'
        )
        UserInfo.objects.create(
            user=self.staff_user,
            employee_id='STAFF001',
            contact_info='staff@test.com'
        )

        self.valid_payload = {
            'name': 'New Item',
            'description': 'New item description',
            'category': 'New Category',
            'count': 15,
            'price': 25.50
        }

    def test_create_item_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.first()
        self.assertEqual(item.name, 'New Item')
        self.assertEqual(item.count, 15)

    def test_create_item_as_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)

    def test_create_item_unauthenticated(self):
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Item.objects.count(), 0)

    def test_create_item_with_missing_required_fields(self):
        self.client.force_authenticate(user=self.admin_user)
        required_fields = ['name', 'description', 'category', 'count', 'price']

        for field in required_fields:
            payload = self.valid_payload.copy()
            del payload[field]

            response = self.client.post(self.create_url, payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_create_item_with_zero_count(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = self.valid_payload.copy()
        payload['count'] = 0

        response = self.client.post(self.create_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = Item.objects.first()
        self.assertEqual(item.count, 0)


class ItemUpdateTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            role='admin',
            is_staff=True
        )
        UserInfo.objects.create(
            user=self.admin_user,
            employee_id='ADMIN001',
            contact_info='admin@test.com'
        )

        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass',
            role='staff'
        )
        UserInfo.objects.create(
            user=self.staff_user,
            employee_id='STAFF001',
            contact_info='staff@test.com'
        )

        self.item = Item.objects.create(
            name='Original Name',
            description='Original description',
            category='Original Category',
            count=10,
            price=10.00
        )
        self.update_url = f'/api/items/{self.item.id}/'

    def test_update_item_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'category': 'Updated Category',
            'count': 20,
            'price': 20.00
        }

        response = self.client.put(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Updated Name')
        self.assertEqual(self.item.count, 20)

    def test_partial_update_item_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {'count': 25}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 25)
        self.assertEqual(self.item.name, 'Original Name')  # Unchanged

    def test_update_item_as_staff(self):
        self.client.force_authenticate(user=self.staff_user)
        payload = {'count': 25}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 25)  
    def test_update_item_unauthenticated(self):
        payload = {'count': 25}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_nonexistent_item(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {'count': 25}

        response = self.client.patch('/api/items/99999/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ItemDeleteTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            role='admin',
            is_staff=True
        )
        UserInfo.objects.create(
            user=self.admin_user,
            employee_id='ADMIN001',
            contact_info='admin@test.com'
        )

        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass',
            role='staff'
        )
        UserInfo.objects.create(
            user=self.staff_user,
            employee_id='STAFF001',
            contact_info='staff@test.com'
        )

    def test_delete_item_as_admin(self):
        item = Item.objects.create(
            name='To Delete',
            description='Will be deleted',
            category='Test',
            count=5,
            price=5.00
        )
        delete_url = f'/api/items/{item.id}/'

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Item.objects.count(), 0)

    def test_delete_item_as_staff(self):
        item = Item.objects.create(
            name='To Delete',
            description='Should be deleted',
            category='Test',
            count=5,
            price=5.00
        )
        delete_url = f'/api/items/{item.id}/'

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Item.objects.count(), 0)  

    def test_delete_item_unauthenticated(self):
        item = Item.objects.create(
            name='To Delete',
            description='Should not be deleted',
            category='Test',
            count=5,
            price=5.00
        )
        delete_url = f'/api/items/{item.id}/'

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Item.objects.count(), 1)

    def test_delete_nonexistent_item(self):

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete('/api/items/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ItemPermissionTestCase(APITestCase):


    def setUp(self):
        self.client = APIClient()


        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            role='admin',
            is_staff=True
        )
        UserInfo.objects.create(
            user=self.admin_user,
            employee_id='ADMIN001',
            contact_info='admin@test.com'
        )

        self.staff_user = User.objects.create_user(
            username='staff',
            password='staffpass',
            role='staff'
        )
        UserInfo.objects.create(
            user=self.staff_user,
            employee_id='STAFF001',
            contact_info='staff@test.com'
        )

        self.item = Item.objects.create(
            name='Permission Test',
            description='Testing permissions',
            category='Test',
            count=10,
            price=10.00
        )

    def test_staff_can_view_and_modify(self):
        self.client.force_authenticate(user=self.staff_user)


        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        response = self.client.post('/api/items/', {
            'name': 'Test',
            'description': 'Test',
            'category': 'Test',
            'count': 1,
            'price': 1.00
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


        response = self.client.patch(f'/api/items/{self.item.id}/', {'count': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        response = self.client.delete(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

   