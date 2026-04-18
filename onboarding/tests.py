"""
Tests for the HireFlow onboarding app.
Covers: models, views (HR + Employee), resume parser utilities.
"""
import datetime
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import Employee
from .models import Document, Task, Attendance, LeaveRequest, Salary
from .resume_parser import extract_skills, calculate_match


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def make_user(email, password="pass1234"):
    return User.objects.create_user(username=email, email=email, password=password)


def make_employee(user, role="EMPLOYEE", **kwargs):
    defaults = dict(
        employee_id=f"E{user.pk:04d}",
        role=role,
        full_name=f"{user.first_name} {user.last_name}".strip() or user.username,
        email=user.email,
        department="Engineering",
        position="Developer",
        joining_date=datetime.date(2024, 1, 1),
    )
    defaults.update(kwargs)
    return Employee.objects.create(user=user, **defaults)


def make_hr():
    u = make_user("hr@example.com", "hrpass")
    return make_employee(u, role="HR", employee_id="HRTEST001")


def make_emp():
    u = make_user("emp@example.com", "emppass")
    u.first_name = "John"
    u.save()
    return make_employee(u, role="EMPLOYEE", employee_id="ETEST001")


# ─── MODEL TESTS ──────────────────────────────────────────────────────────────

class EmployeeModelTest(TestCase):
    def test_str(self):
        emp = make_emp()
        self.assertIn("ETEST001", str(emp))

    def test_default_status(self):
        emp = make_emp()
        self.assertEqual(emp.status, "onboarding")


class SalaryModelTest(TestCase):
    def setUp(self):
        self.emp = make_emp()

    def test_net_salary_calculated_on_save(self):
        s = Salary.objects.create(
            employee=self.emp, month=1, year=2024,
            basic_salary=50000, hra=10000, allowances=5000, deductions=3000
        )
        self.assertEqual(s.net_salary, 62000)

    def test_month_name_property(self):
        s = Salary(employee=self.emp, month=3, year=2024)
        self.assertEqual(s.month_name, "March")

    def test_unique_together_employee_month_year(self):
        from django.db import IntegrityError
        Salary.objects.create(employee=self.emp, month=1, year=2024, net_salary=40000)
        with self.assertRaises(IntegrityError):
            Salary.objects.create(employee=self.emp, month=1, year=2024, net_salary=50000)


class LeaveRequestModelTest(TestCase):
    def setUp(self):
        self.emp = make_emp()

    def test_days_property(self):
        lr = LeaveRequest(
            employee=self.emp, leave_type="sick",
            start_date=datetime.date(2024, 3, 1),
            end_date=datetime.date(2024, 3, 5),
            reason="Flu",
        )
        self.assertEqual(lr.days, 5)

    def test_default_status_pending(self):
        lr = LeaveRequest.objects.create(
            employee=self.emp, leave_type="casual",
            start_date=datetime.date(2024, 4, 1),
            end_date=datetime.date(2024, 4, 2),
            reason="Personal",
        )
        self.assertEqual(lr.status, "pending")


class AttendanceModelTest(TestCase):
    def setUp(self):
        self.emp = make_emp()

    def test_unique_together_employee_date(self):
        from django.db import IntegrityError
        Attendance.objects.create(employee=self.emp, date=datetime.date(2024, 1, 10))
        with self.assertRaises(IntegrityError):
            Attendance.objects.create(employee=self.emp, date=datetime.date(2024, 1, 10))


class DocumentModelTest(TestCase):
    def setUp(self):
        self.emp = make_emp()

    def test_str(self):
        doc = Document(employee=self.emp, document_type="resume")
        self.assertIn("resume", str(doc))

    def test_default_not_verified(self):
        doc = Document.objects.create(
            employee=self.emp, document_type="id_proof", file="docs/test.pdf"
        )
        self.assertFalse(doc.verified)
        self.assertFalse(doc.rejected)


# ─── RESUME PARSER TESTS ──────────────────────────────────────────────────────

