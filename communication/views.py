# communication/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import (
    InAppEmail, EmailAttachment, InAppChat, ChatMessage, ChatAttachment,
    Notification, Task, DepartmentAnnouncement, Newsletter
)
from .forms import (
    InAppEmailForm, ChatMessageForm, TaskForm, AnnouncementForm,
    NewsletterForm
)
from core.models import Employee, Department

# Email Views

@login_required
def inbox(request):
    emails = InAppEmail.objects.filter(recipients=request.user).order_by('-sent_at')
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'communication/inbox.html', {'page_obj': page_obj})

@login_required
def sent_emails(request):
    emails = InAppEmail.objects.filter(sender=request.user).order_by('-sent_at')
    paginator = Paginator(emails, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'communication/sent_emails.html', {'page_obj': page_obj})

@login_required
def compose_email(request):
    if request.method == 'POST':
        form = InAppEmailForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.save(commit=False)
            email.sender = request.user
            email.save()
            form.save_m2m()
            
            # Handle attachments
            for file in request.FILES.getlist('attachments'):
                EmailAttachment.objects.create(email=email, file=file, filename=file.name)
            
            messages.success(request, 'Email sent successfully.')
            return redirect('communication:inbox')
    else:
        form = InAppEmailForm()
    return render(request, 'communication/compose_email.html', {'form': form})

@login_required
def view_email(request, email_id):
    email = get_object_or_404(InAppEmail, id=email_id)
    if request.user in email.recipients.all() or request.user == email.sender:
        if request.user not in email.is_read.all():
            email.is_read.add(request.user)
        return render(request, 'communication/view_email.html', {'email': email})
    else:
        messages.error(request, "You don't have permission to view this email.")
        return redirect('communication:inbox')

@login_required
@require_POST
def delete_email(request, email_id):
    email = get_object_or_404(InAppEmail, id=email_id)
    if request.user in email.recipients.all() or request.user == email.sender:
        email.delete()
        messages.success(request, 'Email deleted successfully.')
    else:
        messages.error(request, "You don't have permission to delete this email.")
    return redirect('communication:inbox')

# Chat Views

@login_required
def chat_list(request):
    chats = InAppChat.objects.filter(participants=request.user).order_by('-updated_at')
    return render(request, 'communication/chat_list.html', {'chats': chats})

@login_required
def create_chat(request):
    if request.method == 'POST':
        participants = request.POST.getlist('participants')
        if len(participants) > 1:
            chat = InAppChat.objects.create(is_group_chat=len(participants) > 2)
            chat.participants.add(request.user, *participants)
            return redirect('communication:chat_room', chat_id=chat.id)
        else:
            messages.error(request, 'Please select at least one participant.')
    employees = Employee.objects.exclude(id=request.user.id)
    return render(request, 'communication/create_chat.html', {'employees': employees})

@login_required
def chat_room(request, chat_id):
    chat = get_object_or_404(InAppChat, id=chat_id, participants=request.user)
    messages = ChatMessage.objects.filter(chat=chat).order_by('timestamp')
    
    if request.method == 'POST':
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.save()
            
            # Handle attachments
            for file in request.FILES.getlist('attachments'):
                ChatAttachment.objects.create(message=message, file=file, filename=file.name)
            
            chat.updated_at = timezone.now()
            chat.save()
            
            return JsonResponse({'status': 'success', 'message': 'Message sent.'})
    else:
        form = ChatMessageForm()
    
    return render(request, 'communication/chat_room.html', {
        'chat': chat,
        'messages': messages,
        'form': form
    })

@login_required
@require_POST
def leave_chat(request, chat_id):
    chat = get_object_or_404(InAppChat, id=chat_id, participants=request.user)
    chat.participants.remove(request.user)
    messages.success(request, 'You have left the chat.')
    return redirect('communication:chat_list')

