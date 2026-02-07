"""
This module defines the database models for the accounts app.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

class User(AbstractUser):
    """
    Custom user model extending the default Django AbstractUser.

    Attributes:
        email (EmailField): Unique email address for the user.
        role (CharField): Role of the user (e.g., Customer, Admin, Merchant).
    """

    class Roles(models.TextChoices):
        CUSTOMER = 'customer', _('Customer')
        ADMIN = 'admin', _('Admin')
        MERCHANT = 'merchant', _('Merchant')

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self) -> str:
        """
        Return the string representation of the user.

        Returns:
            str: The username of the user.
        """
        return self.username

class Country(models.Model):
    """
    Represents a country with its code, name, and other details.

    Attributes:
        code (CharField): ISO 3166-1 alpha-2 country code.
        name (CharField): Name of the country.
        phone_code (CharField): Country's phone code.
        currency_code (CharField): Country's currency code.
        is_active (BooleanField): Indicates if the country is active.
        created_at (DateTimeField): Timestamp of creation.
    """

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    phone_code = models.CharField(max_length=10, blank=True, null=True)
    currency_code = models.CharField(max_length=3, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        """
        Return the string representation of the country.

        Returns:
            str: The name of the country.
        """
        return self.name

class Address(models.Model):
    """
    Represents an address associated with a user.

    Attributes:
        id (UUIDField): Unique identifier for the address.
        user (ForeignKey): Reference to the associated user.
        address_type (CharField): Type of address (e.g., Home, Work).
        contact_name (CharField): Name of the contact person.
        phone (CharField): Contact phone number.
        street_line1 (CharField): First line of the street address.
    """

    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='home')
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    street_line1 = models.CharField(max_length=255)
    street_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='addresses')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """
        Return the string representation of the address.

        Returns:
            str: A description of the address type and associated user.
        """
        return f"{self.address_type} address for {self.user.username}"
