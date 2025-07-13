# Compatibilidade com Frontend TypeScript

Este documento detalha todas as funcionalidades implementadas no backend Python que são compatíveis com o frontend TypeScript.

## 🔄 Mapeamento de Funções

### EmergencyService (TypeScript) → EmergencyService (Python)

| Frontend TypeScript | Backend Python | Descrição |
|-------------------|---------------|-----------|
| `getEmergencies(filters?)` | `get_emergencies(filters?)` | Lista emergências com filtros opcionais |
| `updateEmergencyStatus(id, status)` | `update_emergency_status(id, status)` | Atualiza apenas o status de uma emergência |
| `getMockEmergencies()` | `get_mock_emergencies()` | Retorna dados mock para desenvolvimento |

### Função de Conversão

| Frontend TypeScript | Backend Python | Descrição |
|-------------------|---------------|-----------|
| `backendToEmergency(backend, id)` | `backend_to_emergency(backend_data, id?)` | Converte BackendEmergency para Emergency |

## 📊 Estrutura de Dados

### Interface Emergency (TypeScript)

```typescript
interface Emergency {
  id: string;
  title: string;
  description: string;
  level: 'CRÍTICO' | 'ALTO' | 'MÉDIO' | 'BAIXO';
  status: 'ATIVO' | 'EM_ANDAMENTO' | 'RESOLVIDO' | 'FINALIZADO';
  responsible: string;
  location: string;
  victim?: string;
  createdAt: string;
  updatedAt: string;
  reporter: string;
}
```

### Equivalente Python

```python
{
    'id': str,
    'title': str,
    'description': str,
    'level': str,  # 'CRÍTICO' | 'ALTO' | 'MÉDIO' | 'BAIXO'
    'status': str,  # 'ATIVO' | 'EM_ANDAMENTO' | 'RESOLVIDO' | 'FINALIZADO'
    'responsible': str,
    'location': str,
    'victim': Optional[str],
    'createdAt': str,  # ISO format
    'updatedAt': str,  # ISO format
    'reporter': str
}
```

### Interface BackendEmergency (TypeScript)

```typescript
interface BackendEmergency {
  success: boolean;
  emergency_type: string[];
  urgency_level: number;
  situation: string;
  confidence_score: number;
  location?: string | null;
  victim?: string | null;
  reporter?: string | null;
  timestamp?: string;
}
```

### Equivalente Python

```python
{
    'success': bool,
    'emergency_type': List[str],
    'urgency_level': int,  # 1-5
    'situation': str,
    'confidence_score': float,  # 0.0-1.0
    'location': Optional[str],
    'victim': Optional[str],
    'reporter': Optional[str],
    'timestamp': Optional[str]
}
```

## 🔧 Funções de Mapeamento

### Nível de Urgência

```python
def map_urgency_level(level: int) -> str:
    if level >= 5: return 'CRÍTICO'
    if level == 4: return 'ALTO'
    if level == 3: return 'MÉDIO'
    return 'BAIXO'
```

### Tipo de Emergência

```python
def map_emergency_type(types: List[str]) -> str:
    if 'samu' in types: return 'SAMU'
    if 'bombeiros' in types: return 'Bombeiros'
    if 'policia' in types: return 'Polícia'
    return ', '.join(types)
```

## 📝 Exemplos de Uso

### 1. Buscar Emergências

**Frontend TypeScript:**
```typescript
const emergencies = await EmergencyService.getEmergencies();
const filtered = await EmergencyService.getEmergencies({
  status: 'ATIVO',
  level: 'CRÍTICO'
});
```

**Backend Python:**
```python
emergencies = await emergency_service.get_emergencies()
filtered = await emergency_service.get_emergencies(
    filters={'status': 'ATIVO', 'level': 'CRÍTICO'}
)
```

### 2. Atualizar Status

**Frontend TypeScript:**
```typescript
const updated = await EmergencyService.updateEmergencyStatus(
  emergencyId, 
  'EM_ANDAMENTO'
);
```

**Backend Python:**
```python
updated = await emergency_service.update_emergency_status(
    emergency_id, 
    'EM_ANDAMENTO'
)
```

### 3. Conversão de Dados

**Frontend TypeScript:**
```typescript
const emergency = backendToEmergency(backendData, uuid());
```

**Backend Python:**
```python
emergency = backend_to_emergency(backend_data, str(uuid.uuid4()))
```

## 🧪 Testes de Compatibilidade

Execute o script de teste:

```bash
python test_frontend_compatibility.py
```

Este script verifica:
- ✅ Todas as funções compatíveis funcionam
- ✅ Estrutura de dados está correta
- ✅ Conversões são realizadas corretamente
- ✅ Filtros funcionam conforme esperado
- ✅ Dados são serializáveis para JSON

## 🔌 Integração com API REST

### Endpoints Sugeridos

```python
# GET /api/emergencies
# GET /api/emergencies?status=ATIVO&level=CRÍTICO
async def get_emergencies(filters: dict = None):
    return await emergency_service.get_emergencies(filters)

# PATCH /api/emergencies/{id}
async def update_emergency_status(id: str, status: str):
    return await emergency_service.update_emergency_status(id, status)

# POST /api/emergencies/from-backend
async def create_from_backend(backend_data: dict):
    return await emergency_service.create_emergency_from_backend(backend_data)
```

## 📚 Dados Mock

O sistema inclui dados mock idênticos aos do frontend para desenvolvimento:

```python
mock_emergencies = emergency_service.get_mock_emergencies()
```

## ⚡ Recursos Adicionais

### 1. Criação Simultânea de Ticket e Emergência

```python
result = await ticket_service.create_ticket_and_emergency(backend_data)
ticket = result['ticket']
emergency = result['emergency']
```

### 2. Validação de Dados

- **Nível de urgência**: Validado entre 1-5
- **Confidence score**: Validado entre 0.0-1.0
- **Status e Level**: Validados contra ENUMs do banco
- **Timestamps**: Formato ISO 8601

### 3. Tratamento de Erros

```python
try:
    emergency = await emergency_service.get_emergency_by_id(id)
except Exception as e:
    # Tratamento de erro compatível com frontend
    return {"error": str(e), "status": "error"}
```

## 🎯 Próximos Passos

1. Implementar endpoints REST usando FastAPI
2. Adicionar validação de dados usando Pydantic
3. Configurar CORS para frontend
4. Implementar autenticação se necessário
5. Adicionar testes unitários

## 📋 Checklist de Compatibilidade

- ✅ Estrutura de dados idêntica ao TypeScript
- ✅ Funções com nomes compatíveis
- ✅ Filtros funcionando corretamente
- ✅ Conversão BackendEmergency → Emergency
- ✅ Dados mock para desenvolvimento
- ✅ Serialização JSON compatível
- ✅ Tratamento de campos opcionais
- ✅ Validação de dados
- ✅ Timestamps em formato ISO
- ✅ Mapeamento de tipos de emergência 