# programs/models.py

from django.db import models

class Program(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    STATUS_CHOICES =[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField()
    end_date = models.DateField()
    # Add other fields as necessary

    def __str__(self):
        return self.name