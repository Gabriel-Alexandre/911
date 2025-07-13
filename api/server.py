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
    
    async def send_message(self, phone_number: str, message: str) -> bool:
        """
        Envia mensagem para um número de telefone
        
        Args:
            phone_number: Número do telefone (ex: 5511999999999)
            message: Texto da mensagem
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            async with httpx.AsyncClient() as client:
                url = urljoin(self.base_url, f"/chat/sendText/{self.instance}")
                
                # Formatar número do telefone
                if not phone_number.endswith("@s.whatsapp.net"):
                    phone_number = f"{phone_number}@s.whatsapp.net"
                
                payload = {
                    "number": phone_number,
                    "text": message
                }
                
                logger.info(f"Enviando mensagem para {phone_number}: {message}")
                
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Mensagem enviada com sucesso: {data}")
                    return True
                else:
                    logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return False

# Instanciar cliente da Evolution API
evolution_client = EvolutionAPIClient(
    APIConfig.EV_URL, 
    APIConfig.EV_API_KEY, 
    APIConfig.EV_INSTANCE
)

def formatar_agencias(agencias: list) -> str:
    """
    Formata lista de agências de forma gramatical em português
    
    Args:
        agencias: Lista de strings com nomes das agências
        
    Returns:
        String formatada gramaticalmente
    """
    if not agencias:
        return ""
    
    if len(agencias) == 1:
        return agencias[0]
    elif len(agencias) == 2:
        return f"{agencias[0]} e {agencias[1]}"
    else:
        # Para 3 ou mais: "SAMU, Polícia e Bombeiros"
        return ", ".join(agencias[:-1]) + f" e {agencias[-1]}"

async def enviar_mensagem_whatsapp(phone_number: str, message: str) -> bool:
    """
    Função externa para enviar mensagens via WhatsApp
    
    Args:
        phone_number: Número do telefone (ex: 5511999999999)
        message: Texto da mensagem
        
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        return await evolution_client.send_message(phone_number, message)
    except Exception as e:
        logger.error(f"Erro na função enviar_mensagem_whatsapp: {e}")
        return False

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
        
        
        if parsed_message:
            classificacao = classificar_emergencia(parsed_message)
            print(f"Relato: {parsed_message} foi classificado como {classificacao}")

            agencias = classificacao["emergency_classification"] 
            
            agencias_texto = formatar_agencias(agencias)
            
            message_result = f"Olá, {contact_name}, recebemos sua mensagem e estamos encaminhando para o atendimento do {agencias_texto}, em breve um atendente irá entrar em contato com você."
            
            # Enviar mensagem de resposta
            success = await evolution_client.send_message(contact_number, message_result)
            
            if success:
                logger.info(f"Mensagem de resposta enviada com sucesso para {contact_number}")
            else:
                logger.error(f"Falha ao enviar mensagem de resposta para {contact_number}")

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

@app.post("/send-message")
async def send_message_endpoint(request: dict):
    """
    Endpoint para testar envio de mensagens
    
    Body:
        {
            "phone_number": "5511999999999",
            "message": "Teste de mensagem"
        }
    """
    try:
        phone_number = request.get("phone_number")
        message = request.get("message")
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="phone_number e message são obrigatórios")
        
        success = await enviar_mensagem_whatsapp(phone_number, message)
        
        return {
            "status": "success" if success else "error",
            "message": "Mensagem enviada com sucesso" if success else "Falha ao enviar mensagem",
            "phone_number": phone_number
        }
        
    except Exception as e:
        logger.error(f"Erro no endpoint send-message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "911 Server",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "classify": "/classify",
            "health": "/health",
            "send-message": "/send-message"
        }
    } 
