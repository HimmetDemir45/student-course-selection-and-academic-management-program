"""
Üretim ortamı güvenlik başlıkları (CSP, X-Frame-Options, HSTS) testleri.
"""
import pytest
from django.test import Client, override_settings

pytestmark = [pytest.mark.security, pytest.mark.smoke]


@override_settings(
    SECURE_HSTS_SECONDS=31536000,
    SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
    SECURE_HSTS_PRELOAD=True,
    X_FRAME_OPTIONS="DENY",
    SECURE_CONTENT_TYPE_NOSNIFF=True,
    SECURE_REFERRER_POLICY="same-origin",
    SECURE_SSL_REDIRECT=False,
)
@pytest.mark.django_db
def test_security_headers_presence_on_homepage():
    client = Client()
    response = client.get("/", secure=True)

    assert response.status_code in (200, 302), "Ana sayfa yaniti beklenen aralikta degil."

    # Kritik headerlar
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"].lower() == "nosniff"

    assert "Referrer-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "same-origin"

    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

    # TODO: project-specific endpoint/header policy (CSP)
    assert "Content-Security-Policy" in response.headers, "CSP header eksik."
