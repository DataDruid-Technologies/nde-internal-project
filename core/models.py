from django.contrib.auth.models import *
from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords
import logging


logger = logging.getLogger(__name__)


class EmployeeManager(BaseUserManager):
    def create_user(self, employee_id, email, password=None, **extra_fields):
        if not employee_id:
            raise ValueError('The Employee ID field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(employee_id=employee_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(employee_id, email, password, **extra_fields)


class ActiveEmployeeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=50, blank=True)
    # To distinguish between system-defined and custom roles
    is_system_role = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Department(models.Model):
    code = models.CharField(max_length=10, unique=False)
    name = models.CharField(max_length=100, unique=True)
    DEPT_TYPES = [
        ('DG OFFICE', 'Director General Office'),
        ('SERVICE', 'Service Department'),
        ('PROGRAMME', 'Programme Department'),
        ('ZONAL', 'Zonal Department'),
        ('BRANCH', 'Branch'),
        ('UNIT', 'Unit'),
    ]
    type = models.CharField(
        max_length=20, choices=DEPT_TYPES, default='SERVICE')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='units')

    def __str__(self):
        return self.name

class Zone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class State(models.Model):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100, unique=True)
    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE, related_name='states')

    def __str__(self):
        return self.name


class LGA(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    state = models.ForeignKey(
        State, on_delete=models.CASCADE, related_name='lgas')

    class Meta:
        unique_together = ('name', 'state')

    def __str__(self):
        return f"{self.name}, {self.state.name}"



class Bank(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
class Employee(AbstractUser):
    username = None  # Remove username field
    employee_id = models.CharField(
        max_length=20, unique=True, db_index=True, verbose_name="Employee ID")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    first_name = models.CharField(
        max_length=50, verbose_name="First Name")
    middle_name = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Middle Name")
    last_name = models.CharField(
        max_length=50, verbose_name="Last Name")
    date_joined = models.DateField(verbose_name="Date of First Appointment")
    ippis_number = models.IntegerField(
        unique=True, null=True, blank=True,
    )
    # Access Type
    ACCESS_TYPES = [
        ('STAFF', 'Staff'),
        ('RETIRED', 'Retired'),
    ]
    access_type = models.CharField(
        max_length=10, choices=ACCESS_TYPES, default='STAFF', verbose_name="Access Type")

    # Role and Department
    ROLE_CHOICES = [
        ('DG', 'Director General'),
        ('DIR', 'Director'),
        ('ZD', 'Zonal Director'),
        ('HOD', 'Head of Department'),
        ('HOU', 'Head of Unit'),
        ('STAFF', 'Staff'),
        ('IT_ADMIN', 'IT Admin'),
    ]
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='STAFF')
    department = models.ForeignKey(
        'Department', on_delete=models.CASCADE, null=True,
        blank=True, related_name='employees', verbose_name="Department")

    # Personal Information
    date_of_birth = models.DateField(
        null=True, blank=True, verbose_name="Date of Birth")
    gender = models.CharField(max_length=10, choices=[(
        'M', 'Male'), ('F', 'Female')], verbose_name="Gender")

    # Employment Information
    current_rank = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Rank")
    EMP_STATUS_CHOICES = [
        ('Active', 'Active'), 
        ('Inactive', 'Inactive'),
        ('On Leave', 'On Leave'),
        ('LOA', 'Leave of Absence'),
        ('Secondment', 'Secondment'), 
        ('AWOL', 'Absent Without Leave'), 
        ('Illness', 'Illness')
    ]
    employment_status = models.CharField(
        max_length=20, choices=EMP_STATUS_CHOICES,
        default='Active', verbose_name="Employment Status")
    date_of_confirmation = models.DateField(
        null=True, blank=True, verbose_name="Date of Confirmation")
    retirement_date = models.DateField(
        null=True, blank=True, verbose_name="Retirement Date")

    # Control Sections (No changes needed here)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EmployeeManager()
    history = HistoricalRecords()
    active_objects = ActiveEmployeeManager()
    

    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})"

    def save(self, *args, **kwargs):
        if self.retirement_date and self.retirement_date <= timezone.now().date():
            self.access_type = 'RETIRED'
            self.is_active = False

            # Create or update RetiredEmployee instance
            retired_employee, created = RetiredEmployee.objects.get_or_create(
                employee=self,
                defaults={'access_expiry': timezone.now().date() +
                          relativedelta(months=1)}
            )
            if not created:
                retired_employee.access_expiry = timezone.now().date() + relativedelta(months=1)
                retired_employee.save()

        super().save(*args, **kwargs)
        



class Leave(models.Model):
    emploqyee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='leaves', verbose_name="Employee")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    LEAVE_TYPES = [
        ('CL', 'Casual Leave'),
        ('STL', 'Study Leave'),
        ('ML', 'Maternity Leave'),
        ('PL', 'Paternity Leave'),
        ('OL', 'Other Leave')
    ]
    type = models.CharField(max_length=6,choices=LEAVE_TYPES, default='CL', verbose_name="Leave Type")
    reason = models.TextField(verbose_name="Reason")
    
    
