"""
Pacote de Agentes para Classificação de Emergências

Este pacote contém o agente classificador que utiliza LangChain e OpenAI
para identificar tipos de emergência e sugerir qual serviço acionar.
"""

from .emergency_classifier import EmergencyClassifierAgent

__all__ = ["EmergencyClassifierAgent"] 