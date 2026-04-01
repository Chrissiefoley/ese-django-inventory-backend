from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserInfo, Staff

User = get_user_model()


class UserRegistrationTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'

        self.staff_record = Staff.objects.create(
            employee_id='EMP001',
            full_name='Test User',
            email='test@example.com',
            department='Engineering'
        )

        self.valid_payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'employee_id': 'EMP001',
            'contact_info': '0123 450065',
            'avatar': 'https://example.com/avatar.jpg'
        }

    def test_register_user_with_valid_data(self):
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertEqual(response.data['user']['role'], 'staff')
        self.assertTrue(response.data['user']['is_staff_verified'])

        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('SecurePass123!'))

        self.assertEqual(UserInfo.objects.count(), 1)
        user_info = UserInfo.objects.get(user=user)
        self.assertEqual(user_info.employee_id, 'EMP001')
        self.assertEqual(user_info.contact_info, '0123 450065')
        self.assertEqual(user_info.avatar, 'https://example.com/avatar.jpg')

    def test_register_sets_jwt_cookies(self):
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']
        self.assertTrue(access_cookie['httponly'])
        self.assertTrue(refresh_cookie['httponly'])

    def test_register_with_duplicate_username(self):
        self.client.post(self.register_url, self.valid_payload, format='json')

        duplicate_payload = self.valid_payload.copy()
        duplicate_payload['email'] = 'different@example.com'
        duplicate_payload['employee_id'] = 'EMP002'

        response = self.client.post(self.register_url, duplicate_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_with_missing_required_fields(self):
        required_fields = ['username', 'password', 'employee_id']

        for field in required_fields:
            payload = self.valid_payload.copy()
            del payload[field]

            response = self.client.post(self.register_url, payload, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_register_with_invalid_email(self):
        payload = self.valid_payload.copy()
        payload['email'] = 'not-an-email'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
            role='staff'
        )
        UserInfo.objects.create(
            user=self.user,
            employee_id='EMP001',
            contact_info='+1234567890'
        )

    def test_login_with_valid_credentials(self):
        payload = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_login_sets_jwt_cookies(self):
        payload = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])

        self.assertEqual(response.cookies['access_token']['samesite'], 'Lax')
        self.assertEqual(response.cookies['refresh_token']['samesite'], 'Lax')

    def test_login_with_invalid_username(self):
        payload = {
            'username': 'nonexistent',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_invalid_password(self):

        payload = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_missing_credentials(self):
        response = self.client.post(self.login_url, {'username': 'testuser'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.login_url, {'password': 'SecurePass123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_user_data(self):
        payload = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        user_data = response.data['user']

        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['role'], 'staff')

        self.assertIn('user_info', user_data)
        self.assertEqual(user_data['user_info']['employee_id'], 'EMP001')


class UserProfileUpdateTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.profile_url = '/api/auth/me/'

        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='SecurePass123!',
            role='staff'
        )
        UserInfo.objects.create(
            user=self.user,
            employee_id='EMP001',
            contact_info='0123 456056',
            avatar=''
        )

    def test_update_avatar_authenticated(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            'avatar': 'https://res.cloudinary.com/demo/image/upload/sample.jpg'
        }
        response = self.client.patch(self.profile_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.user_info.refresh_from_db()
        self.assertEqual(self.user.user_info.avatar, payload['avatar'])

        self.assertEqual(response.data['user_info']['avatar'], payload['avatar'])

    def test_update_contact_info(self):
        self.client.force_authenticate(user=self.user)

        payload = {'contact_info': '0123 350350'}
        response = self.client.patch(self.profile_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.user_info.refresh_from_db()
        self.assertEqual(self.user.user_info.contact_info, '0123 350350')

    def test_update_email(self):
        self.client.force_authenticate(user=self.user)

        payload = {'email': 'newemail@example.com'}
        response = self.client.patch(self.profile_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')


class StaffVerificationTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'

        Staff.objects.create(
            employee_id='EMP001',
            full_name='John Doe',
            email='john@company.com',
            department='Engineering'
        )
        Staff.objects.create(
            employee_id='EMP002',
            full_name='Jane Smith',
            email='jane@company.com',
            department='Marketing'
        )

    def test_register_with_matching_employee_id_and_email(self):

        payload = {
            'username': 'johndoe',
            'email': 'john@company.com',
            'password': 'SecurePass123!',
            'employee_id': 'EMP001',
            'contact_info': '+1234567890'
        }

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='johndoe')
        self.assertTrue(user.is_staff_verified)
        self.assertEqual(user.role, 'staff')

    def test_register_with_wrong_email(self):
        payload = {
            'username': 'johndoe',
            'email': 'wrong@email.com',
            'password': 'SecurePass123!',
            'employee_id': 'EMP001',
            'contact_info': '+1234567890'
        }

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('employee_id', response.data)
        self.assertFalse(User.objects.filter(username='johndoe').exists())

    def test_register_with_wrong_employee_id(self):

        payload = {
            'username': 'johndoe',
            'email': 'john@company.com',
            'password': 'SecurePass123!',
            'employee_id': 'FAKE999',
            'contact_info': '+1234567890'
        }

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('employee_id', response.data)
        self.assertFalse(User.objects.filter(username='johndoe').exists())

    def test_register_without_staff_record(self):

        payload = {
            'username': 'newuser',
            'email': 'random@email.com',
            'password': 'SecurePass123!',
            'employee_id': 'NOTINDB',
            'contact_info': '+1234567890'
        }

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('employee_id', response.data)
        self.assertFalse(User.objects.filter(username='newuser').exists())


class PermissionTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.verified_admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password',
            role='admin',
            is_staff_verified=True
        )

        self.verified_staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='password',
            role='staff',
            is_staff_verified=True
        )

        self.verified_viewer = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='password',
            role='viewer',
            is_staff_verified=True
        )

        self.unverified_user = User.objects.create_user(
            username='unverified',
            email='unverified@test.com',
            password='password',
            role='viewer',
            is_staff_verified=False
        )

    def test_verified_viewer_can_view_inventory(self):
        self.client.force_authenticate(user=self.verified_viewer)
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verified_viewer_can_create_item(self):

        self.client.force_authenticate(user=self.verified_viewer)
        payload = {
            'name': 'Test Item',
            'description': 'Test Description',
            'category': 'Test',
            'count': 10,
            'price': '99.99'
        }
        response = self.client.post('/api/items/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_verified_staff_can_create_item(self):

        self.client.force_authenticate(user=self.verified_staff)
        payload = {
            'name': 'Test Item',
            'description': 'Test Description',
            'category': 'Test',
            'count': 10,
            'price': '99.99'
        }
        response = self.client.post('/api/items/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unverified_user_cannot_view_inventory(self):

        self.client.force_authenticate(user=self.unverified_user)
        response = self.client.get('/api/items/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_admin_can_create_item(self):

        self.client.force_authenticate(user=self.verified_admin)
        payload = {
            'name': 'Admin Item',
            'description': 'Admin Description',
            'category': 'Admin',
            'count': 5,
            'price': '199.99'
        }
        response = self.client.post('/api/items/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
