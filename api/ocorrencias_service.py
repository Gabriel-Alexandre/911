"""
Serviço para gerenciar ocorrências
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import asyncpg
from .config import db_client


class OcorrenciaService:
    """Serviço para gerenciar ocorrências"""
    
    async def create_ocorrencia(self, ocorrencia_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma nova ocorrência"""
        query = """
            INSERT INTO ocorrencias (
                id, success, emergency_type, urgency_level, situation, 
                confidence_score, location, victim, reporter, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
        """
        
        ocorrencia_id = str(uuid.uuid4())
        
        # Converter timestamp string para datetime se fornecido
        timestamp = ocorrencia_data.get('timestamp')
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        try:
            result = await db_client.fetchone(
                query,
                ocorrencia_id,
                ocorrencia_data.get('success', True),
                ocorrencia_data['emergency_type'],
                ocorrencia_data['urgency_level'],
                ocorrencia_data['situation'],
                ocorrencia_data['confidence_score'],
                ocorrencia_data.get('location'),
                ocorrencia_data.get('victim'),
                ocorrencia_data.get('reporter'),
                timestamp
            )
            
            return self._format_ocorrencia(result)
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao criar ocorrência: {str(e)}")
    
    async def get_all_ocorrencias(self) -> List[Dict[str, Any]]:
        """Lista todas as ocorrências"""
        query = "SELECT * FROM ocorrencias ORDER BY created_at DESC"
        
        try:
            results = await db_client.execute_query(query)
            return [self._format_ocorrencia(row) for row in results]
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao listar ocorrências: {str(e)}")
    
    def _format_ocorrencia(self, row: asyncpg.Record) -> Dict[str, Any]:
        """Formata um registro de ocorrência para retorno"""
        if not row:
            return None
        
        return {
            'id': str(row['id']),
            'success': row['success'],
            'emergency_type': row['emergency_type'],
            'urgency_level': row['urgency_level'],
            'situation': row['situation'],
            'confidence_score': float(row['confidence_score']),
            'location': row['location'],
            'victim': row['victim'],
            'reporter': row['reporter'],
            'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
            'createdAt': row['created_at'].isoformat(),
            'updatedAt': row['updated_at'].isoformat()
        }


# Instância do serviço
ocorrencia_service = OcorrenciaService() 
