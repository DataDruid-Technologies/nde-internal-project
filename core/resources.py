# resources.py
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from .models import *

class BaseResource(resources.ModelResource):
    def before_import_row(self, row, **kwargs):
        for field in self.fields:
            if field not in row:
                row[field] = None
            elif row[field] == '':
                row[field] = None

class DepartmentResource(BaseResource):
    class Meta:
        model = Department
        import_id_fields = ('name',)
        fields = ('id', 'name', 'description', 'parent')
        export_order = fields

    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ForeignKeyWidget(Department, 'name')
    )

class EmployeeResource(BaseResource):
    class Meta:
        model = Employee
        import_id_fields = ('employee_id',)
        fields = ('id', 'employee_id', 'email', 'first_name', 'middle_name', 'last_name', 
                  'department', 'role', 'is_active', 'is_staff', 'is_superuser', 
                  'date_of_birth', 'date_joined', 'date_of_confirmation', 'ippis_number', 
                  'gender', 'access_type', 'password')
        export_order = fields[:len(fields)-1]  # Exclude password from export

    department = fields.Field(
        column_name='department',
        attribute='department',
        widget=ForeignKeyWidget(Department, 'name')
    )

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        if 'password' not in row or not row['password']:
            row['password'] = get_random_string(length=12)
        row['password'] = make_password(row['password'])
        for bool_field in ['is_active', 'is_staff', 'is_superuser']:
            if bool_field in row and row[bool_field]:
                row[bool_field] = row[bool_field].lower() in ('true', 'yes', '1')

class StateResource(BaseResource):
    class Meta:
        model = State
        import_id_fields = ('name',)
        fields = ('id', 'name', 'zone')
        export_order = fields

    zone = fields.Field(
        column_name='zone',
        attribute='zone',
        widget=ForeignKeyWidget('core.Zone', 'name')
    )

class LGAResource(BaseResource):
    class Meta:
        model = LGA
        import_id_fields = ('name', 'state')
        fields = ('id', 'name', 'state')
        export_order = fields

    state = fields.Field(
        column_name='state',
        attribute='state',
        widget=ForeignKeyWidget(State, 'name')
    )

class WorkflowStepResource(BaseResource):
    class Meta:
        model = WorkflowStep
        import_id_fields = ('name',)
        fields = ('id', 'name', 'description', 'order', 'required_role', 'required_permission')
        export_order = fields

    required_role = fields.Field(
        column_name='required_role',
        attribute='required_role',
        widget=ForeignKeyWidget('core.Role', 'name')
    )

    required_permission = fields.Field(
        column_name='required_permission',
        attribute='required_permission',
        widget=ForeignKeyWidget('core.CustomPermission', 'codename')
    )

class WorkflowInstanceResource(BaseResource):
    class Meta:
        model = WorkflowInstance
        import_id_fields = ('workflow', 'initiator')
        fields = ('id', 'workflow', 'current_step', 'initiator', 'status', 'created_at', 'updated_at')
        export_order = fields

    workflow = fields.Field(
        column_name='workflow',
        attribute='workflow',
        widget=ForeignKeyWidget('core.Workflow', 'name')
    )

    current_step = fields.Field(
        column_name='current_step',
        attribute='current_step',
        widget=ForeignKeyWidget(WorkflowStep, 'name')
    )

    initiator = fields.Field(
        column_name='initiator',
        attribute='initiator',
        widget=ForeignKeyWidget(Employee, 'employee_id')
    )