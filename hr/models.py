from django.db import models
from django.conf import settings
from core.models import *

class EmployeeDetail(models.Model):
    """Main model storing comprehensive employee information"""

    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    ]
    ACCOUNT_TYPES = [
        ('S', 'Savings'),
        ('C', 'Current'),
    ]
    NOK_RELATIONSHIP_CHOICES = [
        ('SPOUSE', 'Spouse'),
        ('CHILD', 'Child'),
        ('PARENT', 'Parent'),
        ('SIBLING', 'Sibling'),
        ('OTHER', 'Other'),
    ]

    employee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='details', verbose_name="Employee")
    file_number = models.CharField(
        max_length=7, unique=True, blank=True, null=True, verbose_name="File Number")
    nin = models.CharField(max_length=11, unique=True, blank=True,
                           null=True, verbose_name="National Identification Number")
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    middle_name = models.CharField(
        max_length=50, blank=True, verbose_name="Middle Name")
    surname = models.CharField(max_length=50, verbose_name="Surname")
    date_of_birth = models.DateField(
        null=True, blank=True, verbose_name="Date of Birth")
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name="Gender")
    marital_status = models.CharField(
        max_length=1, choices=MARITAL_STATUS_CHOICES, blank=True, verbose_name="Marital Status")
    phone_number = models.CharField(max_length=11, validators=[RegexValidator(
        r'^(080|081|090|091|070)\d{8}$')], blank=True, null=True, verbose_name="Phone Number")
    residential_address = models.CharField(
        max_length=150, blank=True, verbose_name="Residential Address")
    state_of_residence = models.ForeignKey(
        State, on_delete=models.PROTECT, related_name='employees_residence', null=True, blank=True, verbose_name="State of Residence")
    lga_of_residence = models.ForeignKey(
        LGA, on_delete=models.PROTECT, related_name='employees_residence', null=True, blank=True, verbose_name="LGA of Residence")  # Corrected related_name
    state_of_origin = models.ForeignKey(
        State, on_delete=models.PROTECT, related_name='employees_origin', null=True, blank=True, verbose_name="State of Origin")
    lga_of_origin = models.ForeignKey(
        LGA, on_delete=models.PROTECT, related_name='employees_origin', null=True, blank=True, verbose_name="LGA of Origin")

    # Employment Details
    date_of_first_appointment = models.DateField(
        null=True, blank=True, verbose_name="Date of First Appointment")
    date_of_present_appointment = models.DateField(
        null=True, blank=True, verbose_name="Date of Present Appointment")
    date_of_confirmation = models.DateField(
        null=True, blank=True, verbose_name="Date of Confirmation")
    date_of_confirmation_exam = models.DateField(
        null=True, blank=True, verbose_name="Date When Confirmation Exam was taken")
    cadre = models.CharField(max_length=1, choices=OfficialAppointment.CADRE_CHOICES,
                             null=True, blank=True, verbose_name="Cadre")
    current_grade_level = models.ForeignKey(
        GradeLevel, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Current Grade Level")
    current_step = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Current Step")
    current_department = models.ForeignKey(
        Department, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Department")
    currrent_division = models.ForeignKey(
        Division, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Division")
    passport = models.ImageField(
        upload_to='employee_passports/', null=True, blank=True, verbose_name="Passport Photo")
    state_of_posting = models.ForeignKey(
        State, on_delete=models.PROTECT, related_name='employees_posting', null=True, blank=True, verbose_name="State of Posting")
    station = models.ForeignKey(LGA, on_delete=models.PROTECT, null=True,
                                blank=True, related_name='employees_lga_posting', verbose_name="Station")  # Corrected related_name
    present_appointment = models.ForeignKey(
        OfficialAppointment, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Present Appointment")
    last_promotion_date = models.DateField(
        null=True, blank=True, verbose_name="Last Promotion Date")
    retirement_date = models.DateField(
        null=True, blank=True, verbose_name="Retirement Date")

    # Financial Information
    bank = models.ForeignKey(
        Bank, on_delete=models.PROTECT, blank=True, null=True)
    account_type = models.CharField(
        max_length=1, choices=ACCOUNT_TYPES, blank=True, null=True)
    account_number = models.CharField(max_length=10, validators=[
        RegexValidator(r'^\d{10}$')], blank=True, null=True)
    pfa = models.ForeignKey(PFA, on_delete=models.PROTECT, null=True,
                            blank=True, verbose_name='Pension Fund Administrator')
    pfa_number = models.CharField(max_length=12, blank=True, validators=[
        RegexValidator(r'^\d{12}$')], verbose_name="PFA PEN")

    # Spouse Information
    full_name_spouse = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Spouse Full Name")
    phone_number_spouse = models.CharField(
        max_length=15, null=True, blank=True, verbose_name="Spouse Phone Number")
    residential_address_spouse = models.CharField(
        max_length=150, null=True, blank=True, verbose_name="Spouse Residential Address")
    employer_spouse = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Spouse Employer")

    # Children Information
    number_of_children = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Number of Children")
 
    # Next of Kin Information
    nok1_name = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Next of Kin 1 Name")
    nok1_relationship = models.CharField(
        max_length=50, choices=NOK_RELATIONSHIP_CHOICES, null=True, blank=True, verbose_name="Next of Kin 1 Relationship")
    nok1_address = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Next of Kin 1 Address")
    nok1_phone_number = models.CharField(
        max_length=15, null=True, blank=True, verbose_name="Next of Kin 1 Phone Number")
    nok2_name = models.CharField(
        max_length=50, null=True, blank=True, verbose_name='Next of Kin 2 Name')
    nok2_relationship = models.CharField(
        max_length=50, choices=NOK_RELATIONSHIP_CHOICES, null=True, blank=True, verbose_name='Next of Kin 2 Relationship')
    nok2_address = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='Next of Kin 2 Address')
    nok2_phone_number = models.CharField(
        max_length=15, null=True, blank=True, verbose_name='Next of Kin 2 Phone Number')

    # Additional Information
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created At")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name='employee_creations', verbose_name="Created By")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name='employee_updates', verbose_name="Updated By")

    def is_eligible_for_promotion(self):
        if not self.employee.current_grade_level:
            return False

        today = timezone.now().date()
        
        reference_date = self.last_promotion_date or self.employee.date_of_first_appointment
        if not reference_date:
            return False

        years_since_reference = relativedelta(today, reference_date).years

        if self.employee.current_grade_level.level <= 6:
            required_years = 2
        elif 7 <= self.employee.current_grade_level.level <= 14:
            required_years = 3
        else:  # Grade Level 15 and above
            required_years = 4

        if years_since_reference >= required_years:
            if self.last_examination_date:
                years_since_exam = relativedelta(today, self.last_examination_date).years
                return years_since_exam <= 2
            else:
                return False
        else:
            return False

    def get_years_to_promotion_eligibility(self):
        if not self.employee.current_grade_level:
            return None

        today = timezone.now().date()
        reference_date = self.last_promotion_date or self.employee.date_of_first_appointment
        if not reference_date:
            return None

        years_since_reference = relativedelta(today, reference_date).years

        if self.employee.current_grade_level.level <= 6:
            required_years = 2
        elif 7 <= self.employee.current_grade_level.level <= 14:
            required_years = 3
        else:  # Grade Level 15 and above
            required_years = 4

        years_to_eligibility = max(0, required_years - years_since_reference)
        return years_to_eligibility

    class Meta:
        verbose_name = "Employee Detail"
        verbose_name_plural = "Employee Details"

    def __str__(self):
        return f"Employee Details for {self.employee.first_name} {self.employee.last_name}"

class Promotion(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='promotions', verbose_name="Employee")
    from_grade = models.ForeignKey(GradeLevel, on_delete=models.PROTECT, related_name='promotions_from', verbose_name="From Grade")
    to_grade = models.ForeignKey(GradeLevel, on_delete=models.PROTECT, related_name='promotions_to', verbose_name="To Grade")
    from_step = models.PositiveIntegerField(verbose_name="From Step")
    to_step = models.PositiveIntegerField(verbose_name="To Step")
    promotion_date = models.DateField(verbose_name="Promotion Date")
    effective_date = models.DateField(verbose_name="Effective Date")
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='approved_promotions', verbose_name="Approved By")
    remarks = models.TextField(blank=True, verbose_name="Remarks")

    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"

    def __str__(self):
        return f"{self.employee} promoted to GL {self.to_grade.level} Step {self.to_step} on {self.promotion_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.employee.current_grade_level = self.to_grade
        self.employee.current_step = self.to_step
        self.employee.save()
        employee_detail = self.employee.employee_profile
        employee_detail.last_promotion_date = self.promotion_date
        employee_detail.save()

class Examination(models.Model):
    EXAM_TYPES = [
        ('PROMOTION', 'Promotion Exam'),
        ('CONFIRMATION', 'Confirmation Exam'),
        ('PROFICIENCY', 'Proficiency Test'),
        ('OTHER', 'Other')
    ]

    RESULT_STATUSES = [
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
        ('AWAITING', 'Awaiting Result'),
        ('EXEMPTED', 'Exempted')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='examinations', verbose_name="Employee")
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, verbose_name="Examination Type")
    exam_date = models.DateField(verbose_name="Examination Date")
    exam_title = models.CharField(max_length=255, verbose_name="Examination Title")
    result_status = models.CharField(max_length=20, choices=RESULT_STATUSES, default='AWAITING', verbose_name="Result Status")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Score")
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Passing Score")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    certificate_issued = models.BooleanField(default=False, verbose_name="Certificate Issued")
    certificate_issue_date = models.DateField(null=True, blank=True, verbose_name="Certificate Issue Date")
    exam_document = models.FileField(upload_to='examination_documents/', null=True, blank=True, verbose_name="Examination Document")
    result_document = models.FileField(upload_to='examination_results/', null=True, blank=True, verbose_name="Result Document")

    class Meta:
        verbose_name = "Examination"
        verbose_name_plural = "Examinations"
        ordering = ['-exam_date']

    def __str__(self):
        return f"{self.employee} - {self.exam_title} on {self.exam_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        employee_detail = self.employee.employee_profile
        if not employee_detail.last_examination_date or self.exam_date > employee_detail.last_examination_date:
            employee_detail.last_examination_date = self.exam_date
            employee_detail.save()



class LeaveRequest(models.Model):
    LEAVE_TYPES = (
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('study', 'Study Leave'),
        ('compassionate', 'Compassionate Leave'),
    )
    
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests', verbose_name="Employee")
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES, verbose_name="Leave Type")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    reason = models.TextField(verbose_name="Reason")
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', verbose_name="Status")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves', verbose_name="Approved By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"

