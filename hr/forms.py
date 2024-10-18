# hr/forms.py

from django import forms
from django.contrib.auth import get_user_model
from .models import (
    EmployeeDetail, Promotion, Examination, LeaveRequest, Transfer,
    TemporaryAccess, PerformanceReview, Training, Retirement, Repatriation,
    Documentation, IPPISManagement, StaffVerification, ChangeOfVitalInformation,
    RecordOfService
)

User = get_user_model()

# # class EmployeeDetailForm(forms.ModelForm):
# #     class Meta:
# #         model = EmployeeDetail
# #         exclude = ['id', 'employee', 'created_at', 'created_by', 'updated_at', 'updated_by']
# #         widgets = {
# #             'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
# #             'date_of_first_appointment': forms.DateInput(attrs={'type': 'date'}),
# #             'date_of_present_appointment': forms.DateInput(attrs={'type': 'date'}),
# #             'date_of_confirmation': forms.DateInput(attrs={'type': 'date'}),
# #         }

# class PromotionForm(forms.ModelForm):
#     class Meta:
#         model = Promotion
#         exclude = ['employee', 'approved_by']
#         widgets = {
#             'promotion_date': forms.DateInput(attrs={'type': 'date'}),
#             'effective_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class ExaminationForm(forms.ModelForm):
#     class Meta:
#         model = Examination
#         exclude = ['employee']
#         widgets = {
#             'exam_date': forms.DateInput(attrs={'type': 'date'}),
#             'certificate_issue_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class LeaveRequestForm(forms.ModelForm):
#     class Meta:
#         model = LeaveRequest
#         exclude = ['employee', 'status', 'approved_by']
#         widgets = {
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         start_date = cleaned_data.get("start_date")
#         end_date = cleaned_data.get("end_date")

#         if start_date and end_date and start_date > end_date:
#             raise forms.ValidationError("End date should be after the start date.")

# class TransferForm(forms.ModelForm):
#     class Meta:
#         model = Transfer
#         exclude = ['employee', 'approved_by']
#         widgets = {
#             'transfer_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class TemporaryAccessForm(forms.ModelForm):
#     class Meta:
#         model = TemporaryAccess
#         exclude = ['employee', 'granted_by']
#         widgets = {
#             'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#             'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#         }

# class PerformanceReviewForm(forms.ModelForm):
#     class Meta:
#         model = PerformanceReview
#         exclude = ['employee', 'reviewer']
#         widgets = {
#             'review_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class TrainingForm(forms.ModelForm):
#     class Meta:
#         model = Training
#         fields = '__all__'
#         widgets = {
#             'start_date': forms.DateInput(attrs={'type': 'date'}),
#             'end_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class RetirementForm(forms.ModelForm):
#     class Meta:
#         model = Retirement
#         exclude = ['employee']
#         widgets = {
#             'retirement_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class RepatriationForm(forms.ModelForm):
#     class Meta:
#         model = Repatriation
#         exclude = ['employee', 'approved_by']
#         widgets = {
#             'repatriation_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class DocumentationForm(forms.ModelForm):
#     class Meta:
#         model = Documentation
#         exclude = ['employee']

# class IPPISManagementForm(forms.ModelForm):
#     class Meta:
#         model = IPPISManagement
#         exclude = ['employee']
#         widgets = {
#             'date_enrolled': forms.DateInput(attrs={'type': 'date'}),
#         }

# class StaffVerificationForm(forms.ModelForm):
#     class Meta:
#         model = StaffVerification
#         exclude = ['employee', 'verified_by']
#         widgets = {
#             'verification_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class ChangeOfVitalInformationForm(forms.ModelForm):
#     class Meta:
#         model = ChangeOfVitalInformation
#         exclude = ['employee', 'approved_by']
#         widgets = {
#             'change_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class RecordOfServiceForm(forms.ModelForm):
#     class Meta:
#         model = RecordOfService
#         exclude = ['employee']
#         widgets = {
#             'event_date': forms.DateInput(attrs={'type': 'date'}),
#         }

# # Additional utility forms

# class AssignRoleForm(forms.Form):
#     role = forms.ChoiceField(choices=User.ROLE_CHOICES)

# class AssignUnitForm(forms.Form):
#     unit = forms.ModelChoiceField(queryset=None)  # queryset will be set in the view

#     def __init__(self, *args, **kwargs):
#         department = kwargs.pop('department', None)
#         super().__init__(*args, **kwargs)
#         if department:
#             self.fields['unit'].queryset = department.units.all()

# class BulkUploadForm(forms.Form):
#     file = forms.FileField()\
        
# class EmployeeDataUploadForm(forms.Form):
#     file = forms.FileField()
    
# class EmployeeDetailUpdateForm(forms.Form):
#     model = EmployeeDetail
#     fields = ['date_of_birth', 'date_of_first_appointment', 
#               'date_of_present_appointment', 'date_of_confirmation']
#     widgets = {
#         'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
#         'date_of_first_appointment': forms.DateInput(attrs={'type': 'date'}),
#         'date_of_present_appointment': forms.DateInput(attrs={'type': 'date'}),
#         'date_of_confirmation': forms.DateInput(attrs={'type': 'date'}),
#     }