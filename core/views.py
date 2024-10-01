from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmployeeForm, LoginForm, UserCreationForm, UserUploadForm
from .models import Department, Employee, User


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data.get('employee_id')
            password = form.cleaned_data.get('password')
            user = authenticate(request, employee_id=employee_id, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid employee ID or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    employee = request.user.employee_profile
    context = {
        'employee': employee,
    }
    return render(request, 'dashboard.html', context)

@login_required
def employee_list_view(request):
    query = request.GET.get('q')
    employees = Employee.objects.all()
    if query:
        employees = employees.filter(
            Q(user__employee_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(surname__icontains=query) |
            Q(department__name__icontains=query)
        )
    paginator = Paginator(employees, 20)  # Show 20 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'employee_list.html', {'page_obj': page_obj, 'query': query})

@login_required
def employee_detail_view(request, employee_id):
    employee = get_object_or_404(Employee, user__employee_id=employee_id)
    return render(request, 'employee_detail.html', {'employee': employee})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='HR Staff').exists())
def employee_create_view(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            user = User.objects.create_user(
                employee_id=form.cleaned_data['employee_id'],
                email=form.cleaned_data['email'],
                password=User.objects.make_random_password()
            )
            employee.user = user
            employee.save()
            messages.success(request, 'Employee created successfully')
            return redirect('employee_detail', employee_id=employee.user.employee_id)
    else:
        form = EmployeeForm()
    return render(request, 'employee_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='HR Staff').exists())
def employee_update_view(request, employee_id):
    employee = get_object_or_404(Employee, user__employee_id=employee_id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully')
            return redirect('employee_detail', employee_id=employee.user.employee_id)
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employee_form.html', {'form': form, 'action': 'Update'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_create_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User account created for {user.employee_id}')
            return redirect('employee_list')
    else:
        form = UserCreationForm()
    return render(request, 'user_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_upload_view(request):
    if request.method == 'POST':
        form = UserUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            # Process the CSV file and create users
            # You'll need to implement the CSV processing logic here
            messages.success(request, 'Users uploaded successfully')
            return redirect('employee_list')
    else:
        form = UserUploadForm()
    return render(request, 'user_upload.html', {'form': form})

@login_required
def settings_view(request):
    # Implement settings logic here
    return render(request, 'settings.html')
