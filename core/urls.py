from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/<str:employee_id>/', views.employee_detail_view, name='employee_detail'),
    path('employees/create/', views.employee_create_view, name='employee_create'),
    path('employees/<str:employee_id>/update/', views.employee_update_view, name='employee_update'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/upload/', views.user_upload_view, name='user_upload'),
    path('settings/', views.settings_view, name='settings'),
]