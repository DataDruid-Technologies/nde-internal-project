# finance/models.py

from django.db import models
from django.conf import settings
from core.models import Department, State
from monitoring.models import Project

class Budget(models.Model):
    BUDGET_TYPE_CHOICES = [
        ('DEPARTMENT', 'Department'),
        ('PROJECT', 'Project'),
        ('STATE', 'State'),
    ]
    
    year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    approved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('year', 'budget_type', 'department', 'project', 'state')

    def __str__(self):
        if self.budget_type == 'DEPARTMENT':
            return f"{self.year} {self.department.name} Budget"
        elif self.budget_type == 'PROJECT':
            return f"{self.year} {self.project.title} Budget"
        else:
            return f"{self.year} {self.state.name} Budget"

class Expenditure(models.Model):
    EXPENDITURE_TYPE_CHOICES = [
        ('OPERATIONAL', 'Operational'),
        ('CAPITAL', 'Capital'),
        ('PROJECT', 'Project'),
    ]
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    date = models.DateField()
    expenditure_type = models.CharField(max_length=20, choices=EXPENDITURE_TYPE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='expenditures')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='expenditures')
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='expenditures')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_expenditures')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='submitted_expenditures')
    
    def __str__(self):
        return f"{self.date} - {self.description[:50]}..."

class FinancialReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUAL', 'Annual'),
    ]
    
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='financial_reports/')
    
    def __str__(self):
        return f"{self.get_report_type_display()} Report - {self.start_date} to {self.end_date}"

class Grant(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    granting_agency = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='grants', null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='grants')
    
    def __str__(self):
        return f"{self.name} - {self.granting_agency}"

class Asset(models.Model):
    ASSET_TYPE_CHOICES = [
        ('EQUIPMENT', 'Equipment'),
        ('VEHICLE', 'Vehicle'),
        ('BUILDING', 'Building'),
        ('LAND', 'Land'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    purchase_date = models.DateField()
    purchase_value = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='assets')
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='assets')
    
    def __str__(self):
        return f"{self.name} - {self.get_asset_type_display()}"