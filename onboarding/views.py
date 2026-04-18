import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from accounts.models import Employee
from .models import Document, Task
from .forms import AddEmployeeForm, DocumentUploadForm, AssignTaskForm


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
    pending_docs = Document.objects.filter(verified=False).count()
    verified_docs = Document.objects.filter(verified=True).count()
    pending_tasks = Task.objects.filter(completed=False).count()
    return render(request, 'hr_dashboard.html', {
        'total_employees': total,
        'pending_docs':    pending_docs,
        'verified_docs':   verified_docs,
        'pending_tasks':   pending_tasks,
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
    return render(request, 'employee_profile.html', {
        'employee':  employee,
        'documents': documents,
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

            messages.success(
                request,
                f"Employee added! ID: {emp_id} | Default password: HireFlow@1234"
            )
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

from django.shortcuts import get_object_or_404, redirect
from .models import Document  # make sure this is correct

def reject_document(request, pk):
    if request.method == "POST":
        document = get_object_or_404(Document, id=pk)
        reason = request.POST.get('reason')
        document.status = 'rejected'
        document.rejection_reason = reason
        document.save()
    return redirect('/hr/documents/')


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
    from django.db.models import Count

    total_employees = Employee.objects.filter(role='EMPLOYEE').count()
    verified_docs   = Document.objects.filter(verified=True).count()
    pending_docs    = Document.objects.filter(verified=False).count()

    dept_data   = (
        Employee.objects
        .filter(role='EMPLOYEE')
        .values('department')
        .annotate(count=Count('id'))
    )
    departments = [d['department'] for d in dept_data]
    counts      = [d['count']      for d in dept_data]

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
    form = DocumentUploadForm()
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc          = form.save(commit=False)
            doc.employee = Employee.objects.get(user=request.user)
            doc.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('employee_dashboard')
    return render(request, 'upload_document.html', {'form': form})


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