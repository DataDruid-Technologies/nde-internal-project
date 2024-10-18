# communication/urls.py

from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Email URLs
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent_emails, name='sent_emails'),
    path('compose/', views.compose_email, name='compose_email'),
    path('email/<int:email_id>/', views.view_email, name='view_email'),
    path('email/<int:email_id>/delete/', views.delete_email, name='delete_email'),

    # Chat URLs
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/create/', views.create_chat, name='create_chat'),
    path('chats/<int:chat_id>/', views.chat_room, name='chat_room'),
    path('chats/<int:chat_id>/leave/', views.leave_chat, name='leave_chat'),

    # Task URLs
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:task_id>/', views.view_task, name='view_task'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/update/', views.update_task, name='update_task'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),

    # Announcement URLs
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),

    # Newsletter URLs
    path('newsletters/', views.NewsletterListView.as_view(), name='newsletter_list'),
    path('newsletters/create/', views.create_newsletter, name='create_newsletter'),

    # Notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),

    # Utility URLs
    path('search-employees/', views.search_employees, name='search_employees'),
    path('dashboard/', views.communication_dashboard, name='dashboard'),
]