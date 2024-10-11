from django import forms
from .models import *
from core.models import Employee, Department

# InAppEmail Form
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class InAppEmailForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-multiselect'})
    )
    attachments = MultipleFileField(required=False)

    class Meta:
        model = InAppEmail
        fields = ['recipients', 'cc', 'bcc', 'subject', 'body']
        widgets = {
            'cc': forms.SelectMultiple(attrs={'class': 'form-multiselect'}),
            'bcc': forms.SelectMultiple(attrs={'class': 'form-multiselect'}),
            'subject': forms.TextInput(attrs={'class': 'form-input'}),
            'body': forms.Textarea(attrs={'class': 'form-textarea'}),
        }

    def save(self, commit=True):
        email = super().save(commit=False)
        if commit:
            email.save()
            self.save_m2m()
            for attachment in self.cleaned_data['attachments']:
                EmailAttachment.objects.create(
                    email=email,
                    file=attachment,
                    filename=attachment.name
                )
        return email

# ChatMessage Form
class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

# Task Form
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'department', 'priority', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }

# DepartmentAnnouncement Form
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = DepartmentAnnouncement
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'content': forms.Textarea(attrs={'class': 'form-textarea'}),
        }

# Newsletter Form
class NewsletterForm(forms.ModelForm):
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-multiselect'})
    )

    class Meta:
        model = Newsletter
        fields = ['title', 'content', 'departments', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'content': forms.Textarea(attrs={'class': 'form-textarea'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        