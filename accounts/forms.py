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

POSITION_CHOICES = [
    ('', 'Select Position'),
    ('Software Engineer', 'Software Engineer'),
    ('Frontend Developer', 'Frontend Developer'),
    ('Backend Developer', 'Backend Developer'),
    ('Full Stack Developer', 'Full Stack Developer'),
    ('UI/UX Designer', 'UI/UX Designer'),
    ('DevOps Engineer', 'DevOps Engineer'),
    ('QA Engineer', 'QA Engineer'),
    ('HR Associate', 'HR Associate'),
    ('HR Manager', 'HR Manager'),
    ('Sales Executive', 'Sales Executive'),
    ('Sales Manager', 'Sales Manager'),
    ('Marketing Specialist', 'Marketing Specialist'),
    ('Marketing Manager', 'Marketing Manager'),
    ('Financial Analyst', 'Financial Analyst'),
    ('Accountant', 'Accountant'),
    ('Operations Manager', 'Operations Manager'),
    ('IT Support Specialist', 'IT Support Specialist'),
    ('Customer Success Specialist', 'Customer Success Specialist'),
    ('Product Manager', 'Product Manager'),
    ('Founder & CEO', 'Founder & CEO'),
]

class SignupForm(forms.Form):
    role         = forms.ChoiceField(choices=[('EMPLOYEE','Employee'),('HR','HR')])
    first_name   = forms.CharField(max_length=50)
    last_name    = forms.CharField(max_length=50)
    email        = forms.EmailField()
    phone        = forms.CharField(max_length=15, required=True)
    department   = forms.ChoiceField(choices=DEPARTMENT_CHOICES)
    position     = forms.ChoiceField(choices=POSITION_CHOICES)
    joining_date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    password     = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        cleaned_digits = phone.replace('+', '')
        if not cleaned_digits.isdigit() or len(cleaned_digits) < 10 or len(cleaned_digits) > 13:
            raise forms.ValidationError("Please enter a valid Phone Number.")
        return phone

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