from django.urls import path
from .views import UserRegistrationView, UserProfileView, AddressListCreateView, AddressDetailView

urlpatterns = [
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('users/addresses/<uuid:pk>/', AddressDetailView.as_view(), name='address-detail'),
]