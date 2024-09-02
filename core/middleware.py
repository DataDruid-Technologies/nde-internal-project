from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch

class LoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                login_url = reverse('login')
                if request.path == login_url:
                    return redirect('dashboard')
            except NoReverseMatch:
                # If 'login' URL is not found, we'll just continue with the request
                pass
        return self.get_response(request)
    

class AutoNavigationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path == reverse('login'):
            return redirect('dashboard')
        response = self.get_response(request)
        return response