class Transfer(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transfers', verbose_name="Employee")
    from_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='transfers_from', verbose_name="From Department")
    to_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='transfers_to', verbose_name="To Department")
    transfer_date = models.DateField(verbose_name="Transfer Date")
    reason = models.TextField(verbose_name="Reason for Transfer")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_transfers', verbose_name="Approved By")

    class Meta:
        verbose_name = "Transfer"
        verbose_name_plural = "Transfers"

    def __str__(self):
        return f"{self.employee} transferred to {self.to_department} on {self.transfer_date}"


class TemporaryAccess(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='temporary_accesses', verbose_name="Employee")
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='granted_accesses', verbose_name="Granted By")
    start_date = models.DateTimeField(verbose_name="Start Date")
    end_date = models.DateTimeField(verbose_name="End Date")
    reason = models.TextField(verbose_name="Reason")
    permissions = models.ManyToManyField('auth.Permission', blank=True, verbose_name="Temporary Permissions")

    class Meta:
        verbose_name = "Temporary Access"
        verbose_name_plural = "Temporary Accesses"

    def __str__(self):
        return f"Temporary Access for {self.employee} from {self.start_date} to {self.end_date}"

    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date

class PerformanceReview(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='performance_reviews', verbose_name="Employee")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conducted_reviews', verbose_name="Reviewer")
    review_date = models.DateField(verbose_name="Review Date")
    performance_score = models.DecimalField(max_digits=3, decimal_places=2, verbose_name="Performance Score")
    comments = models.TextField(verbose_name="Comments")
    goals_set = models.TextField(verbose_name="Goals Set")

    class Meta:
        verbose_name = "Performance Review"
        verbose_name_plural = "Performance Reviews"

    def __str__(self):
        return f"Performance Review for {self.employee} on {self.review_date}"

