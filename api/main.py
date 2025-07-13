"""
Arquivo principal para executar o servidor webhook
"""

import uvicorn
from .webhook_server import app
from .config import APIConfig

def main():
    """Função principal para executar o servidor"""
    config = APIConfig.get_server_config()
    
    print("🚀 Iniciando servidor webhook Evolution API...")
    print(f"📍 Host: {config['host']}")
    print(f"🔌 Porta: {config['port']}")
    print(f"🔄 Reload: {config['reload']}")
    print(f"📝 Log Level: {config['log_level']}")
    print("=" * 50)
    
    uvicorn.run(
        "api.webhook_server:app",
        host=config["host"],
        port=config["port"],
        reload=config["reload"],
        log_level=config["log_level"]
    )

if __name__ == "__main__":
    main() 
