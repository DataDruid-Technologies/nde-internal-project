# hr/views.py

import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views import View
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    EmployeeDetail, Promotion, Examination, LeaveRequest, Transfer,
    TemporaryAccess, PerformanceReview, Training, Retirement, Repatriation,
    Documentation, IPPISManagement, StaffVerification, ChangeOfVitalInformation,
    RecordOfService
)
from .forms import *
from core.models import Employee, Department
from datetime import timezone

class CachedListView(View):
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

@login_required
def employee_list(request):
    query = request.GET.get('q')
    employees = Employee.objects.all()
    employee_details = EmployeeDetail.objects.all()

    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'employee_details': employee_details,
    }
    return render(request, 'hr/employee_list.html', context)

@login_required
@permission_required('hr.view_employeedetail')
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    employee_detail = get_object_or_404(EmployeeDetail, employee=employee)
    
    context = {
        'employee': employee,
        'employee_detail': employee_detail,
    }
    return render(request, 'hr/employee_detail.html', context)

@login_required
@permission_required('hr.change_employeedetail')
def update_employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    employee_detail = get_object_or_404(EmployeeDetail, employee=employee)

    if request.method == 'POST':
        form = EmployeeDetailForm(request.POST, request.FILES, instance=employee_detail)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee details updated successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = EmployeeDetailForm(instance=employee_detail)

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/update_employee_detail.html', context)

