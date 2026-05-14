"""
Core app için genel testler (middleware, breadcrumbs, permissions).
"""
from django.test import Client, TestCase
from django.urls import reverse


class RequestIdMiddlewareTests(TestCase):
    def test_health_live_includes_x_request_id(self):
        response = Client().get(reverse("health_live"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response)
        self.assertTrue(response["X-Request-ID"])
