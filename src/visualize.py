"""
Módulo de visualización: mapas, leyendas y estadísticas.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import rasterio
from rasterio.transform import from_bounds
import folium
from folium import plugins
import yaml
from pathlib import Path
from collections import Counter


# Paleta de colores para clases (estilo ESA WorldCover)
CLASS_COLORS = {
    0: "#000000",   # No data - negro
    1: "#006400",   # Tree cover - verde oscuro
    2: "#ffbb22",   # Shrubland - naranja claro
    3: "#ffff4c",   # Grassland - amarillo
    4: "#f096ff",   # Cropland - rosa
    5: "#fa0000",   # Built-up - rojo
    6: "#b4b4b4",   # Bare / sparse - gris
    7: "#f0f0f0",   # Snow and ice - blanco
    8: "#0064c8",   # Open water - azul
    9: "#0096a0",   # Herbaceous wetland - cian
    10: "#00cf75",  # Mangroves - verde claro
    11: "#fae6a0",  # Moss and lichen - beige
}


def create_colormap(config: dict) -> ListedColormap:
    """Crea un colormap personalizado para las clases."""
    n_classes = len(config["model"]["classes"])
    colors = [CLASS_COLORS.get(i, "#000000") for i in range(n_classes)]
    return ListedColormap(colors)


def plot_classification_map(
    class_map: np.ndarray,
    config: dict,
    output_path: str,
    title: str = "Cobertura Terrestre - San Andrés",
):
    """Genera un mapa 2D con la clasificación."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    cmap = create_colormap(config)
    im = ax.imshow(class_map, cmap=cmap, vmin=0, vmax=len(config["model"]["classes"])-1)
    
    # Leyenda
    classes = config["model"]["classes"]
    relevant = config["model"]["relevant_classes"]
    patches = [
        mpatches.Patch(color=CLASS_COLORS.get(i, "#000000"), label=classes[i])
        for i in relevant
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=9)
    
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Mapa guardado en: {output_path}")


def compute_statistics(class_map: np.ndarray, config: dict) -> dict:
    """Calcula estadísticas de cobertura por clase."""
    classes = config["model"]["classes"]
    relevant = config["model"]["relevant_classes"]
    
    # Contar píxeles por clase
    counts = Counter(class_map.flatten())
    total_pixels = class_map.size
    
    stats = {}
    for class_id in relevant:
        count = counts.get(class_id, 0)
        percentage = (count / total_pixels) * 100
        stats[classes[class_id]] = {
            "pixels": int(count),
            "percentage": round(percentage, 2),
        }
    
    return stats


def save_geotiff(
    class_map: np.ndarray,
    bbox: object,
    output_path: str,
    config: dict,
):
    """Guarda el mapa clasificado como GeoTIFF."""
    H, W = class_map.shape
    
    # Transformación geoespacial
    min_lon, min_lat, max_lon, max_lat = bbox
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, W, H)
    
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=H,
        width=W,
        count=1,
        dtype=class_map.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(class_map, 1)
        dst.update_tags(
            AREA_OR_POINT="Area",
            DESCRIPTION="Clasificación de cobertura terrestre - Prithvi",
        )
    
    print(f"GeoTIFF guardado en: {output_path}")


def create_interactive_map(
    class_map: np.ndarray,
    bbox: object,
    config: dict,
    output_path: str,
):
    """Crea un mapa interactivo HTML con Folium."""
    classes = config["model"]["classes"]
    relevant = config["model"]["relevant_classes"]
    
    # Centro del mapa
    min_lon, min_lat, max_lon, max_lat = bbox
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    # Crear mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="OpenStreetMap",
    )
    
    # Añadir capa de imagen clasificada
    # Convertir a imagen para overlay
    from PIL import Image
    import io
    import base64
    
    # Crear imagen con colores
    cmap = create_colormap(config)
    colored = cmap(class_map / max(len(classes) - 1, 1))
    img = Image.fromarray((colored[:, :, :3] * 255).astype(np.uint8))
    
    # Guardar en buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()
    
    # Añadir overlay
    folium.raster_layers.ImageOverlay(
        image=f"data:image/png;base64,{img_str}",
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=0.7,
        name="Cobertura Terrestre",
    ).add_to(m)
    
    # Añadir leyenda
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 180px;
                border:2px solid grey; z-index:9999; 
                background-color:white;
                padding: 10px;
                font-size: 12px;">
    <b>Leyenda</b><br>
    """
    for i in relevant:
        color = CLASS_COLORS.get(i, "#000000")
        legend_html += f'<i style="background:{color};width:12px;height:12px;display:inline-block;"></i> {classes[i]}<br>'
    legend_html += "</div>"
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Control de capas
    folium.LayerControl().add_to(m)
    
    m.save(output_path)
    print(f"Mapa interactivo guardado en: {output_path}")


def print_statistics(stats: dict):
    """Imprime estadísticas en consola."""
    print("\n" + "="*50)
    print("ESTADÍSTICAS DE COBERTURA TERRESTRE")
    print("="*50)
    print(f"{'Clase':<30} {'% Cobertura':>12}")
    print("-"*50)
    for class_name, data in sorted(stats.items(), key=lambda x: x[1]["percentage"], reverse=True):
        print(f"{class_name:<30} {data['percentage']:>10.2f}%")
    print("="*50)
