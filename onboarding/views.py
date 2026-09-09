import random
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from accounts.models import Employee
from .models import Document, Task, Attendance, LeaveRequest, Salary
from .forms import (
    AddEmployeeForm, DocumentUploadForm, AssignTaskForm,
    AttendanceMarkForm, LeaveRequestForm, LeaveReviewForm, SalaryForm,
)


# ─── DECORATORS ─────────────────────────────────────────

def hr_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        try:
            Employee.objects.get(user=request.user, role='HR')
        except Employee.DoesNotExist:
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


def employee_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        try:
            Employee.objects.get(user=request.user, role='EMPLOYEE')
        except Employee.DoesNotExist:
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── HR VIEWS ───────────────────────────────────────────

@hr_required
def hr_dashboard(request):
    total        = Employee.objects.filter(role='EMPLOYEE').count()
    pending_docs = Document.objects.filter(verified=False, rejected=False).count()
    verified_docs = Document.objects.filter(verified=True).count()
    pending_tasks = Task.objects.filter(completed=False).count()
    pending_leave = LeaveRequest.objects.filter(status='pending').count()
    return render(request, 'hr_dashboard.html', {
        'total_employees': total,
        'pending_docs':    pending_docs,
        'verified_docs':   verified_docs,
        'pending_tasks':   pending_tasks,
        'pending_leave':   pending_leave,
    })

@hr_required
def employee_list(request):
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    # ✅ ALWAYS full data (for stats)
    all_employees = Employee.objects.filter(role='EMPLOYEE')

    # ✅ Filtered data (for table only)
    employees = all_employees

    if q:
        employees = employees.filter(full_name__icontains=q)

    if status_filter:
        employees = employees.filter(status=status_filter)

    # ✅ Counts from full data ONLY
    total_count = all_employees.count()
    active_count = all_employees.filter(status='active').count()
    onboarding_count = all_employees.filter(status='onboarding').count()
    inactive_count = all_employees.filter(status='inactive').count()

    return render(request, 'employee_list.html', {
        'employees': employees,  # table
        'q': q,
        'status_filter': status_filter,

        # stats (stable)
        'total_count': total_count,
        'active_count': active_count,
        'onboarding_count': onboarding_count,
        'inactive_count': inactive_count,
    })


@hr_required
def employee_profile(request, pk):
    employee  = get_object_or_404(Employee, pk=pk)
    documents = Document.objects.filter(employee=employee)
    skills = [s.strip() for s in employee.skills.split(',') if s.strip()] if employee.skills else []
    return render(request, 'employee_profile.html', {
        'employee':  employee,
        'documents': documents,
        'skills': skills,
    })


@hr_required
def add_employee(request):
    form = AddEmployeeForm()

    if request.method == 'POST':
        form = AddEmployeeForm(request.POST, request.FILES)

        if form.is_valid():
            data = form.cleaned_data

            # Check email not already used
            if User.objects.filter(email=data['email']).exists():
                messages.error(request, "An account with this email already exists.")
                return render(request, 'add_employee.html', {'form': form})

            # Split full_name into first / last
            name_parts = data['full_name'].strip().split()
            first_name = name_parts[0]
            last_name  = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            # Create Django User with default password
            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                password='HireFlow@1234',
                first_name=first_name,
                last_name=last_name,
            )

            # Generate Employee ID  (E + first2 + last2 + year + 4-digit random)
            last_for_id = last_name[:2].upper() if last_name else 'XX'
            year   = data['joining_date'].year
            emp_id = f"E{first_name[:2].upper()}{last_for_id}{year}{random.randint(1000, 9999)}"

            # Save Employee — attach the user we just created
            emp = form.save(commit=False)
            emp.user        = user
            emp.employee_id = emp_id
            emp.role        = 'EMPLOYEE'
            emp.full_name   = data['full_name']
            emp.save()

            # ── Auto-parse resume if uploaded ──────────────────────────────
            if emp.resume:
                try:
                    from .resume_parser import parse_resume_and_update_employee
                    result = parse_resume_and_update_employee(emp, emp.resume.path)
                    
                    # Also create a Document record so it appears in the documents list
                    Document.objects.get_or_create(
                        employee=emp,
                        document_type='resume',
                        defaults={'file': emp.resume, 'verified': True}
                    )

                    if result['skills']:
                        messages.info(request, f"Resume parsed! Skills found: {', '.join(result['skills'])}")
                except Exception as e:
                    messages.warning(request, f"Resume uploaded but skill parsing failed: {e}")

            messages.success(request, f"Employee added! ID: {emp_id} | Default password: HireFlow@1234")
            return redirect('employee_list')

    return render(request, 'add_employee.html', {'form': form})


