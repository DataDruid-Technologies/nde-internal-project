from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Employee management
    path('employees/list/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('employee/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    path('employee/<int:employee_id>/assign-role/', views.assign_role, name='assign_role'),
    path('profile/', views.profile, name='profile'),
]