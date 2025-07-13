"""
Configurações do módulo API
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class APIConfig:
    """Configurações da API"""
    
    # Configurações da Evolution API
    EV_URL: str = os.getenv("EV_URL", "http://localhost:8080")
    EV_API_KEY: Optional[str] = os.getenv("EV_API_KEY")
    EV_INSTANCE: Optional[str] = os.getenv("EV_INSTANCE")
    
    # Configuração OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Configurações do servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    @classmethod
    def validate(cls) -> bool:
        """Valida se todas as variáveis obrigatórias estão configuradas"""
        
        missing_vars = []
        for var_name, var_value in [
            ("EV_API_KEY", cls.EV_API_KEY),
            ("EV_INSTANCE", cls.EV_INSTANCE),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY)
        ]:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente obrigatórias não configuradas: {', '.join(missing_vars)}")
                
        return True
    
    @classmethod
    def get_server_config(cls) -> dict:
        """Retorna configuração do servidor"""
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "reload": cls.RELOAD,
            "log_level": cls.LOG_LEVEL
        } 
