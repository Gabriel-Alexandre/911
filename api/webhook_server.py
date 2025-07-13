import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import openai

from .config import APIConfig

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validar configurações
APIConfig.validate()

# Configurar OpenAI
openai.api_key = APIConfig.OPENAI_API_KEY

app = FastAPI(title="Evolution API Webhook Server", version="1.0.0")

class EvolutionAPIClient:
    def __init__(self, base_url: str, api_key: str, instance: str):
        self.base_url = base_url
        self.api_key = api_key
        self.instance = instance
        self.headers = {
            "Content-Type": "application/json",
            "apikey": api_key
        }
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """Configura o webhook na Evolution API"""
        try:
            async with httpx.AsyncClient() as client:
                url = urljoin(self.base_url, f"/webhook/set/{self.instance}")
                payload = {
                    "url": webhook_url,
                    "enabled": True,
                    "webhook_by_events": True,
                    "webhook_base64": False,
                    "events": ["MESSAGES_UPSERT"]
                }
                
                response = await client.post(url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    logger.info(f"Webhook configurado com sucesso: {webhook_url}")
                    return True
                else:
                    logger.error(f"Erro ao configurar webhook: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")
            return False
    
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

@app.on_event("startup")
async def startup_event():
    """Configura o webhook na Evolution API na inicialização"""
    logger.info("Iniciando servidor webhook...")
    
    # Aguardar um pouco para garantir que a Evolution API esteja pronta
    await asyncio.sleep(2)
    
    # Configurar webhook
    success = await evolution_client.setup_webhook(APIConfig.WEBHOOK_URL)
    if success:
        logger.info("Servidor webhook iniciado com sucesso!")
    else:
        logger.error("Falha ao configurar webhook!")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Endpoint principal do webhook que recebe eventos da Evolution API"""
    try:
        # Obter dados do request
        body = await request.json()
        logger.info(f"Webhook recebido: {json.dumps(body, indent=2)}")
        
        # Verificar se é um evento de mensagem
        if body.get("event") == "MESSAGES_UPSERT":
            await process_message_event(body.get("data", {}))
        
        return JSONResponse({"status": "success"})
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_message_event(data: Dict[str, Any]):
    """Processa eventos de mensagens"""
    try:
        # Extrair informações da mensagem
        key = data.get("key", {})
        message = data.get("message", {})
        
        user_jid = key.get("remoteJid", "unknown")
        message_type = message.get("messageType", "unknown")
        
        if message_type == "conversation":
            # Mensagem de texto
            content = message.get("conversation", "")
            print(f"[TEXTO] {user_jid}: {content}")
            
        elif message_type == "audioMessage":
            # Mensagem de áudio
            audio_message = message.get("audioMessage", {})
            message_id = key.get("id")
            
            if message_id:
                # Obter base64 do áudio
                base64_audio = await evolution_client.get_base64_from_media_message(message_id)
                
                if base64_audio:
                    # Transcrever áudio
                    transcription = await transcribe_audio(base64_audio)
                    
                    if transcription:
                        print(f"[ÁUDIO] {user_jid}: {transcription}")
                    else:
                        print(f"[ÁUDIO] {user_jid}: Erro na transcrição")
                else:
                    print(f"[ÁUDIO] {user_jid}: Erro ao obter áudio")
            else:
                print(f"[ÁUDIO] {user_jid}: ID da mensagem não encontrado")
                
        else:
            logger.info(f"Mensagem ignorada do tipo: {message_type}")
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde"""
    return {"status": "healthy", "service": "on-caller"}

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "On Caller Server",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    } 
