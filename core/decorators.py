# core/decorators.py
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

def role_required(allowed_roles):
    def check_role(user):
        return user.role in allowed_roles
    return user_passes_test(check_role, login_url='core:login')