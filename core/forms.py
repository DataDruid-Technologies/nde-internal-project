
from django import forms
from .models import Employee, User

class LoginForm(forms.Form):
    employee_id = forms.CharField(label='Employee ID')
    password = forms.CharField(widget=forms.PasswordInput)

class EmployeeForm(forms.ModelForm):
    employee_id = forms.CharField(max_length=20)
    email = forms.EmailField()

    class Meta:
        model = Employee
        fields = ['employee_id', 'email', 'first_name', 'middle_name', 'surname', 'date_of_birth', 'gender',
                  'marital_status', 'phone_number', 'residential_address', 'state_of_origin', 'lga_of_origin',
                  'date_of_first_appointment', 'department', 'division', 'current_grade_level', 'current_step',
                  'passport']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_of_first_appointment': forms.DateInput(attrs={'type': 'date'}),
        }

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['employee_id', 'email', 'ippis_number']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserUploadForm(forms.Form):
    csv_file = forms.FileField()