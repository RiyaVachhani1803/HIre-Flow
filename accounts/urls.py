from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('login/hr/', views.login_hr, name='login_hr'),
    path('login/employee/', views.login_employee, name='login_employee'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-id/', views.forgot_id, name='forgot_id'),
]