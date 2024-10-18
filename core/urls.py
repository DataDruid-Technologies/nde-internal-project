# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Existing URLs
    path('login/', views.login_view, name='login'),
    path('change-password/', views.change_password, name='change_password'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('calendar/', views.calendar, name='calendar'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings, name='settings'),
    path('help/', views.help, name='help'),
    
    path('files/', views.file_list, name='file_list'),
    path('files/create/', views.file_create, name='file_create'),
    path('files/<int:file_id>/', views.file_detail, name='file_detail'),
    path('files/<int:file_id>/update/', views.file_update, name='file_update'),
    path('files/<int:file_id>/history/add/', views.file_history_add, name='file_history_add'),
    
    path('performance-overview/', views.performance_overview, name='performance_overview'),
    
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/create/', views.employee_create_view, name='employee_create'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/update/', views.employee_update_view, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete_view, name='employee_delete'),
    path('data-upload/', views.data_upload_view, name='data_upload'),
    path('employees/<int:pk>/assign-role/', views.assign_role_view, name='assign_role'),
    path('employees/<int:pk>/assign-unit/', views.assign_unit_view, name='assign_unit'),
    
    # Password Reset URLs
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),

    # New URLs for search, notifications, and messages
    path('search/', views.search, name='search'),
    path('get-notifications/', views.get_notifications, name='get_notifications'),
    path('get-messages/', views.get_messages, name='get_messages'),
    path('mark-notification-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
]