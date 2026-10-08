"""
Módulo de descarga de imágenes Sentinel-2 y Sentinel-1.
Usa sentinelhub-py para acceder a datos Copernicus.
"""

import os
import yaml
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox,
    bbox_to_dimensions,
)


def load_config(config_path: str = "config.yaml") -> dict:
    """Carga la configuración desde YAML."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_sentinelhub_config() -> SHConfig:
    """Configura credenciales de Sentinel Hub."""
    config = SHConfig()
    # Intentar cargar desde variables de entorno
    config.sh_client_id = os.getenv("SENTINELHUB_CLIENT_ID", "")
    config.sh_client_secret = os.getenv("SENTINELHUB_CLIENT_SECRET", "")
    if not config.sh_client_id or not config.sh_client_secret:
        raise ValueError(
            "Credenciales de Sentinel Hub no encontradas. "
            "Define SENTINELHUB_CLIENT_ID y SENTINELHUB_CLIENT_SECRET."
        )
    return config


def get_aoi_bbox(config: dict) -> BBox:
    """Define el bounding box de interés para San Andrés."""
    lat = config["zone"]["lat"]
    lon = config["zone"]["lon"]
    buffer = config["zone"]["buffer_deg"]
    
    # BBox: [min_lon, min_lat, max_lon, max_lat]
    bbox_coords = [
        lon - buffer,
        lat - buffer,
        lon + buffer,
        lat + buffer,
    ]
    return BBox(bbox=bbox_coords, crs=CRS.WGS84)


def get_dates(config: dict) -> list:
    """Genera fechas para composición temporal."""
    start = datetime.strptime(config["dates"]["start"], "%Y-%m-%d")
    end = datetime.strptime(config["dates"]["end"], "%Y-%m-%d")
    n_dates = config["dates"]["n_dates"]
    preferred_months = config["dates"]["preferred_months"]
    
    # Generar fechas candidatas en meses preferidos
    candidates = []
    current = start
    while current <= end:
        if current.month in preferred_months:
            candidates.append(current)
        current += timedelta(days=15)
    
    # Seleccionar n_dates espaciadas uniformemente
    if len(candidates) >= n_dates:
        indices = np.linspace(0, len(candidates) - 1, n_dates, dtype=int)
        selected = [candidates[i] for i in indices]
    else:
        selected = candidates
    
    return [d.strftime("%Y-%m-%d") for d in selected]


def download_sentinel2(
    config: dict,
    bbox: BBox,
    date: str,
    output_dir: str,
) -> np.ndarray:
    """
    Descarga imagen Sentinel-2 L2A para una fecha específica.
    Retorna array numpy con forma (H, W, 6) para las bandas de Prithvi.
    """
    sh_config = get_sentinelhub_config()
    
    # Calcular dimensiones
    resolution = config["sentinel2"]["resolution"]
    size = bbox_to_dimensions(bbox, resolution=resolution)
    
    # Limitar tamaño máximo para evitar problemas de memoria
    max_size = 512
    if size[0] > max_size or size[1] > max_size:
        scale = max(size) / max_size
        size = (int(size[0] / scale), int(size[1] / scale))
        resolution = resolution * scale
    
    bands = config["sentinel2"]["bands"]
    
    # Script evalscript para Sentinel-2
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"],
            output: { bands: 7, sampleType: "FLOAT32" }
        };
    }
    function evaluatePixel(sample) {
        return [
            sample.B02, sample.B03, sample.B04,
            sample.B08, sample.B11, sample.B12,
            sample.SCL
        ];
    }
    """
    
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(date, date),
                mosaicking_order="leastCC",
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF),
        ],
        bbox=bbox,
        size=size,
        config=sh_config,
        data_folder=output_dir,
    )
    
    data = request.get_data()[0]
    return data


def download_sentinel1(
    config: dict,
    bbox: BBox,
    date: str,
    output_dir: str,
) -> np.ndarray:
    """
    Descarga imagen Sentinel-1 GRD para una fecha específica.
    Retorna array numpy con forma (H, W, 2) con bandas VV y VH.
    """
    sh_config = get_sentinelhub_config()
    
    resolution = config["sentinel1"]["resolution"]
    size = bbox_to_dimensions(bbox, resolution=resolution)
    
    max_size = 512
    if size[0] > max_size or size[1] > max_size:
        scale = max(size) / max_size
        size = (int(size[0] / scale), int(size[1] / scale))
        resolution = resolution * scale
    
    evalscript_s1 = """
    //VERSION=3
    function setup() {
        return {
            input: ["VV", "VH"],
            output: { bands: 2, sampleType: "FLOAT32" }
        };
    }
    function evaluatePixel(sample) {
        return [sample.VV, sample.VH];
    }
    """
    
    request = SentinelHubRequest(
        evalscript=evalscript_s1,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL1_GRD,
                time_interval=(date, date),
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF),
        ],
        bbox=bbox,
        size=size,
        config=sh_config,
        data_folder=output_dir,
    )
    
    data = request.get_data()[0]
    return data


def download_all(config: dict) -> dict:
    """
    Descarga todas las imágenes para la composición temporal.
    Retorna diccionario con arrays apilados.
    """
    bbox = get_aoi_bbox(config)
    dates = get_dates(config)
    
    output_dir = config["paths"]["data_dir"]
    s2_dir = os.path.join(output_dir, "sentinel2")
    s1_dir = os.path.join(output_dir, "sentinel1")
    os.makedirs(s2_dir, exist_ok=True)
    os.makedirs(s1_dir, exist_ok=True)
    
    s2_stack = []
    s1_stack = []
    
    for date in dates:
        print(f"Descargando datos para {date}...")
        try:
            s2_data = download_sentinel2(config, bbox, date, s2_dir)
            s2_stack.append(s2_data)
        except Exception as e:
            print(f"  Error Sentinel-2: {e}")
        
        try:
            s1_data = download_sentinel1(config, bbox, date, s1_dir)
            s1_stack.append(s1_data)
        except Exception as e:
            print(f"  Error Sentinel-1: {e}")
    
    if not s2_stack or not s1_stack:
        raise RuntimeError("No se pudieron descargar imágenes suficientes.")
    
    return {
        "sentinel2": np.stack(s2_stack, axis=0),  # (T, H, W, 7)
        "sentinel1": np.stack(s1_stack, axis=0),  # (T, H, W, 2)
        "dates": dates,
        "bbox": bbox,
    }
