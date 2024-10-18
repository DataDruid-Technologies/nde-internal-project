# hr/urls.py

from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<str:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<str:employee_id>/update/', views.update_employee_detail, name='update_employee_detail'),
    path('employees/<str:employee_id>/promote/', views.create_promotion, name='create_promotion'),
    path('employees/<str:employee_id>/promotions/', views.promotion_list, name='promotion_list'),
    path('employees/<str:employee_id>/examination/', views.create_examination, name='create_examination'),
    
    path('leave-requests/create/', views.create_leave_request, name='create_leave_request'),
    path('leave-requests/', views.LeaveRequestListView.as_view(), name='leave_request_list'),
    path('leave-requests/<int:leave_request_id>/approve/', views.approve_leave_request, name='approve_leave_request'),
    
    path('employees/<str:employee_id>/transfer/', views.create_transfer, name='create_transfer'),
    path('employees/<str:employee_id>/temporary-access/', views.create_temporary_access, name='create_temporary_access'),
    path('employees/<str:employee_id>/performance-review/', views.create_performance_review, name='create_performance_review'),
    
    path('trainings/create/', views.create_training, name='create_training'),
    path('trainings/', views.TrainingListView.as_view(), name='training_list'),
    
    path('employees/<str:employee_id>/retire/', views.create_retirement, name='create_retirement'),
    path('employees/<str:employee_id>/repatriate/', views.create_repatriation, name='create_repatriation'),
    path('employees/<str:employee_id>/documentation/', views.update_documentation, name='update_documentation'),
    
    path('employee-data-upload/', views.employee_data_upload, name='employee_data_upload'),
    path('update-employee-details/', views.update_employee_details, name='update_employee_details'),
    path('verify-employee/<int:employee_id>/', views.verify_employee, name='verify_employee'),
    path('educational-discrepancies/', views.check_educational_discrepancies, name='educational_discrepancies'),
    path('employees/<str:employee_id>/ippis/', views.update_ippis_management, name='update_ippis_management'),
    
    path('employees/<str:employee_id>/vital-info-change/', views.create_change_of_vital_information, name='create_change_of_vital_information'),
    path('employees/<str:employee_id>/service-record/', views.create_record_of_service, name='create_record_of_service'),
    path('employees/<str:employee_id>/service-records/', views.RecordOfServiceListView.as_view(), name='record_of_service_list'),
    path('departments/<int:department_id>/employees/', views.department_employees, name='department_employees'),
    path('employees/<str:employee_id>/promotion-history/', views.promotion_history, name='promotion_history'),
    path('employees/<str:employee_id>/examination-history/', views.examination_history, name='examination_history'),
    path('employees/<str:employee_id>/transfer-history/', views.transfer_history, name='transfer_history'),
    path('employees/<str:employee_id>/performance-history/', views.performance_review_history, name='performance_review_history'),
    
    path('employees/<str:employee_id>/trainings/', views.employee_trainings, name='employee_trainings'),
    path('employees/<str:employee_id>/assign-training/', views.assign_training, name='assign_training'),
    path('employees/<str:employee_id>/leave-history/', views.employee_leave_history, name='employee_leave_history'),
    path('employees/<str:employee_id>/temp-access-history/', views.temporary_access_history, name='temporary_access_history'),
    path('employees/<str:employee_id>/vital-info-changes/', views.vital_information_changes, name='vital_information_changes'),
    path('employees/<str:employee_id>/verification-history/', views.staff_verification_history, name='staff_verification_history'),
    path('employees/<str:employee_id>/retirement/', views.retirement_details, name='retirement_details'),
    path('employees/<str:employee_id>/repatriation-history/', views.repatriation_history, name='repatriation_history'),
    
    path('employee-search/' , views.employee_search, name='employee_search'),
    path('employees/<str:employee_id>/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('departments/<int:department_id>/dashboard/', views.department_dashboard, name='department_dashboard'),
]