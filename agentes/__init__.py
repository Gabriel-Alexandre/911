"""
Módulo API - Servidor Webhook Evolution API

Este módulo contém o servidor webhook completo para processar eventos
da Evolution API, incluindo mensagens de texto e áudio com transcrição.
"""

from .emergency_classifier import EmergencyClassifierAgent
from .urgency_classifier import UrgencyClassifier
from .rag_service import RAGService
from .vectordb_config import VectorDBConfig


__all__ = ["EmergencyClassifierAgent", "UrgencyClassifier", "RAGService", "VectorDBConfig"]
__version__ = "1.0.0" 
