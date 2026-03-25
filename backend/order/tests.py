from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Order
from inventory.models import Item
from authentication.models import UserInfo

User = get_user_model()


class OrderModelTestCase(TestCase):
    """Test suite for Order model"""

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            role='staff'
        )
        UserInfo.objects.create(
            user=self.user,
            employee_id='EMP001',
            contact_info='test@test.com'
        )

        # Create test item
        self.item = Item.objects.create(
            name='Test Item',
            description='Test description',
            category='Test Category',
            count=10,
            price=50.00
        )

        # Create test order
        self.order = Order.objects.create(
            item=self.item,
            user=self.user,
            quantity=2,
            price=50.00,
            seat_no='12A'
        )

    def test_order_creation(self):
        """Test that an order can be created with valid data"""
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.order.item, self.item)
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.quantity, 2)
        self.assertEqual(float(self.order.price), 50.00)
        self.assertEqual(self.order.seat_no, '12A')

    def test_order_string_representation(self):
        """Test the __str__ method returns formatted string"""
        expected = f"Order {self.order.id}: Seat 12A"
        self.assertEqual(str(self.order), expected)

    def test_order_get_cost_method(self):
        """Test that get_cost() calculates total correctly"""
        cost = self.order.get_cost()
        expected_cost = 50.00 * 2  # price * quantity
        self.assertEqual(float(cost), expected_cost)

    def test_order_timestamps(self):
        """Test that created_at and updated_at are set automatically"""
        self.assertIsNotNone(self.order.created_at)
        self.assertIsNotNone(self.order.updated_at)

    def test_order_cascade_delete_with_item(self):
        """Test that deleting an item deletes associated orders"""
        order_id = self.order.id
        self.item.delete()

        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(id=order_id)

    def test_order_cascade_delete_with_user(self):
        """Test that deleting a user deletes associated orders"""
        order_id = self.order.id
        self.user.delete()

        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(id=order_id)


