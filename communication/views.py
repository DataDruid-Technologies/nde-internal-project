from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
from .models import *
from .forms import *
from core.models import *
from datetime import datetime, timedelta


@login_required
def inbox(request):
    emails = InAppEmail.objects.filter(recipients=request.user).order_by('-sent_at')
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'communication/inbox.html', {'page_obj': page_obj})

@login_required
def compose_email(request):
    if request.method == 'POST':
        form = InAppEmailForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.save(commit=False)
            email.sender = request.user
            email.save()
            form.save_m2m()  # This will now also save the attachments
            
            messages.success(request, 'Email sent successfully.')
            
            # Send notification to personal email if enabled
            for recipient in email.recipients.all():
                if recipient.notify_personal_email:
                    send_mail(
                        f'New in-app email: {email.subject}',
                        f'You have received a new in-app email from {email.sender}. Log in to view the full message.',
                        settings.DEFAULT_FROM_EMAIL,
                        [recipient.email],
                        fail_silently=True,
                    )
            
            return redirect('communication:inbox')
    else:
        form = InAppEmailForm()
    return render(request, 'communication/compose_email.html', {'form': form})

@login_required
def view_email(request, email_id):
    email = get_object_or_404(InAppEmail, id=email_id, recipients=request.user)
    if request.user not in email.is_read.all():
        email.is_read.add(request.user)
    return render(request, 'communication/view_email.html', {'email': email})

@login_required
def delete_email(request, email_id):
    email = get_object_or_404(InAppEmail, id=email_id, recipients=request.user)
    email.recipients.remove(request.user)
    messages.success(request, 'Email deleted successfully.')
    return redirect('communication:inbox')

@login_required
def search_emails(request):
    query = request.GET.get('q', '')
    emails = InAppEmail.objects.filter(
        recipients=request.user,
        subject__icontains=query
    ).order_by('-sent_at')
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'communication/search_results.html', {'page_obj': page_obj, 'query': query})


# In app chat views
@login_required
def chat_list(request):
    chats = InAppChat.objects.filter(participants=request.user).order_by('-updated_at')
    return render(request, 'communication/chat_list.html', {'chats': chats})

@login_required
def create_chat(request):
    if request.method == 'POST':
        participant_ids = request.POST.getlist('participants')
        participants = Employee.objects.filter(id__in=participant_ids)
        chat = InAppChat.objects.create(is_group_chat=len(participants) > 2)
        chat.participants.add(request.user, *participants)
        return redirect('communication:chat_detail', chat_id=chat.id)
    employees = Employee.objects.exclude(id=request.user.id)
    return render(request, 'communication/create_chat.html', {'employees': employees})

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(InAppChat, id=chat_id, participants=request.user)
    messages = ChatMessage.objects.filter(chat=chat).order_by('timestamp')
    
    if request.method == 'POST':
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.save()
            chat.updated_at = message.timestamp
            chat.save()
            return redirect('communication:chat_detail', chat_id=chat.id)
    else:
        form = ChatMessageForm()
    
    return render(request, 'communication/chat_detail.html', {
        'chat': chat,
        'messages': messages,
        'form': form
    })

@login_required
def search_chats(request):
    query = request.GET.get('q', '')
    chats = InAppChat.objects.filter(
        participants=request.user
    ).filter(
        Q(group_name__icontains=query) |
        Q(participants__first_name__icontains=query) |
        Q(participants__last_name__icontains=query)
    ).distinct()
    return render(request, 'communication/search_chats.html', {'chats': chats, 'query': query})

# Notifiation Views
@login_required
def notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'communication/notifications.html', {'page_obj': page_obj})

@login_required
def mark_notification_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('communication:notifications')

@login_required
def clear_all_notifications(request):
    Notification.objects.filter(recipient=request.user).update(is_read=True)
    return redirect('communication:notifications')



# Tasks Views

@login_required
def task_list(request):
    tasks = Task.objects.filter(assigned_to=request.user).order_by('-due_date')
    return render(request, 'communication/task_list.html', {'tasks': tasks})

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            
            Notification.objects.create(
                recipient=task.assigned_to,
                notification_type='TASK',
                title=f'New Task: {task.title}',
                content=f'You have been assigned a new task by {request.user.get_full_name()}.'
            )
            
            # Send email notification
            if task.assigned_to.notify_personal_email:
                send_mail(
                    f'New Task Assigned: {task.title}',
                    f'You have been assigned a new task by {request.user.get_full_name()}. Due date: {task.due_date}',
                    settings.DEFAULT_FROM_EMAIL,
                    [task.assigned_to.email],
                    fail_silently=True,
                )
            
            messages.success(request, 'Task created successfully.')
            return redirect('communication:task_list')
    else:
        form = TaskForm()
    return render(request, 'communication/create_task.html', {'form': form})

