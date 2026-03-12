import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_ip():
    return getattr(_thread_locals, 'ip_address', None)


def clear_current_request():
    _thread_locals.user = None
    _thread_locals.ip_address = None


class CurrentUserMiddleware:
    """Stores the authenticated user and IP in thread-local storage so that
    signal handlers can access them without receiving the request object."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        clear_current_request()
        user = getattr(request, 'user', None)
        _thread_locals.user = user if (user and user.is_authenticated) else None
        _thread_locals.ip_address = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        try:
            response = self.get_response(request)
            return response
        finally:
            clear_current_request()
