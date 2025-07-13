"""
Pacote de Agentes para Classificação de Emergências

Este pacote contém os agentes classificadores que utilizam LangChain e OpenAI
para identificar tipos de emergência e sugerir qual serviço acionar.
"""

from .emergency_classifier import EmergencyClassifierAgent
from .urgency_classifier import UrgencyClassifier
from .vectordb_config import VectorDBConfig
from .rag_service import RAGService

__all__ = [
    "EmergencyClassifierAgent",
    "UrgencyClassifier", 
    "VectorDBConfig",
    "RAGService"
] 