@login_required
@permission_required('hr.add_promotion')
def create_promotion(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            promotion = form.save(commit=False)
            promotion.employee = employee
            promotion.approved_by = request.user
            promotion.save()
            messages.success(request, 'Promotion created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = PromotionForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_promotion.html', context)

@login_required
@permission_required('hr.view_promotion')
def promotion_list(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    promotions = Promotion.objects.filter(employee=employee).order_by('-promotion_date')

    context = {
        'employee': employee,
        'promotions': promotions,
    }
    return render(request, 'hr/promotion_list.html', context)

@login_required
@permission_required('hr.add_examination')
def create_examination(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = ExaminationForm(request.POST, request.FILES)
        if form.is_valid():
            examination = form.save(commit=False)
            examination.employee = employee
            examination.save()
            messages.success(request, 'Examination record created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = ExaminationForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_examination.html', context)

@login_required
def create_leave_request(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = request.user
            leave_request.save()
            messages.success(request, 'Leave request submitted successfully.')
            return redirect('hr:leave_request_list')
    else:
        form = LeaveRequestForm()

    context = {
        'form': form,
    }
    return render(request, 'hr/create_leave_request.html', context)

@method_decorator(login_required, name='dispatch')
class LeaveRequestListView(CachedListView):
    def get(self, request):
        leave_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-created_at')
        context = {
            'leave_requests': leave_requests,
        }
        return render(request, 'hr/leave_request_list.html', context)

@login_required
@permission_required('hr.change_leaverequest')
def approve_leave_request(request, leave_request_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)
    
    if request.method == 'POST':
        leave_request.status = 'approved'
        leave_request.approved_by = request.user
        leave_request.save()
        
        # Send email notification
        subject = 'Leave Request Approved'
        message = f'Your leave request from {leave_request.start_date} to {leave_request.end_date} has been approved.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [leave_request.employee.email])
        
        messages.success(request, 'Leave request approved successfully.')
        return redirect('hr:leave_request_list')

    context = {
        'leave_request': leave_request,
    }
    return render(request, 'hr/approve_leave_request.html', context)

@login_required
@permission_required('hr.add_transfer')
def create_transfer(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.employee = employee
            transfer.approved_by = request.user
            transfer.save()
            messages.success(request, 'Transfer created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = TransferForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_transfer.html', context)

@login_required
@permission_required('hr.add_temporaryaccess')
def create_temporary_access(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = TemporaryAccessForm(request.POST)
        if form.is_valid():
            temp_access = form.save(commit=False)
            temp_access.employee = employee
            temp_access.granted_by = request.user
            temp_access.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Temporary access granted successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = TemporaryAccessForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_temporary_access.html', context)

@login_required
@permission_required('hr.add_performancereview')
def create_performance_review(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = PerformanceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.employee = employee
            review.reviewer = request.user
            review.save()
            messages.success(request, 'Performance review created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = PerformanceReviewForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_performance_review.html', context)

@login_required
@permission_required('hr.add_training')
def create_training(request):
    if request.method == 'POST':
        form = TrainingForm(request.POST)
        if form.is_valid():
            training = form.save()
            messages.success(request, 'Training created successfully.')
            return redirect('hr:training_list')
    else:
        form = TrainingForm()

    context = {
        'form': form,
    }
    return render(request, 'hr/create_training.html', context)

@method_decorator(login_required, name='dispatch')
class TrainingListView(CachedListView):
    def get(self, request):
        trainings = Training.objects.all().order_by('-start_date')
        context = {
            'trainings': trainings,
        }
        return render(request, 'hr/training_list.html', context)

@login_required
@permission_required('hr.add_retirement')
def create_retirement(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = RetirementForm(request.POST)
        if form.is_valid():
            retirement = form.save(commit=False)
            retirement.employee = employee
            retirement.save()
            messages.success(request, 'Retirement record created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = RetirementForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_retirement.html', context)

@login_required
@permission_required('hr.add_repatriation')
def create_repatriation(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = RepatriationForm(request.POST)
        if form.is_valid():
            repatriation = form.save(commit=False)
            repatriation.employee = employee
            repatriation.approved_by = request.user
            repatriation.save()
            messages.success(request, 'Repatriation record created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = RepatriationForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_repatriation.html', context)

@login_required
@permission_required('hr.change_documentation')
def update_documentation(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    documentation, created = Documentation.objects.get_or_create(employee=employee)

    if request.method == 'POST':
        form = DocumentationForm(request.POST, request.FILES, instance=documentation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documentation updated successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = DocumentationForm(instance=documentation)

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/update_documentation.html', context)

@login_required
@permission_required('hr.change_ippismanagement')
def update_ippis_management(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    ippis_management, created = IPPISManagement.objects.get_or_create(employee=employee)

    if request.method == 'POST':
        form = IPPISManagementForm(request.POST, instance=ippis_management)
        if form.is_valid():
            form.save()
            messages.success(request, 'IPPIS management information updated successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = IPPISManagementForm(instance=ippis_management)

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/update_ippis_management.html', context)

@login_required
@permission_required('hr.add_staffverification')
def employee_data_upload(request):
    if request.method == 'POST':
        form = EmployeeDataUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)  # Skip the header row
            for row in csv.reader(io_string, delimiter=',', quotechar='"'):
                employee_id = row[0]
                if not employee_id:
                    continue  # Skip rows without employee_id
                employee, created = Employee.objects.update_or_create(
                    employee_id=employee_id,
                    defaults={
                        'first_name': row[1] if row[1] else None,
                        'last_name': row[2] if row[2] else None,
                        'email': row[3] if row[3] else None,
                        # Add other Employee model fields as needed
                    }
                )
                if created:
                    employee.set_password('changeme')  # Set default password
                    employee.password_change_required = True
                    employee.save()

                # Update or create EmployeeDetail
                EmployeeDetail.objects.update_or_create(
                    employee=employee,
                    defaults={
                        'date_of_birth': row[4] if row[4] else None,
                        'date_of_first_appointment': row[5] if row[5] else None,
                        # Add other EmployeeDetail fields as needed
                    }
                )
            messages.success(request, 'Employee data uploaded successfully.')
            return redirect('core:employee_list')
    else:
        form = EmployeeDataUploadForm()
    return render(request, 'core/employee_data_upload.html', {'form': form})


@login_required
@permission_required('hr.add_changeofvitalinformation')
def create_change_of_vital_information(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = ChangeOfVitalInformationForm(request.POST)
        if form.is_valid():
            change = form.save(commit=False)
            change.employee = employee
            change.approved_by = request.user
            change.save()
            messages.success(request, 'Change of vital information record created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = ChangeOfVitalInformationForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_change_of_vital_information.html', context)

@login_required
@permission_required('hr.add_recordofservice')
def create_record_of_service(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        form = RecordOfServiceForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.employee = employee
            record.save()
            messages.success(request, 'Record of service created successfully.')
            return redirect('hr:employee_detail', employee_id=employee_id)
    else:
        form = RecordOfServiceForm()

    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'hr/create_record_of_service.html', context)

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('hr.view_recordofservice'), name='dispatch')
class RecordOfServiceListView(CachedListView):
    def get(self, request, employee_id):
        employee = get_object_or_404(Employee, employee_id=employee_id)
        records = RecordOfService.objects.filter(employee=employee).order_by('-event_date')
        
        context = {
            'employee': employee,
            'records': records,
        }
        return render(request, 'hr/record_of_service_list.html', context)

@login_required
@permission_required('hr.view_employeedetail')
def department_employees(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    employees = Employee.objects.filter(current_department=department)

    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'department': department,
        'page_obj': page_obj,
    }
    return render(request, 'hr/department_employees.html', context)

@login_required
@permission_required('hr.view_promotion')
def promotion_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    promotions = Promotion.objects.filter(employee=employee).order_by('-promotion_date')

    context = {
        'employee': employee,
        'promotions': promotions,
    }
    return render(request, 'hr/promotion_history.html', context)

@login_required
@permission_required('hr.view_examination')
def examination_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    examinations = Examination.objects.filter(employee=employee).order_by('-exam_date')

    context = {
        'employee': employee,
        'examinations': examinations,
    }
    return render(request, 'hr/examination_history.html', context)

@login_required
@permission_required('hr.view_transfer')
def transfer_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    transfers = Transfer.objects.filter(employee=employee).order_by('-transfer_date')

    context = {
        'employee': employee,
        'transfers': transfers,
    }
    return render(request, 'hr/transfer_history.html', context)

@login_required
@permission_required('hr.view_performancereview')
def performance_review_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    reviews = PerformanceReview.objects.filter(employee=employee).order_by('-review_date')

    context = {
        'employee': employee,
        'reviews': reviews,
    }
    return render(request, 'hr/performance_review_history.html', context)

@login_required
@permission_required('hr.view_training')
def employee_trainings(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    trainings = Training.objects.filter(participants=employee).order_by('-start_date')

    context = {
        'employee': employee,
        'trainings': trainings,
    }
    return render(request, 'hr/employee_trainings.html', context)

@login_required
@permission_required('hr.add_training')
def assign_training(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)

    if request.method == 'POST':
        training_id = request.POST.get('training_id')
        training = get_object_or_404(Training, id=training_id)
        training.participants.add(employee)
        messages.success(request, f'{employee.get_full_name()} has been assigned to the training.')
        return redirect('hr:employee_trainings', employee_id=employee_id)

    available_trainings = Training.objects.exclude(participants=employee)
    
    context = {
        'employee': employee,
        'available_trainings': available_trainings,
    }
    return render(request, 'hr/assign_training.html', context)

@login_required
@permission_required('hr.view_leaverequest')
def employee_leave_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    leave_requests = LeaveRequest.objects.filter(employee=employee).order_by('-start_date')

    context = {
        'employee': employee,
        'leave_requests': leave_requests,
    }
    return render(request, 'hr/employee_leave_history.html', context)

@login_required
@permission_required('hr.view_temporaryaccess')
def temporary_access_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    temp_accesses = TemporaryAccess.objects.filter(employee=employee).order_by('-start_date')

    context = {
        'employee': employee,
        'temp_accesses': temp_accesses,
    }
    return render(request, 'hr/temporary_access_history.html', context)

@login_required
@permission_required('hr.view_changeofvitalinformation')
def vital_information_changes(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    changes = ChangeOfVitalInformation.objects.filter(employee=employee).order_by('-change_date')

    context = {
        'employee': employee,
        'changes': changes,
    }
    return render(request, 'hr/vital_information_changes.html', context)

@login_required
@permission_required('hr.view_staffverification')
def staff_verification_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    verifications = StaffVerification.objects.filter(employee=employee).order_by('-verification_date')

    context = {
        'employee': employee,
        'verifications': verifications,
    }
    return render(request, 'hr/staff_verification_history.html', context)

@login_required
@permission_required('hr.view_retirement')
def retirement_details(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    retirement = get_object_or_404(Retirement, employee=employee)

    context = {
        'employee': employee,
        'retirement': retirement,
    }
    return render(request, 'hr/retirement_details.html', context)

@login_required
@permission_required('hr.view_repatriation')
def repatriation_history(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    repatriations = Repatriation.objects.filter(employee=employee).order_by('-repatriation_date')

    context = {
        'employee': employee,
        'repatriations': repatriations,
    }
    return render(request, 'hr/repatriation_history.html', context)

# Additional utility views

@login_required
@permission_required('hr.view_employeedetail')
def employee_search(request):
    query = request.GET.get('q', '')
    employees = Employee.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(employee_id__icontains=query) |
        Q(email__icontains=query)
    )[:10]  # Limit to 10 results for performance

    results = [{'id': emp.employee_id, 'text': f"{emp.get_full_name()} ({emp.employee_id})"} for emp in employees]
    return JsonResponse({'results': results})

@login_required
@permission_required('hr.view_employeedetail')
def employee_dashboard(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=employee_id)
    
    context = {
        'employee': employee,
        'recent_promotions': Promotion.objects.filter(employee=employee).order_by('-promotion_date')[:5],
        'recent_trainings': Training.objects.filter(participants=employee).order_by('-start_date')[:5],
        'recent_leave_requests': LeaveRequest.objects.filter(employee=employee).order_by('-start_date')[:5],
        'recent_performance_reviews': PerformanceReview.objects.filter(employee=employee).order_by('-review_date')[:5],
    }
    return render(request, 'hr/employee_dashboard.html', context)

@login_required
@permission_required('hr.view_employeedetail')
def department_dashboard(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    employees = Employee.objects.filter(current_department=department)
    
    context = {
        'department': department,
        'employee_count': employees.count(),
        'recent_transfers': Transfer.objects.filter(to_department=department).order_by('-transfer_date')[:5],
        'upcoming_trainings': Training.objects.filter(participants__in=employees, start_date__gte=timezone.now()).order_by('start_date')[:5],
        'pending_leave_requests': LeaveRequest.objects.filter(employee__in=employees, status='pending').order_by('start_date')[:5],
    }
    return render(request, 'hr/department_dashboard.html', context)


@login_required
def update_employee_details(request):
    employee = request.user
    employee_detail, created = EmployeeDetail.objects.get_or_create(employee=employee)
    if request.method == 'POST':
        form = EmployeeDetailUpdateForm(request.POST, instance=employee_detail)
        if form.is_valid():
            form.save()
            StaffVerification.objects.update_or_create(
                employee=employee,
                defaults={'is_verified': False}
            )
            messages.success(request, 'Your details have been updated and are pending verification.')
            return redirect('core:employee_detail', employee_id=employee.id)
    else:
        form = EmployeeDetailUpdateForm(instance=employee_detail)
    return render(request, 'hr/update_employee_details.html', {'form': form})

@login_required
@permission_required('hr.verify_employee')
def verify_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    verification, created = StaffVerification.objects.get_or_create(employee=employee)
    if request.method == 'POST':
        verification.is_verified = True
        verification.verified_by = request.user
        verification.verification_date = timezone.now()
        verification.save()
        messages.success(request, f'Employee {employee} has been verified.')
        return redirect('core:employee_detail', employee_id=employee.id)
    return render(request, 'core/verify_employee.html', {'employee': employee})

def check_educational_discrepancies(request):
    discrepancies = []
    for employee_detail in EmployeeDetail.objects.all():
        employee = employee_detail.employee
        education = employee_detail.education.all().order_by('start_date')
        
        # Check for unusual age in education
        for edu in education:
            age_at_start = (edu.start_date - employee_detail.date_of_birth).days / 365.25
            age_at_end = (edu.end_date - employee_detail.date_of_birth).days / 365.25
            
            if edu.level == 'PRIMARY' and (age_at_start < 5 or age_at_end > 14):
                discrepancies.append({
                    'employee': employee,
                    'message': f"Unusual age for primary education: {age_at_start:.1f} to {age_at_end:.1f} years old"
                })
            elif edu.level == 'SECONDARY' and (age_at_start < 11 or age_at_end > 20):
                discrepancies.append({
                    'employee': employee,
                    'message': f"Unusual age for secondary education: {age_at_start:.1f} to {age_at_end:.1f} years old"
                })
            elif edu.level == 'TERTIARY' and age_at_start < 16:
                discrepancies.append({
                    'employee': employee,
                    'message': f"Unusual age for tertiary education: started at {age_at_start:.1f} years old"
                })
        
        # Check for overlapping education periods
        for i in range(len(education) - 1):
            if education[i].end_date > education[i+1].start_date:
                discrepancies.append({
                    'employee': employee,
                    'message': f"Overlapping education periods: {education[i]} and {education[i+1]}"
                })
        
    return render(request, 'core/educational_discrepancies.html', {'discrepancies': discrepancies})