from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout, name='logout'),
    path('employee/list/', views.employee_list, name='employee_list'),
    path('employee/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('employee/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    
    # New URLs for inbox
    path('inbox/', views.inbox, name='inbox_list'),
    path('inbox/sent/', views.sent_messages, name='sent_messages'),
    path('inbox/compose/', views.compose_message, name='compose_message'),
    path('inbox/<int:message_id>/', views.message_detail, name='message_detail'),
    path('inbox/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    
    # New URLs for chat
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:other_user_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:other_user_id>/popup/', views.chat_popup, name='chat_popup'),
    path('chat/update-status/', views.update_chat_status, name='update_chat_status'),
    path('chat/unread-count/', views.get_unread_count, name='get_unread_count'),
    
    # New URL for dashboard search
    path('search/', views.dashboard_search, name='dashboard_search'),
    path('date_hpload/', views.data_upload, name='data_upload'),
    
    # # New URLs for roles and permissions
    # path('admin/roles/', views.role_list, name='role_list'),
    # path('admin/roles/create/', views.role_create, name='role_create'),
    # path('admin/roles/<int:role_id>/update/', views.role_update, name='role_update'),
    # path('admin/permissions/', views.custom_permission_list, name='custom_permission_list'),
    # path('admin/permissions/create/', views.custom_permission_create, name='custom_permission_create'),
    
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/<int:pk>/', views.workflow_detail, name='workflow_detail'),
    path('workflows/create/', views.workflow_create, name='create_workflow'),
    path('workflows/<int:pk>/update/', views.workflow_update, name='workflow_update'),
    path('step-library/', views.step_library_list, name='step_library_list'),
    path('step-library/create/', views.step_library_create, name='step_library_create'),
    path('subordinate-access/', views.subordinate_access_management, name='subordinate_access_management'),
    path('email-list/', views.email_list, name='email_list'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('test-email/', views.test_email, name='test_email'),

    # Workflow URLs

    path('performance/', views.performance_management, name='performance_management'),
    path('performance/create/<int:employee_id>/', views.performance_create, name='performance_create'),
    
    path('training/', views.training_management, name='training_management'),
    path('training/create/', views.training_create, name='training_create'),
    
    path('retirement/', views.retirement_management, name='retirement_management'),
    path('retirement/create/<int:employee_id>/', views.retirement_create, name='retirement_create'),
    path('reports/', views.hr_reporting, name='hr_reporting'),
    
    path('search-employees/', views.search_employees, name='search_employees'),


    path('departments/', views.department_list, name='department_list'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/update/', views.department_update, name='department_update'),

    # Project URLs
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/create/', views.project_create, name='create_project'),
    path('projects/<int:pk>/update/', views.project_update, name='project_update'),

    # Task URLs
    path('projects/<int:project_pk>/tasks/create/', views.task_create, name='task_create'),
    path('user-search/', views.user_search, name='user_search'),
   
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/update/', views.task_update, name='task_update'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    


    # Announcement URLs
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/create/', views.announcement_create, name='create_announcement'),

    # Notification URLs
    path('notifications/', views.notifications, name='notifications'),
    
]