from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # InAppEmail URLs
    path('inbox/', views.inbox, name='inbox'),
    path('compose/', views.compose_email, name='compose_email'),
    path('email/<int:email_id>/', views.view_email, name='view_email'),
    path('email/<int:email_id>/delete/', views.delete_email, name='delete_email'),
    path('search-emails/', views.search_emails, name='search_emails'),

    # InAppChat URLs
    path('chats/', views.chat_list, name='chat_list'),
    path('chat/create/', views.create_chat, name='create_chat'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('search-chats/', views.search_chats, name='search_chats'),

    # Notification URLs
    path('notifications/', views.notifications, name='notifications'),
    path('notification/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),

    # Task URLs
    path('tasks/', views.task_list, name='task_list'),
    path('task/create/', views.create_task, name='create_task'),
    path('task/<int:task_id>/update/', views.update_task, name='update_task'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    # DepartmentAnnouncement URLs
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcement/create/', views.create_announcement, name='create_announcement'),
    path('announcement/<int:announcement_id>/update/', views.update_announcement, name='update_announcement'),
    path('announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('announcement/<int:announcement_id>/', views.view_announcement, name='view_announcement'),

    # Newsletter URLs
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletter/create/', views.create_newsletter, name='create_newsletter'),
    path('newsletter/<int:newsletter_id>/update/', views.update_newsletter, name='update_newsletter'),
    path('newsletter/<int:newsletter_id>/delete/', views.delete_newsletter, name='delete_newsletter'),
    path('newsletter/<int:newsletter_id>/', views.view_newsletter, name='view_newsletter'),

    # CommunicationLog URL
    path('communication-log/', views.communication_log, name='communication_log'),
]