@hr_required
def document_list(request):
    documents = Document.objects.select_related('employee').all()
    return render(request, 'document_list.html', {'documents': documents})


@hr_required
def verify_document(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.verified = True
    doc.rejected = False
    doc.rejection_reason = ""
    doc.save()

    # Update onboarding progress
    emp      = doc.employee
    total    = Document.objects.filter(employee=emp).count()
    verified = Document.objects.filter(employee=emp, verified=True).count()
    if total > 0:
        emp.onboarding_progress = int((verified / total) * 100)
        emp.save()

    messages.success(request, 'Document verified.')
    return redirect('document_list')

@hr_required
def reject_document(request, pk):
    if request.method == "POST":
        document = get_object_or_404(Document, id=pk)
        reason = request.POST.get('reason', '').strip()
        document.rejected = True
        document.verified = False
        document.rejection_reason = reason
        document.save()
        messages.warning(request, f"Document rejected: {reason or 'No reason provided'}")
    return redirect('document_list')


@hr_required
def assign_task(request):
    form = AssignTaskForm()
    if request.method == 'POST':
        form = AssignTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task assigned successfully.')
            return redirect('hr_dashboard')
    return render(request, 'assign_task.html', {'form': form})


@hr_required
def analytics(request):
    from django.db.models import Count, Sum

    total_employees = Employee.objects.filter(role='EMPLOYEE').count()
    verified_docs   = Document.objects.filter(verified=True).count()
    pending_docs    = Document.objects.filter(verified=False, rejected=False).count()
    dept_data       = Employee.objects.filter(role='EMPLOYEE').values('department').annotate(count=Count('id'))
    departments     = [d['department'] for d in dept_data]
    counts          = [d['count']      for d in dept_data]

    return render(request, 'analytics_dashboard.html', {
        'total_employees': total_employees,
        'verified_docs':   verified_docs,
        'pending_docs':    pending_docs,
        'departments':     departments,
        'counts':          counts,
    })


# ─── EMPLOYEE VIEWS ──────────────────────────────────────

@employee_required
def employee_dashboard(request):
    emp = Employee.objects.get(user=request.user)
    return render(request, 'employee_dashboard.html', {'employee': emp})


@employee_required
def upload_document(request):
    """Unified upload: handles documents + resume skill parsing."""
    emp = get_object_or_404(Employee, user=request.user)
    documents = Document.objects.filter(employee=emp).order_by('-uploaded_at')
    form = DocumentUploadForm()

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc          = form.save(commit=False)
            doc.employee = emp
            doc.save()
            doc.refresh_from_db()  # ensure file path is resolved

            messages.success(request, 'Document uploaded successfully.')

            if doc.document_type == 'resume':
                try:
                    from .resume_parser import parse_resume_and_update_employee
                    
                    # Sync to Employee.resume field
                    emp.resume = doc.file
                    emp.save(update_fields=['resume'])

                    result = parse_resume_and_update_employee(emp, doc.file.path)
                    emp.refresh_from_db()
                    if result['skills']:
                        messages.info(request, f"Skills extracted: {', '.join(result['skills'])}")
                    else:
                        messages.warning(request, "Resume uploaded but no skills could be extracted.")
                except Exception as e:
                    messages.warning(request, f"Skill parsing failed: {e}")

            return redirect('upload_document')

    return render(request, 'upload_document.html', {
        'form':      form,
        'employee':  emp,
        'documents': documents,
    })


@employee_required
def employee_tasks(request):
    emp   = Employee.objects.get(user=request.user)
    tasks = Task.objects.filter(employee=emp)
    return render(request, 'employee_tasks.html', {'tasks': tasks})


@employee_required
def complete_task(request, pk):
    task          = get_object_or_404(Task, pk=pk)
    task.completed = True
    task.save()
    return redirect('employee_tasks')



# ─── HR: ATTENDANCE ───────────────────────────────────────────────────────────

@hr_required
def hr_attendance(request):
    """HR views all attendance records, can filter by employee or date."""
    emp_id      = request.GET.get('employee')
    date_filter = request.GET.get('date')
    records     = Attendance.objects.select_related('employee').all()

    if emp_id:
        records = records.filter(employee_id=emp_id)
    if date_filter:
        records = records.filter(date=date_filter)

    employees = Employee.objects.filter(role='EMPLOYEE')
    form      = AttendanceMarkForm()

    if request.method == 'POST':
        form = AttendanceMarkForm(request.POST)
        if form.is_valid():
            # Use update_or_create so re-marking the same day just updates
            obj, created = Attendance.objects.update_or_create(
                employee=form.cleaned_data['employee'],
                date=form.cleaned_data['date'],
                defaults={
                    'status':    form.cleaned_data['status'],
                    'check_in':  form.cleaned_data['check_in'],
                    'check_out': form.cleaned_data['check_out'],
                    'remarks':   form.cleaned_data['remarks'],
                }
            )
            messages.success(request, f"Attendance {'marked' if created else 'updated'} successfully.")
            return redirect('hr_attendance')

    return render(request, 'hr_attendance.html', {
        'records':   records[:100],   # latest 100
        'employees': employees,
        'form':      form,
        'emp_id':    emp_id,
        'date_filter': date_filter,
    })


# ─── HR: LEAVE MANAGEMENT ─────────────────────────────────────────────────────

@hr_required
def hr_leaves(request):
    """HR sees all leave requests and can approve / reject."""
    status_filter = request.GET.get('status', '')
    leaves = LeaveRequest.objects.select_related('employee').all()
    if status_filter:
        leaves = leaves.filter(status=status_filter)

    return render(request, 'hr_leaves.html', {
        'leaves':        leaves,
        'status_filter': status_filter,
        'pending_count': LeaveRequest.objects.filter(status='pending').count(),
    })


@hr_required
def hr_leave_review(request, pk):
    """HR approves or rejects a single leave request."""
    leave = get_object_or_404(LeaveRequest, pk=pk)
    form  = LeaveReviewForm(instance=leave)

    if request.method == 'POST':
        form = LeaveReviewForm(request.POST, instance=leave)
        if form.is_valid():
            obj             = form.save(commit=False)
            obj.reviewed_on = timezone.now()
            obj.save()
            messages.success(request, f"Leave request {obj.status}.")
            return redirect('hr_leaves')

    return render(request, 'hr_leave_review.html', {'leave': leave, 'form': form})


# ─── HR: SALARY ───────────────────────────────────────────────────────────────

@hr_required
def hr_salary(request):
    """HR views and manages all salary records."""
    emp_filter  = request.GET.get('employee')
    year_filter = request.GET.get('year')
    salaries    = Salary.objects.select_related('employee').all()

    if emp_filter:
        salaries = salaries.filter(employee_id=emp_filter)
    if year_filter:
        salaries = salaries.filter(year=year_filter)

    employees   = Employee.objects.filter(role='EMPLOYEE')
    total_paid  = salaries.filter(paid=True).aggregate(total=Sum('net_salary'))['total'] or 0
    form        = SalaryForm()

    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            obj, created = Salary.objects.update_or_create(
                employee=form.cleaned_data['employee'],
                month=form.cleaned_data['month'],
                year=form.cleaned_data['year'],
                defaults={
                    'basic_salary': form.cleaned_data['basic_salary'],
                    'hra':          form.cleaned_data['hra'],
                    'allowances':   form.cleaned_data['allowances'],
                    'deductions':   form.cleaned_data['deductions'],
                    'paid':         form.cleaned_data['paid'],
                    'remarks':      form.cleaned_data['remarks'],
                }
            )
            messages.success(request, f"Salary record {'created' if created else 'updated'}.")
            return redirect('hr_salary')

    return render(request, 'hr_salary.html', {
        'salaries':   salaries,
        'employees':  employees,
        'total_paid': total_paid,
        'form':       form,
        'emp_filter': emp_filter,
        'year_filter': year_filter,
    })


@hr_required
def mark_salary_paid(request, pk):
    salary         = get_object_or_404(Salary, pk=pk)
    salary.paid    = True
    salary.paid_on = timezone.now().date()
    salary.save()
    messages.success(request, "Salary marked as paid.")
    return redirect('hr_salary')



# ─── EMPLOYEE: ATTENDANCE ─────────────────────────────────────────────────────

@employee_required
def employee_attendance(request):
    """Employee views their own attendance history."""
    emp     = Employee.objects.get(user=request.user)
    records = Attendance.objects.filter(employee=emp)
    leaves  = LeaveRequest.objects.filter(employee=emp, status='approved')

    # Quick stats for current month
    from django.utils import timezone as tz
    today  = tz.now().date()
    month_records = records.filter(date__year=today.year, date__month=today.month)
    present_days  = month_records.filter(status__in=['present', 'work_from_home', 'half_day']).count()
    absent_days   = month_records.filter(status='absent').count()

    return render(request, 'employee_attendance.html', {
        'employee':     emp,
        'records':      records[:60],
        'leaves':       leaves,
        'present_days': present_days,
        'absent_days':  absent_days,
    })


# ─── EMPLOYEE: LEAVE ──────────────────────────────────────────────────────────

@employee_required
def employee_leave(request):
    """Employee applies for leave and views their leave history."""
    emp    = Employee.objects.get(user=request.user)
    leaves = LeaveRequest.objects.filter(employee=emp)
    form   = LeaveRequestForm()

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave          = form.save(commit=False)
            leave.employee = emp
            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect('employee_leave')

    return render(request, 'employee_leave.html', {
        'employee': emp,
        'leaves':   leaves,
        'form':     form,
    })


# ─── EMPLOYEE: SALARY ─────────────────────────────────────────────────────────

@employee_required
def employee_salary(request):
    """Employee views their own salary slips (read-only)."""
    emp      = Employee.objects.get(user=request.user)
    salaries = Salary.objects.filter(employee=emp)
    return render(request, 'employee_salary.html', {
        'employee': emp,
        'salaries': salaries,
    })


# ─── EMPLOYEE: PROFILE / SKILLS ───────────────────────────────────────────────

@employee_required
def employee_profile_view(request):
    """Employee views their own profile with extracted skills."""
    emp    = Employee.objects.get(user=request.user)
    skills = [s.strip() for s in emp.skills.split(',') if s.strip()] if emp.skills else []
    return render(request, 'employee_profile_self.html', {
        'employee': emp,
        'skills':   skills,
    })


@employee_required
def upload_resume(request):
    """Redirect to unified upload page, pre-selecting resume type."""
    return redirect('upload_document')


# ─── DASHBOARD QUICK-VIEW PAGES ───────────────────────────────────────────────

@hr_required
def dash_employees(request):
    employees = Employee.objects.filter(role='EMPLOYEE').order_by('full_name').values(
        'id', 'full_name', 'employee_id', 'joining_date', 'department'
    )
    return render(request, 'dash_employees.html', {'employees': employees})


@hr_required
def dash_verified_docs(request):
    documents = Document.objects.filter(verified=True).select_related('employee').order_by('-uploaded_at')
    return render(request, 'dash_verified_docs.html', {'documents': documents})


@hr_required
def dash_pending_docs(request):
    documents = Document.objects.filter(verified=False, rejected=False).select_related('employee').order_by('-uploaded_at')
    return render(request, 'dash_pending_docs.html', {'documents': documents})


@hr_required
def dash_pending_tasks(request):
    tasks = Task.objects.filter(completed=False).select_related('employee').order_by('employee__full_name')
    return render(request, 'dash_pending_tasks.html', {'tasks': tasks})


@hr_required
def dash_pending_leaves(request):
    leaves = LeaveRequest.objects.filter(status='pending').select_related('employee').order_by('-applied_on')
    return render(request, 'dash_pending_leaves.html', {'leaves': leaves})