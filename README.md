# 🛰️ Cobertura Terrestre - San Andrés, Colombia

Pipeline de clasificación de cobertura terrestre usando inteligencia artificial geoespacial.

## 📋 Descripción

Este proyecto utiliza el modelo **Prithvi** (NASA-IBM) para clasificar la cobertura terrestre del municipio de San Andrés (Archipiélago de San Andrés, Providencia y Santa Catalina, Colombia) usando imágenes **Sentinel-2** (óptico) y **Sentinel-1** (radar).

## 🚀 Características

- **Modelo**: Prithvi (foundation model geoespacial de NASA-IBM)
- **Datos**: Sentinel-2 L2A (6 bandas) + Sentinel-1 GRD (VV, VH)
- **Composición temporal**: Mediana de múltiples fechas para minimizar nubes
- **Clasificación**: Píxel a píxel con 12 clases de cobertura
- **Visualización**: Mapa interactivo web + GeoTIFF + estadísticas

## 📦 Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Configuración

1. **Credenciales de Sentinel Hub**:
   ```bash
   export SENTINELHUB_CLIENT_ID="tu_client_id"
   export SENTINELHUB_CLIENT_SECRET="tu_client_secret"
   ```
   Obtén credenciales gratuitas en [Sentinel Hub](https://www.sentinel-hub.com/).

2. **Editar `config.yaml`** según tus necesidades (fechas, zona, clases).

## 📊 Uso

### Pipeline completo (CLI)

```bash
python main.py
```

Esto ejecutará:
1. Descarga de imágenes Sentinel-2 y Sentinel-1
2. Composición temporal y preprocesado
3. Carga del modelo Prithvi
4. Inferencia y clasificación
5. Generación de resultados (mapa, GeoTIFF, estadísticas)

### Interfaz web

```bash
python run_web.py
```

Abre http://127.0.0.1:8000 en tu navegador.

## 📁 Estructura del proyecto

```
cobertura_sanandres/
├── config.yaml              # Configuración del pipeline
├── main.py                  # Pipeline end-to-end (CLI)
├── run_web.py               # Servidor web
├── requirements.txt         # Dependencias Python
├── src/
│   ├── download.py          # Descarga de imágenes Sentinel
│   ├── preprocess.py        # Composición temporal y normalización
│   ├── model.py             # Carga y adaptación de Prithvi
│   ├── predict.py           # Inferencia tile a tile
│   └── visualize.py         # Mapas y estadísticas
├── web/
│   ├── app.py               # API FastAPI
│   ├── static/
│   │   ├── index.html       # Interfaz web
│   │   └── app.js           # Lógica frontend
│   └── templates/
├── data/                    # Datos descargados (creado automáticamente)
└── outputs/                 # Resultados (creado automáticamente)
```

## 📈 Resultados

El pipeline genera:
- `mapa_clasificacion.png` - Mapa 2D con leyenda
- `cobertura_sanandres.tif` - GeoTIFF clasificado
- `mapa_interactivo.html` - Mapa web interactivo
- `estadisticas.json` - Porcentajes por clase

## 🎨 Clases de cobertura

| ID | Clase | Color |
|---|---|---|
| 0 | No data | Negro |
| 1 | Tree cover | Verde oscuro |
| 2 | Shrubland | Naranja |
| 3 | Grassland | Amarillo |
| 4 | Cropland | Rosa |
| 5 | Built-up | Rojo |
| 6 | Bare / sparse vegetation | Gris |
| 7 | Snow and ice | Blanco |
| 8 | Open water | Azul |
| 9 | Herbaceous wetland | Cian |
| 10 | Mangroves | Verde claro |
| 11 | Moss and lichen | Beige |

## 📚 Referencias

- [Prithvi Model](https://huggingface.co/ibm-nasa-geospatial/Prithvi-100M)
- [Sentinel Hub](https://www.sentinel-hub.com/)
- [ESA WorldCover](https://esa-worldcover.org/)

## 📄 Licencia

Este proyecto es código abierto. Los modelos y datos tienen sus propias licencias:
- Prithvi: CC-BY-4.0
- Sentinel-2/1: Libre uso (Copernicus)
