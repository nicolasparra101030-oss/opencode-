"""
Módulo de carga y configuración del modelo Prithvi.
"""

import torch
import torch.nn as nn
from transformers import AutoModel, AutoConfig
import yaml
from pathlib import Path


class PrithviClassifier(nn.Module):
    """
    Clasificador basado en Prithvi con adaptación para 8 canales de entrada.
    """
    
    def __init__(
        self,
        model_id: str = "ibm-nasa-geospatial/Prithvi-100M",
        n_channels: int = 8,
        n_classes: int = 12,
        pretrained: bool = True,
    ):
        super().__init__()
        
        # Cargar modelo base
        if pretrained:
            self.backbone = AutoModel.from_pretrained(model_id)
        else:
            config = AutoConfig.from_pretrained(model_id)
            self.backbone = AutoModel.from_config(config)
        
        # Adaptar primera capa convolucional para 8 canales si es necesario
        original_in_channels = 6  # Prithvi original usa 6 bandas
        if n_channels != original_in_channels:
            self._adapt_input_layer(n_channels)
        
        # Obtener dimensión del embedding
        hidden_size = self.backbone.config.hidden_size
        
        # Cabeza de clasificación
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, n_classes),
        )
    
    def _adapt_input_layer(self, n_channels: int):
        """Adapta la primera capa para aceptar más canales."""
        # Buscar la primera capa convolucional
        for name, module in self.backbone.named_modules():
            if isinstance(module, nn.Conv2d):
                # Crear nueva capa con el número correcto de canales
                new_conv = nn.Conv2d(
                    n_channels,
                    module.out_channels,
                    kernel_size=module.kernel_size,
                    stride=module.stride,
                    padding=module.padding,
                    bias=module.bias is not None,
                )
                
                # Inicializar con pesos existentes (promedio para canales extra)
                with torch.no_grad():
                    if n_channels > module.in_channels:
                        # Copiar pesos existentes
                        new_conv.weight[:, :module.in_channels] = module.weight
                        # Promediar para canales adicionales
                        mean_weight = module.weight.mean(dim=1, keepdim=True)
                        new_conv.weight[:, module.in_channels:] = mean_weight.expand(
                            -1, n_channels - module.in_channels, -1, -1
                        )
                    else:
                        new_conv.weight = module.weight[:, :n_channels]
                    if module.bias is not None:
                        new_conv.bias = module.bias
                
                # Reemplazar la capa
                parent_name = ".".join(name.split(".")[:-1])
                child_name = name.split(".")[-1]
                parent = self.backbone.get_submodule(parent_name) if parent_name else self.backbone
                setattr(parent, child_name, new_conv)
                break
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Tensor (B, 8, H, W) con bandas normalizadas
        
        Returns:
            Logits (B, n_classes, H, W)
        """
        # Prithvi espera (B, C, H, W)
        outputs = self.backbone(pixel_values=x)
        
        # Obtener features del último hidden state
        features = outputs.last_hidden_state  # (B, seq_len, hidden_size)
        
        # Reshape a mapa espacial
        B, seq_len, hidden = features.shape
        H = W = int(seq_len ** 0.5)
        features = features.transpose(1, 2).reshape(B, hidden, H, W)
        
        # Clasificación píxel a píxel
        logits = self.classifier(features.mean(dim=[2, 3]))  # (B, n_classes)
        
        return logits


def load_model(config: dict, device: str = "auto") -> PrithviClassifier:
    """
    Carga el modelo Prithvi con la configuración especificada.
    
    Args:
        config: Diccionario de configuración
        device: Dispositivo a usar
    
    Returns:
        Modelo cargado y listo para inferencia
    """
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    model_config = config["model"]
    
    model = PrithviClassifier(
        model_id=model_config["hf_model_id"],
        n_channels=model_config["n_channels"],
        n_classes=len(model_config["classes"]),
        pretrained=True,
    )
    
    model = model.to(device)
    model.eval()
    
    print(f"Modelo cargado en {device}")
    return model


def get_device(config: dict) -> str:
    """Determina el dispositivo a usar."""
    device = config["processing"]["device"]
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device
