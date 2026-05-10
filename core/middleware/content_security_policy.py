"""Tarayıcıya varsayılan Content-Security-Policy başlığı ekler (Akademik 2.0 ile uyumlu)."""


class ContentSecurityPolicyMiddleware:
    """Tailwind derlendi, CDN kaldırıldı.

    script-src 'unsafe-inline': base.html içindeki inline tema/sidebar JS blokları için gerekli.
    style-src: 'unsafe-inline' kaldırıldı — Tailwind build pipeline'a geçildi.
    """

    HEADER = "Content-Security-Policy"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self.HEADER not in response:
            response[self.HEADER] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
                "style-src 'self' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        return response
