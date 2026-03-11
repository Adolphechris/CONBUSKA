from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404

# URL names that are always accessible even when force_password_change=True
EXEMPT_URL_NAMES = {
    'user_password_change',
    'user_profile',
}

# URL path prefixes that are always accessible (static files, media, admin, auth)
EXEMPT_PATH_PREFIXES = (
    '/login/',
    '/accounts/',
    '/admin/',
    '/static/',
    '/media/',
    '/select2/',
)


class ForcePasswordChangeMiddleware:
    """
    If an authenticated user has force_password_change=True, redirect every
    request to the password-change page until they set a new password.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_redirect(request):
            return redirect(reverse('user_password_change'))
        return self.get_response(request)

    def _should_redirect(self, request):
        if not request.user.is_authenticated:
            return False
        if not getattr(request.user, 'force_password_change', False):
            return False

        path = request.path_info

        # Allow exempt path prefixes
        if any(path.startswith(prefix) for prefix in EXEMPT_PATH_PREFIXES):
            return False

        # Allow exempt named URLs
        try:
            match = resolve(path)
            if match.url_name in EXEMPT_URL_NAMES:
                return False
        except Resolver404:
            pass

        return True
