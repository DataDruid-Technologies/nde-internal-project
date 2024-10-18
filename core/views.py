# core/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import *
from .forms import *
from .decorators import role_required
import csv
import io
from django.conf import settings
from django.http import JsonResponse
from calendar import monthcalendar, monthrange

from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model

from communication.models import *
from hr.models import *
from monitoring.models import *
from finance.models import *
from programs.models import *
from django.db.models import Count, Q, Sum, Avg
from datetime import datetime, timedelta


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data.get('employee_id')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=employee_id, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    if remember_me:
                        request.session.set_expiry(1209600)  # 2 weeks
                    else:
                        request.session.set_expiry(0)
                    
                    if hasattr(user, 'password_change_required') and user.password_change_required:
                        messages.warning(request, 'You need to change your password.')
                        return redirect('core:change_password')
                    
                    next_url = request.GET.get('next')
                    return redirect(next_url or 'core:dashboard')
                else:
                    messages.error(request, 'Your account is not active. Please contact the administrator.')
            else:
                messages.error(request, 'Invalid employee ID or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()

    context = {
        'form': form,
    }
    return render(request, 'core/login.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'form_fields': form.fields.keys(),  # For debugging
    }
    return render(request, 'core/change_password.html', context)
    
    
@login_required
def logout_view(request):
    logout(request)
    return redirect('core:login')


def get_user_permissions(user):
    permissions = user.get_all_permissions()
    return permissions

@login_required
def dashboard(request):
    context = {
        'quick_stats': get_quick_stats(request.user),
        'quick_actions': get_quick_actions(request.user),
        'tasks': Task.objects.filter(assigned_to=request.user).order_by('-created_at')[:5],
        'announcements': DepartmentAnnouncement.objects.filter(department=request.user.current_department).order_by('-created_at')[:5],
        'recent_emails': InAppEmail.objects.filter(recipients=request.user).order_by('-sent_at')[:5],
    }
    return render(request, 'core/dashboard.html', context)

# In utils.py
def get_quick_stats(user):
    return [
        {'title': 'Total Tasks', 'value': Task.objects.filter(assigned_to=user).count(), 'icon': 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2'},
        {'title': 'Pending Tasks', 'value': Task.objects.filter(assigned_to=user, status='PENDING').count(), 'icon': 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'},
        {'title': 'Announcements', 'value': DepartmentAnnouncement.objects.filter(department=user.current_department).count(), 'icon': 'M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z'},
        {'title': 'Unread Emails', 'value': InAppEmail.objects.filter(recipients=user, is_read=False).count(), 'icon': 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'},
    ]


def get_quick_actions(user):
    return [
        {'name': 'New Task', 'url': 'communication:create_task', 'icon': 'M12 6v6m0 0v6m0-6h6m-6 0H6'},
        {'name': 'Send Email', 'url': 'communication:compose_email', 'icon': 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'},
        {'name': 'View Calendar', 'url': 'core:calendar', 'icon': 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'},
        {'name': 'Reports', 'url': 'core:reports', 'icon': 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'},
        {'name': 'Settings', 'url': 'core:settings', 'icon': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'},
        {'name': 'Help', 'url': 'core:help', 'icon': 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'},
    ]


# calendar views

@login_required
def calendar(request):
    current_date = timezone.now().date()
    year = current_date.year
    month = current_date.month
    day = current_date.day

    calendar_data = generate_calendar_data(year, month, request.user)
    week_data = generate_week_data(year, month, day, request.user)
    day_data = generate_day_data(year, month, day, request.user)

    context = {
        'calendar_data': calendar_data,
        'week_data': week_data,
        'day_data': day_data,
        'current_month': current_date.strftime('%B'),
        'current_year': year,
        'current_date': current_date.isoformat(),
    }
    return render(request, 'core/calendar.html', context)

def generate_calendar_data(year, month, user):
    _, num_days = monthrange(year, month)
    first_day = datetime(year, month, 1)
    start_day = (first_day.weekday() - 1) % 7  # Adjust to make Monday the first day of the week

    calendar_data = []
    day = 1
    for week in range(6):
        week_data = []
        for weekday in range(7):
            if (week == 0 and weekday < start_day) or (day > num_days):
                week_data.append({'date': None, 'events': []})
            else:
                date = datetime(year, month, day).date()
                week_data.append({
                    'date': day,
                    'events': get_events_for_date(date, user)
                })
                day += 1
        calendar_data.append(week_data)
        if day > num_days:
            break

    return calendar_data

def generate_week_data(year, month, day, user):
    date = datetime(year, month, day).date()
    start_of_week = date - timedelta(days=date.weekday())
    week_data = []
    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        week_data.append({
            'date': current_date,
            'events': get_events_for_date(current_date, user)
        })
    return week_data

def generate_day_data(year, month, day, user):
    date = datetime(year, month, day).date()
    return {
        'date': date,
        'events': get_events_for_date(date, user)
    }

def get_events_for_date(date, user):
    # Fetch tasks, projects, and milestones for the given date
    tasks = Task.objects.filter(due_date=date, assigned_to=user)
    projects = Project.objects.filter(start_date__lte=date, end_date__gte=date, assigned_to=user)
    milestones = Milestone.objects.filter(due_date=date, project__assigned_to=user)

    events = []
    for task in tasks:
        events.append({
            'id': f'task_{task.id}',
            'title': task.title,
            'type': 'task',
            'start': task.due_date.isoformat(),
            'end': task.due_date.isoformat(),
        })
    for project in projects:
        events.append({
            'id': f'project_{project.id}',
            'title': project.name,
            'type': 'project',
            'start': project.start_date.isoformat(),
            'end': project.end_date.isoformat(),
        })
    for milestone in milestones:
        events.append({
            'id': f'milestone_{milestone.id}',
            'title': milestone.title,
            'type': 'milestone',
            'start': milestone.due_date.isoformat(),
            'end': milestone.due_date.isoformat(),
        })

    return events


@login_required
def reports(request):
    # Get overall project status
    project_statuses = ProjectStatus.objects.values('status').annotate(count=models.Count('status'))
    
    # Get KPIs
    kpis = KPI.objects.filter(date__gte=timezone.now() - timedelta(days=30))
    
    # Get upcoming milestones
    upcoming_milestones = Milestone.objects.filter(due_date__gte=timezone.now()).order_by('due_date')[:5]

    context = {
        'project_statuses': project_statuses,
        'kpis': kpis,
        'upcoming_milestones': upcoming_milestones,
    }
    return render(request, 'core/reports.html', context)

@login_required
def settings(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user settings
        user_settings.theme = request.POST.get('theme', 'light')
        user_settings.notification_preference = request.POST.get('notification_preference', 'email')
        user_settings.language = request.POST.get('language', 'en')
        user_settings.save()
        return redirect('core:settings')

    context = {
        'user_settings': user_settings,
    }
    return render(request, 'core/settings.html', context)

@login_required
def help(request):
    help_articles = HelpArticle.objects.all().order_by('category', 'title')
    
    context = {
        'help_articles': help_articles,
    }
    return render(request, 'core/help.html', context)

         
def get_dg_context(current_year):
    total_budget = Budget.objects.filter(year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenditure = Expenditure.objects.filter(date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    budget_utilization = (total_expenditure / total_budget * 100) if total_budget > 0 else 0

    projects = Project.objects.all()
    total_projects = projects.count()
    ongoing_projects = projects.filter(status='ONGOING').count()
    completed_projects = projects.filter(status='COMPLETED').count()
    delayed_projects = projects.filter(status='DELAYED').count()
    project_completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0


    return {
        'total_budget': total_budget,
        'total_expenditure': total_expenditure,
        'budget_utilization': round(budget_utilization, 2),
        'total_projects': total_projects,
        'ongoing_projects': ongoing_projects,
        'completed_projects': completed_projects,
        'delayed_projects': delayed_projects,
        'project_completion_rate': round(project_completion_rate, 2),
        
    }

def get_management_context(user, current_year):
    department = user.current_department
    department_budget = Budget.objects.filter(department=department, year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    department_expenditure = Expenditure.objects.filter(department=department, date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    budget_utilization = (department_expenditure / department_budget * 100) if department_budget > 0 else 0

    return {
        'department_employees': Employee.objects.filter(current_department=department).count(),
        'department_budget': department_budget,
        'department_expenditure': department_expenditure,
        'budget_utilization': round(budget_utilization, 2),
        'department_tasks': Task.objects.filter(department=department).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='COMPLETED')),
            pending=Count('id', filter=Q(status__in=['PENDING', 'IN_PROGRESS']))
        ),
        'department_leave_requests': LeaveRequest.objects.filter(
            employee__current_department=department,
            status='PENDING'
        ).count(),
    }

def get_state_coordinator_context(user, current_year):
    state = user.current_state
    state_budget = Budget.objects.filter(state=state, year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    state_expenditure = Expenditure.objects.filter(state=state, date__year=current_year).aggregate(Sum('amount'))['amount__sum'] or 0
    budget_utilization = (state_expenditure / state_budget * 100) if state_budget > 0 else 0

    return {
        'state_employees': Employee.objects.filter(current_state=state).count(),
        'state_budget': state_budget,
        'state_expenditure': state_expenditure,
        'budget_utilization': round(budget_utilization, 2),
        'state_projects': Project.objects.filter(state=state).aggregate(
            total=Count('id'),
            ongoing=Count('id', filter=Q(status='ONGOING')),
            completed=Count('id', filter=Q(status='COMPLETED')),
            delayed=Count('id', filter=Q(status='DELAYED'))
        ),
    }
    
@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=request.user)
        inapp_email_form = InAppEmailForm(request.POST, instance=request.user)
        chat_username_form = ChatUsernameForm(request.POST, instance=request.user)
        
        if profile_form.is_valid() and inapp_email_form.is_valid() and chat_username_form.is_valid():
            profile_form.save()
            
            if not request.user.in_app_email:
                inapp_email_form.save()
                messages.success(request, 'In-app email set successfully.')
            
            if not request.user.in_app_chat_name:
                chat_username_form.save()
                messages.success(request, 'Chat username set successfully.')
            
            messages.success(request, 'Profile updated successfully.')
            return redirect('core:profile')
    else:
        profile_form = ProfileForm(instance=request.user)
        inapp_email_form = InAppEmailForm(instance=request.user)
        chat_username_form = ChatUsernameForm(instance=request.user)
    
    context = {
        'profile_form': profile_form,
        'inapp_email_form': inapp_email_form,
        'chat_username_form': chat_username_form,
        'employee': request.user,
    }
    return render(request, 'core/profile.html', context)

@login_required
def file_list(request):
    files = File.objects.filter(
        Q(assigned_to=request.user) | Q(current_department=request.user.current_department)
    ).distinct()
    return render(request, 'core/file_list.html', {'files': files})

@login_required
def file_detail(request, file_id):
    file = get_object_or_404(File, id=file_id)
    return render(request, 'core/file_detail.html', {'file': file})

@login_required
def file_create(request):
    if request.method == 'POST':
        form = FileForm(request.POST)
        if form.is_valid():
            file = form.save(commit=False)
            file.created_by = request.user
            file.save()
            messages.success(request, 'File created successfully.')
            return redirect('core:file_detail', file_id=file.id)
    else:
        form = FileForm()
    return render(request, 'core/file_form.html', {'form': form})

@login_required
def file_update(request, file_id):
    file = get_object_or_404(File, id=file_id)
    if request.method == 'POST':
        form = FileForm(request.POST, instance=file)
        if form.is_valid():
            form.save()
            messages.success(request, 'File updated successfully.')
            return redirect('core:file_detail', file_id=file.id)
    else:
        form = FileForm(instance=file)
    return render(request, 'core/file_form.html', {'form': form, 'file': file})

@login_required
def file_history_add(request, file_id):
    file = get_object_or_404(File, id=file_id)
    if request.method == 'POST':
        form = FileHistoryForm(request.POST)
        if form.is_valid():
            history = form.save(commit=False)
            history.file = file
            history.performed_by = request.user
            history.save()
            messages.success(request, 'File history entry added successfully.')
            return redirect('core:file_detail', file_id=file.id)
    else:
        form = FileHistoryForm()
    return render(request, 'core/file_history_form.html', {'form': form, 'file': file})


@login_required
def performance_overview(request):
    # Implement performance overview logic here
    return render(request, 'core/performance_overview.html')

def get_monitoring_summary():
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    summary = {
        'project_status': ProjectStatus.objects.values('status').annotate(count=Count('status')),
        'kpi_performance': KPI.objects.filter(date__gte=thirty_days_ago).aggregate(
            avg_performance=Avg('performance_score')
        )['avg_performance'],
        'upcoming_milestones': Milestone.objects.filter(
            due_date__gt=today,
            due_date__lte=today + timedelta(days=30)
        ).order_by('due_date')[:5],
        'completed_milestones': Milestone.objects.filter(
            completion_date__gte=thirty_days_ago
        ).count(),
        'delayed_projects': ProjectStatus.objects.filter(
            status='DELAYED',
            last_updated__gte=thirty_days_ago
        ).count(),
    }
    
    return summary

def get_recent_state_activities(state):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    activities = {
        'recent_programs': Program.objects.filter(
            state=state,
            start_date__gte=thirty_days_ago
        ).order_by('-start_date')[:5],
        'recent_expenditures': Expenditure.objects.filter(
            state=state,
            date__gte=thirty_days_ago
        ).order_by('-date')[:5],
        'ongoing_projects': ProjectStatus.objects.filter(
            project__state=state,
            status='ONGOING'
        ).count(),
    }
    
    return activities

def get_recent_personal_activities(user):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    activities = {
        'completed_tasks': Task.objects.filter(
            assigned_to=user,
            status='COMPLETED',
            updated_at__gte=thirty_days_ago
        ).order_by('-updated_at')[:5],
        'pending_tasks': Task.objects.filter(
            assigned_to=user,
            status='PENDING',
            due_date__lte=today + timedelta(days=7)
        ).order_by('due_date')[:5],
        'recent_leave_requests': LeaveRequest.objects.filter(
            employee=user,
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')[:3],
        'recent_expenditures': Expenditure.objects.filter(
            submitted_by=user,
            date__gte=thirty_days_ago
        ).order_by('-date')[:5],
    }
    
    # Calculate task completion rate
    total_tasks = Task.objects.filter(
        assigned_to=user,
        created_at__gte=thirty_days_ago
    ).count()
    completed_tasks = Task.objects.filter(
        assigned_to=user,
        status='COMPLETED',
        updated_at__gte=thirty_days_ago
    ).count()
    activities['task_completion_rate'] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return activities

def get_department_summary(department):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    summary = {
        'total_employees': department.employees.count(),
        'active_projects': ProjectStatus.objects.filter(
            project__department=department,
            status__in=['ONGOING', 'DELAYED']
        ).count(),
        'completed_projects': ProjectStatus.objects.filter(
            project__department=department,
            status='COMPLETED',
            completion_date__gte=thirty_days_ago
        ).count(),
        'department_budget': department.budgets.filter(year=today.year).aggregate(
            total_budget=Sum('amount')
        )['total_budget'] or 0,
        'department_expenditure': Expenditure.objects.filter(
            department=department,
            date__year=today.year
        ).aggregate(total_expenditure=Sum('amount'))['total_expenditure'] or 0,
        'employees_on_leave': LeaveRequest.objects.filter(
            employee__current_department=department,
            status='approved',
            start_date__lte=today,
            end_date__gte=today
        ).count(),
    }
    
    # Calculate department task completion rate
    total_tasks = Task.objects.filter(
        department=department,
        created_at__gte=thirty_days_ago
    ).count()
    completed_tasks = Task.objects.filter(
        department=department,
        status='COMPLETED',
        updated_at__gte=thirty_days_ago
    ).count()
    summary['task_completion_rate'] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return summary

@login_required
@role_required(['DG', 'DIR', 'ZD', 'SC'])
def employee_list_view(request):
    employees = Employee.objects.all()
    
    if request.user.current_role == 'DIR':
        employees = employees.filter(current_department=request.user.current_department)
    elif request.user.current_role == 'ZD':
        employees = employees.filter(current_zone=request.user.current_zone)
    elif request.user.current_role == 'SC':
        employees = employees.filter(current_state=request.user.current_state)

    query = request.GET.get('q')
    if query:
        employees = employees.filter(
            Q(employee_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/employee_list.html', {'page_obj': page_obj})

@login_required
@role_required(['DG', 'DIR'])
def employee_create_view(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.set_password(form.cleaned_data['password'])
            employee.save()
            messages.success(request, 'Employee created successfully')
            return redirect('core:employee_list')
    else:
        form = EmployeeCreationForm()
    return render(request, 'core/employee_form.html', {'form': form})

@login_required
@role_required(['DG', 'DIR', 'ZD', 'SC'])
def employee_update_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeUpdateForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully')
            return redirect('core:employee_list')
    else:
        form = EmployeeUpdateForm(instance=employee)
    return render(request, 'core/employee_form.html', {'form': form})


@login_required
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    
    context = {
        'employee': employee,
        'recent_leave_requests': LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:5],
        'recent_performance_reviews': PerformanceReview.objects.filter(employee=employee).order_by('-review_date')[:3],
        'pending_tasks': Task.objects.filter(assigned_to=employee, status='PENDING').order_by('due_date')[:5],
    }
    
    return render(request, 'core/employee_detail.html', context)

@login_required
@role_required(['DG'])
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully')
        return redirect('core:employee_list')
    return render(request, 'core/employee_confirm_delete.html', {'employee': employee})

@login_required
@role_required(['DG', 'DIR'])
def data_upload_view(request):
    if request.method == 'POST':
        form = DataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)
            for row in csv.reader(io_string, delimiter=',', quotechar="|"):
                _, created = Employee.objects.update_or_create(
                    employee_id=row[0],
                    defaults={
                        'email': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'current_role': row[4],
                    }
                )
            messages.success(request, 'Data uploaded successfully')
            return redirect('core:dashboard')
    else:
        form = DataUploadForm()
    return render(request, 'core/data_upload.html', {'form': form})

@login_required
@role_required(['DG', 'DIR', 'ZD', 'SC'])
def assign_role_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        role = request.POST.get('role')
        if role in dict(Employee.ROLE_CHOICES):
            employee.current_role = role
            employee.save()
            messages.success(request, f'Role assigned to {employee} successfully')
        else:
            messages.error(request, 'Invalid role')
        return redirect('core:employee_list')
    return render(request, 'core/assign_role.html', {'employee': employee, 'roles': Employee.ROLE_CHOICES})

@login_required
@role_required(['DG', 'DIR', 'ZD', 'SC'])
def assign_unit_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = UnitAssignmentForm(request.POST)
        if form.is_valid():
            unit = form.cleaned_data['unit']
            unit.head = employee
            unit.save()
            messages.success(request, f'{employee} assigned as head of {unit} successfully')
            return redirect('core:employee_list')
    else:
        form = UnitAssignmentForm()
    return render(request, 'core/assign_unit.html', {'employee': employee, 'form': form})


# Password Reset Views


User = get_user_model()

def password_reset_request(request):
    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email=email).first()
            if user:
                subject = "Password Reset for NDE Internal Management System"
                email_template_name = "core/password_reset_email.html"
                c = {
                    "email": user.email,
                    'domain': request.META['HTTP_HOST'],
                    'site_name': 'NDE Internal Management System',
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'https' if request.is_secure() else 'http',
                }
                email_html_message = render_to_string(email_template_name, c)
                email_plaintext_message = strip_tags(email_html_message)
                
                try:
                    msg = EmailMultiAlternatives(
                        subject,
                        email_plaintext_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email]
                    )
                    msg.attach_alternative(email_html_message, "text/html")
                    msg.send()
                    messages.success(request, "An email has been sent with instructions to reset your password.")
                except Exception as e:
                    messages.error(request, f"An error occurred while sending the email: {str(e)}")
                    return render(request, "core/password_reset_form.html", {"form": form})
                
                return redirect("core:password_reset_done")
            else:
                messages.error(request, "No user found with that email address.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomPasswordResetForm()
    
    return render(request, "core/password_reset_form.html", {"form": form})

def password_reset_done(request):
    return render(request, "core/password_reset_done.html")

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been set. You may go ahead and log in now.")
                return redirect("core:login")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = CustomSetPasswordForm(user)
        return render(request, "core/password_reset_confirm.html", {"form": form})
    else:
        messages.error(request, "The password reset link was invalid, possibly because it has already been used. Please request a new password reset.")
        return redirect("core:password_reset_request")

def password_reset_complete(request):
    return render(request, "core/password_reset_complete.html")


User = get_user_model()

@login_required
def search(request):
    query = request.GET.get('q', '')
    user = request.user
    results = {
        'employees': [],
        'tasks': [],
        'announcements': []
    }

    if query:
        # Employee search
        if user.has_perm('core.view_employee'):
            employee_queryset = Employee.objects.filter(
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) | 
                Q(email__icontains=query)
            )
            
            # If user is not a superuser or HR, limit to their department
            if not (user.is_superuser or user.current_role == 'HR'):
                employee_queryset = employee_queryset.filter(current_department=user.current_department)
            
            results['employees'] = employee_queryset[:10]

        # Task search
        if user.has_perm('communication.view_task'):
            task_queryset = Task.objects.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
            
            # Limit tasks to those assigned to the user or created by the user
            if not user.is_superuser:
                task_queryset = task_queryset.filter(Q(assigned_to=user) | Q(assigned_by=user))
            
            results['tasks'] = task_queryset[:10]

        # Announcement search
        if user.has_perm('communication.view_departmentannouncement'):
            announcement_queryset = DepartmentAnnouncement.objects.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query)
            )
            
            # Limit announcements to user's department or general announcements
            if not user.is_superuser:
                announcement_queryset = announcement_queryset.filter(
                    Q(department=user.current_department) | Q(department__isnull=True)
                )
            
            results['announcements'] = announcement_queryset[:10]

    context = {
        'query': query,
        'results': results,
        'user_permissions': {
            'can_view_employees': user.has_perm('core.view_employee'),
            'can_view_tasks': user.has_perm('communication.view_task'),
            'can_view_announcements': user.has_perm('communication.view_departmentannouncement'),
        }
    }
    return render(request, 'core/search_results.html', context)


def get_notifications(request):
    notifications = Notification.objects.filter(recipients=request.user, is_read=False).order_by('-timestamp')[:5]
    return JsonResponse([{
        'id': n.id,
        'title': n.title,
        'content': n.content,
        'timestamp': n.timestamp.isoformat(),
        'url': n.get_absolute_url()
    } for n in notifications], safe=False)

def get_messages(request):
    try:
        unread_messages = ChatMessage.objects.filter(
            chat__participants=request.user,
            is_read=False
        ).exclude(sender=request.user)
        
        recent_chats = InAppChat.objects.filter(participants=request.user).order_by('-updated_at')[:5]
        
        return JsonResponse({
            'unread_count': unread_messages.count(),
            'recent_chats': [{
                'id': chat.id,
                'name': chat.get_chat_name(request.user),
                'last_message': chat.messages.last().content if chat.messages.exists() else '',
                'timestamp': chat.updated_at.isoformat(),
                'url': reverse('communication:chat_room', args=[str(chat.id)])
            } for chat in recent_chats]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def mark_notification_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})