from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from students.models import StudentProfile


class LoginFlowTests(TestCase):
    def setUp(self):
        UserModel = get_user_model()
        self.user = UserModel.objects.create_user(
            username="logintest",
            email="logintest@example.com",
            password="good-pass-xyz-99",
            first_name="Lt",
            last_name="User",
        )

    def test_login_post_success_redirects_when_csrf_valid(self):
        client = Client(enforce_csrf_checks=True)
        login_url = reverse("accounts:login")
        r = client.get(login_url)
        self.assertEqual(r.status_code, 200)
        csrf = client.cookies.get("csrftoken")
        self.assertIsNotNone(csrf)
        r = client.post(
            login_url,
            {
                "csrfmiddlewaretoken": csrf.value,
                "login": self.user.username,
                "password": "good-pass-xyz-99",
                "remember_me": "",
            },
        )
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)

    def test_login_post_with_wrong_password_renders_errors(self):
        client = Client(enforce_csrf_checks=True)
        login_url = reverse("accounts:login")
        client.get(login_url)
        csrf = client.cookies.get("csrftoken")
        self.assertIsNotNone(csrf)
        r = client.post(
            login_url,
            {
                "csrfmiddlewaretoken": csrf.value,
                "login": self.user.username,
                "password": "wrong-pass",
                "remember_me": "",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Geçersiz giriş bilgileri")
        content = r.content.decode()
        self.assertIn("csrfmiddlewaretoken", content)


class RegistrationProfileTests(TestCase):
    def test_register_post_creates_student_profile(self):
        client = Client(enforce_csrf_checks=True)
        url = reverse("accounts:register")
        client.get(url)
        csrf = client.cookies.get("csrftoken")
        self.assertIsNotNone(csrf)
        email = "reg_unique_student@example.edu"
        r = client.post(
            url,
            {
                "csrfmiddlewaretoken": csrf.value,
                "first_name": "Reg",
                "last_name": "Student",
                "email": email,
                "password1": "good-pass-reg-xyz-99",
                "password2": "good-pass-reg-xyz-99",
            },
        )
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)
        user = get_user_model().objects.get(email=email)
        self.assertEqual(user.role, User.Role.STUDENT)
        sp = StudentProfile.objects.get(user=user)
        self.assertTrue(sp.student_no.startswith("S"))
        self.assertGreater(len(sp.student_no), 1)


class SuperuserDefaultsTests(TestCase):
    def test_create_superuser_sets_admin_role_without_student_profile(self):
        UserModel = get_user_model()
        user = UserModel.objects.create_superuser(
            username="su_admin",
            email="su_admin@example.edu",
            password="super-pass-xyz-99!!",
        )
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertFalse(StudentProfile.objects.filter(user=user).exists())
