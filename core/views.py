import csv
import chardet
import dateutil.parser
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

from import_export.formats import base_formats
from .resources import *
from tablib import Dataset

from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy


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


from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboards/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Common context data
        context['total_employees'] = Employee.objects.count()
        context['total_departments'] = Department.objects.count()
        context['active_projects'] = Project.objects.filter(status='ACTIVE').count()
        context['pending_tasks'] = Task.objects.filter(status='PENDING').count()
        context['recent_announcements'] = Announcement.objects.order_by('-created_at')[:5]

        # Role-specific context data
        if user.role == 'DG':
            context['department_stats'] = Department.objects.annotate(employee_count=models.Count('employees'))[:5]
            context['recent_hires'] = Employee.objects.order_by('-date_joined')[:5]
        elif user.role in ['DIR', 'ZD']:
            context['managed_departments'] = Department.objects.filter(employees__role__in=['DIR', 'ZD'])
            context['department_projects'] = Project.objects.filter(department__employees__role__in=['DIR', 'ZD']).order_by('-start_date')[:5]
        elif user.role in ['HOD', 'HOU']:
            context['department'] = user.department
            context['department_employees'] = user.department.employees.count()
            context['department_projects'] = Project.objects.filter(department=user.department).order_by('-start_date')[:5]
        else:  # Regular staff and IT Admin
            context['my_tasks'] = Task.objects.filter(assigned_to=user).order_by('due_date')[:5]
            context['my_projects'] = Project.objects.filter(team_members=user).order_by('-start_date')[:5]

        return context
    

@login_required
def chat_view(request):
    chats = ChatMessage.objects.filter(Q(sender=request.user) | Q(recipient=request.user)).order_by('-timestamp')
    return render(request, 'core/chat.html', {'chats': chats})


from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Employee, EmployeeDetail, Department, Leave
from .forms import EmployeeForm, EmployeeDetailForm
from datetime import date, timedelta

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
    distinct_fields = ['sender', 'recipient']
    chat_messages = ChatMessage.objects.filter(Q(sender__in=distinct_fields) | Q(recipient__in=distinct_fields)).order_by('-timestamp')
    return render(request, 'core/chat_list.html', {'chats': chats_messages})

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


from django.http import JsonResponse
from .models import ChatMessage

@login_required
def chat_list(request):
    chats = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-timestamp').distinct('sender', 'recipient')
    return render(request, 'messaging/chat_list.html', {'chats': chats})

@login_required
def chat_detail(request, other_user_id):
    other_user = get_object_or_404(Employee, id=other_user_id)
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('timestamp')
    return render(request, 'messaging/chat_detail.html', {'messages': messages, 'other_user': other_user})

@login_required
def send_chat_message(request):
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        recipient = get_object_or_404(Employee, id=recipient_id)
        message = ChatMessage.objects.create(sender=request.user, recipient=recipient, content=content)
        return JsonResponse({'status': 'success', 'message': message.content, 'timestamp': message.timestamp})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_new_messages(request, other_user_id, last_message_id):
    other_user = get_object_or_404(Employee, id=other_user_id)
    new_messages = ChatMessage.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user)),
        id__gt=last_message_id
    ).order_by('timestamp')
    messages_data = [{'content': msg.content, 'sender': msg.sender.id, 'timestamp': msg.timestamp} for msg in new_messages]
    return JsonResponse({'messages': messages_data})


from django.db.models import Q
from .models import InboxMessage

@login_required
def inbox(request):
    messages = InboxMessage.objects.filter(recipient=request.user).order_by('-timestamp')
    paginator = Paginator(messages, 15)  # Show 15 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'messaging/inbox.html', {'page_obj': page_obj})

@login_required
def sent_messages(request):
    messages = InboxMessage.objects.filter(sender=request.user).order_by('-timestamp')
    paginator = Paginator(messages, 15)  # Show 15 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'messaging/sent_messages.html', {'page_obj': page_obj})

@login_required
def compose_message(request):
    if request.method == 'POST':
        form = InboxMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, 'Message sent successfully.')
            return redirect('inbox')
    else:
        form = InboxMessageForm()
    return render(request, 'messaging/compose_message.html', {'form': form})

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(InboxMessage, id=message_id)
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
    return render(request, 'messaging/message_detail.html', {'message': message})

@login_required
def search_messages(request):
    query = request.GET.get('q')
    if query:
        messages = InboxMessage.objects.filter(
            Q(recipient=request.user) | Q(sender=request.user)
        ).filter(
            Q(subject__icontains=query) | Q(content__icontains=query)
        ).order_by('-timestamp')
    else:
        messages = InboxMessage.objects.none()
    
    paginator = Paginator(messages, 15)  # Show 15 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'messaging/search_results.html', {'page_obj': page_obj, 'query': query})



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
    