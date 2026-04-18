from django.urls import path
from . import views

urlpatterns = [
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
]