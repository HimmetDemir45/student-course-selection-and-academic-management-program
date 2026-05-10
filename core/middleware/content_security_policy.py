"""Tarayıcıya varsayılan Content-Security-Policy başlığı ekler (Akademik 2.0 ile uyumlu)."""


class ContentSecurityPolicyMiddleware:
    """Şablonlarda Tailwind Play CDN, Google Fonts ve Lucide icons izinlidir.

    NOT (production sertleştirme): Tailwind Play CDN runtime'da inline style enjekte
    ettiği için 'unsafe-inline' gerekli. Prod'da Tailwind'i build pipeline ile derleyip
    'unsafe-inline'ı kaldırmak gerekir.
    """

    HEADER = "Content-Security-Policy"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self.HEADER not in response:
            response[self.HEADER] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' "
                "https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' "
                "https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        return response
