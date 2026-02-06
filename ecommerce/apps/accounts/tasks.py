"""
This module defines asynchronous tasks for the accounts app.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_password_reset_email(email: str, reset_url: str) -> None:
    """
    Send a password reset email to the specified email address.

    Args:
        email (str): Recipient's email address.
        reset_url (str): URL for resetting the password.

    Returns:
        None
    """
    send_mail(
        subject="Password Reset Request",
        message=f"Click the link to reset your password: {reset_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )