from django.urls import path
from . import views

urlpatterns = [
    # Dashboard quick-view URLs
    path('hr/dash/employees/',     views.dash_employees,     name='dash_employees'),
    path('hr/dash/verified-docs/', views.dash_verified_docs, name='dash_verified_docs'),
    path('hr/dash/pending-docs/',  views.dash_pending_docs,  name='dash_pending_docs'),
    path('hr/dash/pending-tasks/', views.dash_pending_tasks, name='dash_pending_tasks'),
    path('hr/dash/pending-leaves/',views.dash_pending_leaves,name='dash_pending_leaves'),

    # HR URLs
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/employees/', views.employee_list, name='employee_list'),
    path('hr/employee/<int:pk>/', views.employee_profile, name='employee_profile'),
    path('hr/add-employee/', views.add_employee, name='add_employee'),
    path('hr/documents/', views.document_list, name='document_list'),
    path('hr/document/verify/<int:pk>/', views.verify_document, name='verify_document'),
    path('hr/documents/<int:pk>/reject/', views.reject_document, name='reject_document'),
    path('hr/assign-task/', views.assign_task, name='assign_task'),
    path('hr/analytics/', views.analytics, name='analytics'),

    # Employee URLs
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/upload-document/', views.upload_document, name='upload_document'),
    path('employee/tasks/', views.employee_tasks, name='employee_tasks'),
    path('employee/complete-task/<int:pk>/', views.complete_task, name='complete_task'),

    # ── HR: Attendance 
    path('hr/attendance/', views.hr_attendance, name='hr_attendance'),

    # ── HR: Leave 
    path('hr/leaves/', views.hr_leaves, name='hr_leaves'),
    path('hr/leaves/<int:pk>/review/', views.hr_leave_review, name='hr_leave_review'),

    # ── HR: Salary 
    path('hr/salary/',  views.hr_salary, name='hr_salary'),
    path('hr/salary/<int:pk>/mark-paid/', views.mark_salary_paid, name='mark_salary_paid'),

    # ── Employee: Attendance 
    path('employee/attendance/', views.employee_attendance, name='employee_attendance'),

    # ── Employee: Leave 
    path('employee/leave/', views.employee_leave,name='employee_leave'),

    # ── Employee: Salary 
    path('employee/salary/', views.employee_salary, name='employee_salary'),

    # ── Employee: Profile & Resume 
    path('employee/profile/', views.employee_profile_view, name='employee_profile_view'),
    path('employee/upload-resume/',  views.upload_resume, name='upload_resume'),
]