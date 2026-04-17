"""İstek başına şablon bağlamı (Phase 15: menü aktif durumu)."""


def navigation(request):
    match = getattr(request, "resolver_match", None)
    if not match:
        return {
            "nav_url_name": "",
            "nav_namespace": "",
            "nav_view_name": "",
        }
    return {
        "nav_url_name": match.url_name or "",
        "nav_namespace": match.namespace or "",
        "nav_view_name": f"{match.namespace}:{match.url_name}" if match.namespace else (match.url_name or ""),
    }
