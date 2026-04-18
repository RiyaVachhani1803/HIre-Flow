from django.contrib import admin
from .models import Document, Task, Attendance, LeaveRequest, Salary


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'document_type', 'verified', 'rejected', 'uploaded_at')
    list_filter   = ('document_type', 'verified', 'rejected')
    search_fields = ('employee__full_name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display  = ('title', 'employee', 'completed', 'assigned_at')
    list_filter   = ('completed',)
    search_fields = ('employee__full_name', 'title')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'date', 'status', 'check_in', 'check_out')
    list_filter   = ('status', 'date')
    search_fields = ('employee__full_name',)
    date_hierarchy = 'date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'applied_on')
    list_filter   = ('status', 'leave_type')
    search_fields = ('employee__full_name',)


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'month', 'year', 'basic_salary', 'net_salary', 'paid')
    list_filter   = ('paid', 'year', 'month')
    search_fields = ('employee__full_name',)