class Training(models.Model):
    title = models.CharField(max_length=200, verbose_name="Training Title")
    description = models.TextField(verbose_name="Description")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    trainer = models.CharField(max_length=100, verbose_name="Trainer")
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='trainings', verbose_name="Participants")

    class Meta:
        verbose_name = "Training"
        verbose_name_plural = "Trainings"

    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"


class Retirement(models.Model):
    employee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retirement')
    retirement_date = models.DateField()
    reason = models.CharField(max_length=100, choices=[
        ('AGE', 'Age'),
        ('YEARS_OF_SERVICE', 'Years of Service'),
        ('VOLUNTARY', 'Voluntary'),
        ('MEDICAL', 'Medical'),
        ('OTHER', 'Other')
    ])
    additional_info = models.TextField(blank=True)

    class Meta:
        verbose_name = "Retirement"
        verbose_name_plural = "Retirements"

    def __str__(self):
        return f"{self.employee} - Retirement on {self.retirement_date}"

class Repatriation(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='repatriations')
    from_state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='repatriations_from')
    to_state = models.ForeignKey(State, on_delete=models.PROTECT, related_name='repatriations_to')
    repatriation_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_repatriations')

    class Meta:
        verbose_name = "Repatriation"
        verbose_name_plural = "Repatriations"

    def __str__(self):
        return f"{self.employee} repatriated from {self.from_state} to {self.to_state} on {self.repatriation_date}"

