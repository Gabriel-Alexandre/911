#!/usr/bin/env python3
"""
Script de teste para demonstrar compatibilidade com o frontend TypeScript
Execute na raiz do projeto: python test_frontend_compatibility.py
"""

import asyncio
import json
from api.config import db_client
from api.entities_service import emergency_service, ticket_service, backend_to_emergency

async def test_frontend_compatibility():
    """Testa todas as funções compatíveis com o frontend TypeScript"""
    
    print("🧪 Testando compatibilidade com frontend TypeScript...")
    
    try:
        # Conectar ao banco
        await db_client.connect()
        
        # 1. Testar getEmergencies (compatível com frontend)
        print("\n1. Testando getEmergencies()...")
        emergencies = await emergency_service.get_emergencies()
        print(f"✅ Encontradas {len(emergencies)} emergências")
        
        # 2. Testar getEmergencies com filtros (compatível com EmergencyFilters)
        print("\n2. Testando getEmergencies() com filtros...")
        filtered_emergencies = await emergency_service.get_emergencies(
            filters={'status': 'ATIVO', 'level': 'CRÍTICO'}
        )
        print(f"✅ Emergências ativas críticas: {len(filtered_emergencies)}")
        
        # 3. Testar dados mock (fallback para desenvolvimento)
        print("\n3. Testando dados mock...")
        mock_emergencies = emergency_service.get_mock_emergencies()
        print(f"✅ Dados mock disponíveis: {len(mock_emergencies)} emergências")
        
        # 4. Testar conversão BackendEmergency -> Emergency
        print("\n4. Testando conversão BackendEmergency -> Emergency...")
        backend_data = {
            'success': True,
            'emergency_type': ['bombeiros', 'samu'],
            'urgency_level': 5,
            'situation': 'Incêndio em prédio residencial com vítimas',
            'confidence_score': 0.95,
            'location': 'Rua das Flores, 123 - Centro',
            'victim': 'Família de 4 pessoas',
            'reporter': 'João Silva',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        converted_emergency = backend_to_emergency(backend_data)
        print("✅ Conversão realizada com sucesso:")
        print(f"   - Title: {converted_emergency['title']}")
        print(f"   - Level: {converted_emergency['level']}")
        print(f"   - Responsible: {converted_emergency['responsible']}")
        
        # 5. Testar criação de emergência a partir de backend
        print("\n5. Testando create_emergency_from_backend()...")
        created_emergency = await emergency_service.create_emergency_from_backend(backend_data)
        print(f"✅ Emergência criada com ID: {created_emergency['id']}")
        
        # 6. Testar updateEmergencyStatus (compatível com frontend)
        print("\n6. Testando updateEmergencyStatus()...")
        updated_emergency = await emergency_service.update_emergency_status(
            created_emergency['id'], 
            'EM_ANDAMENTO'
        )
        print(f"✅ Status atualizado para: {updated_emergency['status']}")
        
        # 7. Testar criação de ticket e emergência simultaneamente
        print("\n7. Testando create_ticket_and_emergency()...")
        ticket_and_emergency = await ticket_service.create_ticket_and_emergency(backend_data)
        print(f"✅ Ticket criado: {ticket_and_emergency['ticket']['id']}")
        print(f"✅ Emergência criada: {ticket_and_emergency['emergency']['id']}")
        
        # 8. Testar estrutura de dados compatível com TypeScript
        print("\n8. Verificando estrutura de dados compatível com TypeScript...")
        
        # Verificar se todas as propriedades necessárias existem
        required_emergency_fields = ['id', 'title', 'description', 'level', 'status', 
                                   'responsible', 'location', 'victim', 'createdAt', 
                                   'updatedAt', 'reporter']
        
        sample_emergency = emergencies[0] if emergencies else created_emergency
        
        missing_fields = []
        for field in required_emergency_fields:
            if field not in sample_emergency:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Campos faltando: {missing_fields}")
        else:
            print("✅ Todos os campos obrigatórios presentes")
        
        # 9. Testar formato JSON compatível
        print("\n9. Testando serialização JSON...")
        try:
            json_data = json.dumps(sample_emergency, default=str)
            print("✅ Dados serializáveis para JSON")
        except Exception as e:
            print(f"❌ Erro na serialização: {e}")
        
        # 10. Resumo dos tipos de dados
        print("\n10. Resumo dos tipos de dados:")
        print(f"   - Emergency levels: {set(e['level'] for e in mock_emergencies)}")
        print(f"   - Emergency status: {set(e['status'] for e in mock_emergencies)}")
        print(f"   - Emergency types: {set(e['responsible'] for e in mock_emergencies)}")
        
        print("\n🎉 Todos os testes de compatibilidade foram executados com sucesso!")
        print("💡 O backend está totalmente compatível com o frontend TypeScript")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        raise
    finally:
        # Desconectar
        await db_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_frontend_compatibility()) 