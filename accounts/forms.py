from django import forms

DEPARTMENT_CHOICES = [
    ('', 'Select Department'),
    ('Engineering', 'Engineering'),
    ('Marketing', 'Marketing'),
    ('Sales', 'Sales'),
    ('Human Resources', 'Human Resources'),
    ('Finance', 'Finance'),
    ('Operations', 'Operations'),
    ('IT Support', 'IT Support'),
    ('Customer Service', 'Customer Service'),
    ('Product Management', 'Product Management'),
    ('Quality Assurance', 'Quality Assurance'),
]

class SignupForm(forms.Form):
    role         = forms.ChoiceField(choices=[('EMPLOYEE','Employee'),('HR','HR')])
    first_name   = forms.CharField(max_length=50)
    last_name    = forms.CharField(max_length=50)
    email        = forms.EmailField()
    phone        = forms.CharField(max_length=15, required=False)
    department   = forms.ChoiceField(choices=DEPARTMENT_CHOICES)
    position     = forms.CharField(max_length=100)
    joining_date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    password     = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class HRLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    hr_id    = forms.CharField()


class EmployeeLoginForm(forms.Form):
    username    = forms.CharField()
    password    = forms.CharField(widget=forms.PasswordInput)
    employee_id = forms.CharField()