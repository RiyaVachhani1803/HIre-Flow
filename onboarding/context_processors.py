from accounts.models import Employee

def user_role(request):
    """Inject is_hr and is_employee into every template context."""
    is_hr       = False
    is_employee = False
    if request.user.is_authenticated:
        try:
            emp         = Employee.objects.get(user=request.user)
            is_hr       = emp.role == 'HR'
            is_employee = emp.role == 'EMPLOYEE'
        except Employee.DoesNotExist:
            pass
    return {'is_hr': is_hr, 'is_employee': is_employee}
