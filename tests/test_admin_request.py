"""
Kurucu yönetici tarafından admin talep onay/red akışı testleri.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from accounts.models import AdminRequest
from audit_logs.models import AuditLog

pytestmark = [pytest.mark.django_db, pytest.mark.integration]

User = get_user_model()


@pytest.fixture
def founder_admin():
    u = User.objects.create_user(
        username="founder",
        email="founder@test.local",
        password="pw-test-123",
        role=User.Role.ADMIN,
    )
    u.is_founder_admin = True
    u.save(update_fields=["is_founder_admin"])
    return u


@pytest.fixture
def plain_admin():
    return User.objects.create_user(
        username="plain_admin",
        email="plain_admin@test.local",
        password="pw-test-123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def applicant():
    return User.objects.create_user(
        username="applicant",
        email="applicant@test.local",
        password="pw-test-123",
        role=User.Role.STUDENT,
    )


def test_admin_request_create(applicant):
    client = Client()
    client.force_login(applicant)
    url = reverse("accounts:admin_request")
    resp = client.post(url, data={"reason": "Yönetim desteği"}, follow=False)
    assert resp.status_code == 302
    assert AdminRequest.objects.filter(user=applicant, status=AdminRequest.Status.PENDING).exists()
    assert AuditLog.objects.filter(event_type="admin_request_created").exists()


def test_non_founder_cannot_open_queue(plain_admin):
    client = Client()
    client.force_login(plain_admin)
    resp = client.get(reverse("dashboard:admin_requests"))
    assert resp.status_code == 403


def test_founder_approve_assigns_admin(founder_admin, applicant):
    ar = AdminRequest.objects.create(user=applicant, reason="test")
    client = Client()
    client.force_login(founder_admin)
    resp = client.post(reverse("dashboard:admin_request_approve", kwargs={"pk": ar.pk}), follow=False)
    assert resp.status_code == 302
    applicant.refresh_from_db()
    assert applicant.role == User.Role.ADMIN
    ar.refresh_from_db()
    assert ar.status == AdminRequest.Status.APPROVED
    assert AuditLog.objects.filter(event_type="admin_request_approved").exists()


def test_double_approve_is_idempotent(founder_admin, applicant):
    ar = AdminRequest.objects.create(user=applicant, reason="x")
    client = Client()
    client.force_login(founder_admin)
    client.post(reverse("dashboard:admin_request_approve", kwargs={"pk": ar.pk}))
    client.post(reverse("dashboard:admin_request_approve", kwargs={"pk": ar.pk}))
    assert AdminRequest.objects.filter(pk=ar.pk, status=AdminRequest.Status.APPROVED).count() == 1


def test_applicant_cannot_approve_requests(applicant):
    other = User.objects.create_user(
        username="other_student",
        email="other_student@test.local",
        password="pw-test-123",
        role=User.Role.STUDENT,
    )
    ar = AdminRequest.objects.create(user=other, reason="ab")
    client = Client()
    client.force_login(applicant)
    resp = client.post(reverse("dashboard:admin_request_approve", kwargs={"pk": ar.pk}))
    assert resp.status_code == 403
