"""
Módulo API - Servidor Webhook Evolution API

Este módulo contém o servidor webhook completo para processar eventos
da Evolution API, incluindo mensagens de texto e áudio com transcrição.
"""

from .webhook_server import app, EvolutionAPIClient
from .config import APIConfig
from .main import main

__all__ = ["app", "EvolutionAPIClient", "APIConfig", "main"]
__version__ = "1.0.0" 
