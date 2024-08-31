from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import *

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
    return render(request, 'core/access/login.html', {'form': form})

@login_required
def dashboard_view(request):
    return render(request, 'core/dashboards/dashboard.html')