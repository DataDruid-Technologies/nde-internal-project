from datetime import date, timedelta
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

"""
This module defines the core models for the NDE Internal Management System, including:

* CustomUserManager: A custom user manager for handling employee authentication
* User: A custom user model based on employee ID
* Zone, State, LGA: Models for geographic locations
* Department, Division: Models for organizational structure
* GradeLevel: Model for employee grade levels and associated benefits
* OfficialAppointment: Model for official job appointments
* Bank, PFA: Models for financial institutions
* Employee: Main model storing employee information
"""


class CustomUserManager(BaseUserManager):
    """Custom user manager for creating users based on employee ID"""

    def create_user(self, employee_id, email, password=None, **extra_fields):
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


class User(AbstractUser):
    """Custom user model using employee ID as the username"""

    username = None
    employee_id = models.CharField(
        max_length=20, unique=True, db_index=True, verbose_name="Employee ID")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    ippis_number = models.CharField(
        max_length=8, unique=True, verbose_name="IPPIS Number")
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',
    # Add a unique related_name here
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set', 
    # Add a unique related_name here
        
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['email', 'ippis_number']

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"


class Zone(models.Model):
    """Model representing a geographical zone"""

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True, primary_key=True)

    def __str__(self):
        return self.name


class State(models.Model):
    """Model representing a state within a zone"""

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=3, unique=True, primary_key=True)
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


class Employee(models.Model):
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

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='employee_profile')
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
    cadre = models.CharField(max_length=1, choices=OfficialAppointment.CADRE_CHOICES,
                             null=True, blank=True, verbose_name="Cadre")
    current_grade_level = models.ForeignKey(
        GradeLevel, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Current Grade Level")
    current_step = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Current Step")
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Department")
    division = models.ForeignKey(
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
    child1_name = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Child 1 Name")
    child1_date_of_birth = models.DateField(
        null=True, blank=True, verbose_name="Child 1 Date of Birth")

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
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name='employee_updates', verbose_name="Updated By")

    def calculate_retirement_date(self):
        """Calculates the retirement date based on years of service or age"""

        if not all([self.date_of_first_appointment, self.date_of_birth, self.current_grade_level]):
            return None

        today = date.today()
        years_in_service = today.year - self.date_of_first_appointment.year

        if years_in_service >= 35:
            retirement_date = self.date_of_first_appointment + timedelta(days=365*35)
        else:
            age = today.year - self.date_of_birth.year
            if age >= 60:
                retirement_date = self.date_of_birth.replace(year=today.year)
            else:
                retirement_date = self.date_of_birth.replace(year=today.year + 60 - age)

        return retirement_date

    def save(self, *args, **kwargs):
        if not self.retirement_date:
            self.retirement_date = self.calculate_retirement_date()
        super().save(*args, **kwargs)

    def __str__(self):
        """Returns a string representation of the employee"""
        return f"{self.file_number} - {self.surname}, {self.first_name}"

    class Meta:
        ordering = ['surname', 'first_name']
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        

class File(models.Model):
    file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField() 
    description = models.TextField()
    origin = models.CharField(max_length=255)
    current_location = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('In Transit', 'In Transit'), ('Delivered', 'Delivered'), ('Archived', 'Archived')], default='Pending')

class FileTransfer(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_files')
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_files')
    transfer_date = models.DateTimeField(auto_now_add=True)
    transfer_method = models.CharField(max_length=100)
    transfer_details = models.TextField()
    

class ChatRoom(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(User, related_name='chat_rooms')

    def __str__(self):
        return self.name

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.get_full_name()} in {self.room.name}: {self.content[:50]}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ALERT', 'Alert'),
        ('SUCCESS', 'Success'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For linking to specific objects (e.g., a leave request, a project, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.get_full_name()}: {self.title}"

class InternalMail(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_mails')
    recipients = models.ManyToManyField(User, related_name='received_mails')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    attachment = models.FileField(upload_to='internal_mail_attachments/', null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_draft = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.get_full_name()}: {self.subject}"

class MailFolder(models.Model):
    DEFAULT_FOLDERS = [
        ('INBOX', 'Inbox'),
        ('SENT', 'Sent'),
        ('DRAFTS', 'Drafts'),
        ('TRASH', 'Trash'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mail_folders')
    name = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()}'s {self.name} folder"

class MailMessage(models.Model):
    mail = models.ForeignKey(InternalMail, on_delete=models.CASCADE, related_name='mail_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(MailFolder, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.recipient.get_full_name()}'s copy of {self.mail.subject}"