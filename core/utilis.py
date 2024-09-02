from .forms import *
from .models import *

def log_changes(employee, changed_fields, changed_by):
    for field in changed_fields:
        old_value = employee.__dict__.get(field, '') or employee.details.__dict__.get(field, '')
        new_value = employee.__dict__[field] if field in employee.__dict__ else employee.details.__dict__[field]
        if old_value != new_value:
            EmployeeChangeLog.objects.create(
                employee=employee,
                field_name=field,
                old_value=str(old_value),
                new_value=str(new_value),
                changed_by=changed_by
            )