"""
Aplicación FastAPI para visualización de cobertura terrestre.
"""

import os
import json
import yaml
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

# Rutas base
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
CONFIG_PATH = BASE_DIR / "config.yaml"

app = FastAPI(title="Cobertura Terrestre - San Andrés")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página principal con mapa interactivo."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/stats")
async def get_stats():
    """Devuelve estadísticas de cobertura."""
    stats_path = OUTPUT_DIR / "estadisticas.json"
    if not stats_path.exists():
        return JSONResponse(
            content={"error": "No hay resultados. Ejecuta el pipeline primero."},
            status_code=404,
        )
    
    with open(stats_path, "r") as f:
        stats = json.load(f)
    
    return JSONResponse(content=stats)


@app.get("/api/map")
async def get_map():
    """Devuelve el mapa interactivo HTML."""
    map_path = OUTPUT_DIR / "mapa_interactivo.html"
    if not map_path.exists():
        return JSONResponse(
            content={"error": "No hay mapa. Ejecuta el pipeline primero."},
            status_code=404,
        )
    
    with open(map_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    return HTMLResponse(content=html)


@app.get("/api/config")
async def get_config():
    """Devuelve la configuración actual."""
    config = load_config()
    # No exponer credenciales
    safe_config = {
        "zone": config["zone"],
        "dates": config["dates"],
        "model": {
            "name": config["model"]["name"],
            "classes": config["model"]["classes"],
        },
    }
    return JSONResponse(content=safe_config)


@app.post("/api/run")
async def run_pipeline():
    """Ejecuta el pipeline completo (asíncrono)."""
    # En producción, usar Celery o similar
    # Por ahora, solo indicar que se debe ejecutar manualmente
    return JSONResponse(
        content={
            "message": "Para ejecutar el pipeline, usa: python main.py",
            "status": "info",
        }
    )
