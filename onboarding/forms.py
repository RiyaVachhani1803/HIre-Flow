from django import forms
from .models import Document, Task
from accounts.models import Employee

INPUT_CLASS  = 'form-control'
SELECT_CLASS = 'form-select'

class AddEmployeeForm(forms.ModelForm):
    class Meta:
        model  = Employee
        fields = ['full_name', 'email', 'department',
                  'position', 'joining_date', 'status', 'resume']
        widgets = {
            'full_name'    : forms.TextInput(attrs={'class': INPUT_CLASS}),
            'email'        : forms.EmailInput(attrs={'class': INPUT_CLASS}),
            'department'   : forms.TextInput(attrs={'class': INPUT_CLASS}),
            'position'     : forms.TextInput(attrs={'class': INPUT_CLASS}),
            'joining_date' : forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'status'       : forms.Select(attrs={'class': SELECT_CLASS}),
            'resume'       : forms.FileInput(attrs={'class': INPUT_CLASS}),
        }


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model  = Document
        fields = ['document_type', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'file'         : forms.FileInput(attrs={'class': INPUT_CLASS}),
        }


class AssignTaskForm(forms.ModelForm):
    class Meta:
        model  = Task
        fields = ['employee', 'title', 'description']
        widgets = {
            'employee'   : forms.Select(attrs={'class': SELECT_CLASS}),
            'title'      : forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }