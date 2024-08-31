from django.contrib.auth.models import *
from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta

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

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)  # To distinguish between system-defined and custom roles

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subdepartments')

    def __str__(self):
        return self.name

class Zone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='states')

    def __str__(self):
        return self.name

class LGA(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='lgas')

    class Meta:
        unique_together = ('name', 'state')

    def __str__(self):
        return f"{self.name}, {self.state.name}"



class Employee(AbstractUser):
    username = None  # Remove username field
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="Employee ID")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    date_joined = models.DateField(verbose_name="Date Joined")

    # Access Type
    ACCESS_TYPES = [
        ('STAFF', 'Staff'),
        ('GUEST', 'Guest'),
        ('RETIRED', 'Retired'),
    ]
    access_type = models.CharField(max_length=10, choices=ACCESS_TYPES, default='STAFF', verbose_name="Access Type")

    # Role and Department
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Role")
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Department")

    # Location
    zone = models.ForeignKey('Zone', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Zone")
    state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="State")
    lga = models.ForeignKey('LGA', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="LGA")

    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], verbose_name="Gender")
    marital_status = models.CharField(max_length=20, choices=[('Single', 'Single'), ('Married', 'Married'), ('Divorced', 'Divorced'), ('Widowed', 'Widowed')], verbose_name="Marital Status")
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, null=True, verbose_name="Address")

    # Educational Information
    highest_qualification = models.CharField(max_length=100, blank=True, null=True, verbose_name="Highest Qualification")
    institution = models.CharField(max_length=200, blank=True, null=True, verbose_name="Institution")
    year_of_graduation = models.IntegerField(null=True, blank=True, verbose_name="Year of Graduation")

    # Employment Information
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="Position")
    employment_status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('On Leave', 'On Leave')], default='Active', verbose_name="Employment Status")
    retirement_date = models.DateField(null=True, blank=True, verbose_name="Retirement Date")

    # Spouse Information
    spouse_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Spouse Name")
    spouse_phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Spouse Phone Number")

    # Next of Kin
    next_of_kin_name = models.CharField(max_length=200, verbose_name="Next of Kin Name")
    next_of_kin_relationship = models.CharField(max_length=50, verbose_name="Next of Kin Relationship")
    next_of_kin_phone_number = models.CharField(max_length=15, verbose_name="Next of Kin Phone Number")

    # Financial Information
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bank Name")
    account_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Account Number")
    bvn = models.CharField(max_length=11, blank=True, null=True, verbose_name="BVN")  # Bank Verification Number

    # Control Sections (No changes needed here)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EmployeeManager()

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
                defaults={'access_expiry': timezone.now().date() + relativedelta(months=1)}
            )
            if not created:
                retired_employee.access_expiry = timezone.now().date() + relativedelta(months=1)
                retired_employee.save()

        super().save(*args, **kwargs)



class CustomPermission(models.Model):
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('content_type', 'codename')

    def __str__(self):
        return self.name

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(CustomPermission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"

class EmployeePermission(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='custom_permissions')
    permission = models.ForeignKey(CustomPermission, on_delete=models.CASCADE)
    granted_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='permissions_granted')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'permission')

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.permission.name}"

class WorkflowStep(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField()
    required_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    required_permission = models.ForeignKey(CustomPermission, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class Workflow(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    steps = models.ManyToManyField(WorkflowStep, through='WorkflowStepOrder')

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
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True)
    initiator = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='initiated_workflows')
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
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='approvals')
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
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='retired_info')
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
    retired_employee = models.ForeignKey(RetiredEmployee, on_delete=models.CASCADE, related_name='downloaded_documents')
    document = models.ForeignKey(RetirementDocument, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('retired_employee', 'document')

    def __str__(self):
        return f"{self.retired_employee.employee.get_full_name()} - {self.document.title}"

# Existing models like EmployeeInfoChangeLog, LeaveRequest, etc. remain unchanged