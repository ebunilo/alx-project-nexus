from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView, UserLoginView, PasswordResetView, PasswordResetConfirmView,
    UserProfileView, AddressListCreateView, AddressDetailView, AllUsersView
)

urlpatterns = [
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', UserLoginView.as_view(), name='user-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', TokenRefreshView.as_view(), name='user-logout'),  # Placeholder for logout
    path('auth/password/reset/', PasswordResetView.as_view(), name='password-reset'),
    path('auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('users/addresses/<uuid:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('users/all/', AllUsersView.as_view(), name='all_users'),
]