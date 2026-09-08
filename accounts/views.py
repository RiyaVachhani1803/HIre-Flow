from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignupForm, HRLoginForm, EmployeeLoginForm
from .models import Employee
import random


def generate_employee_id(role, first, last, year):
    prefix = 'E' if role == 'EMPLOYEE' else 'H'
    f = first[:2].upper() if len(first) >= 2 else first.upper()
    l = last[:2].upper()  if len(last)  >= 2 else last.upper()
    code = random.randint(1000, 9999)
    return f"{prefix}{f}{l}{year}{code}"


def home(request):
    return render(request, 'home.html')


# ✅ SIGNUP
def signup_view(request):
    form = SignupForm()

    if request.method == 'POST':
        form = SignupForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            # Check if email already registered
            if User.objects.filter(username=data['email']).exists():
                messages.error(request, "Email already registered. Please login.")
                return render(request, 'signup.html', {'form': form})

            # Create Django user
            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
            )

            # Use ID from frontend if available, otherwise generate fresh
            year   = data['joining_date'].year
            emp_id = (
                request.POST.get('employee_id_preview')
                or generate_employee_id(data['role'], data['first_name'], data['last_name'], year)
            )

            # Save Employee profile
            Employee.objects.create(
                user=user,
                employee_id=emp_id,
                role=data['role'],
                full_name=f"{data['first_name']} {data['last_name']}",
                email=data['email'],
                phone=data['phone'],
                department=data['department'],
                position=data['position'],
                joining_date=data['joining_date'],
            )

            # Store ID in session and redirect to success page
            request.session['employee_id'] = emp_id
            return redirect('signup_success')

    return render(request, 'signup.html', {'form': form})


# ✅ SUCCESS PAGE
def signup_success(request):
    emp_id = request.session.get('employee_id')

    # Remove from session after showing once
    request.session.pop('employee_id', None)

    return render(request, 'signup_success.html', {
        'employee_id': emp_id
    })


# ✅ HR LOGIN
def login_hr(request):
    form = HRLoginForm()

    if request.method == 'POST':
        form = HRLoginForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            user = authenticate(
                request,
                username=data['username'],
                password=data['password']
            )

            if user:
                try:
                    emp = Employee.objects.get(
                        user=user,
                        role='HR',
                        employee_id=data['hr_id']
                    )
                    login(request, user)
                    return redirect('/hr/dashboard/')
                except Employee.DoesNotExist:
                    messages.error(request, "Invalid HR ID or not an HR account.")
            else:
                messages.error(request, "Invalid email or password.")

    return render(request, 'login_hr.html', {'form': form})


# ✅ EMPLOYEE LOGIN
def login_employee(request):
    form = EmployeeLoginForm()

    if request.method == 'POST':
        form = EmployeeLoginForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            user = authenticate(
                request,
                username=data['username'],
                password=data['password']
            )

            if user:
                try:
                    emp = Employee.objects.get(
                        user=user,
                        role='EMPLOYEE',
                        employee_id=data['employee_id']
                    )
                    login(request, user)
                    return redirect('/employee/dashboard/')
                except Employee.DoesNotExist:
                    messages.error(request, "Invalid Employee ID or not an employee account.")
            else:
                messages.error(request, "Invalid email or password.")

    return render(request, 'login_employee.html', {'form': form})


# ✅ LOGOUT
def logout_view(request):
    logout(request)
    return redirect('/')


# ✅ FORGOT PASSWORD
def forgot_password(request):
    sent = False
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        sent = True
    return render(request, 'forgot_password.html', {'sent': sent})

def forgot_id(request):
    found_id = None
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            emp = Employee.objects.get(email=email)
            found_id = emp.employee_id
        except Employee.DoesNotExist:
            error = "No account found with that email address."
    return render(request, 'forgot_id.html', {'found_id': found_id, 'error': error})