from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.web.routes import router as web_router


app = FastAPI(
    title="Herramienta de laminados MAD Formula Team",
    version="0.1.0",
    description=(
        "Calculadora web de teoría del laminado con compatibilidad legado MATLAB, "
        "desplegable por Docker y preparada para operación pública en la nube."
    ),
)
app.state.settings = settings

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(web_router)
