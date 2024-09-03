import csv
import chardet
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, login_not_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .forms import *
from .models import *
# views.py
from django.db.models import Count, Q
from django.utils import timezone
from django.db import transaction

from .utilis import *

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
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
        'total_employees': Employee.objects.count(),
        'total_departments': Department.objects.count(),
        'active_projects': Project.objects.filter(status='ACTIVE').count(),
        'pending_tasks': Task.objects.filter(status='PENDING').count(),
        'recent_announcements': Announcement.objects.order_by('-created_at')[:5],
    }

    if user.role == 'DG':
        context.update({
            'department_stats': Department.objects.annotate(employee_count=Count('employees')),
            'recent_hires': Employee.objects.order_by('-date_joined')[:5],
        })
    elif user.role in ['DIR', 'ZD']:
        context.update({
            'managed_departments': Department.objects.filter(director=user),
            'department_projects': Project.objects.filter(department__director=user).order_by('-start_date')[:5],
        })
    elif user.role == 'HOD':
        context.update({
            'department': user.department,
            'department_employees': Employee.objects.filter(department=user.department).count(),
            'department_projects': Project.objects.filter(department=user.department).order_by('-start_date')[:5],
            'pending_tasks': Task.objects.filter(assigned_to__department=user.department, status='PENDING').count(),
        })
    else:
        context.update({
            'my_tasks': Task.objects.filter(assigned_to=user).order_by('due_date')[:5],
            'my_projects': Project.objects.filter(team_members=user).order_by('-start_date')[:3],
        })

    return render(request, 'dashboards/dashboard.html', context)

@login_required
def chat_view(request):
    chats = ChatMessage.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('-timestamp')
    return render(request, 'core/chat.html', {'chats': chats})

@login_required
def inbox_view(request):
    messages = InboxMessage.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'core/inbox.html', {'messages': messages})


@login_required
# @user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD'])
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employees/employee_list.html', {'employees': employees})

@login_required
# @user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD'])
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    return render(request, 'employees/employee_detail.html', {'employee': employee})

@login_required
# @user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD'])
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        detail_form = EmployeeDetailForm(request.POST)
        if form.is_valid() and detail_form.is_valid():
            with transaction.atomic():
                employee = form.save()
                detail = detail_form.save(commit=False)
                detail.employee = employee
                detail.save()
            messages.success(request, 'Employee created successfully.')
            return redirect('employee_detail', employee_id=employee.employee_id)
    else:
        form = EmployeeCreationForm()
        detail_form = EmployeeDetailForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'detail_form': detail_form})

@login_required
# @user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD'])
def employee_update(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    
    # Check if EmployeeDetail exists, if not create one
    employee_detail, created = EmployeeDetail.objects.get_or_create(employee=employee)
    
    if request.method == 'POST':
        form = EmployeeChangeForm(request.POST, instance=employee)
        detail_form = EmployeeDetailForm(request.POST, instance=employee_detail)
        if form.is_valid() and detail_form.is_valid():
            with transaction.atomic():
                form.save()
                detail_form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_detail', employee_id=employee.employee_id)
    else:
        form = EmployeeChangeForm(instance=employee)
        detail_form = EmployeeDetailForm(instance=employee_detail)
    
    return render(request, 'employees/employee_form.html', {
        'form': form,
        'detail_form': detail_form,
        'employee': employee
    })


@login_required
# @user_passes_test(lambda u: u.role in ['DG', 'DIR', 'ZD', 'HOD'])
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
@user_passes_test(is_authorized)
def workflow_step_list(request):
    steps = WorkflowStep.objects.all()
    return render(request, 'workflow/step_list.html', {'steps': steps})

@login_required
@user_passes_test(is_authorized)
def workflow_step_create(request):
    if request.method == 'POST':
        form = WorkflowStepForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workflow step created successfully.')
            return redirect('workflow_step_list')
    else:
        form = WorkflowStepForm()
    return render(request, 'workflow/step_form.html', {'form': form})

@login_required
@user_passes_test(is_authorized)
def workflow_list(request):
    workflows = Workflow.objects.all()
    return render(request, 'workflow/list.html', {'workflows': workflows})

@login_required
@user_passes_test(is_authorized)
def workflow_create(request):
    if request.method == 'POST':
        form = WorkflowForm(request.POST)
        if form.is_valid():
            workflow = form.save()
            messages.success(request, 'Workflow created successfully.')
            return redirect('workflow_detail', pk=workflow.pk)
    else:
        form = WorkflowForm()
    return render(request, 'workflow/form.html', {'form': form})

@login_required
@user_passes_test(is_authorized)
def workflow_detail(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return render(request, 'workflow/detail.html', {'workflow': workflow})

@login_required
@user_passes_test(is_authorized)
def workflow_instance_create(request):
    if request.method == 'POST':
        form = WorkflowInstanceForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.current_step = instance.workflow.steps.first()
            instance.save()
            messages.success(request, 'Workflow instance created successfully.')
            return redirect('workflow_instance_detail', pk=instance.pk)
    else:
        form = WorkflowInstanceForm()
    return render(request, 'workflow/instance_form.html', {'form': form})

@login_required
@user_passes_test(is_authorized)
def workflow_instance_detail(request, pk):
    instance = get_object_or_404(WorkflowInstance, pk=pk)
    return render(request, 'workflow/instance_detail.html', {'instance': instance})

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
def chat_list(request):
    chats = ChatMessage.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('-timestamp')
    return render(request, 'core/chat_list.html', {'chats': chats})

@login_required
def chat_detail(request, user_id):
    other_user = User.objects.get(id=user_id)
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
            return redirect('chat_detail', user_id=user_id)
    else:
        form = ChatMessageForm()
    
    return render(request, 'core/chat_detail.html', {
        'messages': messages,
        'other_user': other_user,
        'form': form
    })

@login_required
def inbox_list(request):
    inbox_messages = InboxMessage.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'core/inbox_list.html', {'inbox_messages': inbox_messages})

@login_required
def inbox_detail(request, message_id):
    message = InboxMessage.objects.get(id=message_id, recipient=request.user)
    message.is_read = True
    message.save()
    return render(request, 'core/inbox_detail.html', {'message': message})

@login_required
def compose_message(request):
    if request.method == 'POST':
        form = InboxMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            return redirect('inbox_list')
    else:
        form = InboxMessageForm()
    return render(request, 'core    /compose_message.html', {'form': form})

