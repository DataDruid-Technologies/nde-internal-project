import csv
import json
import chardet
import dateutil.parser
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, login_not_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib import messages
from django.http import HttpResponseForbidden
from .forms import *
from .models import *
# views.py
from django.db.models import Count, Q, Sum, Max
from django.utils import timezone
from django.db import transaction

from .utilis import *

from import_export.formats import base_formats
from .resources import *
from tablib import Dataset
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from datetime import date, timedelta

# Assuming you have these models

def home_view(request):
    return render(request, 'core/home.html')

@login_not_required
def login_view(request):
    if request.method == 'POST':
        form = EmployeeLoginForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data.get('employee_id')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=employee_id, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome, {user.get_full_name()}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid employee ID or password.")
    else:
        form = EmployeeLoginForm()
    return render(request, 'access/login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def custom_logout(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    context = {
        'user_role': user.role,
        'user_department': user.department,
    }

    if user.role in ['DG', 'HOD', 'ADMIN']:
        if user.role == 'DG':
            employees = Employee.objects.all()
            projects = Project.objects.all()
            departments = Department.objects.all()
        elif user.role == 'HOD':
            employees = Employee.objects.filter(department=user.department)
            projects = Project.objects.filter(department=user.department)
            departments = Department.objects.filter(id=user.department.id)
        else:  # ADMIN
            employees = Employee.objects.all()
            projects = Project.objects.all()
            departments = Department.objects.all()

        context.update({
            'total_employees': employees.count(),
            'total_departments': departments.count(),
            'total_projects': projects.count(),
            'new_employees': employees.filter(date_joined__gte=thirty_days_ago).count(),
            'active_projects': projects.filter(status='ACTIVE').count(),
            'completed_projects': projects.filter(status='COMPLETED').count(),
            'recent_employees': employees.order_by('-date_joined')[:5],
            'recent_projects': projects.order_by('-start_date')[:5],
        })
    else:  # Regular staff
        context.update({
            'my_tasks': Task.objects.filter(assigned_to=user).order_by('deadline')[:5],
            'my_projects': Project.objects.filter(team_members=user).order_by('-start_date')[:5],
        })

    # Common for all roles
    context.update({
        'recent_announcements': Announcement.objects.order_by('-created_at')[:5],
        'my_tasks_count': Task.objects.filter(assigned_to=user).count(),
        'my_overdue_tasks_count': Task.objects.filter(assigned_to=user, deadline__lt=today, status__in=['PENDING', 'IN_PROGRESS']).count(),
    })

    return render(request, 'dashboards/dashboard.html', context)



@login_required
def task_dashboard(request):
    user = request.user
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    context = {
        # Task statistics
        'total_tasks': Task.objects.count(),
        'my_tasks': Task.objects.filter(assigned_to=user).count(),
        'overdue_tasks': Task.objects.filter(deadline__lt=timezone.now(), status__in=['PENDING', 'IN_PROGRESS']).count(),
        'completed_tasks': Task.objects.filter(status='COMPLETED', updated_at__gte=thirty_days_ago).count(),

        # Project statistics
        'total_projects': Project.objects.count(),
        'active_projects': Project.objects.filter(status='ACTIVE').count(),

        # Employee statistics
        'total_employees': Employee.objects.count(),
        'new_employees': Employee.objects.filter(date_joined__gte=thirty_days_ago).count(),

        # Recent items
        'recent_tasks': Task.objects.filter(Q(assigned_to=user) | Q(created_by=user)).order_by('-created_at')[:5],
        'recent_projects': Project.objects.order_by('-start_date')[:5],
        'recent_announcements': Announcement.objects.order_by('-created_at')[:5],

        # Task distribution
        'task_status_distribution': Task.objects.values('status').annotate(count=Count('id')),
        'my_task_status_distribution': Task.objects.filter(assigned_to=user).values('status').annotate(count=Count('id')),

        # Timeline of tasks due this week
        'this_week_tasks': Task.objects.filter(
            deadline__gte=today,
            deadline__lt=today + timedelta(days=7)
        ).order_by('deadline'),
    }

    if user.role in ['DG', 'DIR', 'ZD', 'HOD']:
        context.update({
            'department_task_counts': Task.objects.values('project__department__name').annotate(count=Count('id')),
            'top_task_creators': Employee.objects.annotate(task_count=Count('created_tasks')).order_by('-task_count')[:5],
        })

    return render(request, 'dashboards/tasks_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD', 'SD'])