class ResumeParserTest(TestCase):
    def test_extracts_known_skills(self):
        text = "Experienced in Python, Django, and PostgreSQL. Also know React and Docker."
        skills = extract_skills(text)
        self.assertIn("python", skills)
        self.assertIn("django", skills)
        self.assertIn("postgresql", skills)
        self.assertIn("react", skills)
        self.assertIn("docker", skills)

    def test_no_false_positives(self):
        text = "Worked with CISCO networking equipment"
        skills = extract_skills(text)
        self.assertNotIn("c", skills)

    def test_empty_text_returns_empty(self):
        self.assertEqual(extract_skills(""), [])

    def test_calculate_match_perfect(self):
        score, matched, missing = calculate_match("python, django, react", "python, django, react")
        self.assertEqual(score, 100.0)
        self.assertEqual(missing, set())

    def test_calculate_match_partial(self):
        score, matched, missing = calculate_match("python, django", "python, django, react")
        self.assertAlmostEqual(score, 66.67, places=1)
        self.assertIn("react", missing)

    def test_calculate_match_no_requirements(self):
        score, _, __ = calculate_match("python", "")
        self.assertEqual(score, 0)

    def test_calculate_match_empty_candidate(self):
        score, _, missing = calculate_match("", "python, django")
        self.assertEqual(score, 0.0)
        self.assertIn("python", missing)


# ─── HR VIEW TESTS ────────────────────────────────────────────────────────────

class HRViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr = make_hr()
        self.client.login(username="hr@example.com", password="hrpass")
        self.emp = make_emp()

    def test_hr_dashboard_200(self):
        r = self.client.get(reverse("hr_dashboard"))
        self.assertEqual(r.status_code, 200)

    def test_hr_dashboard_redirects_anonymous(self):
        self.client.logout()
        r = self.client.get(reverse("hr_dashboard"))
        self.assertRedirects(r, "/", fetch_redirect_response=False)

    def test_employee_list_200(self):
        r = self.client.get(reverse("employee_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.emp.full_name)

    def test_employee_list_search(self):
        r = self.client.get(reverse("employee_list") + "?q=John")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "John")

    def test_employee_profile_200(self):
        r = self.client.get(reverse("employee_profile", args=[self.emp.pk]))
        self.assertEqual(r.status_code, 200)

    def test_document_list_200(self):
        r = self.client.get(reverse("document_list"))
        self.assertEqual(r.status_code, 200)

    def test_verify_document(self):
        doc = Document.objects.create(
            employee=self.emp, document_type="id_proof", file="docs/id.pdf"
        )
        self.assertFalse(doc.verified)
        r = self.client.get(reverse("verify_document", args=[doc.pk]))
        self.assertRedirects(r, reverse("document_list"), fetch_redirect_response=False)
        doc.refresh_from_db()
        self.assertTrue(doc.verified)

    def test_reject_document(self):
        doc = Document.objects.create(
            employee=self.emp, document_type="id_proof", file="docs/id.pdf"
        )
        r = self.client.post(
            reverse("reject_document", args=[doc.pk]),
            {"reason": "Blurry image"}
        )
        self.assertRedirects(r, reverse("document_list"), fetch_redirect_response=False)
        doc.refresh_from_db()
        self.assertTrue(doc.rejected)
        self.assertFalse(doc.verified)
        self.assertEqual(doc.rejection_reason, "Blurry image")

    def test_analytics_200(self):
        r = self.client.get(reverse("analytics"))
        self.assertEqual(r.status_code, 200)

    def test_hr_attendance_get(self):
        r = self.client.get(reverse("hr_attendance"))
        self.assertEqual(r.status_code, 200)

    def test_hr_attendance_mark(self):
        r = self.client.post(reverse("hr_attendance"), {
            "employee": self.emp.pk,
            "date": "2024-03-15",
            "status": "present",
            "check_in": "09:00",
            "check_out": "18:00",
            "remarks": "",
        })
        self.assertRedirects(r, reverse("hr_attendance"), fetch_redirect_response=False)
        self.assertTrue(Attendance.objects.filter(employee=self.emp, date="2024-03-15").exists())

    def test_hr_leaves_200(self):
        r = self.client.get(reverse("hr_leaves"))
        self.assertEqual(r.status_code, 200)

    def test_hr_salary_200(self):
        r = self.client.get(reverse("hr_salary"))
        self.assertEqual(r.status_code, 200)

    def test_mark_salary_paid(self):
        s = Salary.objects.create(
            employee=self.emp, month=1, year=2024,
            basic_salary=50000, net_salary=50000
        )
        self.assertFalse(s.paid)
        r = self.client.get(reverse("mark_salary_paid", args=[s.pk]))
        self.assertRedirects(r, reverse("hr_salary"), fetch_redirect_response=False)
        s.refresh_from_db()
        self.assertTrue(s.paid)
        self.assertIsNotNone(s.paid_on)


# ─── EMPLOYEE VIEW TESTS ──────────────────────────────────────────────────────

class EmployeeViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.emp = make_emp()
        self.client.login(username="emp@example.com", password="emppass")

    def test_employee_dashboard_200(self):
        r = self.client.get(reverse("employee_dashboard"))
        self.assertEqual(r.status_code, 200)

    def test_employee_dashboard_blocks_hr(self):
        make_hr()
        self.client.login(username="hr@example.com", password="hrpass")
        r = self.client.get(reverse("employee_dashboard"))
        self.assertRedirects(r, "/", fetch_redirect_response=False)

    def test_employee_tasks_200(self):
        r = self.client.get(reverse("employee_tasks"))
        self.assertEqual(r.status_code, 200)

    def test_complete_task(self):
        task = Task.objects.create(employee=self.emp, title="Read handbook")
        self.assertFalse(task.completed)
        r = self.client.get(reverse("complete_task", args=[task.pk]))
        self.assertRedirects(r, reverse("employee_tasks"), fetch_redirect_response=False)
        task.refresh_from_db()
        self.assertTrue(task.completed)

    def test_employee_attendance_200(self):
        r = self.client.get(reverse("employee_attendance"))
        self.assertEqual(r.status_code, 200)

    def test_employee_leave_get(self):
        r = self.client.get(reverse("employee_leave"))
        self.assertEqual(r.status_code, 200)

    def test_employee_leave_submit(self):
        r = self.client.post(reverse("employee_leave"), {
            "leave_type": "sick",
            "start_date": "2024-05-01",
            "end_date": "2024-05-03",
            "reason": "Fever",
        })
        self.assertRedirects(r, reverse("employee_leave"), fetch_redirect_response=False)
        self.assertTrue(LeaveRequest.objects.filter(employee=self.emp, leave_type="sick").exists())

    def test_employee_salary_200(self):
        r = self.client.get(reverse("employee_salary"))
        self.assertEqual(r.status_code, 200)

    def test_employee_profile_view_200(self):
        r = self.client.get(reverse("employee_profile_view"))
        self.assertEqual(r.status_code, 200)


# ─── ACCOUNT VIEW TESTS ───────────────────────────────────────────────────────

class AccountViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_200(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)

    def test_signup_get_200(self):
        r = self.client.get(reverse("signup"))
        self.assertEqual(r.status_code, 200)

    def test_signup_password_mismatch(self):
        r = self.client.post(reverse("signup"), {
            "role": "EMPLOYEE", "first_name": "Jane", "last_name": "Doe",
            "email": "jane@example.com", "department": "Engineering",
            "position": "Dev", "joining_date": "2024-01-01",
            "password": "abc12345", "confirm_password": "xyz99999",
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(email="jane@example.com").exists())

    def test_hr_login_invalid(self):
        r = self.client.post(reverse("login_hr"), {
            "username": "nobody@example.com",
            "password": "wrong",
            "hr_id": "HRZZ0001",
        })
        self.assertEqual(r.status_code, 200)

    def test_forgot_id_found(self):
        emp = make_emp()
        r = self.client.post(reverse("forgot_id"), {"email": emp.email})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, emp.employee_id)

    def test_forgot_id_not_found(self):
        r = self.client.post(reverse("forgot_id"), {"email": "ghost@example.com"})
        self.assertContains(r, "No account found")

    def test_logout_redirects(self):
        emp = make_emp()
        self.client.login(username=emp.email, password="pass1234")
        r = self.client.get(reverse("logout"))
        self.assertRedirects(r, "/", fetch_redirect_response=False)
