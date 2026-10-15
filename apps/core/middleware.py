from django.utils import translation


class SiteLanguageMiddleware:
    """Use English on the storefront and Arabic in staff interfaces."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        language = "ar" if path.startswith(("/dashboard/", "/django-admin/")) else "en"
        translation.activate(language)
        request.LANGUAGE_CODE = language
        return self.get_response(request)
