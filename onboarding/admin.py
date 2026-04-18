from django.contrib import admin
from .models import Document, Task

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'document_type', 'verified', 'uploaded_at']
    list_filter   = ['verified', 'document_type']
    search_fields = ['employee__full_name']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display  = ['title', 'employee', 'completed', 'assigned_at']
    list_filter   = ['completed']
    search_fields = ['title', 'employee__full_name']