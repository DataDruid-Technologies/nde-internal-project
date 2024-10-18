# monitoring/forms.py

from django import forms
from .models import *
from core.models import *

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'department', 'state', 'project_manager']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date should be after the start date.")

class ProjectStatusForm(forms.ModelForm):
    class Meta:
        model = ProjectStatus
        fields = ['status', 'comment']

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'due_date', 'completed_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'completed_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        due_date = cleaned_data.get("due_date")
        completed_date = cleaned_data.get("completed_date")

        if due_date and completed_date and completed_date < due_date:
            raise forms.ValidationError("Completed date should not be before the due date.")

class KPIForm(forms.ModelForm):
    class Meta:
        model = KPI
        fields = ['name', 'description', 'target_value', 'actual_value', 'unit', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class RiskForm(forms.ModelForm):
    class Meta:
        model = Risk
        fields = ['description', 'severity', 'mitigation_plan']

class ProjectFilterForm(forms.Form):
    department = forms.ModelChoiceField(queryset=None, required=False)
    state = forms.ModelChoiceField(queryset=None, required=False)
    status = forms.ChoiceField(choices=[('', '----')] + ProjectStatus.STATUS_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()
        self.fields['state'].queryset = State.objects.all()