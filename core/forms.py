from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import *
from django_ckeditor_5.widgets import CKEditor5Widget


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = '__all__'


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'


class EmployeeLoginForm(forms.Form):
    employee_id = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'employee_id',
            'password',
            Submit('submit', 'Log in', css_class='btn btn-primary')
        )


class EmployeeCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Employee
        fields = ('employee_id', 'email', 'first_name',
                  'last_name', 'date_joined', 'role', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('employee_id', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'date_joined',
            Row(
                Column('role', css_class='form-group col-md-6 mb-0'),
                Column('department', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'password1',
            'password2',
            Submit('submit', 'Create Employee', css_class='btn btn-primary')
        )


class EmployeeChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Employee
        fields = ('employee_id', 'email', 'first_name', 'last_name',
                  'role', 'department', 'is_active', 'employment_status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('employee_id', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('role', css_class='form-group col-md-6 mb-0'),
                Column('department', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_active', css_class='form-group col-md-6 mb-0'),
                Column('employment_status',
                       css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Update Employee', css_class='btn btn-primary')
        )


class EmployeeDetailForm(forms.ModelForm):
    class Meta:
        model = EmployeeDetail
        exclude = ('employee',)
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                Column('gender', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('nationality', css_class='form-group col-md-6 mb-0'),
                Column('state_of_origin', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'local_government_area',
            Row(
                Column('employee_grade_level',
                       css_class='form-group col-md-6 mb-0'),
                Column('date_of_first_appointment',
                       css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'date_of_present_appointment',
            'professional_qualifications',
            Row(
                Column('blood_group', css_class='form-group col-md-6 mb-0'),
                Column('allergies', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('pension_fund_administrator',
                       css_class='form-group col-md-6 mb-0'),
                Column('pension_account_number',
                       css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'last_promotion_date',
            Submit('submit', 'Update Details', css_class='btn btn-primary')
        )


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'content',
            Submit('submit', 'Send', css_class='btn btn-primary')
        )


class InboxMessageForm(forms.ModelForm):
    class Meta:
        model = InboxMessage
        fields = ['recipient', 'subject', 'content']
        widgets = {
            'content': CKEditor5Widget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'recipient',
            'subject',
            'content',
            Submit('submit', 'Send', css_class='btn btn-primary')
        )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['theme', 'notification_preferences']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'theme',
            'notification_preferences',
            Submit('submit', 'Update Profile', css_class='btn btn-primary')
        )


class RoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ('role', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.all()
        self.fields['department'].queryset = Department.objects.all()

# Workflow Steps


class WorkflowStepForm(forms.ModelForm):
    class Meta:
        model = WorkflowStep
        fields = ['name', 'description', 'order', 'required_role']


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ['name', 'description']


class WorkflowInstanceForm(forms.ModelForm):
    class Meta:
        model = WorkflowInstance
        fields = ['workflow', 'initiator']


class CSVUploadForm(forms.Form):
    file = forms.FileField()
    file_type = forms.ChoiceField(choices=[
        ('employee', 'Employee Data'),
        ('project', 'Project Data'),
        ('task', 'Task Data'),
    ])


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'employee_id', 'department',
                  'current_rank', 'date_of_birth', 'date_joined']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_joined': forms.DateInput(attrs={'type': 'date'}),
        }


class EmployeeDetailForm(forms.ModelForm):
    class Meta:
        model = EmployeeDetail
        fields = ['bank_name','account_number',]


class RoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['role']
        widgets = {
            'role': forms.Select(choices=Employee.ROLE_CHOICES)
        }
