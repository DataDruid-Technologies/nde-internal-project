from django.contrib import admin
from .models import *
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin

# Register your models here.
admin.site.register(Role)
admin.site.register(Workflow)
admin.site.register(WorkflowInstance)
admin.site.register(WorkflowStep)


class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        import_id_fields = ('code',)
        fields = ('id', 'code', 'name', 'type','parent')
        export_order = fields

    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ForeignKeyWidget(Department, 'name')
    )

    def before_import_row(self, row, **kwargs):
        # Convert empty strings to None for ForeignKey fields
        if 'parent' in row and row['parent'] == '':
            row['parent'] = None

            
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string

class EmployeeResource(resources.ModelResource):
    class Meta:
        model = Employee
        import_id_fields = ('employee_id',)
        fields = ('id', 'employee_id', 'email', 'first_name', 'middle_name', 'last_name', 
                  'department', 'role', 'date_of_birth', 'date_joined', 'date_of_confirmation', 'ippis_number', 
                  'gender', 'access_type',  'is_active', 'is_staff', 'is_superuser',  'password')
        export_order = fields[:len(fields)-1]  # Exclude password from export

    department = fields.Field(
        column_name='department',
        attribute='department',
        widget=ForeignKeyWidget(Department, 'name')
    )

    def before_import_row(self, row, **kwargs):
        # Convert empty strings to None for ForeignKey fields
        if 'department' in row and row['department'] == '':
            row['department'] = None

        # Generate a random password if not provided
        if 'password' not in row or not row['password']:
            row['password'] = get_random_string(length=12)
        
        # Hash the password
        row['password'] = make_password(row['password'])

        # Convert string boolean values to actual booleans
        for bool_field in ['is_active', 'is_staff', 'is_superuser']:
            if bool_field in row:
                row[bool_field] = row[bool_field].lower() in ('true', 'yes', '1')

    def after_import_instance(self, instance, new, **kwargs):
        # If this is a new instance, save the plain text password temporarily
        if new:
            instance._password = kwargs['row']['password']

    def after_import_row(self, row, row_result, **kwargs):
        if row_result.import_type == 'new':
            # Log the employee_id and plain text password
            print(f"Created employee: {row['employee_id']}, Password: {row['password']}")
            # In a real-world scenario, you might want to email this to the user
            # or save it securely for admin to distribute

    def get_export_fields(self):
        # Don't include password in exports
        return [field for field in self.get_fields() if field.column_name != 'password']


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    resource_class = DepartmentResource
    list_display = ('code', 'name', 'type', 'parent')
    list_filter = ('type', 'parent')
    search_fields = ('code', 'name')


@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    list_display = ('employee_id', 'first_name', 'last_name', 'email', 'department', 'role', 'date_joined', 'is_active')
    list_filter = ('department', 'role', 'date_joined', 'is_active', 'gender', 'access_type')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email', 'ippis_number')


    
admin.site.register(EmployeeChangeLog)