def employee_list(request):
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    paginator = Paginator(employees, 20)  # Show 20 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'employees/employee_list.html', {'page_obj': page_obj})

@login_required
@user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD', 'SD'])
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'employees/employee_detail.html', {'employee': employee})

@login_required
@user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD', 'SD'])
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        detail_form = EmployeeDetailForm(request.POST)
        if form.is_valid() and detail_form.is_valid():
            employee = form.save()
            detail = detail_form.save(commit=False)
            detail.employee = employee
            detail.save()
            messages.success(request, 'Employee created successfully.')
            return redirect('employee_detail', employee_id=employee.id)
    else:
        form = EmployeeForm()
        detail_form = EmployeeDetailForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'detail_form': detail_form})

# In views.py

@login_required
@user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD', 'SD'])
def employee_update(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        detail_form = EmployeeDetailForm(request.POST, instance=employee.employeedetail)
        if form.is_valid() and detail_form.is_valid():
            form.save()
            detail_form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_detail', employee_id=employee.id)
    else:
        form = EmployeeForm(instance=employee)
        detail_form = EmployeeDetailForm(instance=employee.employeedetail)
    return render(request, 'hr/employee_form.html', {'form': form, 'detail_form': detail_form, 'employee': employee})

def calculate_retirement_date(employee):
    if not employee.date_of_birth or not employee.date_joined:
        return None

    retirement_age = 60
    max_years_of_service = 35

    date_of_retirement_by_age = employee.date_of_birth.replace(year=employee.date_of_birth.year + retirement_age)
    date_of_retirement_by_service = employee.date_joined + timedelta(days=365.25 * max_years_of_service)

    return min(date_of_retirement_by_age, date_of_retirement_by_service)

@login_required
@user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD', 'SD'])
def retirement_calculation(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    retirement_date = calculate_retirement_date(employee)
    return render(request, 'employees/retirement_calculation.html', {
        'employee': employee,
        'retirement_date': retirement_date
    })

@login_required
def leave_request(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user
            leave.save()
            messages.success(request, 'Leave request submitted successfully.')
            return redirect('leave_list')
    else:
        form = LeaveRequestForm()
    return render(request, 'employees/leave_request_form.html', {'form': form})

@login_required
def leave_list(request):
    if request.user.role in ['DG', 'DIR', 'ZD', 'HOD', 'SD']:
        leaves = Leave.objects.all().order_by('-start_date')
    else:
        leaves = Leave.objects.filter(employee=request.user).order_by('-start_date')
    
    paginator = Paginator(leaves, 10)  # Show 10 leave requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'employees/leave_list.html', {'page_obj': page_obj})


@login_required
@user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD', 'SD'])
def assign_role(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    if request.method == 'POST':
        form = RoleAssignmentForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Role updated for {employee.get_full_name()}")
            return redirect('employee_detail', employee_id=employee.employee_id)
    else:
        form = RoleAssignmentForm(instance=employee)
    return render(request, 'employees/assign_role.html', {'form': form, 'employee': employee})

@login_required
def profile(request):
    employee = request.user
    if request.method == 'POST':
        detail_form = EmployeeDetailForm(request.POST, instance=employee.details)
        if detail_form.is_valid():
            detail_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        detail_form = EmployeeDetailForm(instance=employee.details)
    return render(request, 'employees/profile.html', {'employee': employee, 'detail_form': detail_form})


# Workflow Management Views

def is_authorized(user):
    return Employee.role in ['DG', 'DIR', 'ZD', 'HOD', 'HOU', 'IT_ADMIN']


@login_required
def workflow_list(request):
    workflows = Workflow.objects.filter(department=request.user.department)
    return render(request, 'core/workflow_list.html', {'workflows': workflows})

@login_required
def workflow_detail(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    steps = workflow.steps.all().order_by('order')
    return render(request, 'core/workflow_detail.html', {'workflow': workflow, 'steps': steps})

@login_required
def workflow_create(request):
    if request.method == 'POST':
        form = WorkflowForm(request.POST)
        if form.is_valid():
            workflow = form.save(commit=False)
            workflow.created_by = request.user
            workflow.save()
            messages.success(request, 'Workflow created successfully.')
            return redirect('workflow_detail', pk=workflow.pk)
    else:
        form = WorkflowForm()
    return render(request, 'core/create_workflow.html', {'form': form})

@login_required
def workflow_update(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    if request.method == 'POST':
        form = WorkflowForm(request.POST, instance=workflow)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workflow updated successfully.')
            return redirect('workflow_detail', pk=workflow.pk)
    else:
        form = WorkflowForm(instance=workflow)
    return render(request, 'core/upadte_workflow.html', {'form': form, 'workflow': workflow})

@login_required
def step_library_list(request):
    steps = StepLibrary.objects.all()
    return render(request, 'core/step_library_list.html', {'steps': steps})

@login_required
def step_library_create(request):
    if request.method == 'POST':
        form = StepLibraryForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.created_by = request.user
            step.save()
            messages.success(request, 'Step added to library successfully.')
            return redirect('step_library_list')
    else:
        form = StepLibraryForm()
    return render(request, 'core/step_library_form.html', {'form': form})

@login_required
def subordinate_access_management(request):
    if request.method == 'POST':
        form = SubordinateAccessForm(request.POST)
        if form.is_valid():
            subordinate = form.cleaned_data['subordinate']
            role = form.cleaned_data['role']
            permissions = form.cleaned_data['permissions']
            subordinate.role = role
            subordinate.user_permissions.set(permissions)
            subordinate.save()
            messages.success(request, f'Access updated for {subordinate.get_full_name()}')
            return redirect('subordinate_access_management')
    else:
        form = SubordinateAccessForm()
    
    subordinates = Employee.objects.filter(department=request.user.department).exclude(pk=request.user.pk)
    return render(request, 'core/subordinate_access_management.html', {'form': form, 'subordinates': subordinates})

@login_required
def email_list(request):
    form = EmailSearchForm(request.GET)
    employees = Employee.objects.all()

    if form.is_valid():
        search = form.cleaned_data.get('search')
        department = form.cleaned_data.get('department')
        role = form.cleaned_data.get('role')

        if search:
            employees = employees.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        if department:
            employees = employees.filter(department=department)
        if role:
            employees = employees.filter(role=role)

    paginator = Paginator(employees, 20)  # Show 20 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'email_list.html', {'form': form, 'page_obj': page_obj})

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('password_reset_complete')

def test_email(request):
    subject = 'Test Email'
    message = 'This is a test email from your Django application.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ['recipient@example.com']
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return render(request, 'email_test_success.html')
    except Exception as e:
        return render(request, 'email_test_failure.html', {'error': str(e)})
    

@login_required
@user_passes_test(lambda u: u.is_authorised())
def csv_upload(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            file_type = form.cleaned_data['file_type']
            
            # Detect file encoding
            raw_data = file.read()
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']
            
            # Decode the file content
            file_content = raw_data.decode(file_encoding)
            csv_data = csv.DictReader(file_content.splitlines())
            
            try:
                if file_type == 'employee':
                    for row in csv_data:
                        Employee.objects.create(
                            username=row['username'],
                            email=row['email'],
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                            role=row['role']
                        )
                elif file_type == 'project':
                    for row in csv_data:
                        Project.objects.create(
                            name=row['name'],
                            description=row['description'],
                            start_date=row['start_date'],
                            end_date=row['end_date'],
                            status=row['status']
                        )
                elif file_type == 'task':
                    for row in csv_data:
                        Task.objects.create(
                            title=row['title'],
                            description=row['description'],
                            project_id=row['project_id'],
                            assigned_to_id=row['assigned_to_id'],
                            due_date=row['due_date'],
                            status=row['status']
                        )
                messages.success(request, 'CSV file uploaded and processed successfully.')
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
            return redirect('csv_upload')
    else:
        form = CSVUploadForm()
    return render(request, 'it_admin/csv_upload.html', {'form': form})


@login_required
def settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('settings')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'settings.html', {'form': form})


@login_required
def inbox(request):
    messages = InboxMessage.objects.filter(recipient=request.user).order_by('-timestamp')
    query = request.GET.get('q')
    if query:
        messages = messages.filter(
            Q(subject__icontains=query) | 
            Q(content__icontains=query) |
            Q(sender__first_name__icontains=query) |
            Q(sender__last_name__icontains=query)
        )
    
    paginator = Paginator(messages, 20)  # Show 20 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def sent_messages(request):
    messages = InboxMessage.objects.filter(sender=request.user).order_by('-timestamp')
    query = request.GET.get('q')
    if query:
        messages = messages.filter(
            Q(subject__icontains=query) | 
            Q(content__icontains=query) |
            Q(recipient__first_name__icontains=query) |
            Q(recipient__last_name__icontains=query)
        )
    
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'messaging/sent_messages.html', context)

@login_required
def compose_message(request):
    if request.method == 'POST':
        form = InboxMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('inbox')
    else:
        form = InboxMessageForm()
    return render(request, 'messaging/compose_message.html', {'form': form})

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(InboxMessage, id=message_id, recipient=request.user)
    if not message.is_read:
        message.is_read = True
        message.save()
    return render(request, 'messaging/message_detail.html', {'message': message})

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(InboxMessage, id=message_id, recipient=request.user)
    if request.method == 'POST':
        message.delete()
        return redirect('inbox')
    return render(request, 'messaging/delete_message.html', {'message': message})

@login_required
def chat_list(request):
    # Get all conversations involving the current user
    conversations = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).values('sender', 'recipient').annotate(
        last_message_time=Max('timestamp')
    ).order_by('-last_message_time')

    # Process the conversations to get the other user and the last message
    chat_list = []
    for conv in conversations:
        other_user = conv['recipient'] if conv['sender'] == request.user.id else conv['sender']
        last_message = ChatMessage.objects.filter(
            Q(sender_id=conv['sender'], recipient_id=conv['recipient']) |
            Q(sender_id=conv['recipient'], recipient_id=conv['sender'])
        ).latest('timestamp')

        chat_list.append({
            'other_user': other_user,
            'last_message': last_message,
        })

    return render(request, 'messaging/chat_list.html', {'chats': chat_list})

@login_required
def chat_detail(request, other_user_id):
    other_user = get_object_or_404(Employee, id=other_user_id)
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('timestamp')
    
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = other_user
            message.save()
            return JsonResponse({
                'status': 'success',
                'message': {
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat(),
                    'sender_id': message.sender.id
                }
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    
    form = ChatMessageForm()
    return render(request, 'messaging/chat_detail.html', {
        'other_user': other_user,
        'messages': messages,
        'form': form
    })

@login_required
def get_new_messages(request, other_user_id, last_message_id):
    other_user = get_object_or_404(Employee, id=other_user_id)
    new_messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user)),
        id__gt=last_message_id
    ).order_by('timestamp')
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender.id,
        'timestamp': msg.timestamp.isoformat()
    } for msg in new_messages]
    
    return JsonResponse({'messages': messages_data})

@login_required
def chat_popup(request, other_user_id):
    other_user = get_object_or_404(Employee, id=other_user_id)
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('-timestamp')[:20]  # Get last 20 messages
    
    form = ChatMessageForm()
    return render(request, 'messaging/chat_popup.html', {
        'other_user': other_user,
        'other_user': other_user,
        'messages': reversed(messages),  # Reverse to show oldest first
        'form': form
    })

@login_required
def update_chat_status(request):
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        is_open = request.POST.get('is_open') == 'true'
        
        # Update the chat status in the database
        # This is a placeholder - you'll need to implement the actual logic
        # based on how you're storing chat status
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_unread_count(request):
    unread_count = ChatMessage.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})


