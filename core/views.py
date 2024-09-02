from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, login_not_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .forms import *
from .models import *
# views.py
from django.db.models import Count
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
    # Get counts for various entities
    employee_count = Employee.objects.count()
    department_count = Department.objects.count()


    # Get department distribution
    department_distribution = Department.objects.annotate(employee_count=Count('employees')).values('name', 'employee_count')


    context = {
        'employee_count': employee_count,
        'department_count': department_count,
        'department_distribution': department_distribution,
    }

    return render(request, 'dashboards/dashboard.html', context)


# @login_required
# def dashboard(request):
#     user = request.user
#     if user.role == 'DG':
#         return render(request, 'dashboards/dg_dashboard.html')
#     elif user.role in ['DIR', 'ZD']:
#         return render(request, 'dashboards/director_dashboard.html')
#     elif user.role == 'HOD':
#         return render(request, 'dashboards/hod_dashboard.html')
#     else:
#         return render(request, 'dashboards/staff_dashboard.html')

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
    if request.method == 'POST':
        form = EmployeeChangeForm(request.POST, instance=employee)
        detail_form = EmployeeDetailForm(request.POST, instance=employee.details)
        if form.is_valid() and detail_form.is_valid():
            with transaction.atomic():
                form.save()
                detail_form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_detail', employee_id=employee.employee_id)
    else:
        form = EmployeeChangeForm(instance=employee)
        detail_form = EmployeeDetailForm(instance=employee.details)
    return render(request, 'employees/employee_form.html', {'form': form, 'detail_form': detail_form, 'employee': employee})


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


# Role Management Views