@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('communication:task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'communication/update_task.html', {'form': form, 'task': task})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    messages.success(request, 'Task deleted successfully.')
    return redirect('communication:task_list')

@login_required
def overdue_tasks_notification():
    overdue_tasks = Task.objects.filter(
        status__in=['PENDING', 'IN_PROGRESS'],
        due_date__lt=datetime.now()
    )
    
    for task in overdue_tasks:
        Notification.objects.create(
            recipient=task.assigned_to,
            notification_type='TASK',
            title=f'Overdue Task: {task.title}',
            content=f'The task "{task.title}" is overdue. Please update its status or request an extension.'
        )
        
        if task.assigned_to.notify_personal_email:
            send_mail(
                f'Overdue Task: {task.title}',
                f'The task "{task.title}" assigned to you is overdue. Please log in to update its status or request an extension.',
                settings.DEFAULT_FROM_EMAIL,
                [task.assigned_to.email],
                fail_silently=True,
            )

# This function should be called daily using a task scheduler like Celery
def daily_summary():
    yesterday = datetime.now() - timedelta(days=1)
    employees = Employee.objects.all()
    
    for employee in employees:
        new_tasks = Task.objects.filter(assigned_to=employee, created_at__date=yesterday.date())
        unread_messages = InAppEmail.objects.filter(recipients=employee, sent_at__date=yesterday.date(), is_read__isnull=True)
        new_chats = ChatMessage.objects.filter(chat__participants=employee, timestamp__date=yesterday.date(), is_read__isnull=True)
        
        if new_tasks or unread_messages or new_chats:
            summary = f"Daily Summary for {yesterday.date()}:\n\n"
            if new_tasks:
                summary += f"New Tasks: {new_tasks.count()}\n"
            if unread_messages:
                summary += f"Unread Emails: {unread_messages.count()}\n"
            if new_chats:
                summary += f"Unread Chat Messages: {new_chats.count()}\n"
            
            Notification.objects.create(
                recipient=employee,
                notification_type='SYSTEM',
                title='Daily Summary',
                content=summary
            )
            
            if employee.notify_personal_email:
                send_mail(
                    'NDE IMS - Daily Summary',
                    summary,
                    settings.DEFAULT_FROM_EMAIL,
                    [employee.email],
                    fail_silently=True,
                )
                
# Announcement Views

@login_required
def announcement_list(request):
    announcements = DepartmentAnnouncement.objects.filter(department=request.user.current_department, is_active=True).order_by('-created_at')
    return render(request, 'communication/announcement_list.html', {'announcements': announcements})

@login_required
def create_announcement(request):
    if not request.user.has_perm('communication.add_departmentannouncement'):
        messages.error(request, 'You do not have permission to create announcements.')
        return redirect('communication:announcement_list')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.department = request.user.current_department
            announcement.save()
            
            # Notify all department employees
            employees = Employee.objects.filter(current_department=announcement.department)
            for employee in employees:
                Notification.objects.create(
                    recipient=employee,
                    notification_type='ANNOUNCEMENT',
                    title=f'New Announcement: {announcement.title}',
                    content=f'A new announcement has been posted in your department.'
                )
            
            messages.success(request, 'Announcement created successfully.')
            return redirect('communication:announcement_list')
    else:
        form = AnnouncementForm()
    return render(request, 'communication/create_announcement.html', {'form': form})

@login_required
def update_announcement(request, announcement_id):
    announcement = get_object_or_404(DepartmentAnnouncement, id=announcement_id, department=request.user.current_department)
    if not request.user.has_perm('communication.change_departmentannouncement'):
        messages.error(request, 'You do not have permission to update announcements.')
        return redirect('communication:announcement_list')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated successfully.')
            return redirect('communication:announcement_list')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'communication/update_announcement.html', {'form': form, 'announcement': announcement})


