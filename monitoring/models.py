# monitoring/models.py

from django.db import models
from django.conf import settings
from core.models import *

class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    STATUS_CHOICES =[
        ('NOT_STARTED', 'Not Started'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('DELAYED', 'Delayed')
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField()
    end_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='projects')
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    project_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assigned_projects')

    def __str__(self):
        return self.title

class ProjectStatus(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='statuses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    comment = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Project Statuses'

    def __str__(self):
        return f"{self.project.title} - {self.get_status_display()}"

class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.project.title} - {self.title}"

class KPI(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='kpis')
    name = models.CharField(max_length=255)
    description = models.TextField()
    target_value = models.FloatField()
    actual_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50)
    date = models.DateField()
    
    class Meta:
        verbose_name = 'KPI'
        verbose_name_plural = 'KPIs'

    def __str__(self):
        return f"{self.project.title} - {self.name}"

class Risk(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='risks')
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    mitigation_plan = models.TextField()
    identified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    identified_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.title} - {self.get_severity_display()} Risk"