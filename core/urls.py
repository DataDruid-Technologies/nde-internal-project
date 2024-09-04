from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    
    # Employee management
    path('employees/list/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('employee/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    path('employee/<int:employee_id>/assign-role/', views.assign_role, name='assign_role'),
    path('profile/', views.profile, name='profile'),
    
    # Workflow URLs
    path('workflow/steps/', views.workflow_step_list, name='workflow_step_list'),
    path('workflow/steps/create/', views.workflow_step_create, name='workflow_step_create'),
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/create/', views.workflow_create, name='workflow_create'),
    path('workflows/<int:pk>/', views.workflow_detail, name='workflow_detail'),
    path('workflow-instances/create/', views.workflow_instance_create, name='workflow_instance_create'),
    path('workflow-instances/<int:pk>/', views.workflow_instance_detail, name='workflow_instance_detail'),

    path('inbox/', views.InboxListView.as_view(), name='inbox_list'),
    path('inbox/<int:pk>/', views.InboxDetailView.as_view(), name='inbox_detail'),
    path('inbox/create/', views.InboxCreateView.as_view(), name='inbox_create'),
    path('inbox/<int:pk>/delete/', views.InboxDeleteView.as_view(), name='inbox_delete'),

]