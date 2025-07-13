"""
Arquivo principal para executar o servidor para o modulo de on caller
"""

import asyncio
import uvicorn
from .server import app
from .config import APIConfig, init_database, test_database_connection

async def setup_database():
    """Configurar banco de dados"""
    try:
        connection_ok = await test_database_connection()
        if not connection_ok:
            print("⚠️  Inicializando banco de dados...")
            await init_database()
            print("✅ Banco de dados inicializado!")
    except Exception as e:
        print(f"❌ Erro ao configurar banco: {e}")
        print("⚠️  Servidor será iniciado, mas pode não funcionar corretamente.")

def main():
    """Função principal para executar o servidor"""
    config = APIConfig.get_server_config()
    
    print("🚀 Iniciando servidor para o on caller...")
    print(f"📍 Host: {config['host']}")
    print(f"🔌 Porta: {config['port']}")
    print(f"🔄 Reload: {config['reload']}")
    print(f"📝 Log Level: {config['log_level']}")
    print("=" * 50)
    
    # Configurar banco de dados
    try:
        asyncio.run(setup_database())
    except Exception as e:
        print(f"❌ Erro na configuração inicial: {e}")
    
    uvicorn.run(
        "api.server:app",
        host=config["host"],
        port=config["port"],
        reload=config["reload"],
        log_level=config["log_level"]
    )

if __name__ == "__main__":
    main() 
