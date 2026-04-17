"""Breadcrumb öğeleri — yalnızca görünüm bağlamı (iş kuralı yok)."""

from __future__ import annotations

from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def items(*crumbs) -> list[dict]:
    """Her öğe: label, url (son için None), is_last otomatik."""
    out: list[dict] = []
    n = len(crumbs)
    for i, c in enumerate(crumbs):
        item = dict(c)
        item["is_last"] = i == n - 1
        out.append(item)
    return out


def home() -> dict:
    return {"label": _("Ana sayfa"), "url": reverse("core:home")}
