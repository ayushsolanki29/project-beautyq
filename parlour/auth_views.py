from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

from .customer_views import role_login_redirect


class BeautyQLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return role_login_redirect(self.request.user)
