import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, override_settings
from django.urls import reverse

from accounts.login_throttle import is_login_locked

pytestmark = [pytest.mark.security, pytest.mark.integration]


@override_settings(
    LOGIN_THROTTLE_MAX_FAILURES=3,
    LOGIN_THROTTLE_LOCKOUT_SECONDS=120,
)
@pytest.mark.django_db
def test_login_rate_limit_blocks_bruteforce_attempts():
    cache.clear()

    user_model = get_user_model()
    user_model.objects.create_user(
        username="ratelimit_user",
        email="ratelimit_user@test.local",
        password="correct-pass-123",
        role="student",
    )

    client = Client()
    url = reverse("accounts:login")
    remote_ip = "203.0.113.10"

    for _ in range(3):
        resp = client.post(
            url,
            data={"login": "ratelimit_user", "password": "wrong-pass"},
            REMOTE_ADDR=remote_ip,
            follow=False,
        )
        assert resp.status_code in (200, 302)

    request = resp.wsgi_request
    assert is_login_locked(request, "ratelimit_user") is True

    locked_resp = client.post(
        url,
        data={"login": "ratelimit_user", "password": "correct-pass-123"},
        REMOTE_ADDR=remote_ip,
        follow=False,
    )
    assert locked_resp.status_code == 302
    assert "_auth_user_id" not in client.session
