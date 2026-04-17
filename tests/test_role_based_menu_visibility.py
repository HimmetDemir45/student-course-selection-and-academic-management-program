"""
Phase 14: rol bazlı menü görünürlüğü.
Rollback: base.html eski tek menü yapısına dönülürse bu testler güncellenmeli.
"""

import pytest
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from core.test_phase4 import Phase4FactoriesMixin


@pytest.mark.integration
class RoleBasedMenuVisibilityTests(Phase4FactoriesMixin, TestCase):
    def test_student_sees_student_nav_not_admin_nav(self):
        st = self._student("MENU_S1")
        client = Client()
        client.force_login(st.user)
        html = client.get(reverse("core:home")).content.decode("utf-8")
        self.assertIn('id="navStudent"', html)
        self.assertNotIn('id="navAdmin"', html)

    def test_instructor_sees_instructor_nav_not_student_nav(self):
        ins = self._instructor("MENU_I1")
        client = Client()
        client.force_login(ins.user)
        html = client.get(reverse("core:home")).content.decode("utf-8")
        self.assertIn('id="navInstructor"', html)
        self.assertNotIn('id="navStudent"', html)

    def test_admin_sees_admin_nav(self):
        u = self._user("MENU_A1", User.Role.ADMIN, is_staff=True)
        client = Client()
        client.force_login(u)
        html = client.get(reverse("core:home")).content.decode("utf-8")
        self.assertIn('id="navAdmin"', html)

    def test_admin_does_not_see_student_or_instructor_nav(self):
        u = self._user("MENU_A2", User.Role.ADMIN, is_staff=True)
        client = Client()
        client.force_login(u)
        html = client.get(reverse("core:home")).content.decode("utf-8")
        self.assertNotIn('id="navStudent"', html)
        self.assertNotIn('id="navInstructor"', html)

    def test_student_does_not_see_instructor_nav(self):
        st = self._student("MENU_S2")
        client = Client()
        client.force_login(st.user)
        html = client.get(reverse("core:home")).content.decode("utf-8")
        self.assertNotIn('id="navInstructor"', html)
        self.assertNotIn('id="navAdmin"', html)