@login_required
def search_employees(request):
    term = request.GET.get('term', '')
    employees = Employee.objects.filter(
        Q(first_name__icontains=term) | 
        Q(last_name__icontains=term) | 
        Q(employee_id__icontains=term)
    )[:10]  # Limit to 10 results
    data = [{'id': e.id, 'full_name': e.get_full_name(), 'employee_id': e.employee_id} for e in employees]
    return JsonResponse(data, safe=False)




# Helper function to check if user is a manager
def is_manager(user):
    return user.role in ['DG', 'DIR', 'ZD', 'HOD']

@login_required
@user_passes_test(is_manager)
def assign_role(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        form = RoleAssignmentForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Role updated for {employee.get_full_name()}")
            return redirect('employee_detail', employee_id=employee.id)
    else:
        form = RoleAssignmentForm(instanc=employee)
    return render(request, 'hr/assign_role.html', {'form': form, 'employee': employee})

@login_required
@user_passes_test(is_manager)
def performance_management(request):
    performances = Performance.objects.all().order_by('-evaluation_date')
    paginator = Paginator(performances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hr/performance_management.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_manager)
def performance_create(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        form = PerformanceForm(request.POST)
        if form.is_valid():
            performance = form.save(commit=False)
            performance.employee = employee
            performance.save()
            messages.success(request, 'Performance evaluation added successfully.')
            return redirect('performance_management')
    else:
        form = PerformanceForm()
    return render(request, 'hr/performance_form.html', {'form': form, 'employee': employee})

@login_required
@user_passes_test(is_manager)
def training_management(request):
    trainings = Training.objects.all().order_by('-start_date')
    paginator = Paginator(trainings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hr/training_management.html', {'page_obj': page_obj})


@login_required
@user_passes_test(is_manager)
def training_create(request):
    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save()
            messages.success(request, 'Training program created successfully.')
            return redirect('training_management')
    else:
        form = TrainingForm()
    return render(request, 'hr/training_form.html', {'form': form})

@login_required
@user_passes_test(is_manager)
def retirement_management(request):
    retirements = Retirement.objects.all().order_by('-retirement_date')
    paginator = Paginator(retirements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'hr/retirement_management.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_manager)
def retirement_create(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        form = RetirementForm(request.POST)
        if form.is_valid():
            retirement = form.save(commit=False)
            retirement.employee = employee
            retirement.save()
            messages.success(request, 'Retirement process initiated successfully.')
            return redirect('retirement_management')
    else:
        form = RetirementForm()
    return render(request, 'hr/retirement_form.html', {'form': form, 'employee': employee})

@login_required
@user_passes_test(is_manager)
def hr_reporting(request):
    total_employees = Employee.objects.count()
    departments = Department.objects.annotate(employee_count=Count('employees'))
    performance_summary = Performance.objects.values('rating').annotate(count=Count('id'))
    upcoming_retirements = Retirement.objects.filter(retirement_date__gte=timezone.now()).order_by('retirement_date')[:5]
    
    context = {
        'total_employees': total_employees,
        'departments': departments,
        'performance_summary': performance_summary,
        'upcoming_retirements': upcoming_retirements,
    }
    return render(request, 'hr/hr_reporting.html', context)

@login_required
def employee_self_update(request):
    employee = request.user
    employee_detail, created = EmployeeDetail.objects.get_or_create(employee=employee)
    
    if request.method == 'POST':
        form = EmployeeDetailForm(request.POST, instance=employee_detail)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your information has been updated successfully.')
            return redirect('employee_detail', employee_id=employee.id)
    else:
        form = EmployeeDetailForm(instance=employee_detail)
    
    return render(request, 'hr/employee_self_update.html', {'form': form})
    


from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.db.models import Q
import csv
import chardet
import dateutil.parser
from .models import Department, Employee, State, LGA, Zone, Role, CustomPermission, WorkflowStep, WorkflowInstance


@login_required
@user_passes_test(lambda u: u.role in ['DG', 'IT_ADMIN'])
def data_upload(request):
    model_choices = [
        ('Department', 'Departments'),
        ('Employee', 'Employees'),
        ('State', 'States'),
        ('LGA', 'Local Government Areas'),
        ('Zone', 'Zones'),
        ('Role', 'Roles'),
        ('CustomPermission', 'Custom Permissions'),
        ('WorkflowStep', 'Workflow Steps'),
        ('WorkflowInstance', 'Workflow Instances'),
    ]

    if request.method == 'POST':
        file = request.FILES.get('file')
        model_name = request.POST.get('model')

        if not file:
            return JsonResponse({'error': 'No file was uploaded.'}, status=400)

        if not file.name.endswith('.csv'):
            return JsonResponse({'error': 'File must be a CSV.'}, status=400)

        try:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']
            file_content = raw_data.decode(file_encoding)

            csv_preview = get_csv_preview(file_content)

            if model_name == 'Employee':
                result = process_employee_upload(file_content, file_encoding)
            else:
                result = process_general_upload(file_content, file_encoding, model_name)

            return JsonResponse({
                'message': f'{result["created"]} {model_name} records created. {result["updated"]} records updated. {result["errors"]} errors encountered.',
                'created': result['created'],
                'updated': result['updated'],
                'errors': result['errors'],
                'preview': csv_preview
            })
        except Exception as e:
            return JsonResponse({'error': f'Error uploading data: {str(e)}'}, status=500)

    return render(request, 'core/data_upload.html', {'model_choices': model_choices})

def process_employee_upload(file_content, file_encoding):
    reader = csv.DictReader(file_content.splitlines())
    created, updated, errors = 0, 0, 0

    for row in reader:
        try:
            with transaction.atomic():
                employee_id = row['employee_id']
                email = row['email']
                first_name = row['first_name']
                middle_name = row.get('middle_name', '')
                last_name = row['last_name']
                department_name = row.get('department', '')
                role = row.get('role', '')
                password = row.get('password')

                department = Department.objects.filter(name=department_name).first() if department_name else None

                employee, is_created = Employee.objects.update_or_create(
                    employee_id=employee_id,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'last_name': last_name,
                        'department': department,
                        'role': role,
                        'date_of_birth': convert_date(row.get('date_of_birth')),
                        'date_joined': convert_date(row.get('date_joined')),
                        'date_of_confirmation': convert_date(row.get('date_of_confirmation')),
                        'ippis_number': row.get('ippis_number'),
                        'gender': row.get('gender'),
                        'access_type': row.get('access_type', 'STAFF'),
                        'is_active': row.get('is_active', 'True').lower() == 'true',
                        'is_staff': row.get('is_staff', 'False').lower() == 'true',
                        'is_superuser': row.get('is_superuser', 'False').lower() == 'true',
                    }
                )

                # Handle password
                if password:
                    employee.password = make_password(password)
                    employee.save()

                if is_created:
                    created += 1
                else:
                    updated += 1

        except Exception as e:
            errors += 1
            logger.error(f"Error processing row for employee {row.get('employee_id', 'Unknown')}: {str(e)}")

    return {"created": created, "updated": updated, "errors": errors}



def process_general_upload(file_content, file_encoding, model_name):
    reader = csv.DictReader(file_content.splitlines())
    created, updated, errors = 0, 0, 0

    model = globals()[model_name]

    for row in reader:
        try:
            with transaction.atomic():
                instance, created = model.objects.update_or_create(
                    name=row['name'],
                    defaults={k: v for k, v in row.items() if k != 'name'}
                )

                if created:
                    created += 1
                else:
                    updated += 1

        except Exception as e:
            errors += 1
            print(f"Error processing row: {row}. Error: {str(e)}")

    return {"created": created, "updated": updated, "errors": errors}

def get_csv_preview(file_content, num_rows=5):
    csv_reader = csv.reader(file_content.splitlines())
    headers = next(csv_reader)
    preview_rows = []
    for i, row in enumerate(csv_reader):
        if i < num_rows:
            preview_rows.append(row)
        else:
            break
    return {'headers': headers, 'rows': preview_rows}

def convert_date(date_str):
    if date_str:
        try:
            return dateutil.parser.parse(date_str).date()
        except ValueError:
            print(f"Invalid date format: {date_str}")
            return None
    else:
        return None
    


@login_required
def workflow_list(request):
    workflows = Workflow.objects.all()
    return render(request, 'core/workflow_list.html', {'workflows': workflows})

@login_required
def create_or_update_workflow(request, workflow_id=None):
    if workflow_id:
        workflow = get_object_or_404(Workflow, id=workflow_id)
        title = "Edit Workflow"
    else:
        workflow = None
        title = "Create Workflow"

    if request.method == 'POST':
        form = WorkflowForm(request.POST, instance=workflow)
        if form.is_valid():
            with transaction.atomic():
                workflow = form.save()
                
                steps_data = json.loads(request.POST.get('steps', '[]'))
                connections_data = json.loads(request.POST.get('connections', '[]'))
                
                WorkflowStepOrder.objects.filter(workflow=workflow).delete()
                WorkflowConnection.objects.filter(workflow=workflow).delete()
                
                steps = {}
                for index, step_data in enumerate(steps_data):
                    step, created = WorkflowStep.objects.update_or_create(
                        id=step_data.get('id'),
                        defaults={
                            'name': step_data['name'],
                            'description': step_data.get('description', ''),
                            'order': index,
                            'required_role_id': step_data.get('required_role') or None,
                            'required_permission_id': step_data.get('required_permission') or None,
                        }
                    )
                    WorkflowStepOrder.objects.create(
                        workflow=workflow,
                        step=step,
                        order=index
                    )
                    steps[step_data['id']] = step
                
                for connection in connections_data:
                    source_step = steps[connection['source']]
                    target_step = steps[connection['target']]
                    WorkflowConnection.objects.create(
                        workflow=workflow,
                        source_step=source_step,
                        target_step=target_step
                    )
                
                messages.success(request, f"Workflow '{workflow.name}' {'updated' if workflow_id else 'created'} successfully.")
            return redirect('workflow_detail', pk=workflow.id)
    else:
        form = WorkflowForm(instance=workflow)

    context = {
        'form': form,
        'workflow': workflow,
        'title': title,
        'roles': Role.objects.all(),
        'permissions': CustomPermission.objects.all(),
    }
    return render(request, 'core/create_or_update_workflow.html', context)


@login_required
def update_workflow(request, workflow_id):
    workflow = get_object_or_404(Workflow, id=workflow_id)
    if request.method == 'POST':
        form = WorkflowForm(request.POST, instance=workflow)
        if form.is_valid():
            with transaction.atomic():
                workflow = form.save()
                
                steps_data = json.loads(request.POST.get('steps', '[]'))
                connections_data = json.loads(request.POST.get('connections', '[]'))
                
                # Clear existing steps and connections
                WorkflowStepOrder.objects.filter(workflow=workflow).delete()
                WorkflowConnection.objects.filter(workflow=workflow).delete()
                
                steps = {}
                for index, step_data in enumerate(steps_data):
                    step_id = step_data['id']
                    if step_id.startswith('new-step-'):
                        # This is a new step
                        step = WorkflowStep.objects.create(
                            name=step_data['name'],
                            description=step_data.get('description', ''),
                            order=index,
                            required_role_id=step_data.get('required_role') or None,
                            required_permission_id=step_data.get('required_permission') or None,
                        )
                    else:
                        # This is an existing step
                        step = WorkflowStep.objects.get(id=int(step_id))
                        step.name = step_data['name']
                        step.description = step_data.get('description', '')
                        step.order = index
                        step.required_role_id = step_data.get('required_role') or None
                        step.required_permission_id = step_data.get('required_permission') or None
                        step.save()

                    WorkflowStepOrder.objects.create(
                        workflow=workflow,
                        step=step,
                        order=index
                    )
                    steps[step_id] = step
                
                # Create connections
                for connection in connections_data:
                    source_step = steps[connection['source']]
                    target_step = steps[connection['target']]
                    WorkflowConnection.objects.create(
                        workflow=workflow,
                        source_step=source_step,
                        target_step=target_step
                    )
                
                messages.success(request, f"Workflow '{workflow.name}' updated successfully.")
            return redirect('workflow_detail', pk=workflow.id)
    else:
        form = WorkflowForm(instance=workflow)

    context = {
        'form': form,
        'workflow': workflow,
        'roles': Role.objects.all(),
        'permissions': CustomPermission.objects.all(),
    }
    return render(request, 'core/update_workflow.html', context)

@login_required
def workflow_detail(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    steps = workflow.steps.all().order_by('workflowsteporder__order')
    connections = workflow.workflowconnection_set.all()
    
    context = {
        'workflow': workflow,
        'steps': steps,
        'connections': connections,
    }
    return render(request, 'core/workflow_detail.html', context)

@login_required
def delete_workflow(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    if request.method == 'POST':
        workflow.delete()
        messages.success(request, f"Workflow '{workflow.name}' deleted successfully.")
        return redirect('workflow_list')
    return render(request, 'core/delete_workflow.html', {'workflow': workflow})


@login_required
def dashboard_search(request):
    query = request.GET.get('q')
    results = {
        'employees': [],
        'departments': [],
        'projects': [],
        'tasks': []
    }
    
    if query:
        results['employees'] = Employee.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(employee_id__icontains=query)
        )[:5]
        
        results['departments'] = Department.objects.filter(name__icontains=query)[:5]
        
        results['projects'] = Project.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )[:5]
        
        results['tasks'] = Task.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )[:5]
    
    return render(request, 'dashboard/search_results.html', {'results': results, 'query': query})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Department, Project, Task, Announcement, Notification
from .forms import DepartmentForm, ProjectForm, TaskForm, AnnouncementForm

@login_required
def department_list(request):
    departments = Department.objects.annotate(employee_count=Count('employees'))
    return render(request, 'department/list.html', {'departments': departments})

@login_required
def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    employees = department.employees.all()
    projects = Project.objects.filter(department=department)
    return render(request, 'department/detail.html', {
        'department': department,
        'employees': employees,
        'projects': projects
    })

@login_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, 'Department created successfully.')
            return redirect('department_detail', pk=department.pk)
    else:
        form = DepartmentForm()
    return render(request, 'department/form.html', {'form': form})

@login_required
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('department_detail', pk=department.pk)
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'department/form.html', {'form': form, 'department': department})

@login_required
def project_list(request):
    projects = Project.objects.all()
    return render(request, 'project/list.html', {'projects': projects})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    tasks = Task.objects.filter(project=project)
    return render(request, 'project/detail.html', {'project': project, 'tasks': tasks})

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            messages.success(request, 'Project created successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'project/form.html', {'form': form})

@login_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project/form.html', {'form': form, 'project': project})

@login_required
def task_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = TaskForm()
    return render(request, 'core/form.html', {'form': form, 'project': project})


@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Task created successfully.')
            return redirect('task_list')
    else:
        form = TaskForm()
    
    projects = Project.objects.all()
    return render(request, 'core/create_task.html', {'form': form, 'projects': projects})

@login_required
def task_list(request):
    tasks = Task.objects.all().order_by('-created_at')
    return render(request, 'core/task_list.html', {'tasks': tasks})


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'task/task_detail.html', {'task': task})

@login_required
def task_update(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check if the user has permission to update the task
    if request.user != task.created_by and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to edit this task.")
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'task/task_update.html', {'form': form, 'task': task})

@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check if the user has permission to delete the task
    if request.user != task.created_by and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to delete this task.")
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('task_list')
    
    return render(request, 'task/task_delete.html', {'task': task})


@login_required
def user_search(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) | 
        Q(email__icontains=query)
    )[:10]  # Limit to 10 results
    data = [{'id': user.id, 'text': f"{user.get_full_name()} ({user.email})"} for user in users]
    return JsonResponse({'results': data})

@login_required
def announcement_create(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, 'Announcement created successfully.')
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()
    return render(request, 'announcement/form.html', {'form': form})


@login_required
def announcement_list(request):
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'announcement/list.html', {'announcements': announcements})


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})