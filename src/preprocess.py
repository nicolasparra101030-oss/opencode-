"""
Módulo de preprocesado: composición temporal, normalización y stack de bandas.
"""

import numpy as np
import yaml
from pathlib import Path


def temporal_median_composite(data: np.ndarray, cloud_mask_idx: int = 6) -> np.ndarray:
    """
    Crea composición temporal usando mediana, ignorando nubes.
    
    Args:
        data: Array (T, H, W, C) donde la última banda es la máscara de nubes (SCL)
        cloud_mask_idx: Índice de la banda de máscara de nubes
    
    Returns:
        Array (H, W, C-1) con la mediana temporal sin nubes
    """
    # Separar máscara de nubes
    cloud_mask = data[..., cloud_mask_idx]  # (T, H, W)
    optical_bands = data[..., :cloud_mask_idx]  # (T, H, W, 6)
    
    # Valores SCL que indican nubes/sombra: 0 (no data), 1 (saturado), 3 (sombra), 8, 9 (nubes)
    cloud_values = [0, 1, 3, 8, 9, 10, 11]
    
    # Crear máscara de píxeles válidos
    valid_mask = np.ones_like(cloud_mask, dtype=bool)
    for cv in cloud_values:
        valid_mask &= (cloud_mask != cv)
    
    # Para cada píxel, calcular mediana solo sobre fechas válidas
    T, H, W, C = optical_bands.shape
    result = np.zeros((H, W, C), dtype=np.float32)
    
    for i in range(H):
        for j in range(W):
            valid_t = valid_mask[:, i, j]
            if valid_t.sum() > 0:
                result[i, j] = np.median(optical_bands[valid_t, i, j], axis=0)
            else:
                # Si no hay fechas válidas, usar mediana de todas
                result[i, j] = np.median(optical_bands[:, i, j], axis=0)
    
    return result


def temporal_median_radar(data: np.ndarray) -> np.ndarray:
    """
    Crea composición temporal para radar (VV, VH).
    
    Args:
        data: Array (T, H, W, 2)
    
    Returns:
        Array (H, W, 2) con mediana temporal
    """
    return np.median(data, axis=0).astype(np.float32)


def normalize_optical(data: np.ndarray) -> np.ndarray:
    """
    Normaliza bandas ópticas de Sentinel-2 a rango [0, 1].
    Los valores típicos de reflectancia están en [0, 10000].
    """
    # Clip a rango válido y normalizar
    data = np.clip(data, 0, 10000)
    data = data / 10000.0
    return data.astype(np.float32)


def normalize_radar(data: np.ndarray) -> np.ndarray:
    """
    Normaliza bandas de radar Sentinel-1 (VV, VH) a dB y luego [0, 1].
    """
    # Convertir a dB
    data = 10 * np.log10(np.clip(data, 1e-6, None))
    # Normalizar típicamente de [-25, 0] a [0, 1]
    data = (data + 25) / 25
    data = np.clip(data, 0, 1)
    return data.astype(np.float32)


def create_prithvi_input(
    s2_composite: np.ndarray,
    s1_composite: np.ndarray,
) -> np.ndarray:
    """
    Crea el tensor de entrada para Prithvi combinando óptico y radar.
    
    Args:
        s2_composite: (H, W, 6) bandas B02, B03, B04, B08, B11, B12
        s1_composite: (H, W, 2) bandas VV, VH
    
    Returns:
        (H, W, 8) tensor normalizado listo para Prithvi
    """
    # Normalizar
    s2_norm = normalize_optical(s2_composite)
    s1_norm = normalize_radar(s1_composite)
    
    # Apilar: 6 bandas ópticas + 2 bandas radar
    combined = np.concatenate([s2_norm, s1_norm], axis=-1)
    
    return combined


def preprocess_pipeline(raw_data: dict, config: dict) -> np.ndarray:
    """
    Pipeline completo de preprocesado.
    
    Args:
        raw_data: Diccionario con 'sentinel2' y 'sentinel1' del módulo download
        config: Configuración del pipeline
    
    Returns:
        Tensor (H, W, 8) listo para inferencia
    """
    print("Creando composición temporal Sentinel-2...")
    s2_composite = temporal_median_composite(raw_data["sentinel2"])
    
    print("Creando composición temporal Sentinel-1...")
    s1_composite = temporal_median_radar(raw_data["sentinel1"])
    
    print("Normalizando y combinando bandas...")
    prithvi_input = create_prithvi_input(s2_composite, s1_composite)
    
    print(f"Tensor de entrada: {prithvi_input.shape}")
    return prithvi_input
