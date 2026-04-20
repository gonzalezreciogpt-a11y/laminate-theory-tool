from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.web.routes import router as web_router


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "; ".join(
                [
                    "default-src 'self'",
                    "img-src 'self' data: https:",
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                    "font-src 'self' https://fonts.gstatic.com data:",
                    "script-src 'self' 'unsafe-inline'",
                    "connect-src 'self'",
                    "object-src 'none'",
                    "base-uri 'self'",
                    "form-action 'self'",
                    "frame-ancestors 'none'",
                ]
            ),
        )
        return response


app = FastAPI(
    title="Herramienta de laminados MAD Formula Team",
    version="0.1.0",
    description=(
        "Calculadora web de teoría del laminado con compatibilidad legado MATLAB, "
        "desplegable por Docker y preparada para operación pública en la nube."
    ),
)
app.state.settings = settings
app.add_middleware(SecurityHeadersMiddleware)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(web_router)