class Documentation(models.Model):
    employee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documentation')
    birth_certificate = models.FileField(upload_to='employee_documents/', null=True, blank=True)
    educational_certificates = models.FileField(upload_to='employee_documents/', null=True, blank=True)
    medical_certificate = models.FileField(upload_to='employee_documents/', null=True, blank=True)
    reference_letters = models.FileField(upload_to='employee_documents/', null=True, blank=True)
    other_documents = models.FileField(upload_to='employee_documents/', null=True, blank=True)
    documentation_complete = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Documentation"
        verbose_name_plural = "Documentations"

    def __str__(self):
        return f"Documentation for {self.employee}"

class IPPISManagement(models.Model):
    employee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ippis_management')
    ippis_number = models.CharField(max_length=20, unique=True)
    date_enrolled = models.DateField()
    last_updated = models.DateField(auto_now=True)
    salary_grade = models.ForeignKey(GradeLevel, on_delete=models.PROTECT)
    salary_step = models.PositiveIntegerField()

    class Meta:
        verbose_name = "IPPIS Management"
        verbose_name_plural = "IPPIS Management"

    def __str__(self):
        return f"IPPIS Management for {self.employee} - {self.ippis_number}"

class StaffVerification(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verifications')
    verification_date = models.DateField()
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='conducted_verifications')
    is_verified = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Staff Verification"
        verbose_name_plural = "Staff Verifications"

    def __str__(self):
        return f"Verification for {self.employee} on {self.verification_date}"

class ChangeOfVitalInformation(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vital_info_changes')
    field_changed = models.CharField(max_length=100)
    old_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)
    change_date = models.DateField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_vital_info_changes')
    reason = models.TextField()

    class Meta:
        verbose_name = "Change of Vital Information"
        verbose_name_plural = "Changes of Vital Information"

    def __str__(self):
        return f"{self.employee} - {self.field_changed} changed on {self.change_date}"

class RecordOfService(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_records')
    event_type = models.CharField(max_length=100, choices=[
        ('APPOINTMENT', 'Appointment'),
        ('PROMOTION', 'Promotion'),
        ('TRANSFER', 'Transfer'),
        ('DISCIPLINARY_ACTION', 'Disciplinary Action'),
        ('AWARD', 'Award'),
        ('OTHER', 'Other')
    ])
    event_date = models.DateField()
    description = models.TextField()
    
    class Meta:
        verbose_name = "Record of Service"
        verbose_name_plural = "Records of Service"
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.employee} - {self.event_type} on {self.event_date}"