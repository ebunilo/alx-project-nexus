"""
This module defines API views for the accounts app.
"""

from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer,
    UserLoginSerializer, AddressSerializer
)
from .models import Address
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from .tasks import send_password_reset_email

User = get_user_model()

class UserRegistrationView(APIView):
    """
    API view for user registration.

    Methods:
        post: Handles user registration requests.
    """

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Create a new user account with email, password, and other details.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="User's email address"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="User's password"),
                "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="User's first name"),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="User's last name"),
                "username": openapi.Schema(type=openapi.TYPE_STRING, description="Optional username"),
            },
            required=["email", "password"],
        ),
        responses={
            201: openapi.Response("User created successfully"),
            400: openapi.Response("Validation error"),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Register a new user.

        Args:
            request (Request): The HTTP request containing user data.

        Returns:
            Response: HTTP response with user data or validation errors.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    API view for user login.

    Methods:
        post: Handles user login requests.
    """

    @swagger_auto_schema(
        operation_summary="Log in a user",
        operation_description="Authenticate a user with their email and password to receive a JWT token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="User's email address"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="User's password"),
            },
            required=["email", "password"],
        ),
        responses={
            200: openapi.Response("Login successful"),
            401: openapi.Response("Invalid credentials"),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Log in a user and return a JWT token.

        Args:
            request (Request): The HTTP request containing login credentials.

        Returns:
            Response: HTTP response with JWT tokens or error message.
        """
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """
    API view for password reset requests.

    Methods:
        post: Sends a password reset email to the user.
    """

    @swagger_auto_schema(
        operation_summary="Request password reset",
        operation_description="Send a password reset email to the user's email address.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's email address"
                ),
            },
            required=["email"],
        ),
        responses={
            200: openapi.Response("Password reset email sent"),
            400: openapi.Response("Email is required"),
            404: openapi.Response("No user is associated with this email"),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Send a password reset email to the user.

        Args:
            request (Request): The HTTP request containing the user's email.

        Returns:
            Response: HTTP response indicating email sent or error.
        """
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "No user is associated with this email."}, status=status.HTTP_404_NOT_FOUND)

        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        # Send the email asynchronously using Celery
        send_password_reset_email.delay(email, reset_url)

        return Response({"detail": "Password reset email sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    API view for password reset confirmation.

    Methods:
        post: Resets the user's password using a token.
    """

    @swagger_auto_schema(
        operation_summary="Confirm a password reset",
        operation_description="Reset the user's password using a token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "token": openapi.Schema(type=openapi.TYPE_STRING, description="Password reset token"),
                "new_password": openapi.Schema(type=openapi.TYPE_STRING, description="New password"),
            },
            required=["token", "new_password"],
        ),
        responses={
            200: openapi.Response("Password reset successful"),
            400: openapi.Response("Invalid token or password"),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Reset the user's password.

        Args:
            request (Request): The HTTP request containing token and password.

        Returns:
            Response: HTTP response indicating success or failure.
        """
        # Your existing implementation
        pass


class UserProfileView(APIView):
    """
    API view for user profile retrieval and updates.

    Methods:
        get: Retrieves the authenticated user's profile.
        put: Updates the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve user profile",
        operation_description="Get the details of the currently authenticated user.",
        responses={
            200: openapi.Response("User profile retrieved successfully"),
        },
    )
    def get(self, request: Request) -> Response:
        """
        Retrieve the authenticated user's profile.

        Args:
            request (Request): The HTTP request from authenticated user.

        Returns:
            Response: HTTP response with user profile data.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description="Update the details of the currently authenticated user.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="User's first name"),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="User's last name"),
            },
            required=["first_name", "last_name"],
        ),
        responses={
            200: openapi.Response("User profile updated successfully"),
            400: openapi.Response("Validation error"),
        },
    )
    def put(self, request: Request) -> Response:
        """
        Update the authenticated user's profile.

        Args:
            request (Request): The HTTP request with updated profile data.

        Returns:
            Response: HTTP response with updated data or errors.
        """
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressListCreateView(APIView):
    """
    API view for listing and creating user addresses.

    Methods:
        get: Retrieves all addresses for the authenticated user.
        post: Creates a new address for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List all addresses",
        operation_description="Retrieve all addresses for the authenticated user.",
        responses={
            200: openapi.Response("Addresses retrieved successfully"),
        },
    )
    def get(self, request: Request) -> Response:
        """
        List all addresses for the authenticated user.

        Args:
            request (Request): The HTTP request from authenticated user.

        Returns:
            Response: HTTP response with list of addresses.
        """
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Create a new address",
        operation_description="Create a new address for the authenticated user.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "address_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Type of address",
                    enum=["home", "work", "billing", "shipping"]
                ),
                "contact_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Name of the contact person (optional)"
                ),
                "phone": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Contact phone number (optional)"
                ),
                "street_line1": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Street address line 1 (required)"
                ),
                "street_line2": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Street address line 2 (optional)"
                ),
                "city": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="City name (required)"
                ),
                "state_province": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="State or province (optional)"
                ),
                "postal_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Postal/ZIP code (optional)"
                ),
                "country_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="ISO 3166-1 alpha-2 country code, e.g., 'NG' for Nigeria (required)"
                ),
                "is_default": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Set as default address (default: false)"
                ),
            },
            required=["street_line1", "city", "country_code"],
        ),
        responses={
            201: openapi.Response("Address created successfully"),
            400: openapi.Response("Validation error"),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Create a new address for the authenticated user.

        Args:
            request (Request): The HTTP request with address data.

        Returns:
            Response: HTTP response with created address or errors.
        """
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDetailView(APIView):
    """
    API view for retrieving, updating, and deleting a specific address.

    Methods:
        get: Retrieves a specific address.
        put: Updates a specific address.
        delete: Deletes a specific address.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk: str, user):
        """
        Get address object by pk, ensuring it belongs to the user.

        Args:
            pk (str): The primary key of the address.
            user: The authenticated user.

        Returns:
            Address: The address object or None.
        """
        try:
            return Address.objects.get(pk=pk, user=user)
        except Address.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary="Retrieve address details",
        operation_description="Get the details of a specific address by its ID.",
        responses={
            200: openapi.Response("Address retrieved successfully"),
            404: openapi.Response("Address not found"),
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        """
        Retrieve a specific address.

        Args:
            request (Request): The HTTP request.
            pk (str): The primary key of the address.

        Returns:
            Response: HTTP response with address data or not found.
        """
        address = self.get_object(pk, request.user)
        if not address:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AddressSerializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Update address details",
        operation_description="Update the details of a specific address by its ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "address_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Type of address",
                    enum=["home", "work", "billing", "shipping"]
                ),
                "contact_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Name of the contact person"
                ),
                "phone": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Contact phone number"
                ),
                "street_line1": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Street address line 1"
                ),
                "street_line2": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Street address line 2"
                ),
                "city": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="City name"
                ),
                "state_province": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="State or province"
                ),
                "postal_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Postal/ZIP code"
                ),
                "country_code": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="ISO 3166-1 alpha-2 country code, e.g., 'NG' for Nigeria"
                ),
                "is_default": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Set as default address"
                ),
            },
        ),
        responses={
            200: openapi.Response("Address updated successfully"),
            400: openapi.Response("Validation error"),
            404: openapi.Response("Address not found"),
        },
    )
    def put(self, request: Request, pk: str) -> Response:
        """
        Update a specific address.

        Args:
            request (Request): The HTTP request with updated data.
            pk (str): The primary key of the address.

        Returns:
            Response: HTTP response with updated data or errors.
        """
        address = self.get_object(pk, request.user)
        if not address:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete an address",
        operation_description="Delete a specific address by its ID.",
        responses={
            204: openapi.Response("Address deleted successfully"),
            404: openapi.Response("Address not found"),
        },
    )
    def delete(self, request: Request, pk: str) -> Response:
        """
        Delete a specific address.

        Args:
            request (Request): The HTTP request.
            pk (str): The primary key of the address.

        Returns:
            Response: HTTP response indicating success or not found.
        """
        address = self.get_object(pk, request.user)
        if not address:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AllUsersView(APIView):
    """
    API view for retrieving all user profiles (Admin only).

    Methods:
        get: Retrieves all user profiles.
    """
    permission_classes = [IsAdminUser]

    def get(self, request: Request) -> Response:
        """
        Retrieve all user profiles.

        Args:
            request (Request): The HTTP request from admin user.

        Returns:
            Response: HTTP response with all user profiles.
        """
        users = User.objects.all()
        serializer = UserProfileSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
