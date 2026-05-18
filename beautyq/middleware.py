from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

PARLOUR_OWNER_PATH_PREFIXES = (
    '/dashboard',
    '/appointments/',
    '/catalog/',
    '/staff/',
    '/duty-roster/',
    '/duty/',
    '/payouts/',
    '/earnings/',
    '/transactions/',
    '/export/',
    '/reviews/',
    '/messages/',
    '/supportdesk/',
)


def _is_parlour_owner_path(path):
    return any(
        path == prefix.rstrip('/') or path.startswith(prefix)
        for prefix in PARLOUR_OWNER_PATH_PREFIXES
    )


class StaffAdminMiddleware:
    """Require staff login for custom admin routes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/myadmin/'):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url=settings.LOGIN_URL)
            if not request.user.is_staff:
                messages.error(request, 'You do not have permission to access the admin panel.')
                return redirect('/')
        return self.get_response(request)


class ParlourOwnerMiddleware:
    """Require parlour owner login for owner dashboard routes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _is_parlour_owner_path(request.path):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url=settings.LOGIN_URL)
            if not (request.user.parlours.exists() or request.user.is_staff):
                messages.error(request, 'You need a parlour owner account to access this area.')
                return redirect('/')
        return self.get_response(request)
