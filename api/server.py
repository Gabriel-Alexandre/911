import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import openai

from .config import APIConfig, db_client
from .entities_service import emergency_service, ticket_service, backend_to_emergency
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

# Configurar CORS para permitir conexões do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique as origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Classe para receber o relato
class RelatoRequest(BaseModel):
    relato: str

# Modelos Pydantic para validação das rotas de emergência
class EmergencyStatusUpdate(BaseModel):
    status: str

class BackendEmergencyData(BaseModel):
    success: bool = True
    emergency_type: List[str]
    urgency_level: int
    situation: str
    confidence_score: float
    location: Optional[str] = None
    victim: Optional[str] = None
    reporter: Optional[str] = None
    timestamp: Optional[str] = None

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
                url = urljoin(self.base_url, f"/message/sendText/{self.instance}")
                
                # Formatar número do telefone
                if not phone_number.endswith("@s.whatsapp.net"):
                    phone_number = f"{phone_number}@s.whatsapp.net"
                
                payload = {
                    "number": phone_number,
                    "text": message,
                    "options": {
                        "delay": 0,
                        "presence": "composing",
                        "linkPreview": False
                    }
                }
                
                logger.info(f"Enviando mensagem para {phone_number}: {message}")
                
                response = await client.post(url, json=payload, headers=self.headers)
                print(f"Response: {response.json()}")
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

@app.on_event("startup")
async def startup_event():
    """Conectar ao banco de dados na inicialização"""
    await db_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Desconectar do banco de dados no encerramento"""
    await db_client.disconnect()

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

# === ROTAS ORIGINAIS ===

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

# === ROTAS DE EMERGÊNCIA (COMPATÍVEIS COM FRONTEND) ===

@app.get("/api/emergencies")
async def get_emergencies(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    level: Optional[str] = Query(None, description="Filtrar por nível"),
    responsible: Optional[str] = Query(None, description="Filtrar por responsável"),
    location: Optional[str] = Query(None, description="Filtrar por localização")
):
    """
    Endpoint compatível com EmergencyService.getEmergencies()
    GET /api/emergencies?status=ATIVO&level=CRÍTICO
    """
    try:
        filters = {}
        if status:
            filters['status'] = status
        if level:
            filters['level'] = level
        if responsible:
            filters['responsible'] = responsible
        if location:
            filters['location'] = location
        
        emergencies = await emergency_service.get_emergencies(filters if filters else None)
        return emergencies
    except Exception as e:
        # Em caso de erro, retornar dados mock para desenvolvimento
        return emergency_service.get_mock_emergencies()

@app.patch("/api/emergencies/{emergency_id}")
async def update_emergency_status(emergency_id: str, update_data: EmergencyStatusUpdate):
    """
    Endpoint compatível com EmergencyService.updateEmergencyStatus()
    PATCH /api/emergencies/{id}
    """
    try:
        emergency = await emergency_service.update_emergency_status(emergency_id, update_data.status)
        if not emergency:
            raise HTTPException(status_code=404, detail="Emergência não encontrada")
        return emergency
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emergencies/{emergency_id}")
async def get_emergency_by_id(emergency_id: str):
    """
    Buscar emergência por ID
    GET /api/emergencies/{id}
    """
    try:
        emergency = await emergency_service.get_emergency_by_id(emergency_id)
        if not emergency:
            raise HTTPException(status_code=404, detail="Emergência não encontrada")
        return emergency
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emergencies")
async def create_emergency(emergency_data: dict):
    """
    Criar nova emergência
    POST /api/emergencies
    """
    try:
        emergency = await emergency_service.create_emergency(emergency_data)
        return emergency
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emergencies/from-backend")
async def create_emergency_from_backend(backend_data: BackendEmergencyData):
    """
    Criar emergência a partir de dados BackendEmergency
    POST /api/emergencies/from-backend
    """
    try:
        emergency = await emergency_service.create_emergency_from_backend(backend_data.dict())
        return emergency
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === ROTAS DE TICKET ===

@app.get("/api/tickets")
async def get_tickets(
    urgency_level: Optional[int] = Query(None, description="Filtrar por nível de urgência"),
    emergency_type: Optional[str] = Query(None, description="Filtrar por tipo de emergência"),
    location: Optional[str] = Query(None, description="Filtrar por localização")
):
    """
    Listar tickets
    GET /api/tickets?urgency_level=5&emergency_type=bombeiros
    """
    try:
        filters = {}
        if urgency_level:
            filters['urgency_level'] = urgency_level
        if emergency_type:
            filters['emergency_type'] = emergency_type
        if location:
            filters['location'] = location
        
        tickets = await ticket_service.get_all_tickets(filters if filters else None)
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tickets")
async def create_ticket(ticket_data: BackendEmergencyData):
    """
    Criar novo ticket
    POST /api/tickets
    """
    try:
        ticket = await ticket_service.create_ticket(ticket_data.dict())
        return ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tickets/with-emergency")
async def create_ticket_with_emergency(backend_data: BackendEmergencyData):
    """
    Criar ticket e emergência simultaneamente
    POST /api/tickets/with-emergency
    """
    try:
        result = await ticket_service.create_ticket_and_emergency(backend_data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde"""
    try:
        # Testar conexão com banco
        connection_ok = await db_client.test_connection()
        
        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "service": "911-server",
            "database": "connected" if connection_ok else "disconnected",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "911-server",
            "error": str(e),
            "version": "1.0.0"
        }

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
        
        # Classificar a mensagem antes de enviar
        classificacao = classificar_emergencia(message)
        
        # Preparar dados para salvar no banco
        backend_data = {
            "success": True,
            "emergency_type": classificacao["emergency_classification"],
            "urgency_level": classificacao["nivel_urgencia"],
            "situation": message,
            "confidence_score": 0.9,  # Pode ajustar baseado na classificação
            "location": "Não informado",
            "victim": None,
            "reporter": phone_number,
            "timestamp": datetime.now().isoformat()
        }
        
        # Salvar ticket e emergência no banco de dados
        try:
            saved_data = await ticket_service.create_ticket_and_emergency(backend_data)
            logger.info(f"Dados salvos no banco - Ticket ID: {saved_data['ticket']['id']}, Emergency ID: {saved_data['emergency']['id']}")
        except Exception as db_error:
            logger.error(f"Erro ao salvar no banco de dados: {db_error}")
            # Continuar mesmo se houver erro no banco
        
        # Enviar mensagem para WhatsApp
        success = await enviar_mensagem_whatsapp(phone_number, message)
        
        return {
            "status": "success" if success else "error",
            "message": "Mensagem enviada com sucesso" if success else "Falha ao enviar mensagem",
            "phone_number": phone_number,
            "classification": classificacao,
            "saved_to_database": "saved_data" in locals()
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
            "emergencies": "/api/emergencies",
            "tickets": "/api/tickets",
            "send-message": "/send-message"
        }
    } 
