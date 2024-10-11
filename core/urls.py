# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('change-password/', views.change_password, name='change_password'),
    path('logout/', views.logout_view, name='logout'),
    
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/create/', views.employee_create_view, name='employee_create'),
    path('employees/<int:pk>/update/', views.employee_update_view, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete_view, name='employee_delete'),
    path('data-upload/', views.data_upload_view, name='data_upload'),
    path('employees/<int:pk>/assign-role/', views.assign_role_view, name='assign_role'),
    path('employees/<int:pk>/assign-unit/', views.assign_unit_view, name='assign_unit'),
    
    #pssword Reset views
    
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
]
