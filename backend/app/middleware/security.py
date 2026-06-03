"""
Security Middleware for RetailMind
Enforces secure HTTP headers including HSTS, CSP, and XFO using a pure ASGI middleware
to prevent streaming response buffering or event-loop blockage issues.
"""
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.datastructures import MutableHeaders

class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message.setdefault("headers", []))
                
                # Prevent MIME type sniffing
                headers["X-Content-Type-Options"] = "nosniff"
                
                # Prevent clickjacking
                headers["X-Frame-Options"] = "DENY"
                
                # Enforce XSS protection in legacy browsers
                headers["X-XSS-Protection"] = "1; mode=block"
                
                # Control referrer information
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                
                # Restrict browser APIs/features
                headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
                
                # Content Security Policy (CSP)
                csp_parts = [
                    "default-src 'self'",
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                    "style-src 'self' 'unsafe-inline'",
                    "img-src 'self' data: https: blob:",
                    "font-src 'self' data:",
                    "connect-src 'self' https://generativelanguage.googleapis.com ws: wss:",
                    "frame-ancestors 'none'"
                ]
                headers["Content-Security-Policy"] = "; ".join(csp_parts)
                
                # Enforce HSTS for secure connections (HTTPS)
                if scope.get("scheme") == "https":
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

            await send(message)

        await self.app(scope, receive, send_wrapper)