@login_required
def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(DepartmentAnnouncement, id=announcement_id, department=request.user.current_department)
    if not request.user.has_perm('communication.delete_departmentannouncement'):
        messages.error(request, 'You do not have permission to delete announcements.')
        return redirect('communication:announcement_list')
    
    announcement.is_active = False
    announcement.save()
    messages.success(request, 'Announcement deleted successfully.')
    return redirect('communication:announcement_list')

@login_required
def view_announcement(request, announcement_id):
    announcement = get_object_or_404(DepartmentAnnouncement, id=announcement_id, department=request.user.current_department, is_active=True)
    return render(request, 'communication/view_announcement.html', {'announcement': announcement})


# Newsletter Views

@login_required
def newsletter_list(request):
    if request.user.has_perm('communication.view_newsletter'):
        newsletters = Newsletter.objects.all().order_by('-created_at')
    else:
        newsletters = Newsletter.objects.filter(is_published=True, departments=request.user.current_department).order_by('-published_at')
    return render(request, 'communication/newsletter_list.html', {'newsletters': newsletters})

@login_required
def create_newsletter(request):
    if not request.user.has_perm('communication.add_newsletter'):
        messages.error(request, 'You do not have permission to create newsletters.')
        return redirect('communication:newsletter_list')
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()  # Save many-to-many relationships
            
            if newsletter.is_published:
                publish_newsletter(newsletter)
            
            messages.success(request, 'Newsletter created successfully.')
            return redirect('communication:newsletter_list')
    else:
        form = NewsletterForm()
    return render(request, 'communication/create_newsletter.html', {'form': form})

@login_required
def update_newsletter(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    if not request.user.has_perm('communication.change_newsletter'):
        messages.error(request, 'You do not have permission to update newsletters.')
        return redirect('communication:newsletter_list')
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            was_published = newsletter.is_published
            newsletter = form.save()
            
            if not was_published and newsletter.is_published:
                publish_newsletter(newsletter)
            
            messages.success(request, 'Newsletter updated successfully.')
            return redirect('communication:newsletter_list')
    else:
        form = NewsletterForm(instance=newsletter)
    return render(request, 'communication/update_newsletter.html', {'form': form, 'newsletter': newsletter})

@login_required
def delete_newsletter(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    if not request.user.has_perm('communication.delete_newsletter'):
        messages.error(request, 'You do not have permission to delete newsletters.')
        return redirect('communication:newsletter_list')
    
    newsletter.delete()
    messages.success(request, 'Newsletter deleted successfully.')
    return redirect('communication:newsletter_list')

@login_required
def view_newsletter(request, newsletter_id):
    if request.user.has_perm('communication.view_newsletter'):
        newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    else:
        newsletter = get_object_or_404(Newsletter, id=newsletter_id, is_published=True, departments=request.user.current_department)
    return render(request, 'communication/view_newsletter.html', {'newsletter': newsletter})

def publish_newsletter(newsletter):
    newsletter.is_published = True
    newsletter.published_at = timezone.now()
    newsletter.save()
    
    # Create notifications for all employees in the target departments
    target_employees = Employee.objects.filter(current_department__in=newsletter.departments.all())
    for employee in target_employees:
        Notification.objects.create(
            recipient=employee,
            notification_type='SYSTEM',
            title=f'New Newsletter: {newsletter.title}',
            content=f'A new newsletter has been published for your department.'
        )
    
    # Send email notifications
    email_messages = []
    for employee in target_employees:
        if employee.notify_personal_email:
            email_messages.append((
                f'New Newsletter: {newsletter.title}',
                f'A new newsletter titled "{newsletter.title}" has been published for your department. Log in to the NDE IMS to read it.',
                settings.DEFAULT_FROM_EMAIL,
                [employee.email]
            ))
    
    send_mass_mail(email_messages, fail_silently=True)
    
# Communication Log Views
@login_required
def communication_log(request):
    if not request.user.has_perm('communication.view_communicationlog'):
        messages.error(request, 'You do not have permission to view communication logs.')
        return redirect('core:dashboard')
    
    logs = CommunicationLog.objects.all().order_by('-timestamp')
    paginator = Paginator(logs, 50)  # Show 50 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'communication/communication_log.html', {'page_obj': page_obj})

def log_communication(user, action_type, details=''):
    CommunicationLog.objects.create(
        user=user,
        action_type=action_type,
        details=details
    )