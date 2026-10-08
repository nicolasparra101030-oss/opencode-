"""
Módulo de inferencia: clasificación tile a tile.
"""

import torch
import numpy as np
from typing import Tuple
import yaml


def tile_image(
    image: np.ndarray,
    tile_size: int = 256,
    overlap: int = 32,
) -> Tuple[list, list]:
    """
    Divide la imagen en tiles con solapamiento.
    
    Args:
        image: (H, W, C) tensor de entrada
        tile_size: Tamaño del tile
        overlap: Solapamiento entre tiles
    
    Returns:
        Lista de tiles y lista de posiciones (y, x)
    """
    H, W, C = image.shape
    stride = tile_size - overlap
    
    tiles = []
    positions = []
    
    for y in range(0, H, stride):
        for x in range(0, W, stride):
            # Ajustar para no salir de los límites
            y_end = min(y + tile_size, H)
            x_end = min(x + tile_size, W)
            y_start = max(0, y_end - tile_size)
            x_start = max(0, x_end - tile_size)
            
            tile = image[y_start:y_end, x_start:x_end]
            
            # Pad si es necesario
            if tile.shape[0] < tile_size or tile.shape[1] < tile_size:
                pad_y = tile_size - tile.shape[0]
                pad_x = tile_size - tile.shape[1]
                tile = np.pad(
                    tile,
                    ((0, pad_y), (0, pad_x), (0, 0)),
                    mode="constant",
                    constant_values=0,
                )
            
            tiles.append(tile)
            positions.append((y_start, x_start, y_end - y_start, x_end - x_start))
    
    return tiles, positions


def predict_tiles(
    model: torch.nn.Module,
    tiles: list,
    device: str,
    batch_size: int = 4,
    use_fp16: bool = True,
) -> np.ndarray:
    """
    Ejecuta inferencia sobre los tiles.
    
    Args:
        model: Modelo cargado
        tiles: Lista de tiles (H, W, C)
        device: Dispositivo
        batch_size: Tamaño de batch
        use_fp16: Usar precisión media
    
    Returns:
        Array (n_tiles, n_classes) con logits
    """
    all_predictions = []
    
    with torch.no_grad():
        for i in range(0, len(tiles), batch_size):
            batch_tiles = tiles[i:i + batch_size]
            
            # Convertir a tensor: (B, C, H, W)
            batch = torch.from_numpy(np.stack(batch_tiles)).permute(0, 3, 1, 2)
            batch = batch.float().to(device)
            
            if use_fp16 and device == "cuda":
                batch = batch.half()
                with torch.cuda.amp.autocast():
                    logits = model(batch)
            else:
                logits = model(batch)
            
            all_predictions.append(logits.cpu().numpy())
    
    return np.concatenate(all_predictions, axis=0)


def reconstruct_map(
    predictions: np.ndarray,
    positions: list,
    image_shape: Tuple[int, int],
    n_classes: int,
) -> np.ndarray:
    """
    Reconstruye el mapa de clasificación a partir de las predicciones de tiles.
    
    Args:
        predictions: (n_tiles, n_classes) logits
        positions: Lista de (y, x, h, w) posiciones originales
        image_shape: (H, W) forma de la imagen original
        n_classes: Número de clases
    
    Returns:
        (H, W) mapa de clases
    """
    H, W = image_shape
    class_map = np.zeros((H, W), dtype=np.int32)
    count_map = np.zeros((H, W), dtype=np.float32)
    
    for pred, (y, x, h, w) in zip(predictions, positions):
        # Obtener clase predicha
        class_pred = np.argmax(pred)
        
        # Asignar solo a la región válida (sin padding)
        class_map[y:y+h, x:x+w] += class_pred
        count_map[y:y+h, x:x+w] += 1
    
    # Promediar donde hay solapamiento
    count_map = np.maximum(count_map, 1)
    class_map = np.round(class_map / count_map).astype(np.int32)
    
    return class_map


def run_inference(
    model: torch.nn.Module,
    image: np.ndarray,
    config: dict,
    device: str,
) -> np.ndarray:
    """
    Pipeline completo de inferencia.
    
    Args:
        model: Modelo cargado
        image: (H, W, 8) tensor de entrada
        config: Configuración
        device: Dispositivo
    
    Returns:
        (H, W) mapa de clases
    """
    tile_size = config["model"]["tile_size"]
    batch_size = config["processing"]["batch_size"]
    use_fp16 = config["processing"]["use_fp16"]
    n_classes = len(config["model"]["classes"])
    
    print(f"Dividiendo imagen en tiles de {tile_size}x{tile_size}...")
    tiles, positions = tile_image(image, tile_size=tile_size, overlap=32)
    print(f"  {len(tiles)} tiles generados")
    
    print("Ejecuto inferencia...")
    predictions = predict_tiles(
        model, tiles, device, batch_size=batch_size, use_fp16=use_fp16
    )
    
    print("Reconstruyendo mapa de clasificación...")
    class_map = reconstruct_map(
        predictions, positions, image.shape[:2], n_classes
    )
    
    return class_map
