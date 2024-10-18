from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Zone, State, LGA, Department, Division, GradeLevel,
    OfficialAppointment, Bank, PFA, Employee, 
)


# Model Admins

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'email', 'current_role', 'active_status')
    search_fields = ('first_name','employee_id')
    
    
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



# Register your models here
admin.site.register(Zone, ZoneAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(LGA, LGAAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Division, DivisionAdmin)
admin.site.register(GradeLevel, GradeLevelAdmin)
admin.site.register(OfficialAppointment, OfficialAppointmentAdmin)
admin.site.register(Bank, BankAdmin)
admin.site.register(PFA, PFAAdmin)