class OrderListTestCase(APITestCase):
    """Test suite for listing orders (admin only)"""

    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/orders/'

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
            name='Test Item',
            description='Test',
            category='Test',
            count=100,
            price=10.00
        )

        # Create test orders
        Order.objects.create(
            item=self.item,
            user=self.staff_user,
            quantity=1,
            price=10.00,
            seat_no='1A'
        )
        Order.objects.create(
            item=self.item,
            user=self.staff_user,
            quantity=2,
            price=10.00,
            seat_no='2B'
        )

    def test_list_orders_as_admin(self):
        """Test that admin users can list orders"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_orders_as_staff(self):
        """Test that staff users cannot list orders"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_orders_unauthenticated(self):
        """Test that unauthenticated users cannot list orders"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderCreateTestCase(APITestCase):
    """Test suite for creating orders (admin only)"""

    def setUp(self):
        self.client = APIClient()
        self.create_url = '/api/orders/'

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
            name='Test Item',
            description='Test',
            category='Test',
            count=100,
            price=25.00
        )

        self.valid_payload = {
            'item': self.item.id,
            'user': self.staff_user.id,
            'quantity': 3,
            'price': 25.00,
            'seat_no': '15C'
        }

    def test_create_order_as_admin(self):
        """Test that admin users can create orders"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.quantity, 3)
        self.assertEqual(order.seat_no, '15C')
        self.assertEqual(float(order.get_cost()), 75.00)  # 25 * 3

    def test_create_order_as_staff(self):
        """Test that staff users cannot create orders"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 0)

    def test_create_order_unauthenticated(self):
        """Test that unauthenticated users cannot create orders"""
        response = self.client.post(self.create_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Order.objects.count(), 0)

    def test_create_order_with_missing_fields(self):
        """Test that creating order fails with missing required fields"""
        self.client.force_authenticate(user=self.admin_user)
        required_fields = ['item', 'user', 'quantity', 'price', 'seat_no']

        for field in required_fields:
            payload = self.valid_payload.copy()
            del payload[field]

            response = self.client.post(self.create_url, payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_create_order_with_nonexistent_item(self):
        """Test creating order with item that doesn't exist"""
        self.client.force_authenticate(user=self.admin_user)
        payload = self.valid_payload.copy()
        payload['item'] = 99999

        response = self.client.post(self.create_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_with_zero_quantity(self):
        """Test creating order with zero quantity (should be prevented)"""
        self.client.force_authenticate(user=self.admin_user)
        payload = self.valid_payload.copy()
        payload['quantity'] = 0

        response = self.client.post(self.create_url, payload, format='json')

        # Currently no validation - this succeeds but shouldn't
        # TODO: Add validation to prevent zero or negative quantities
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_order_with_negative_quantity(self):
        """Test creating order with negative quantity (should be prevented)"""
        self.client.force_authenticate(user=self.admin_user)
        payload = self.valid_payload.copy()
        payload['quantity'] = -5

        response = self.client.post(self.create_url, payload, format='json')

        # Currently no validation - this succeeds but shouldn't
        # TODO: Add validation to prevent negative quantities
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class OrderRetrieveTestCase(APITestCase):
    """Test suite for retrieving a single order (admin only)"""

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

        # Create test item and order
        self.item = Item.objects.create(
            name='Test Item',
            description='Test',
            category='Test',
            count=100,
            price=15.00
        )

        self.order = Order.objects.create(
            item=self.item,
            user=self.staff_user,
            quantity=2,
            price=15.00,
            seat_no='10A'
        )
        self.detail_url = f'/api/orders/{self.order.id}/'

    def test_retrieve_order_as_admin(self):
        """Test that admin users can retrieve an order"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['seat_no'], '10A')
        self.assertEqual(response.data['quantity'], 2)

    def test_retrieve_order_as_staff(self):
        """Test that staff users cannot retrieve orders"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_order_unauthenticated(self):
        """Test that unauthenticated users cannot retrieve orders"""
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_nonexistent_order(self):
        """Test retrieving an order that doesn't exist"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/orders/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderUpdateTestCase(APITestCase):
    """Test suite for updating orders (admin only)"""

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

        # Create test item and order
        self.item = Item.objects.create(
            name='Test Item',
            description='Test',
            category='Test',
            count=100,
            price=20.00
        )

        self.order = Order.objects.create(
            item=self.item,
            user=self.staff_user,
            quantity=1,
            price=20.00,
            seat_no='5A'
        )
        self.update_url = f'/api/orders/{self.order.id}/'

    def test_update_order_as_admin(self):
        """Test that admin users can update orders"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'item': self.item.id,
            'user': self.staff_user.id,
            'quantity': 5,
            'price': 20.00,
            'seat_no': '5A'
        }

        response = self.client.put(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 5)

    def test_partial_update_order_as_admin(self):
        """Test that admin users can partially update orders"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {'quantity': 3}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 3)

    def test_update_order_as_staff(self):
        """Test that staff users cannot update orders"""
        self.client.force_authenticate(user=self.staff_user)
        payload = {'quantity': 3}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 1)  # Unchanged

    def test_update_order_unauthenticated(self):
        """Test that unauthenticated users cannot update orders"""
        payload = {'quantity': 3}

        response = self.client.patch(self.update_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderDeleteTestCase(APITestCase):
    """Test suite for deleting orders (admin only)"""

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
            name='Test Item',
            description='Test',
            category='Test',
            count=100,
            price=30.00
        )

    def test_delete_order_as_admin(self):
        """Test that admin users can delete orders"""
        order = Order.objects.create(
            item=self.item,
            user=self.staff_user,
            quantity=1,
            price=30.00,
            seat_no='8B'
        )
        delete_url = f'/api/orders/{order.id}/'

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)

    def test_delete_order_as_staff(self):
        """Test that staff users cannot delete orders"""
        order = Order.objects.create(
            item=self.item,
            user=self.staff_user,
            quantity=1,
            price=30.00,
            seat_no='8B'
        )
        delete_url = f'/api/orders/{order.id}/'

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 1)

    def test_delete_order_unauthenticated(self):
        """Test that unauthenticated users cannot delete orders"""
        order = Order.objects.create(
            item=self.item,
            user=self.staff_user,
            quantity=1,
            price=30.00,
            seat_no='8B'
        )
        delete_url = f'/api/orders/{order.id}/'

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Order.objects.count(), 1)
