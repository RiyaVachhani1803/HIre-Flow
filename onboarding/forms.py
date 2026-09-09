from django import forms
from .models import Document, Task, Attendance, LeaveRequest, Salary
from accounts.models import Employee


INPUT_CLASS  = 'form-control'
SELECT_CLASS = 'form-select'

# Reusable empty-label queryset field for Employee dropdowns
def employee_select(label='Select Employee'):
    return forms.ModelChoiceField(
        queryset=Employee.objects.filter(role='EMPLOYEE'),
        empty_label=label,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
    )


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
    document_type = forms.ChoiceField(
        choices=Document.DOCUMENT_TYPES,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        label="Document Type"
    )

    class Meta:
        model  = Document
        fields = ['document_type', 'file']
        widgets = {
            'file'         : forms.FileInput(attrs={'class': INPUT_CLASS}),
        }


class AssignTaskForm(forms.ModelForm):
    employee = employee_select('Select Employee')

    class Meta:
        model  = Task
        fields = ['employee', 'title', 'description']
        widgets = {
            'title'      : forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }


# ─── ATTENDANCE FORMS ─────────────────────────────────────────────────────────

class AttendanceMarkForm(forms.ModelForm):
    """HR marks attendance for an employee."""
    employee = employee_select('Select Employee')

    class Meta:
        model  = Attendance
        fields = ['employee', 'date', 'status', 'check_in', 'check_out', 'remarks']
        widgets = {
            'date'     : forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'status'   : forms.Select(attrs={'class': SELECT_CLASS}),
            'check_in' : forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time', 'value': '00:00'}),
            'check_out': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time', 'value': '00:00'}),
            'remarks'  : forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Optional remark'}),
        }


class AttendanceSelfForm(forms.ModelForm):
    """Employee marks their own attendance (check-in/out only)."""
    class Meta:
        model  = Attendance
        fields = ['check_in', 'check_out', 'remarks']
        widgets = {
            'check_in' : forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time', 'value': '00:00'}),
            'check_out': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time', 'value': '00:00'}),
            'remarks'  : forms.TextInput(attrs={'class': INPUT_CLASS}),
        }


# ─── LEAVE FORMS ─────────────────────────────────────────────────────────────

class LeaveRequestForm(forms.ModelForm):
    """Employee applies for leave."""
    leave_type = forms.ChoiceField(
        choices=[('', 'Select')] + LeaveRequest.LEAVE_TYPES,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        label="Leave Type"
    )

    class Meta:
        model  = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Select start date'}),
            'end_date'  : forms.DateInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Select end date'}),
            'reason'    : forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }


class LeaveReviewForm(forms.ModelForm):
    """HR approves or rejects a leave request."""
    class Meta:
        model  = LeaveRequest
        fields = ['status', 'hr_remarks']
        widgets = {
            'status'    : forms.Select(attrs={'class': SELECT_CLASS}),
            'hr_remarks': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 2}),
        }


# ─── SALARY FORMS ─────────────────────────────────────────────────────────────

MONTH_CHOICES = [
    (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
    (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
    (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
]

class SalaryForm(forms.ModelForm):
    employee = employee_select('Select Employee')
    month    = forms.ChoiceField(choices=MONTH_CHOICES, widget=forms.Select(attrs={'class': SELECT_CLASS}))

    class Meta:
        model  = Salary
        fields = ['employee', 'month', 'year', 'basic_salary', 'hra', 'allowances', 'deductions', 'paid', 'remarks']
        widgets = {
            'year'        : forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 2020, 'max': 2100}),
            'basic_salary': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'hra'         : forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'allowances'  : forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'deductions'  : forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'paid'        : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remarks'     : forms.TextInput(attrs={'class': INPUT_CLASS}),
        }