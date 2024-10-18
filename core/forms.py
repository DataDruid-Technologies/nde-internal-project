# core/forms.py
from django import forms
from .models import *
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm


class LoginForm(forms.Form):
    employee_id = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-transparent bg-yellow-100', 'placeholder': 'Employee ID'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600 focus:border-transparent bg-yellow-100', 'placeholder': 'Password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            'employee_id',
            'password',
        )

class PasswordChangeForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Employee
        fields = ['password']
                               

User = get_user_model()

class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("There is no user registered with the specified email address.")
        return email

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'mt-1 focus:ring-green-500 focus:border-green-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md'}),
    )
     
                               
class EmployeeCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Employee
        fields = ['employee_id', 'first_name', 'last_name', 'email', 'in_app_email', 'in_app_chat_name',
                  'date_of_birth', 'date_of_first_appointment', 'current_role', 'current_zone', 'current_state',
                  'current_department', 'current_grade_level', 'access_type']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class EmployeeUpdateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'in_app_email', 'in_app_chat_name',
                  'current_role', 'current_zone', 'current_state', 'current_department',
                  'current_grade_level', 'access_type', 'active_status']

class DataUploadForm(forms.Form):
    file = forms.FileField()

class UnitAssignmentForm(forms.Form):
    unit = forms.ModelChoiceField(queryset=Unit.objects.all())
    

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'phone_number']

class InAppEmailForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['in_app_email']

    def clean_in_app_email(self):
        in_app_email = self.cleaned_data['in_app_email']
        if Employee.objects.filter(in_app_email=in_app_email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This in-app email is already in use.")
        return in_app_email

class ChatUsernameForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['in_app_chat_name']

    def clean_in_app_chat_name(self):
        chat_name = self.cleaned_data['in_app_chat_name']
        if Employee.objects.filter(in_app_chat_name=chat_name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This chat username is already in use.")
        return chat_name

class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['title', 'description', 'file_number', 'file_type', 'status', 'current_department', 'assigned_to']

class FileHistoryForm(forms.ModelForm):
    class Meta:
        model = FileHistory
        fields = ['action', 'from_department', 'to_department', 'notes']
        
        
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_date', 'end_date', 'color']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }