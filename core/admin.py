from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Zone, State, LGA, Department, Division, GradeLevel,
    OfficialAppointment, Bank, PFA, Employee, File, FileTransfer
)


# Model Admins
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'zone')
    search_fields = ('name', 'code')
    list_filter = ('zone',)

class LGAAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'code')
    search_fields = ('name', 'state__name')
    list_filter = ('state',)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department')
    search_fields = ('name', 'code', 'department__name')
    list_filter = ('department',)

class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ('level', 'name', 'description')
    search_fields = ('name', 'description')

class OfficialAppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_level', 'cadre', 'department')


class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class PFAAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_number', 'first_name', 'surname', 'department')
    search_fields = ('user__employee_id', 'file_number', 'first_name', 'surname', 'department__name')
    list_filter = ('department', 'state_of_posting', 'station')

class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'file_type', 'file_size', 'origin', 'current_location', 'status')
    search_fields = ('file_name', 'origin', 'current_location')
    list_filter = ('status',)

class FileTransferAdmin(admin.ModelAdmin):
    list_display = ('file', 'sender', 'recipient', 'transfer_date', 'transfer_method')
    search_fields = ('file__file_name', 'sender__employee_id', 'recipient__employee_id')
    list_filter = ('transfer_date',)

# Register your models here
admin.site.register(Zone, ZoneAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(LGA, LGAAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Division, DivisionAdmin)
admin.site.register(GradeLevel, GradeLevelAdmin)
admin.site.register(OfficialAppointment, OfficialAppointmentAdmin)
admin.site.register(Bank, BankAdmin)
admin.site.register(PFA, PFAAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(FileTransfer, FileTransferAdmin)