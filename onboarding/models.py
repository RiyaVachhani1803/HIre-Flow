from django.db import models
from accounts.models import Employee

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('resume', 'Resume'),
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.document_type}"


class Task(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} → {self.employee.full_name}"
    

# ─── ATTENDANCE ───────────────────────────────────────────────────────────────

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('work_from_home', 'Work From Home'),
    ]
    employee  = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date      = models.DateField()
    status    = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    check_in  = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    remarks   = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.status}"


# ─── LEAVE REQUEST ────────────────────────────────────────────────────────────

class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('sick',      'Sick Leave'),
        ('casual',    'Casual Leave'),
        ('earned',    'Earned Leave'),
        ('unpaid',    'Unpaid Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
    ]
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type  = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date  = models.DateField()
    end_date    = models.DateField()
    reason      = models.TextField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_on  = models.DateTimeField(auto_now_add=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)
    hr_remarks  = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.start_date})"

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1


# ─── SALARY ───────────────────────────────────────────────────────────────────

class Salary(models.Model):
    MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    month        = models.IntegerField()
    year         = models.IntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hra          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid         = models.BooleanField(default=False)
    paid_on      = models.DateField(null=True, blank=True)
    remarks      = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.employee.full_name} - {self.MONTH_NAMES[self.month]} {self.year}"

    @property
    def month_name(self):
        return self.MONTH_NAMES[self.month]

    def save(self, *args, **kwargs):
        self.net_salary = self.basic_salary + self.hra + self.allowances - self.deductions
        super().save(*args, **kwargs)