# Task Views

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            
            # Send notification to assigned user
            Notification.objects.create(
                recipient=task.assigned_to,
                notification_type='TASK',
                title=f'New Task: {task.title}',
                content=f'You have been assigned a new task: {task.title}'
            )
            
            # Send email notification
            send_mail(
                subject=f'New Task Assignment: {task.title}',
                message=f'You have been assigned a new task:\n\nTitle: {task.title}\nDue Date: {task.due_date}\nDescription: {task.description}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[task.assigned_to.email],
            )
            
            messages.success(request, 'Task created successfully.')
            return redirect('communication:task_list')
    else:
        form = TaskForm()
    return render(request, 'communication/create_task.html', {'form': form})

@method_decorator(cache_page(60 * 15), name='dispatch')
class TaskListView(View):
    def get(self, request):
        assigned_tasks = Task.objects.filter(assigned_to=request.user).order_by('-due_date')
        created_tasks = Task.objects.filter(assigned_by=request.user).order_by('-due_date')
        return render(request, 'communication/task_list.html', {
            'assigned_tasks': assigned_tasks,
            'created_tasks': created_tasks
        })

@login_required
def view_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user != task.assigned_to and request.user != task.assigned_by:
        messages.error(request, "You don't have permission to view this task.")
        return redirect('communication:task_list')
    return render(request, 'communication/view_task.html', {'task': task})


@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user != task.assigned_to and request.user != task.assigned_by:
        messages.error(request, "You don't have permission to update this task.")
        return redirect('communication:task_list')
    
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
@require_POST
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.status = 'COMPLETED'
    task.save()
    messages.success(request, 'Task marked as completed.')
    return redirect('communication:task_list')

# Announcement Views

@login_required
def create_announcement(request):
    if not request.user.has_perm('communication.add_departmentannouncement'):
        messages.error(request, "You don't have permission to create announcements.")
        return redirect('communication:announcement_list')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            messages.success(request, 'Announcement created successfully.')
            return redirect('communication:announcement_list')
    else:
        form = AnnouncementForm()
    return render(request, 'communication/create_announcement.html', {'form': form})

@method_decorator(cache_page(60 * 15), name='dispatch')
class AnnouncementListView(View):
    def get(self, request):
        announcements = DepartmentAnnouncement.objects.filter(
            Q(department=request.user.current_department) | Q(department__isnull=True)
        ).order_by('-created_at')
        return render(request, 'communication/announcement_list.html', {'announcements': announcements})

# Newsletter Views

@login_required
def create_newsletter(request):
    if not request.user.has_perm('communication.add_newsletter'):
        messages.error(request, "You don't have permission to create newsletters.")
        return redirect('communication:newsletter_list')
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            messages.success(request, 'Newsletter created successfully.')
            return redirect('communication:newsletter_list')
    else:
        form = NewsletterForm()
    return render(request, 'communication/create_newsletter.html', {'form': form})

@method_decorator(cache_page(60 * 15), name='dispatch')
class NewsletterListView(View):
    def get(self, request):
        newsletters = Newsletter.objects.filter(is_published=True).order_by('-published_at')
        return render(request, 'communication/newsletter_list.html', {'newsletters': newsletters})

# Notification Views

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'communication/notification_list.html', {'notifications': notifications})

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

# Additional utility views

@login_required
def search_employees(request):
    query = request.GET.get('q', '')
    employees = Employee.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )[:10]
    results = [{'id': emp.id, 'text': f"{emp.get_full_name()} ({emp.email})"} for emp in employees]
    return JsonResponse({'results': results})

@login_required
def communication_dashboard(request):
    context = {
        'unread_emails': InAppEmail.objects.filter(recipients=request.user).exclude(is_read=request.user).count(),
        'pending_tasks': Task.objects.filter(assigned_to=request.user, status='PENDING').count(),
        'unread_notifications': Notification.objects.filter(recipient=request.user, is_read=False).count(),
        'recent_announcements': DepartmentAnnouncement.objects.filter(
            Q(department=request.user.current_department) | Q(department__isnull=True)
        ).order_by('-created_at')[:5],
    }
    return render(request, 'communication/dashboard.html', context)