class EmployeeDetail(models.Model):
    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_details')
    bank_name = models.ForeignKey(
        'Bank', blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Bank Name')
    account_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Account Number")

    # Additional Personal Information
    nationality = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Nationality")
    state_of_origin = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="State of Origin")
    local_government_area = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Local Government Area")

    # Additional Employment Information
    employee_grade_level = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Employee Grade Level")
    date_of_first_appointment = models.DateField(
        null=True, blank=True, verbose_name="Date of First Appointment")
    date_of_present_appointment = models.DateField(
        null=True, blank=True, verbose_name="Date of Present Appointment")

    # Additional Educational Information
    professional_qualifications = models.TextField(
        blank=True, null=True, verbose_name="Professional Qualifications")

    # Additional Financial Information
    pension_fund_administrator = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Pension Fund Administrator")
    pension_account_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Pension Account Number")

    # Performance Information
    last_promotion_date = models.DateField(
        null=True, blank=True, verbose_name="Last Promotion Date")

    def __str__(self):
        return f"Details for {self.employee.get_full_name()}"

    class Meta:
        verbose_name = "Employee Detail"
        verbose_name_plural = "Employee Details"


class EmployeeChangeLog(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='change_logs')
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, related_name='changes_made')
    change_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Change in {self.field_name} for {self.employee.get_full_name()}"


class CustomPermission(models.Model):
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100)
    content_type = models.ForeignKey(
        'contenttypes.ContentType', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('content_type', 'codename')

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(CustomPermission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class EmployeePermission(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='custom_permissions')
    permission = models.ForeignKey(CustomPermission, on_delete=models.CASCADE)
    granted_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, related_name='permissions_granted')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'permission')

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.permission.name}"


class WorkflowStep(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField()
    required_role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True)
    required_permission = models.ForeignKey(
        CustomPermission, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Workflow(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    steps = models.ManyToManyField(WorkflowStep, through='WorkflowStepOrder', related_name='workflows')
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_workflows')

    def __str__(self):
        return self.name
    

class WorkflowStepOrder(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('workflow', 'step')

    def __str__(self):
        return f"{self.workflow.name} - {self.step.name} (Order: {self.order})"


class WorkflowInstance(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    current_step = models.ForeignKey(
        WorkflowStep, on_delete=models.SET_NULL, null=True)
    initiator = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='initiated_workflows')
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.workflow.name} - {self.initiator.get_full_name()} ({self.status})"


class WorkflowApproval(models.Model):
    workflow_instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name='approvals')
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    approver = models.ForeignKey(Employee, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ], default='PENDING')
    comments = models.TextField(blank=True)
    acted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.workflow_instance} - {self.step.name} - {self.approver.get_full_name()} ({self.status})"


class RetiredEmployee(models.Model):
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name='retired_info')
    retirement_date = models.DateField(auto_now_add=True)
    access_expiry = models.DateField()

    def __str__(self):
        return f"Retired: {self.employee.get_full_name()} (Access until: {self.access_expiry})"


class RetirementDocument(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='retirement_documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class RetiredEmployeeDocument(models.Model):
    retired_employee = models.ForeignKey(
        RetiredEmployee, on_delete=models.CASCADE, related_name='downloaded_documents')
    document = models.ForeignKey(RetirementDocument, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('retired_employee', 'document')

    def __str__(self):
        return f"{self.retired_employee.employee.get_full_name()} - {self.document.title}"


User = get_user_model()


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    department = models.ForeignKey(
        'Department', on_delete=models.CASCADE, related_name='projects')
    team_members = models.ManyToManyField(User, related_name='projects')

    def __str__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='assigned_tasks')
    due_date = models.DateField(db_index=True)
    STATUS_CHOICES=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('OVERDUE', 'Overdue')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    department = models.ForeignKey(
        'Department', on_delete=models.CASCADE, related_name='announcements', null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    is_global = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.sender} to {self.recipient}: {self.content[:50]}'

    @classmethod
    def delete_old_messages(cls):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        cls.objects.filter(timestamp__lt=thirty_days_ago).delete()


class InboxMessage(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_inbox_messages')
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_inbox_messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.sender} to {self.recipient}: {self.subject}'

    @classmethod
    def delete_old_messages(cls):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        cls.objects.filter(timestamp__lt=thirty_days_ago).delete()


User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user}: {self.message}'


@receiver(post_save, sender=InboxMessage)
def create_inbox_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.recipient,
            message=f'New message from {instance.sender}: {instance.subject}'
        )


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    theme = models.CharField(max_length=20, choices=[(
        'light', 'Light'), ('dark', 'Dark')], default='light')
    notification_preferences = models.JSONField(default=dict)

    def __str__(self):
        return f'{self.user.get_full_name()} Profile'


from django.db import models
from django.contrib.auth.models import User

class Performance(models.Model):
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    evaluation_date = models.DateField()
    rating = models.IntegerField(choices=RATING_CHOICES)
    comments = models.TextField()

class Training(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)

class Retirement(models.Model):
    employee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    retirement_date = models.DateField()
    reason = models.CharField(max_length=200)
    pension_details = models.TextField()