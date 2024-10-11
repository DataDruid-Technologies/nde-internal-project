# core/views.py
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


from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model

from communication.models import *
from django.db.models import Count, Q
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
        'SITE_NAME': settings.SITE_NAME,
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


@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'role': user.get_current_role_display(),
    }

    # Quick Actions based on user role
    context['quick_actions'] = get_quick_actions(user)

    # Quick Stats based on user role
    context['quick_stats'] = get_quick_stats(user)

    # Common dashboard elements
    context['tasks'] = Task.objects.filter(assigned_to=user).order_by('-created_at')[:5]
    context['recent_announcements'] = DepartmentAnnouncement.objects.filter(is_active=True).order_by('-created_at')[:3]
    context['recent_messages'] = InAppEmail.objects.filter(recipients=user).order_by('-sent_at')[:3]

    return render(request, 'core/dashboard.html', context)

def get_quick_actions(user):
    actions = []
    if user.has_perm('core.manage_employees'):
        actions.append({'name': 'Manage Employees'})
    if user.has_perm('core.manage_departments'):
        actions.append({'name': 'Manage Departments'})
    if user.has_perm('core.manage_workflows'):
        actions.append({'name': 'Workflows'})
    if user.has_perm('core.view_reports'):
        actions.append({'name': 'Reports'})
    # Add more actions based on permissions
    return actions

def get_quick_stats(user):
    stats = []
    if user.current_role in ['DG', 'DIR', 'ZD', 'SC']:
        stats.append({
            'title': 'Total Employees',
            'value': Employee.objects.count()
        })

    if user.current_role == 'DG':
        stats.append({
            'title': 'Budget Utilization',
            'value': f"{calculate_budget_utilization()}%"
        })
    # Add more stats based on user role
    return stats

def calculate_budget_utilization():
    # Implement your budget utilization calculation logic here
    return 75  # Example value

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