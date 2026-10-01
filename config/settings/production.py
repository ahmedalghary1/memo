from .base import *
DEBUG = False
_public_https = PUBLIC_ORIGIN.startswith("https://")
SESSION_COOKIE_SECURE = _public_https
CSRF_COOKIE_SECURE = _public_https
SECURE_HSTS_SECONDS = 31536000 if _public_https else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1" if _public_https else "0") == "1"
# Evolution and Django share a private Docker network. Keep this single callback
# reachable over internal HTTP even when all public traffic is forced to HTTPS.
SECURE_REDIRECT_EXEMPT = [r"^api/whatsapp/webhook/$"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = (
    [x.strip() for x in _csrf_origins.split(",") if x.strip()]
    if _csrf_origins
    else [PUBLIC_ORIGIN]
)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")
