from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserRegistrationSerializer, UserProfileSerializer, UserLoginSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .tasks import send_password_reset_email

User = get_user_model()

class UserRegistrationView(APIView):
    """
    Handles user registration.
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
    def post(self, request):
        """
        Register a new user.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    Handles user login.
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
    def post(self, request):
        """
        Log in a user and return a JWT token.
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
    Handles password reset requests.
    """

    def post(self, request):
        """
        Send a password reset email to the user.
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
        reset_url = f"https://example.com/reset-password/{uid}/{token}/"

        # Send the email asynchronously using Celery
        send_password_reset_email.delay(email, reset_url)

        return Response({"detail": "Password reset email sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Handles password reset confirmation.
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
    def post(self, request):
        """
        Reset the user's password.
        """
        # Your existing implementation
        pass


class UserProfileView(APIView):
    """
    Handles user profile retrieval and updates.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve user profile",
        operation_description="Get the details of the currently authenticated user.",
        responses={
            200: openapi.Response("User profile retrieved successfully"),
        },
    )
    def get(self, request):
        """
        Retrieve the authenticated user's profile.
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
    def put(self, request):
        """
        Update the authenticated user's profile.
        """
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressListCreateView(APIView):
    """
    Handles listing and creating user addresses.
    """

    @swagger_auto_schema(
        operation_summary="List all addresses",
        operation_description="Retrieve all addresses for the authenticated user.",
        manual_parameters=[
            openapi.Parameter(
                "user_id",
                openapi.IN_QUERY,
                description="ID of the user whose addresses are being retrieved.",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={
            200: openapi.Response("Addresses retrieved successfully"),
        },
    )
    def get(self, request):
        """
        List all addresses for the authenticated user.
        """
        # Your existing implementation
        pass

    def post(self, request):
        """
        Create a new address for the authenticated user.
        """
        # Your existing implementation
        pass


class AddressDetailView(APIView):
    """
    Handles retrieving, updating, and deleting a specific address.
    """

    @swagger_auto_schema(
        operation_summary="Retrieve address details",
        operation_description="Get the details of a specific address by its ID.",
        responses={
            200: openapi.Response("Address retrieved successfully"),
            404: openapi.Response("Address not found"),
        },
    )
    def get(self, request, pk):
        """
        Retrieve a specific address.
        """
        # Your existing implementation
        pass

    @swagger_auto_schema(
        operation_summary="Update address details",
        operation_description="Update the details of a specific address by its ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "address_type": openapi.Schema(type=openapi.TYPE_STRING, description="Type of address"),
                "street_line1": openapi.Schema(type=openapi.TYPE_STRING, description="Street address line 1"),
            },
            required=["address_type", "street_line1"],
        ),
        responses={
            200: openapi.Response("Address updated successfully"),
            400: openapi.Response("Validation error"),
        },
    )
    def put(self, request, pk):
        """
        Update a specific address.
        """
        # Your existing implementation
        pass

    @swagger_auto_schema(
        operation_summary="Delete an address",
        operation_description="Delete a specific address by its ID.",
        responses={
            204: openapi.Response("Address deleted successfully"),
            404: openapi.Response("Address not found"),
        },
    )
    def delete(self, request, pk):
        """
        Delete a specific address.
        """
        # Your existing implementation
        pass


class AllUsersView(APIView):
    """
    Retrieve all user profiles (Admin only).
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all()
        serializer = UserProfileSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
