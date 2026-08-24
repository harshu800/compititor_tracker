"""Thin wrapper around the Razorpay SDK so routes/tests never touch the
SDK directly — makes it easy to swap providers later (spec section 50
calls for this same abstraction pattern used for AI/email providers)."""
import razorpay

from app.config import get_settings

settings = get_settings()

_client: razorpay.Client | None = None


def get_razorpay_client() -> razorpay.Client:
    global _client
    if _client is None:
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise RuntimeError("Razorpay is not configured (RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET missing)")
        _client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    return _client
