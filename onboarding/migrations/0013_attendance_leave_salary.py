from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0012_document_rejected_document_rejection_reason'),
        ('accounts', '0002_employee_delete_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('present', 'Present'),
                        ('absent', 'Absent'),
                        ('half_day', 'Half Day'),
                        ('work_from_home', 'Work From Home'),
                    ],
                    default='present'
                )),
                ('check_in', models.TimeField(null=True, blank=True)),
                ('check_out', models.TimeField(null=True, blank=True)),
                ('remarks', models.CharField(max_length=200, blank=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendance_records',
                    to='accounts.employee'
                )),
            ],
            options={
                'unique_together': {('employee', 'date')},
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='LeaveRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('sick', 'Sick Leave'),
                        ('casual', 'Casual Leave'),
                        ('earned', 'Earned Leave'),
                        ('unpaid', 'Unpaid Leave'),
                        ('maternity', 'Maternity Leave'),
                        ('paternity', 'Paternity Leave'),
                    ]
                )),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField()),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('pending', 'Pending'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                    ],
                    default='pending'
                )),
                ('applied_on', models.DateTimeField(auto_now_add=True)),
                ('reviewed_on', models.DateTimeField(null=True, blank=True)),
                ('hr_remarks', models.TextField(blank=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='leave_requests',
                    to='accounts.employee'
                )),
            ],
            options={
                'ordering': ['-applied_on'],
            },
        ),
        migrations.CreateModel(
            name='Salary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.IntegerField()),
                ('year', models.IntegerField()),
                ('basic_salary', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('hra', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('allowances', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('deductions', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('net_salary', models.DecimalField(max_digits=10, decimal_places=2, default=0)),
                ('paid', models.BooleanField(default=False)),
                ('paid_on', models.DateField(null=True, blank=True)),
                ('remarks', models.CharField(max_length=200, blank=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='salaries',
                    to='accounts.employee'
                )),
            ],
            options={
                'unique_together': {('employee', 'month', 'year')},
                'ordering': ['-year', '-month'],
            },
        ),
    ]
