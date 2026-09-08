from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'employee_id', 'role', 'department', 'position', 'status']
    list_filter  = ['role', 'department', 'status']
    search_fields = ['full_name', 'email', 'employee_id']