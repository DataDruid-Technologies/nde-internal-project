# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('nde-admin/', admin.site.urls),
    path('', include('core.urls')),
]