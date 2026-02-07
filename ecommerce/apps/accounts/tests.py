"""
This module defines tests for the accounts app.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

User = get_user_model()


class PasswordResetViewTests(APITestCase):
    """
    Test cases for the PasswordResetView API endpoint.

    Attributes:
        client (APIClient): The test client for making API requests.
        user (User): A test user for password reset tests.
        url (str): The URL for the password reset endpoint.
    """

    def setUp(self) -> None:
        """
        Set up test data before each test method.

        Returns:
            None
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        self.url = reverse('password-reset')

    def test_password_reset_with_valid_email(self) -> None:
        """
        Test password reset request with a valid registered email.

        Returns:
            None
        """
        with patch(
            'apps.accounts.views.send_password_reset_email.delay'
        ) as mock_send_email:
            response = self.client.post(
                self.url,
                {'email': 'testuser@example.com'}
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data['detail'],
                'Password reset email sent.'
            )
            mock_send_email.assert_called_once()

            # Verify the email and reset_url were passed correctly
            call_args = mock_send_email.call_args
            self.assertEqual(call_args[0][0], 'testuser@example.com')
            self.assertIn('reset-password', call_args[0][1])

    def test_password_reset_with_invalid_email(self) -> None:
        """
        Test password reset request with an unregistered email.

        Returns:
            None
        """
        response = self.client.post(
            self.url,
            {'email': 'nonexistent@example.com'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data['detail'],
            'No user is associated with this email.'
        )

    def test_password_reset_without_email(self) -> None:
        """
        Test password reset request without providing an email.

        Returns:
            None
        """
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Email is required.')

    def test_password_reset_generates_valid_token(self) -> None:
        """
        Test that password reset generates a valid token for the user.

        Returns:
            None
        """
        with patch(
            'apps.accounts.views.send_password_reset_email.delay'
        ) as mock_send_email:
            self.client.post(self.url, {'email': 'testuser@example.com'})

            # Extract the reset URL from the mock call
            call_args = mock_send_email.call_args
            reset_url = call_args[0][1]

            # Extract uid and token from the URL
            parts = reset_url.rstrip('/').split('/')
            token = parts[-1]
            uid = parts[-2]

            # Verify the token is valid for the user
            self.assertTrue(
                default_token_generator.check_token(self.user, token)
            )

            # Verify the uid decodes to the correct user
            expected_uid = urlsafe_base64_encode(force_bytes(self.user.pk))
            self.assertEqual(uid, expected_uid)


class SendPasswordResetEmailTaskTests(TestCase):
    """
    Test cases for the send_password_reset_email Celery task.

    Attributes:
        None
    """

    @patch('apps.accounts.tasks.send_mail')
    def test_send_password_reset_email_calls_send_mail(
        self, mock_send_mail: MagicMock
    ) -> None:
        """
        Test that the task calls Django's send_mail with correct parameters.

        Args:
            mock_send_mail (MagicMock): Mocked send_mail function.

        Returns:
            None
        """
        from apps.accounts.tasks import send_password_reset_email

        email = 'testuser@example.com'
        reset_url = 'https://example.com/reset-password/abc123/token456/'

        send_password_reset_email(email, reset_url)

        mock_send_mail.assert_called_once_with(
            subject='Password Reset Request',
            message=f'Click the link to reset your password: {reset_url}',
            from_email='noreply@example.com',
            recipient_list=[email],
        )

    @patch('apps.accounts.tasks.send_mail')
    def test_send_password_reset_email_with_different_emails(
        self, mock_send_mail: MagicMock
    ) -> None:
        """
        Test that the task correctly handles different email addresses.

        Args:
            mock_send_mail (MagicMock): Mocked send_mail function.

        Returns:
            None
        """
        from apps.accounts.tasks import send_password_reset_email

        test_cases = [
            ('user1@example.com', 'https://example.com/reset/uid1/token1/'),
            ('user2@test.org', 'https://example.com/reset/uid2/token2/'),
        ]

        for email, reset_url in test_cases:
            mock_send_mail.reset_mock()
            send_password_reset_email(email, reset_url)

            mock_send_mail.assert_called_once()
            call_args = mock_send_mail.call_args
            self.assertEqual(call_args[1]['recipient_list'], [email])
            self.assertIn(reset_url, call_args[1]['message'])


class TokenGenerationTests(TestCase):
    """
    Test cases for password reset token generation and validation.

    Attributes:
        user (User): A test user for token tests.
    """

    def setUp(self) -> None:
        """
        Set up test data before each test method.

        Returns:
            None
        """
        self.user = User.objects.create_user(
            username='tokenuser',
            email='tokenuser@example.com',
            password='testpassword123',
            first_name='Token',
            last_name='User'
        )

    def test_token_generation_is_unique_per_user(self) -> None:
        """
        Test that tokens are unique for different users.

        Returns:
            None
        """
        user2 = User.objects.create_user(
            username='tokenuser2',
            email='tokenuser2@example.com',
            password='testpassword123',
            first_name='Token2',
            last_name='User2'
        )

        token1 = default_token_generator.make_token(self.user)
        token2 = default_token_generator.make_token(user2)

        self.assertNotEqual(token1, token2)

    def test_token_validation_succeeds_for_correct_user(self) -> None:
        """
        Test that token validation succeeds for the correct user.

        Returns:
            None
        """
        token = default_token_generator.make_token(self.user)
        is_valid = default_token_generator.check_token(self.user, token)

        self.assertTrue(is_valid)

    def test_token_validation_fails_for_wrong_user(self) -> None:
        """
        Test that token validation fails for a different user.

        Returns:
            None
        """
        user2 = User.objects.create_user(
            username='wronguser',
            email='wronguser@example.com',
            password='testpassword123',
            first_name='Wrong',
            last_name='User'
        )

        token = default_token_generator.make_token(self.user)
        is_valid = default_token_generator.check_token(user2, token)

        self.assertFalse(is_valid)

    def test_token_validation_fails_for_invalid_token(self) -> None:
        """
        Test that token validation fails for an invalid token string.

        Returns:
            None
        """
        is_valid = default_token_generator.check_token(
            self.user,
            'invalid-token-string'
        )

        self.assertFalse(is_valid)

    def test_uid_encoding_and_decoding(self) -> None:
        """
        Test that user ID encoding and decoding works correctly.

        Returns:
            None
        """
        from django.utils.http import urlsafe_base64_decode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        decoded_uid = urlsafe_base64_decode(uid).decode()

        self.assertEqual(str(self.user.pk), decoded_uid)


class UserRegistrationViewTests(APITestCase):
    """
    Test cases for the UserRegistrationView API endpoint.

    Attributes:
        client (APIClient): The test client for making API requests.
        url (str): The URL for the user registration endpoint.
    """

    def setUp(self) -> None:
        """
        Set up test data before each test method.

        Returns:
            None
        """
        self.client = APIClient()
        self.url = reverse('user-register')

    def test_user_registration_with_valid_data(self) -> None:
        """
        Test user registration with valid data.

        Returns:
            None
        """
        data = {
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'first_name': 'New',
            'last_name': 'User',
            'username': 'newuser'
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email='newuser@example.com').exists()
        )

    def test_user_registration_with_duplicate_email(self) -> None:
        """
        Test user registration with an already registered email.

        Returns:
            None
        """
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpassword123',
            first_name='Existing',
            last_name='User'
        )

        data = {
            'email': 'existing@example.com',
            'password': 'securepassword123',
            'first_name': 'New',
            'last_name': 'User',
            'username': 'newuser'
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_with_optional_address(self) -> None:
        """
        Test user registration with optional address fields.

        Returns:
            None
        """
        from apps.accounts.models import Country, Address
        
        # Create a test country
        Country.objects.create(
            code='NG',
            name='Nigeria',
            phone_code='+234',
            currency_code='NGN',
            is_active=True
        )
        
        data = {
            'email': 'addressuser@example.com',
            'password': 'securepassword123',
            'first_name': 'Address',
            'last_name': 'User',
            'username': 'addressuser',
            'street_line1': '123 Main Street',
            'street_line2': 'Apt 4B'
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        user = User.objects.get(email='addressuser@example.com')
        self.assertTrue(user)
        
        # Verify address was created
        address = Address.objects.filter(user=user).first()
        self.assertIsNotNone(address)
        self.assertEqual(address.street_line1, '123 Main Street')
        self.assertEqual(address.street_line2, 'Apt 4B')
        self.assertTrue(address.is_default)

    def test_user_registration_without_address(self) -> None:
        """
        Test user registration without address fields (backward compatibility).

        Returns:
            None
        """
        from apps.accounts.models import Address
        
        data = {
            'email': 'noaddress@example.com',
            'password': 'securepassword123',
            'first_name': 'No',
            'last_name': 'Address',
            'username': 'noaddress'
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        user = User.objects.get(email='noaddress@example.com')
        self.assertTrue(user)
        
        # Verify no address was created
        address_count = Address.objects.filter(user=user).count()
        self.assertEqual(address_count, 0)



class UserLoginViewTests(APITestCase):
    """
    Test cases for the UserLoginView API endpoint.

    Attributes:
        client (APIClient): The test client for making API requests.
        user (User): A test user for login tests.
        url (str): The URL for the user login endpoint.
    """

    def setUp(self) -> None:
        """
        Set up test data before each test method.

        Returns:
            None
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='loginuser',
            email='loginuser@example.com',
            password='testpassword123',
            first_name='Login',
            last_name='User'
        )
        self.url = reverse('user-login')

    def test_login_with_valid_credentials(self) -> None:
        """
        Test login with valid credentials returns JWT tokens.

        Returns:
            None
        """
        data = {
            'email': 'loginuser@example.com',
            'password': 'testpassword123'
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_invalid_credentials(self) -> None:
        """
        Test login with invalid credentials returns error.

        Returns:
            None
        """
        data = {
            'email': 'loginuser@example.com',
            'password': 'wrongpassword'
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
