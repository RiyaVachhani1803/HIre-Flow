from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
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
        
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            reset_url = f"{protocol}://{domain}/reset-password/{uid}/{token}/"
            
            subject = "Password Reset Request - HireFlow"
            message = (
                f"Hello {user.first_name},\n\n"
                f"You requested a password reset for your HireFlow account.\n"
                f"Please click the link below to set a new password:\n\n"
                f"{reset_url}\n\n"
                f"If you did not request this, please ignore this email.\n\n"
                f"Best regards,\n"
                f"HireFlow Team"
            )
            
            send_mail(
                subject,
                message,
                'no-reply@hireflow.com',
                [email],
                fail_silently=False,
            )
        except User.DoesNotExist:
            pass
            
        sent = True
        
    return render(request, 'forgot_password.html', {'sent': sent})


# ✅ RESET PASSWORD CONFIRM
def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    valid_link = False
    if user and default_token_generator.check_token(user, token):
        valid_link = True

    if request.method == 'POST' and valid_link:
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if not password or not confirm_password:
            messages.error(request, "Please enter both password fields.")
        elif password == confirm_password:
            user.set_password(password)
            user.save()
            messages.success(request, "Your password has been successfully reset. Please log in.")
            return redirect('/')
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, 'reset_password_confirm.html', {
        'valid_link': valid_link,
        'uidb64': uidb64,
        'token': token
    })

def forgot_id(request):
    found_id = None
    error = None
    active_tab = 'pwd'
    
    if request.GET.get('tab') == 'id':
        active_tab = 'id'
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            emp = Employee.objects.get(email=email)
            found_id = emp.employee_id
        except Employee.DoesNotExist:
            error = "No account found with that email address."
        active_tab = 'id'
        
    return render(request, 'forgot_id.html', {
        'found_id': found_id,
        'error': error,
        'active_tab': active_tab
    })