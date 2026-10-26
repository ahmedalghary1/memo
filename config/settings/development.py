from .base import *
DEBUG = True
STORAGES = {
    "default": {"BACKEND": "apps.core.storage.WebPImageStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
