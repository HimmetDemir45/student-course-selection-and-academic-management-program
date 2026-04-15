"""
Python 3.14 + Django: test Client, template_rendered sirasinda RequestContext
copy() AttributeError (django.template.context.RequestContext.__copy__).
Yalnizca test/pytest yuklemesinde dev.py / ci.py bu modulu import eder;
response.templates korunur, context saklanmaz (HTML/assert icin yeterli).

Rollback: bu dosyayi silin; dev.py ve ci.py icindeki import satirlarini kaldirin.
"""

from __future__ import annotations

import sys


def apply_patch() -> None:
    if sys.version_info < (3, 14):
        return
    from django.test import client as dj_client

    def store_templates_only(store, signal, sender, template, context, **kwargs):
        store.setdefault("templates", []).append(template)

    dj_client.store_rendered_templates = store_templates_only
