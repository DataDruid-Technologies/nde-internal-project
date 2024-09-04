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

    path('inbox/', views.inbox, name='inbox_list'),
    path('inbox/sent', views.sent_messages, name='sent_messages'),
    path('inbox/compose/', views.compose_message, name='compose_message'),
    path('inbox/<int:pk>/', views.message_detail, name='message_detail'),
    path('inbox/search',views.search_messages,name ='search_messages'),
    
    # Chat utls
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:pk>/', views.chat_detail, name='chat_detail'),
    
    path('data-upload/', views.data_upload, name='data_upload'),
    
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    path('employees/<int:employee_id>/assign-role/', views.assign_role, name='assign_role'),
    path('employees/self-update/', views.employee_self_update, name='employee_self_update'),
    path('performance/', views.performance_management, name='performance_management'),
    path('performance/create/<int:employee_id>/', views.performance_create, name='performance_create'),
    path('training/', views.training_management, name='training_management'),
    path('training/create/', views.training_create, name='training_create'),
    path('retirement/', views.retirement_management, name='retirement_management'),
    path('retirement/create/<int:employee_id>/', views.retirement_create, name='retirement_create'),
    path('reports/', views.hr_reporting, name='hr_reporting'),
# Don't forget to add this URL to your urls.py
    path('search-employees/', views.search_employees, name='search_employees'),
]