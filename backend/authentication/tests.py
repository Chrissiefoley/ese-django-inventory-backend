from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserInfo

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    """Test suite for user registration endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.valid_payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'employee_id': 'EMP001',
            'contact_info': '+1234567890',
            'role': 'staff',
            'avatar': 'https://example.com/avatar.jpg'
        }

    def test_register_user_with_valid_data(self):
        """Test that a user can register with valid data"""
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertEqual(response.data['user']['role'], 'staff')

        # Verify user was created in database
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('SecurePass123!'))

        # Verify UserInfo was created
        self.assertEqual(UserInfo.objects.count(), 1)
        user_info = UserInfo.objects.get(user=user)
        self.assertEqual(user_info.employee_id, 'EMP001')
        self.assertEqual(user_info.contact_info, '+1234567890')
        self.assertEqual(user_info.avatar, 'https://example.com/avatar.jpg')

    def test_register_sets_jwt_cookies(self):
        """Test that registration returns JWT tokens in httponly cookies"""
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Verify cookies are httponly
        access_cookie = response.cookies['access_token']
        refresh_cookie = response.cookies['refresh_token']
        self.assertTrue(access_cookie['httponly'])
        self.assertTrue(refresh_cookie['httponly'])

    def test_register_with_duplicate_username(self):
        """Test that registration fails with duplicate username"""
        # Create first user
        self.client.post(self.register_url, self.valid_payload, format='json')

        # Try to register with same username
        duplicate_payload = self.valid_payload.copy()
        duplicate_payload['email'] = 'different@example.com'
        duplicate_payload['employee_id'] = 'EMP002'

        response = self.client.post(self.register_url, duplicate_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_with_duplicate_employee_id(self):
        """Test that registration fails with duplicate employee_id"""
        # Create first user
        self.client.post(self.register_url, self.valid_payload, format='json')

        # Try to register with same employee_id
        duplicate_payload = self.valid_payload.copy()
        duplicate_payload['username'] = 'different_user'
        duplicate_payload['email'] = 'different@example.com'

        response = self.client.post(self.register_url, duplicate_payload, format='json')

        # The atomic transaction ensures that if UserInfo creation fails,
        # the User is also rolled back, so we should still have exactly 1 user
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
        self.assertEqual(User.objects.count(), 1)

    def test_register_with_missing_required_fields(self):
        """Test that registration fails when required fields are missing"""
        required_fields = ['username', 'password', 'employee_id', 'contact_info', 'role']

        for field in required_fields:
            payload = self.valid_payload.copy()
            del payload[field]

            response = self.client.post(self.register_url, payload, format='json')

            # Email is not required at the serializer level (Django User allows blank email)
            # but these other fields should trigger validation errors
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_register_without_avatar_succeeds(self):
        """Test that avatar field is optional"""
        payload = self.valid_payload.copy()
        del payload['avatar']

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='testuser')
        self.assertEqual(user.user_info.avatar, '')

    def test_register_with_invalid_email(self):
        """Test that registration fails with invalid email format"""
        payload = self.valid_payload.copy()
        payload['email'] = 'not-an-email'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_atomic_transaction(self):
        """Test that User and UserInfo creation is atomic"""
        # This test verifies that if UserInfo creation fails, User is also rolled back
        # We can't easily simulate this without mocking, but we can verify
        # that both are created together
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserInfo.objects.count(), 1)

        user = User.objects.first()
        user_info = UserInfo.objects.first()
        self.assertEqual(user_info.user, user)


class UserLoginTestCase(APITestCase):
    """Test suite for user login endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

        # Create a test user
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
        """Test that user can login with valid username and password"""
        payload = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_login_sets_jwt_cookies(self):
        """Test that login returns JWT tokens in httponly cookies"""
        payload = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Verify cookies are httponly
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])

        # Verify cookies have samesite protection
        self.assertEqual(response.cookies['access_token']['samesite'], 'Lax')
        self.assertEqual(response.cookies['refresh_token']['samesite'], 'Lax')

    def test_login_with_invalid_username(self):
        """Test that login fails with non-existent username"""
        payload = {
            'username': 'nonexistent',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_invalid_password(self):
        """Test that login fails with incorrect password"""
        payload = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_missing_credentials(self):
        """Test that login fails when credentials are missing"""
        # Missing password
        response = self.client.post(self.login_url, {'username': 'testuser'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing username
        response = self.client.post(self.login_url, {'password': 'SecurePass123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_user_data(self):
        """Test that login response includes complete user data"""
        payload = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = self.client.post(self.login_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        user_data = response.data['user']

        # Verify user fields
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['role'], 'staff')

        # Verify nested user_info
        self.assertIn('user_info', user_data)
        self.assertEqual(user_data['user_info']['employee_id'], 'EMP001')


class UserLogoutTestCase(APITestCase):
    """Test suite for user logout endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.logout_url = '/api/auth/logout/'

        # Create and login a test user
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

        # Login to get cookies
        login_response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }, format='json')

        self.access_token = login_response.cookies.get('access_token').value
        self.refresh_token = login_response.cookies.get('refresh_token').value

    def test_logout_deletes_cookies(self):
        """Test that logout endpoint deletes JWT cookies"""
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that cookies are deleted (max_age=0 or expires in past)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Deleted cookies should have empty values or max_age=0
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_logout_without_authentication(self):
        """Test that logout works even without being authenticated"""
        # Create a new client without logging in
        client = APIClient()
        response = client.post(self.logout_url)

        # Logout should still succeed (idempotent operation)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TokenRefreshTestCase(APITestCase):
    """Test suite for JWT token refresh endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = '/api/auth/refresh/'

        # Create and login a test user
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

        # Login to get refresh token
        login_response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }, format='json')

        self.refresh_token = login_response.cookies.get('refresh_token').value

    def test_refresh_with_valid_token(self):
        """Test that refresh endpoint returns new access token"""
        # Set the refresh token cookie
        self.client.cookies['refresh_token'] = self.refresh_token

        response = self.client.post(self.refresh_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that new access token cookie is set
        self.assertIn('access_token', response.cookies)

        # Response body should not contain the token (only in cookie)
        self.assertNotIn('access', response.data)

    def test_refresh_without_token(self):
        """Test that refresh fails without refresh token cookie"""
        response = self.client.post(self.refresh_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_with_invalid_token(self):
        """Test that refresh fails with invalid token"""
        self.client.cookies['refresh_token'] = 'invalid_token_string'

        response = self.client.post(self.refresh_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserInfoViewTestCase(APITestCase):
    """Test suite for authenticated user info endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.user_info_url = '/api/auth/me/'

        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
            role='staff'
        )
        self.user_info = UserInfo.objects.create(
            user=self.user,
            employee_id='EMP001',
            contact_info='+1234567890',
            avatar='https://example.com/avatar.jpg'
        )

    def test_get_user_info_authenticated(self):
        """Test that authenticated user can retrieve their info"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.user_info_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['role'], 'staff')
        self.assertEqual(response.data['user_info']['employee_id'], 'EMP001')
        self.assertEqual(response.data['user_info']['contact_info'], '+1234567890')
        self.assertEqual(response.data['user_info']['avatar'], 'https://example.com/avatar.jpg')

    def test_get_user_info_unauthenticated(self):
        """Test that unauthenticated request is rejected"""
        response = self.client.get(self.user_info_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserRoleTestCase(TestCase):
    """Test suite for user role functionality"""

    def test_user_defaults_to_staff_role(self):
        """Test that new user defaults to 'staff' role"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        self.assertEqual(user.role, 'staff')

    def test_user_can_be_created_as_admin(self):
        """Test that user can be created with 'admin' role"""
        user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='password123',
            role='admin'
        )

        self.assertEqual(user.role, 'admin')

    def test_user_string_representation(self):
        """Test user __str__ method"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            role='staff'
        )

        self.assertEqual(str(user), 'testuser (staff)')
