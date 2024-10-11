from datetime import date, timedelta
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, employee_id, ippis_number, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(employee_id=employee_id, ippis_number=ippis_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, ippis_number, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('current_role', 'DG')  # Set default role for superuser
        return self.create_user(employee_id, ippis_number, email, password, **extra_fields)

class Employee(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('DG', 'Director General'),
        ('DIR', 'Director'),
        ('ZD', 'Zonal Director'),
        ('SC', 'State Coordinator'),
        ('STAFF', 'Staff'),
    )
    
    employee_id = models.CharField(max_length=50, unique=True, verbose_name="Employee ID")
    ippis_number = models.CharField(max_length=50, unique=True, verbose_name="IPPIS Number")
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="First Name")
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Last Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    in_app_email = models.EmailField(unique=True, blank=True, null=True, verbose_name="In-App Email")
    in_app_chat_name = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="In-App Chat Name")

    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    date_of_first_appointment = models.DateField(blank=True, null=True, verbose_name="Date of First Appointment")
    date_of_retirement = models.DateField(null=True, blank=True, verbose_name="Date of Retirement")
    active_status = models.BooleanField(default=True, verbose_name="Active Status")
    is_staff = models.BooleanField(default=False, verbose_name="Staff Status")

    current_role = models.CharField(max_length=5, choices=ROLE_CHOICES, default='STAFF')
    current_zone = models.ForeignKey('Zone', on_delete=models.SET_NULL, null=True, blank=True)
    current_state = models.ForeignKey('State', on_delete=models.SET_NULL, null=True, blank=True)

    access_type = models.CharField(max_length=20, choices=[('staff', 'Staff'), ('adhoc', 'Ad Hoc')], default='staff', verbose_name="Access Type")

    current_group = models.ForeignKey('auth.Group', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Current Group", related_name="current_employees")

    current_department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Department")
    current_grade_level = models.ForeignKey('GradeLevel', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees', verbose_name="Grade Level")
    password_change_required = models.BooleanField(default=False)
    objects = CustomUserManager()

    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['ippis_number', 'email']

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def save(self, *args, **kwargs):
        if self.date_of_birth and self.date_of_first_appointment and not self.date_of_retirement:
            age_60 = self.date_of_birth + relativedelta(years=60)
            service_35 = self.date_of_first_appointment + relativedelta(years=35)
            self.date_of_retirement = min(age_60, service_35)

        if self.date_of_retirement and self.date_of_retirement <= timezone.now().date():
            self.active_status = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} ({self.employee_id})"


class Zone(models.Model):
    """Model representing a geographical zone"""

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True, primary_key=True)
    director = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='directed_zone')

    def __str__(self):
        return self.name


class State(models.Model):
    """Model representing a state within a zone"""

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=3, unique=True, primary_key=True)
    coordinator = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='coordinated_state')
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class LGA(models.Model):
    """Model representing a Local Government Area (LGA) within a state"""

    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, on_delete=models.PROTECT)
    code = models.CharField(max_length=5, unique=True, primary_key=True)

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class Department(models.Model):
    """Model representing a department within the organization"""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True, primary_key=True)

    def __str__(self):
        return self.name


class Division(models.Model):
    """Model representing a division within a department"""

    code = models.CharField(max_length=7, unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="divisions")

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    class Meta:
        ordering = ['code']


class GradeLevel(models.Model):
    """Model representing an employee's grade level and associated benefits"""

    level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(18)],
        primary_key=True)
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=40, blank=True)
    per_diem = models.DecimalField(max_digits=8, decimal_places=2)
    local_running = models.DecimalField(max_digits=8, decimal_places=2)
    estacode = models.DecimalField(max_digits=8, decimal_places=2)
    assumption_of_duty = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.name}"


class OfficialAppointment(models.Model):
    """Model representing an official job appointment"""

    CADRE_CHOICES = [
        ('O', 'OFFICER'),
        ('E', 'EXECUTIVE'),
        ('S', 'SECRETARIAL'),
        ('C', 'CLERICAL'),
        ('D', 'DRIVER'),
    ]
    code = models.CharField(max_length=15, unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE)
    cadre = models.CharField(max_length=1, choices=CADRE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Official Appointment"
        verbose_name_plural = "Official Appointments"


class Bank(models.Model):
    """Model representing a bank"""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)

    def __str__(self):
        return self.name


class PFA(models.Model):
    """Model representing a Pension Fund Administrator (PFA)"""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)

    def __str__(self):
        return self.name
    

class Unit(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    head = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='headed_unit')

    def __str__(self):
        return f"{self.name} - {self.department}"