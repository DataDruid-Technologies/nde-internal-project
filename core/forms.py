from . import models
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *

class EmployeeLoginForm(forms.Form):
    employee_id = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)
    
    
class EmployeeCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Employee
        fields = ('employee_id', 'email', 'first_name', 'last_name', 'date_joined')

class EmployeeChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Employee
        fields = ('employee_id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff')

class EmployeeDetailForm(forms.ModelForm):
    class Meta:
        model = EmployeeDetail
        exclude = ('employee',)
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = '__all__'

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'
        
    
class EmployeeCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Employee
        fields = ('employee_id', 'email', 'first_name', 'last_name', 'date_joined', 'role', 'department')

class EmployeeChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Employee
        fields = ('employee_id', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'employment_status')

class EmployeeDetailForm(forms.ModelForm):
    class Meta:
        model = EmployeeDetail
        exclude = ('employee',)
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

class RoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('role', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.all()
        self.fields['department'].queryset = Department.objects.all()