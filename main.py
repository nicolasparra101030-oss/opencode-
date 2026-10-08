"""
Pipeline end-to-end para detección de cobertura terrestre en San Andrés.
"""

import os
import sys
import yaml
import json
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from download import load_config, download_all
from preprocess import preprocess_pipeline
from model import load_model, get_device
from predict import run_inference
from visualize import (
    plot_classification_map,
    compute_statistics,
    save_geotiff,
    create_interactive_map,
    print_statistics,
)


def main(config_path: str = "config.yaml"):
    """Ejecuta el pipeline completo."""
    
    # Cargar configuración
    print("Cargando configuración...")
    config = load_config(config_path)
    
    # Crear directorios de salida
    output_dir = config["paths"]["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Descargar datos
    print("\n" + "="*50)
    print("PASO 1: Descarga de imágenes Sentinel")
    print("="*50)
    raw_data = download_all(config)
    
    # 2. Preprocesar
    print("\n" + "="*50)
    print("PASO 2: Preprocesado y composición temporal")
    print("="*50)
    prithvi_input = preprocess_pipeline(raw_data, config)
    
    # 3. Cargar modelo
    print("\n" + "="*50)
    print("PASO 3: Carga del modelo Prithvi")
    print("="*50)
    device = get_device(config)
    model = load_model(config, device=device)
    
    # 4. Inferencia
    print("\n" + "="*50)
    print("PASO 4: Inferencia y clasificación")
    print("="*50)
    class_map = run_inference(model, prithvi_input, config, device)
    
    # 5. Visualización y estadísticas
    print("\n" + "="*50)
    print("PASO 5: Generación de resultados")
    print("="*50)
    
    # Mapa 2D
    map_path = os.path.join(output_dir, "mapa_clasificacion.png")
    plot_classification_map(class_map, config, map_path)
    
    # GeoTIFF
    geotiff_path = os.path.join(output_dir, "cobertura_sanandres.tif")
    save_geotiff(class_map, raw_data["bbox"], geotiff_path, config)
    
    # Mapa interactivo
    interactive_path = os.path.join(output_dir, "mapa_interactivo.html")
    create_interactive_map(class_map, raw_data["bbox"], config, interactive_path)
    
    # Estadísticas
    stats = compute_statistics(class_map, config)
    print_statistics(stats)
    
    # Guardar estadísticas en JSON
    stats_path = os.path.join(output_dir, "estadisticas.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*50)
    print("PIPELINE COMPLETADO")
    print("="*50)
    print(f"Resultados en: {output_dir}/")
    print(f"  - mapa_clasificacion.png")
    print(f"  - cobertura_sanandres.tif")
    print(f"  - mapa_interactivo.html")
    print(f"  - estadisticas.json")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Detección de cobertura terrestre - San Andrés"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Ruta al archivo de configuración",
    )
    args = parser.parse_args()
    
    main(args.config)
