"""Tarayıcıya varsayılan Content-Security-Policy başlığı ekler (Bootstrap CDN ile uyumlu)."""


class ContentSecurityPolicyMiddleware:
    """Şablonlarda satır içi script yok; statik ve cdn.jsdelivr.net izinlidir."""

    HEADER = "Content-Security-Policy"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self.HEADER not in response:
            response[self.HEADER] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "style-src 'self' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        return response
