# Bitácora del Proyecto

## Fecha: 2026-10-07

---

### Sesión de Planificación

**Objetivo:** Crear un programa en Python para detectar el tipo de cobertura terrestre de una zona de Colombia empleando modelos de IA geoespacial de código abierto.

**Decisiones tomadas:**
- Zona de estudio: Municipio de San Andrés (Archipiélago de San Andrés, Providencia y Santa Catalina)
- Coordenadas: 12.55° N, 81.72° W
- Modelo: Prithvi (NASA-IBM foundation model)
- Datos: Sentinel-2 (óptico) + Sentinel-1 (radar)
- Composición temporal: Mediana de múltiples fechas
- Interfaz: Web (FastAPI + Leaflet)

---

### Sesión de Implementación

**Estructura del proyecto creada:**
```
cobertura_sanandres/
├── config.yaml
├── main.py
├── run_web.py
├── requirements.txt
├── README.md
├── BITACORA.md
├── src/
│   ├── __init__.py
│   ├── download.py
│   ├── preprocess.py
│   ├── model.py
│   ├── predict.py
│   └── visualize.py
├── web/
│   ├── __init__.py
│   ├── app.py
│   ├── static/
│   │   └── app.js
│   └── templates/
│       └── index.html
├── data/
└── outputs/
```

**Módulos implementados:**

1. **download.py** — Descarga de imágenes Sentinel-2 L2A y Sentinel-1 GRD usando sentinelhub-py
2. **preprocess.py** — Composición temporal (mediana), normalización y stack de bandas (6 ópticas + 2 radar)
3. **model.py** — Carga de Prithvi con adaptación de primera capa convolucional para 8 canales
4. **predict.py** — Inferencia tile a tile (256×256) con solapamiento
5. **visualize.py** — Generación de mapas 2D, GeoTIFF, mapa interactivo HTML y estadísticas
6. **web/app.py** — API FastAPI con endpoints para estadísticas, mapa y configuración
7. **web/static/** — Interfaz web con Leaflet para visualización interactiva

---

### Sesión de Publicación en GitHub

**Repositorio creado:** https://github.com/nicolasparra101030-oss/opencode-

**Commit inicial:**
- Mensaje: `feat: pipeline de cobertura terrestre con Prithvi para San Andrés`
- 15 archivos, 1,735 líneas
- Rama: `main`

**Identidad git configurada:**
- Usuario: nicolasparra
- Email: nicolasparra@users.noreply.github.com

---

### Pendientes / Próximos pasos

- [ ] Configurar credenciales de Sentinel Hub (SENTINELHUB_CLIENT_ID, SENTINELHUB_CLIENT_SECRET)
- [ ] Ejecutar el pipeline por primera vez con datos reales
- [ ] Validar resultados con ground truth (WorldCover 2021)
- [ ] Ajustar clases de cobertura según necesidades específicas
- [ ] Considerar fine-tuning del modelo con datos locales etiquetados
- [ ] Añadir tests unitarios
- [ ] Configurar CI/CD (GitHub Actions)

---

### Notas técnicas

- Prithvi se descarga desde Hugging Face en la primera ejecución (~400MB)
- La inferencia en CPU es viable para San Andrés (~26 km²) pero lenta; con GPU es mucho más rápida
- El modelo clasifica 12 clases: No data, Tree cover, Shrubland, Grassland, Cropland, Built-up, Bare/sparse, Snow/ice, Open water, Herbaceous wetland, Mangroves, Moss/lichen
- Las bandas de radar (VV, VH) ayudan a distinguir vegetación densa y suelo desnudo
