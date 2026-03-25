from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Item
from authentication.models import UserInfo

User = get_user_model()


class ItemModelTestCase(TestCase):
    """Test suite for Item model"""

    def setUp(self):
        self.item = Item.objects.create(
            name='Test Item',
            description='A test item description',
            category='Test Category',
            count=10,
            price=99.99
        )

    def test_item_creation(self):
        """Test that an item can be created with valid data"""
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(self.item.name, 'Test Item')
        self.assertEqual(self.item.description, 'A test item description')
        self.assertEqual(self.item.category, 'Test Category')
        self.assertEqual(self.item.count, 10)
        self.assertEqual(float(self.item.price), 99.99)

    def test_item_string_representation(self):
        """Test the __str__ method returns item name"""
        self.assertEqual(str(self.item), 'Test Item')

    def test_item_price_decimal_places(self):
        """Test that price stores correct decimal places"""
        item = Item.objects.create(
            name='Decimal Test',
            description='Testing decimals',
            category='Test',
            count=5,
            price=19.95
        )
        self.assertEqual(float(item.price), 19.95)


class ItemListTestCase(APITestCase):
    """Test suite for listing items (public access)"""

    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/items/'

        # Create test items
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
        """Test that unauthenticated users can list items"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_items_returns_all_fields(self):
        """Test that list returns all item fields"""
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
        """Test listing items when none exist"""
        Item.objects.all().delete()
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ItemRetrieveTestCase(APITestCase):
    """Test suite for retrieving a single item (public access)"""

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
        """Test that unauthenticated users can retrieve an item"""
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Test Item')
        self.assertEqual(response.data['count'], 5)

    def test_retrieve_nonexistent_item(self):
        """Test retrieving an item that doesn't exist"""
        response = self.client.get('/api/items/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ItemCreateTestCase(APITestCase):
    """Test suite for creating items (admin only)"""

    def setUp(self):
        self.client = APIClient()
        self.create_url = '/api/items/'

        # Create admin user
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

        # Create staff user
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
        """Test that admin users can create items"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.first()
        self.assertEqual(item.name, 'New Item')
        self.assertEqual(item.count, 15)

    def test_create_item_as_staff(self):
        """Test that staff users cannot create items"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Item.objects.count(), 0)

    def test_create_item_unauthenticated(self):
        """Test that unauthenticated users cannot create items"""
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Item.objects.count(), 0)

    def test_create_item_with_missing_required_fields(self):
        """Test that creating item fails with missing required fields"""
        self.client.force_authenticate(user=self.admin_user)
        required_fields = ['name', 'description', 'category', 'count', 'price']

        for field in required_fields:
            payload = self.valid_payload.copy()
            del payload[field]

            response = self.client.post(self.create_url, payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_create_item_with_negative_count(self):
        """Test that creating item with negative count is allowed (validation should be added)"""
        self.client.force_authenticate(user=self.admin_user)
        payload = self.valid_payload.copy()
        payload['count'] = -5

        response = self.client.post(self.create_url, payload, format='json')

        # Currently no validation, so it succeeds
        # TODO: Add validation to prevent negative stock
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_item_with_negative_price(self):
        """Test that creating item with negative price is allowed (validation should be added)"""
        self.client.force_authenticate(user=self.admin_user)
        payload = self.valid_payload.copy()
        payload['price'] = -10.00

        response = self.client.post(self.create_url, payload, format='json')

        # Currently no validation, so it succeeds
        # TODO: Add validation to prevent negative prices
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_item_with_zero_count(self):
        """Test that creating item with zero count is allowed"""
        self.client.force_authenticate(user=self.admin_user)
        payload = self.valid_payload.copy()
        payload['count'] = 0

        response = self.client.post(self.create_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = Item.objects.first()
        self.assertEqual(item.count, 0)


class ItemUpdateTestCase(APITestCase):
    """Test suite for updating items (admin only)"""

    def setUp(self):
        self.client = APIClient()

        # Create admin user
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

        # Create staff user
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

        # Create test item
        self.item = Item.objects.create(
            name='Original Name',
            description='Original description',
            category='Original Category',
            count=10,
            price=10.00
        )
        self.update_url = f'/api/items/{self.item.id}/'

    def test_update_item_as_admin(self):
        """Test that admin users can update items"""
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
        """Test that admin users can partially update items"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {'count': 25}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 25)
        self.assertEqual(self.item.name, 'Original Name')  # Unchanged

    def test_update_item_as_staff(self):
        """Test that staff users cannot update items"""
        self.client.force_authenticate(user=self.staff_user)
        payload = {'count': 25}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.item.refresh_from_db()
        self.assertEqual(self.item.count, 10)  # Unchanged

    def test_update_item_unauthenticated(self):
        """Test that unauthenticated users cannot update items"""
        payload = {'count': 25}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_nonexistent_item(self):
        """Test updating an item that doesn't exist"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {'count': 25}

        response = self.client.patch('/api/items/99999/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ItemDeleteTestCase(APITestCase):
    """Test suite for deleting items (admin only)"""

    def setUp(self):
        self.client = APIClient()

        # Create admin user
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

        # Create staff user
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
        """Test that admin users can delete items"""
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
        """Test that staff users cannot delete items"""
        item = Item.objects.create(
            name='To Delete',
            description='Should not be deleted',
            category='Test',
            count=5,
            price=5.00
        )
        delete_url = f'/api/items/{item.id}/'

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Item.objects.count(), 1)

    def test_delete_item_unauthenticated(self):
        """Test that unauthenticated users cannot delete items"""
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
        """Test deleting an item that doesn't exist"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete('/api/items/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ItemPermissionTestCase(APITestCase):
    """Test suite for verifying permission logic"""

    def setUp(self):
        self.client = APIClient()

        # Create users with different roles
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

        # Create test item
        self.item = Item.objects.create(
            name='Permission Test',
            description='Testing permissions',
            category='Test',
            count=10,
            price=10.00
        )

    def test_staff_can_view_but_not_modify(self):
        """Test that staff can list/retrieve but not create/update/delete"""
        self.client.force_authenticate(user=self.staff_user)

        # Can list
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Can retrieve
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Cannot create
        response = self.client.post('/api/items/', {
            'name': 'Test',
            'description': 'Test',
            'category': 'Test',
            'count': 1,
            'price': 1.00
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Cannot update
        response = self.client.patch(f'/api/items/{self.item.id}/', {'count': 5})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Cannot delete
        response = self.client.delete(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_has_full_access(self):
        """Test that admin can perform all operations"""
        self.client.force_authenticate(user=self.admin_user)

        # Can list
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Can retrieve
        response = self.client.get(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Can create
        response = self.client.post('/api/items/', {
            'name': 'Admin Created',
            'description': 'Test',
            'category': 'Test',
            'count': 1,
            'price': 1.00
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Can update
        response = self.client.patch(f'/api/items/{self.item.id}/', {'count': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Can delete
        response = self.client.delete(f'/api/items/{self.item.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
