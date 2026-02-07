"""
This module defines serializers for the accounts app.
"""

from typing import Any, Dict

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Address
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Attributes:
        username (CharField): Optional username for the user.
        password (CharField): Password for the user.
        street_line1 (CharField): Optional first line of street address.
        street_line2 (CharField): Optional second line of street address.
    """

    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    street_line1 = serializers.CharField(required=False, allow_blank=True, max_length=255)
    street_line2 = serializers.CharField(required=False, allow_blank=True, max_length=255)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role', 'street_line1', 'street_line2']

    def create(self, validated_data: Dict[str, Any]) -> Any:
        """
        Create and return a new user instance.

        Args:
            validated_data (Dict[str, Any]): Validated data from the
                serializer.

        Returns:
            User: The newly created user instance.
        """
        # Extract address fields if present
        street_line1 = validated_data.pop('street_line1', None)
        street_line2 = validated_data.pop('street_line2', None)
        
        # Remove username if it's blank
        if not validated_data.get('username'):
            validated_data['username'] = validated_data['email']
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', User.Roles.CUSTOMER),
        )
        
        # Create initial address if street_line1 is provided
        if street_line1:
            from django.conf import settings
            from .models import Country
            
            # Get default country from settings or use a fallback
            default_country_code = getattr(settings, 'DEFAULT_COUNTRY_CODE', 'NG')
            default_country_name = getattr(settings, 'DEFAULT_COUNTRY_NAME', 'Nigeria')
            default_phone_code = getattr(settings, 'DEFAULT_PHONE_CODE', '+234')
            default_currency_code = getattr(settings, 'DEFAULT_CURRENCY_CODE', 'NGN')
            
            # Get or create the default country
            default_country, _ = Country.objects.get_or_create(
                code=default_country_code,
                defaults={
                    'name': default_country_name,
                    'phone_code': default_phone_code,
                    'currency_code': default_currency_code,
                    'is_active': True
                }
            )
            Address.objects.create(
                user=user,
                address_type='home',
                street_line1=street_line1,
                street_line2=street_line2,
                country_code=default_country,
                is_default=True
            )
        
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Attributes:
        email (EmailField): Email address of the user.
        password (CharField): Password of the user.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset requests.

    Attributes:
        email (EmailField): Email address of the user requesting a password reset.
    """

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        """
        Validate that the email exists in the database.

        Args:
            value (str): The email address to validate.

        Returns:
            str: The validated email address.

        Raises:
            ValidationError: If no user is associated with the email.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('No user is associated with this email.'))
        return value

    def save(self) -> None:
        """
        Send a password reset email to the user.

        Generates a password reset token and sends an email
        with the reset link.
        """
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        reset_url = f"https://example.com/reset-password/{user.pk}/{token}/"
        send_mail(
            subject=_('Password Reset Request'),
            message=f"Click the link to reset your password: {reset_url}",
            from_email='noreply@example.com',
            recipient_list=[email],
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.

    Attributes:
        new_password (CharField): The new password for the user.
        token (CharField): The password reset token.
        user_id (IntegerField): The ID of the user resetting their password.
    """

    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    token = serializers.CharField()
    user_id = serializers.IntegerField()

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the password reset token.

        Args:
            attrs (Dict[str, Any]): The attributes to validate.

        Returns:
            Dict[str, Any]: The validated attributes.

        Raises:
            ValidationError: If the token is invalid or expired.
        """
        user = User.objects.get(pk=attrs['user_id'])
        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError(_('Invalid or expired token.'))
        return attrs

    def save(self) -> None:
        """
        Save the new password for the user.

        Updates the user's password with the new validated password.
        """
        user = User.objects.get(pk=self.validated_data['user_id'])
        user.set_password(self.validated_data['new_password'])
        user.save()

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.

    Used for retrieving and updating user profile details.
    """

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role']

class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for user addresses.

    Handles serialization and deserialization of address data.
    """

    class Meta:
        model = Address
        fields = ['id', 'user', 'address_type', 'contact_name', 'phone', 'street_line1', 'street_line2', 'city', 'state_province', 'postal_code', 'country_code', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']