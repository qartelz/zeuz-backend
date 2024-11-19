from django.core.cache import cache
from django.core.mail import send_mail
import random


def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def set_otp_in_cache(email, otp, purpose):
    """Store OTP in cache with an expiration time (e.g., 10 minutes)."""
    cache_key = f"{purpose}_otp_{email}"
    cache.set(cache_key, otp, timeout=600) 

def get_otp_from_cache(email, purpose):
    """Retrieve OTP from cache."""
    cache_key = f"{purpose}_otp_{email}"
    return cache.get(cache_key)


def delete_otp_from_cache(email, purpose):
    """Delete OTP from cache after verification or expiration."""
    cache_key = f"{purpose}_otp_{email}"
    cache.delete(cache_key)


def send_otp_email(email, otp_code, purpose):
    """Send OTP to user's email."""
    subject = 'Your OTP Code'
    message = f'Your OTP code for {purpose} is {otp_code}. It is valid for 10 minutes.'
    send_mail(subject, message, 'your-email@example.com', [email])
