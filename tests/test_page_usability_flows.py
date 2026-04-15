"""
Phase 14: sayfa kullanılabilirliği ve temel RBAC duman testleri.
Rollback: ilgili view/şablonlar geri alınırsa senaryolar güncellenmeli.
"""

import pytest
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from core.test_phase4 import Phase4FactoriesMixin


@pytest.mark.smoke
class PageUsabilityFlowsTests(Phase4FactoriesMixin, TestCase):
    def test_section_list_filter_returns_200(self):
        inst = self._instructor()
        c = self._course("USAB1", "Usability A")
        off = self._offering(c, instructor=inst)
        self._section(off)
        st = self._student("USAB_ST")
        client = Client()
        client.force_login(st.user)
        r = client.get(reverse("enrollments:browse"), {"q": "USA", "sort": "code"})
        self.assertEqual(r.status_code, 200)

    def test_course_list_search_returns_200(self):
        self._course("USAC1", "Searchable")
        u = self._user("USAC_AD", User.Role.ADMIN, is_staff=True)
        client = Client()
        client.force_login(u)
        r = client.get(reverse("courses:course_list"), {"q": "USA"})
        self.assertEqual(r.status_code, 200)

    def test_instructor_cannot_open_student_transcript(self):
        ins = self._instructor("USAB_INS")
        client = Client()
        client.force_login(ins.user)
        r = client.get(reverse("students:transcript"))
        self.assertEqual(r.status_code, 302)
