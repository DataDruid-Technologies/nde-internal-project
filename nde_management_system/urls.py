# nde_management_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from core.views import login_view, dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_required(dashboard), name='root'),
    path('login/', login_view, name='login'),
    path('', include('core.urls')),
    path('/communication/', include('communication.urls')),
    path('hr/', include('hr.urls')),
    path('finance/', include('finance.urls')),
    path('__reload__/', include('django_browser_reload.urls')),
]