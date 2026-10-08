"""
Servidor web para visualización de resultados.
"""

import uvicorn
import yaml
from pathlib import Path


def main():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    web_config = config["web"]
    
    print(f"Iniciando servidor web en http://{web_config['host']}:{web_config['port']}")
    uvicorn.run(
        "web.app:app",
        host=web_config["host"],
        port=web_config["port"],
        reload=web_config["debug"],
    )


if __name__ == "__main__":
    main()
