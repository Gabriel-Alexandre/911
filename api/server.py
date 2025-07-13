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
from openai import OpenAI
import io

from .config import APIConfig, db_client
from .ocorrencias_service import ocorrencia_service
from Crypto.Cipher import AES
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
import base64
from agentes.emergency_classifier import EmergencyClassifierAgent
from agentes.urgency_classifier import UrgencyClassifier

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validar configurações
APIConfig.validate()

# Configurar OpenAI (nova versão)
openai_client = OpenAI(api_key=APIConfig.OPENAI_API_KEY)


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

# Modelos Pydantic para validação das rotas de ocorrências
class OcorrenciaData(BaseModel):
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

async def download_audio_from_url(url: str) -> Optional[bytes]:
    """Faz download do áudio a partir da URL"""
    try:
        # Headers para simular um navegador e acessar o WhatsApp
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            if response.status_code == 200:
                logger.info(f"Download do áudio realizado com sucesso. Tamanho: {len(response.content)} bytes")
                return response.content
            else:
                logger.error(f"Erro ao fazer download do áudio: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Erro ao fazer download do áudio: {e}")
        return None
    
def decrypt_enc(enc_bytes: bytes, media_key_b64: str, media_type: str = "audio") -> Optional[bytes]:
    """
    Descriptografa mídia do WhatsApp usando o algoritmo correto
    """
    try:
        logger.info(f"Iniciando descriptografia. Tamanho do arquivo: {len(enc_bytes)} bytes")
        
        # Decodificar mediaKey de Base64
        media_key = base64.b64decode(media_key_b64)
        logger.info(f"MediaKey decodificada. Tamanho: {len(media_key)} bytes")
        
        # Gerar chave completa usando HKDF
        info = f"WhatsApp {media_type.capitalize()} Keys".encode()
        full_key = HKDF(
            algorithm=hashes.SHA256(),
            length=112,
            salt=None,
            info=info
        ).derive(media_key)
        
        logger.info(f"Chave completa gerada. Tamanho: {len(full_key)} bytes")
        
        # Extrair IV e chave de criptografia
        iv = full_key[:16]
        enc_key = full_key[16:48]
        
        # Remover MAC (últimos 10 bytes)
        if len(enc_bytes) <= 10:
            logger.error("Arquivo muito pequeno para descriptografar")
            return None
            
        payload = enc_bytes[:-10]
        logger.info(f"Payload para descriptografia: {len(payload)} bytes")
        
        # Descriptografar usando AES-CBC
        cipher = AES.new(enc_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(payload)
        
        # Remover padding
        if len(decrypted) == 0:
            logger.error("Dados descriptografados vazios")
            return None
            
        pad = decrypted[-1]
        if pad > len(decrypted):
            logger.error(f"Padding inválido: {pad}")
            return None
            
        result = decrypted[:-pad]
        logger.info(f"Descriptografia concluída. Tamanho final: {len(result)} bytes")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro na descriptografia: {e}")
        return None

async def transcribe_audio_from_url(audio_url: str, media_key: str) -> Optional[str]:
    """Transcreve áudio do WhatsApp com descriptografia"""
    try:
        # Fazer download do arquivo criptografado
        enc = await download_audio_from_url(audio_url)
        if not enc:
            logger.error("Falha no download")
            return None

        # Descriptografar o arquivo
        decrypted = decrypt_enc(enc, media_key, media_type="audio")
        if not decrypted:
            logger.error("Falha na descriptografia")
            return None

        # Verificar se o arquivo descriptografado é válido
        if len(decrypted) < 100:
            logger.error(f"Arquivo descriptografado muito pequeno: {len(decrypted)} bytes")
            return None

        # Verificar formato do arquivo
        audio_headers = decrypted[:20]
        logger.info(f"Headers do arquivo descriptografado: {audio_headers.hex()}")
        
        if decrypted.startswith(b"OggS"):
            logger.info("✓ Arquivo OGG válido detectado!")
            file_extension = "ogg"
        elif audio_headers.startswith(b'ID3') or audio_headers.startswith(b'\xff\xfb') or audio_headers.startswith(b'\xff\xf3'):
            logger.info("✓ Arquivo MP3 detectado!")
            file_extension = "mp3"
        elif audio_headers.startswith(b'RIFF'):
            logger.info("✓ Arquivo WAV detectado!")
            file_extension = "wav"
        elif audio_headers.startswith(b'ftyp'):
            logger.info("✓ Arquivo M4A/MP4 detectado!")
            file_extension = "m4a"
        else:
            logger.warning(f"Formato de arquivo não reconhecido. Headers: {audio_headers[:8].hex()}")
            # Tentar como OGG mesmo assim
            file_extension = "ogg"

        # Criar arquivo temporário em memória
        audio_file = io.BytesIO(decrypted)
        audio_file.name = f"voice.{file_extension}"
        
        logger.info(f"Enviando arquivo para transcrição. Tamanho: {len(decrypted)} bytes")
        
        # Fazer transcrição
        res = openai_client.audio.transcriptions.create(
            model="whisper-1", file=audio_file, language="pt"
        )
        
        logger.info(f"Transcrição realizada com sucesso: {res.text}")
        return res.text
        
    except Exception as e:
        logger.error(f"Erro na transcrição: {e}")
        
        # Salvar arquivo para debug se disponível
        try:
            if 'decrypted' in locals() and 'file_extension' in locals():
                debug_filename = f"debug_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
                with open(debug_filename, 'wb') as f:
                    f.write(decrypted)
                logger.info(f"Arquivo salvo para debug: {debug_filename}")
        except Exception as save_error:
            logger.error(f"Erro ao salvar arquivo para debug: {save_error}")
        
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
        audio = data["message"]["audioMessage"]
        url = audio.get("url")
        media_key = audio.get("mediaKey")

        if url and media_key:
            logger.info("Processando áudio criptografado via .enc")
            
            return await transcribe_audio_from_url(url, media_key)
        else:
            logger.error("URL do áudio não encontrada no payload")
            return None

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
            
            # Preparar dados para salvar no banco
            backend_data = {
                "success": True,
                "emergency_type": classificacao["emergency_classification"],
                "urgency_level": classificacao["nivel_urgencia"],
                "situation": parsed_message,
                "confidence_score": 0.9,  # Pode ajustar baseado na classificação
                "location": "Não informado",
                "victim": None,
                "reporter": contact_number,
                "timestamp": datetime.now().isoformat()
            }
        
            # Salvar ocorrência no banco de dados
            try:
                saved_data = await ocorrencia_service.create_ocorrencia(backend_data)
                logger.info(f"Ocorrência salva no banco - ID: {saved_data['id']}")
            except Exception as db_error:
                logger.error(f"Erro ao salvar no banco de dados: {db_error}")
                # Continuar mesmo se houver erro no banco
            
            # Enviar mensagem de resposta
            success = await evolution_client.send_message(contact_number, message_result)
            
            if success:
                logger.info(f"Mensagem de resposta enviada com sucesso para {contact_number}")
            else:
                logger.error(f"Falha ao enviar mensagem de resposta para {contact_number}")

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")


async def send_message_with_classification(
    phone_number: str, 
    message: str, 
    original_message: str,
    classification_data: dict,
    contact_name: str = None
):
    """
    Função interna para enviar mensagem com dados de classificação já processados
    """
    try:
        # Preparar dados para salvar no banco usando a classificação já feita
        backend_data = {
            "success": True,
            "emergency_type": classification_data["emergency_classification"],
            "urgency_level": classification_data["nivel_urgencia"],
            "situation": original_message,
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
        success = await evolution_client.send_message(phone_number, message)
        
        if success:
            logger.info(f"Mensagem de resposta enviada com sucesso para {contact_name} ({phone_number})")
        else:
            logger.error(f"Falha ao enviar mensagem de resposta para {contact_name} ({phone_number})")
            
        return success
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem com classificação: {e}")
        return False


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
            "message": "Teste de mensagem",
            "classification_data": {  // Opcional - se não fornecido, será classificado
                "emergency_classification": ["bombeiros"],
                "nivel_urgencia": 5,
                "status": "sucesso"
            }
        }
    """
    try:
        phone_number = request.get("phone_number")
        message = request.get("message")
        classification_data = request.get("classification_data")
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="phone_number e message são obrigatórios")
        
        # Se não tem dados de classificação, classificar a mensagem
        if not classification_data:
            classification_data = classificar_emergencia(message)
            original_message = message
        else:
            # Se tem dados de classificação, usar a mensagem como situação original
            original_message = classification_data.get("relato", message)
        
        # Preparar dados para salvar no banco
        backend_data = {
            "success": True,
            "emergency_type": classification_data["emergency_classification"],
            "urgency_level": classification_data["nivel_urgencia"],
            "situation": original_message,
            "confidence_score": 0.9,
            "location": "Não informado",
            "victim": None,
            "reporter": phone_number,
            "timestamp": datetime.now().isoformat()
        }
        
        # Salvar ocorrência no banco de dados
        try:
            saved_data = await ocorrencia_service.create_ocorrencia(backend_data)
            logger.info(f"Ocorrência salva no banco - ID: {saved_data['id']}")
        except Exception as db_error:
            logger.error(f"Erro ao salvar no banco de dados: {db_error}")
            # Continuar mesmo se houver erro no banco
        
        # Enviar mensagem para WhatsApp
        success = await enviar_mensagem_whatsapp(phone_number, message)
        
        return {
            "status": "success" if success else "error",
            "message": "Mensagem enviada com sucesso" if success else "Falha ao enviar mensagem",
            "phone_number": phone_number,
            "classification": classification_data,
            "saved_to_database": saved_data if saved_data else False
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
            "ocorrencias": "/api/ocorrencias",
            "send-message": "/send-message"
        }
    }


# Rota para listar ocorrências
@app.get("/api/ocorrencias")
async def get_ocorrencias():
    """Lista todas as ocorrências"""
    try:
        ocorrencias = await ocorrencia_service.get_all_ocorrencias()
        return {"ocorrencias": ocorrencias, "total": len(ocorrencias)}
    except Exception as e:
        logger.error(f"Erro ao listar ocorrências: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
