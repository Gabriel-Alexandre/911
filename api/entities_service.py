"""
Serviço para gerenciar entidades Emergency e Ticket
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import asyncpg
from .config import db_client


def map_urgency_level(level: int) -> str:
    """Mapeia nível numérico para string"""
    if level >= 5:
        return 'CRÍTICO'
    elif level == 4:
        return 'ALTO'
    elif level == 3:
        return 'MÉDIO'
    else:
        return 'BAIXO'


def map_emergency_type(types: List[str]) -> str:
    """Mapeia tipo de emergência para responsável"""
    if 'samu' in types:
        return 'SAMU'
    elif 'bombeiros' in types:
        return 'Bombeiros'
    elif 'policia' in types:
        return 'Polícia'
    else:
        return ', '.join(types)


def backend_to_emergency(backend_data: Dict[str, Any], emergency_id: str = None) -> Dict[str, Any]:
    """Converte dados de BackendEmergency para Emergency"""
    if not emergency_id:
        emergency_id = str(uuid.uuid4())
    
    timestamp = backend_data.get('timestamp', datetime.now().isoformat())
    
    return {
        'id': emergency_id,
        'title': backend_data['situation'],
        'description': backend_data['situation'],
        'level': map_urgency_level(backend_data['urgency_level']),
        'status': 'ATIVO',
        'responsible': map_emergency_type(backend_data['emergency_type']),
        'location': backend_data.get('location') or 'Desconhecido',
        'victim': backend_data.get('victim'),
        'createdAt': timestamp,
        'updatedAt': timestamp,
        'reporter': backend_data.get('reporter') or 'Desconhecido'
    }


class EmergencyService:
    """Serviço para gerenciar emergências"""
    
    async def create_emergency(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma nova emergência"""
        query = """
            INSERT INTO emergency (
                id, title, description, level, status, responsible, 
                location, victim, reporter
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        
        emergency_id = str(uuid.uuid4())
        
        try:
            result = await db_client.fetchone(
                query,
                emergency_id,
                emergency_data['title'],
                emergency_data['description'],
                emergency_data['level'],
                emergency_data.get('status', 'ATIVO'),
                emergency_data['responsible'],
                emergency_data['location'],
                emergency_data.get('victim'),
                emergency_data['reporter']
            )
            
            return self._format_emergency(result)
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao criar emergência: {str(e)}")
    
    async def create_emergency_from_backend(self, backend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma emergência a partir de dados BackendEmergency"""
        emergency_data = backend_to_emergency(backend_data)
        return await self.create_emergency(emergency_data)
    
    async def get_emergency_by_id(self, emergency_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma emergência pelo ID"""
        query = "SELECT * FROM emergency WHERE id = $1"
        
        try:
            result = await db_client.fetchone(query, emergency_id)
            return self._format_emergency(result) if result else None
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao buscar emergência: {str(e)}")
    
    async def get_emergencies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Lista todas as emergências com filtros opcionais (compatível com frontend)"""
        return await self.get_all_emergencies(filters)
    
    async def get_all_emergencies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Lista todas as emergências com filtros opcionais"""
        query = "SELECT * FROM emergency"
        params = []
        conditions = []
        
        if filters:
            param_count = 1
            
            if filters.get('status'):
                conditions.append(f"status = ${param_count}")
                params.append(filters['status'])
                param_count += 1
            
            if filters.get('level'):
                conditions.append(f"level = ${param_count}")
                params.append(filters['level'])
                param_count += 1
            
            if filters.get('responsible'):
                conditions.append(f"responsible ILIKE ${param_count}")
                params.append(f"%{filters['responsible']}%")
                param_count += 1
            
            if filters.get('location'):
                conditions.append(f"location ILIKE ${param_count}")
                params.append(f"%{filters['location']}%")
                param_count += 1
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        try:
            results = await db_client.execute_query(query, *params)
            return [self._format_emergency(row) for row in results]
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao listar emergências: {str(e)}")
    
    async def update_emergency(self, emergency_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza uma emergência"""
        set_clauses = []
        params = []
        param_count = 1
        
        # Campos que podem ser atualizados
        updatable_fields = ['title', 'description', 'level', 'status', 'responsible', 'location', 'victim']
        
        for field in updatable_fields:
            if field in update_data:
                set_clauses.append(f"{field} = ${param_count}")
                params.append(update_data[field])
                param_count += 1
        
        if not set_clauses:
            raise ValueError("Nenhum campo válido para atualização")
        
        query = f"""
            UPDATE emergency 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            RETURNING *
        """
        params.append(emergency_id)
        
        try:
            result = await db_client.fetchone(query, *params)
            return self._format_emergency(result) if result else None
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao atualizar emergência: {str(e)}")
    
    async def update_emergency_status(self, emergency_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Atualiza apenas o status de uma emergência (compatível com frontend)"""
        return await self.update_emergency(emergency_id, {'status': status})
    
    async def delete_emergency(self, emergency_id: str) -> bool:
        """Deleta uma emergência"""
        query = "DELETE FROM emergency WHERE id = $1"
        
        try:
            result = await db_client.execute_command(query, emergency_id)
            return result == "DELETE 1"
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao deletar emergência: {str(e)}")
    
    def _format_emergency(self, row: asyncpg.Record) -> Dict[str, Any]:
        """Formata um registro de emergência para retorno"""
        if not row:
            return None
        
        return {
            'id': str(row['id']),
            'title': row['title'],
            'description': row['description'],
            'level': row['level'],
            'status': row['status'],
            'responsible': row['responsible'],
            'location': row['location'],
            'victim': row['victim'],
            'createdAt': row['created_at'].isoformat(),
            'updatedAt': row['updated_at'].isoformat(),
            'reporter': row['reporter']
        }

class TicketService:
    """Serviço para gerenciar tickets"""
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo ticket"""
        query = """
            INSERT INTO ticket (
                id, success, emergency_type, urgency_level, situation, 
                confidence_score, location, victim, reporter, timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
        """
        
        ticket_id = str(uuid.uuid4())
        
        try:
            result = await db_client.fetchone(
                query,
                ticket_id,
                ticket_data.get('success', True),
                ticket_data['emergency_type'],
                ticket_data['urgency_level'],
                ticket_data['situation'],
                ticket_data['confidence_score'],
                ticket_data.get('location'),
                ticket_data.get('victim'),
                ticket_data.get('reporter'),
                ticket_data.get('timestamp')
            )
            
            return self._format_ticket(result)
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao criar ticket: {str(e)}")
    
    async def create_ticket_and_emergency(self, backend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um ticket e converte para emergência se necessário"""
        # Criar o ticket
        ticket = await self.create_ticket(backend_data)
        
        # Criar emergência correspondente
        emergency_data = backend_to_emergency(backend_data)
        emergency = await emergency_service.create_emergency(emergency_data)
        
        return {
            'ticket': ticket,
            'emergency': emergency
        }
    
    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Busca um ticket pelo ID"""
        query = "SELECT * FROM ticket WHERE id = $1"
        
        try:
            result = await db_client.fetchone(query, ticket_id)
            return self._format_ticket(result) if result else None
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao buscar ticket: {str(e)}")
    
    async def get_all_tickets(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Lista todos os tickets com filtros opcionais"""
        query = "SELECT * FROM ticket"
        params = []
        conditions = []
        
        if filters:
            param_count = 1
            
            if filters.get('urgency_level'):
                conditions.append(f"urgency_level = ${param_count}")
                params.append(filters['urgency_level'])
                param_count += 1
            
            if filters.get('emergency_type'):
                conditions.append(f"${param_count} = ANY(emergency_type)")
                params.append(filters['emergency_type'])
                param_count += 1
            
            if filters.get('location'):
                conditions.append(f"location ILIKE ${param_count}")
                params.append(f"%{filters['location']}%")
                param_count += 1
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC"
        
        try:
            results = await db_client.execute_query(query, *params)
            return [self._format_ticket(row) for row in results]
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao listar tickets: {str(e)}")
    
    async def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza um ticket"""
        set_clauses = []
        params = []
        param_count = 1
        
        # Campos que podem ser atualizados
        updatable_fields = ['success', 'emergency_type', 'urgency_level', 'situation', 
                           'confidence_score', 'location', 'victim', 'reporter']
        
        for field in updatable_fields:
            if field in update_data:
                set_clauses.append(f"{field} = ${param_count}")
                params.append(update_data[field])
                param_count += 1
        
        if not set_clauses:
            raise ValueError("Nenhum campo válido para atualização")
        
        query = f"""
            UPDATE ticket 
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            RETURNING *
        """
        params.append(ticket_id)
        
        try:
            result = await db_client.fetchone(query, *params)
            return self._format_ticket(result) if result else None
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao atualizar ticket: {str(e)}")
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Deleta um ticket"""
        query = "DELETE FROM ticket WHERE id = $1"
        
        try:
            result = await db_client.execute_command(query, ticket_id)
            return result == "DELETE 1"
        except asyncpg.PostgresError as e:
            raise Exception(f"Erro ao deletar ticket: {str(e)}")
    
    def _format_ticket(self, row: asyncpg.Record) -> Dict[str, Any]:
        """Formata um registro de ticket para retorno"""
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


# Instâncias dos serviços
emergency_service = EmergencyService()
ticket_service = TicketService()
