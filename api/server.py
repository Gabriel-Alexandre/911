import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import openai

from .config import APIConfig
# Adicionar imports dos classificadores
from agentes.emergency_classifier import EmergencyClassifierAgent
from agentes.urgency_classifier import UrgencyClassifier

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validar configurações
APIConfig.validate()

# Configurar OpenAI
openai.api_key = APIConfig.OPENAI_API_KEY


app = FastAPI(title="911 Server", version="1.0.0")

# Classe para receber o relato
class RelatoRequest(BaseModel):
    relato: str

# Instanciar classificadores
emergency_classifier = EmergencyClassifierAgent()
urgency_classifier = UrgencyClassifier()

class EvolutionAPIClient:
    def __init__(self, base_url: str, api_key: str, instance: str):
        self.base_url = base_url
        self.api_key = api_key
        self.instance = instance
        self.headers = {
            "Content-Type": "application/json",
            "apikey": api_key
        }
    
    async def get_base64_from_media_message(self, message_id: str) -> Optional[str]:
        """Obtém o base64 de uma mensagem de mídia"""
        try:
            async with httpx.AsyncClient() as client:
                url = urljoin(self.base_url, f"/chat/getBase64FromMediaMessage/{self.instance}")
                payload = {"messageId": message_id}
                
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("base64")
                else:
                    logger.error(f"Erro ao obter base64: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erro ao obter base64 da mensagem: {e}")
            return None

# Instanciar cliente da Evolution API
evolution_client = EvolutionAPIClient(
    APIConfig.EV_URL, 
    APIConfig.EV_API_KEY, 
    APIConfig.EV_INSTANCE
)

async def transcribe_audio(base64_audio: str) -> Optional[str]:
    """Transcreve áudio usando OpenAI Whisper"""
    try:
        # Decodificar base64
        audio_data = base64.b64decode(base64_audio)
        
        # Enviar para OpenAI Whisper
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=("audio.ogg", audio_data, "audio/ogg"),
            language="pt"
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"Erro na transcrição: {e}")
        return None

async def parse_message(data: Dict[str, Any]) -> str:
    """
    Extrai o texto da mensagem
    """
    key = data.get("key", {})
    message = data.get("message", {})
    message_type = data.get("messageType", "unknown")
                
    if message_type == "conversation":        
        return message.get("conversation")          
            
    elif message_type == "audioMessage":
        message_id = key.get("id")
        
        if message_id:
            base64_audio = await evolution_client.get_base64_from_media_message(message_id)
            
            if base64_audio:
                transcription = await transcribe_audio(base64_audio)
                
                if transcription:
                    return transcription

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Endpoint principal do webhook que recebe eventos da Evolution API"""
    try:
        # Obter dados do request
        body = await request.json()
        
        # Verificar se é um evento de mensagem
        if body.get("event") == "messages.upsert":
            await process_message_event(body.get("data", {}))
        
        return JSONResponse({"status": "success"})
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_message_event(data: Dict[str, Any]):
    """Processa eventos de mensagens"""
    try:
        contact_name = data.get("pushName")
        user_jid = data.get("key", {}).get("remoteJid", "unknown")
        contact_number = user_jid.split("@")[0]
        
        parsed_message = await parse_message(data)
        
        print(f"Relato: {parsed_message}")
        
        if parsed_message:
            classificacao = classificar_emergencia(parsed_message)
            
            agencias = classificacao["emergency_type"]
            
            # Fazer join da lista de agências
            agencias_texto = ", ".join(agencias) if isinstance(agencias, list) else agencias
            
            message_result = f"Olá, {contact_name}, recebemos sua mensagem e estamos encaminhando para o atendimento do {agencias_texto}, em breve um atendente irá entrar em contato com você."
            
            print(f"Mensagem: {message_result}")

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")


def classificar_emergencia(relato: str):
    # Passo 1: Classificar emergência (tipos de serviço)
    emergency_result = emergency_classifier.classify_emergency(relato)
        
    # Passo 2: Classificar urgência usando o resultado anterior
    urgency_result = urgency_classifier.classify_emergency(relato, emergency_result)
        
    # Passo 3: Retornar resultado completo em formato de dicionário
    return {
        "relato": relato,
        "emergency_classification": emergency_result["tipos_emergencia"],
        "nivel_urgencia": urgency_result.nivel_urgencia,
        "status": "sucesso",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/classify")
async def classify_emergency_report(request: RelatoRequest):
    """
    Rota para classificar relatos de emergência
    
    Args:
        request: Objeto com o relato da emergência
        
    Returns:
        Dict: Resultado da classificação completa
    """
    try:
        relato = request.relato
        
        return classificar_emergencia(relato)
        
    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        raise HTTPException(status_code=500, detail={
            "status": "erro",
            "mensagem": str(e),
            "relato": request.relato if hasattr(request, 'relato') else "Não disponível"
        })

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde"""
    return {"status": "healthy", "service": "911-server"}

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "911 Server",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "classify": "/classify",
            "health": "/health"
        }
    } 
