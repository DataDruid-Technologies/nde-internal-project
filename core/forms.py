from . import models
from django import forms

class EmployeeLoginForm(forms.Form):
    employee_id = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)