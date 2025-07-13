# Sistema de Banco de Dados - Emergency e Ticket

Este documento explica como configurar e usar o sistema de banco de dados para gerenciar emergências e tickets.

## 🏗️ Estrutura das Tabelas

### Tabela `emergency`
Baseada na interface `Emergency`, esta tabela armazena informações sobre emergências:

```sql
CREATE TABLE emergency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    level emergency_level NOT NULL,  -- 'CRÍTICO', 'ALTO', 'MÉDIO', 'BAIXO'
    status emergency_status NOT NULL DEFAULT 'ATIVO',  -- 'ATIVO', 'EM_ANDAMENTO', 'RESOLVIDO', 'FINALIZADO'
    responsible VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    victim VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reporter VARCHAR(255) NOT NULL
);
```

### Tabela `ticket`
Baseada na interface `BackendEmergency`, esta tabela armazena informações sobre tickets:

```sql
CREATE TABLE ticket (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    success BOOLEAN NOT NULL DEFAULT true,
    emergency_type TEXT[] NOT NULL,  -- Ex: ['bombeiros', 'samu']
    urgency_level INTEGER NOT NULL CHECK (urgency_level >= 1 AND urgency_level <= 5),
    situation TEXT NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    location VARCHAR(255),
    victim VARCHAR(255),
    reporter VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Configuração

### 1. Configurar Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=evolution
DB_USER=evolution
DB_PASSWORD=examplepassword
```

### 2. Inicializar o Banco de Dados

**Método 1: Script auxiliar (recomendado)**

```bash
python setup_database.py
```

**Método 2: Usando as funções do config.py**

```python
import asyncio
from api.config import init_database, test_database_connection, check_database_tables

# Inicializar o banco de dados
await init_database()

# Testar conexão
await test_database_connection()

# Verificar se as tabelas existem
await check_database_tables()
```

**Método 3: Usando o cliente diretamente**

```python
from api.config import db_client
await db_client.init_database()
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

## 💻 Uso dos Serviços

### EmergencyService

**Funções compatíveis com o frontend TypeScript:**

```python
from api.entities_service import emergency_service, backend_to_emergency

# getEmergencies() - compatível com frontend
emergencies = await emergency_service.get_emergencies()

# getEmergencies() com filtros - compatível com EmergencyFilters
emergencies = await emergency_service.get_emergencies(
    filters={'status': 'ATIVO', 'level': 'CRÍTICO'}
)

# updateEmergencyStatus() - compatível com frontend
updated = await emergency_service.update_emergency_status(
    emergency_id, 
    'EM_ANDAMENTO'
)

# Dados mock para desenvolvimento
mock_data = emergency_service.get_mock_emergencies()

# Conversão BackendEmergency -> Emergency
backend_data = {
    'success': True,
    'emergency_type': ['bombeiros', 'samu'],
    'urgency_level': 5,
    'situation': 'Incêndio em prédio residencial',
    'confidence_score': 0.95,
    'location': 'Rua das Flores, 123',
    'victim': 'Família de 4 pessoas',
    'reporter': 'João Silva'
}

# Converter dados do backend
emergency_data = backend_to_emergency(backend_data)

# Criar emergência a partir de dados do backend
emergency = await emergency_service.create_emergency_from_backend(backend_data)
```

**Funções básicas do CRUD:**

```python
# Criar uma emergência
emergency_data = {
    'title': 'Incêndio em prédio residencial',
    'description': 'Incêndio de grandes proporções no 5º andar',
    'level': 'CRÍTICO',
    'responsible': 'Bombeiros - Unidade Central',
    'location': 'Rua das Flores, 123 - Centro',
    'victim': 'Família de 4 pessoas',
    'reporter': 'João Silva - (11) 99999-9999'
}

emergency = await emergency_service.create_emergency(emergency_data)

# Buscar emergência por ID
emergency = await emergency_service.get_emergency_by_id(emergency_id)

# Listar todas as emergências
emergencies = await emergency_service.get_all_emergencies()

# Atualizar emergência
updated = await emergency_service.update_emergency(
    emergency_id, 
    {'status': 'EM_ANDAMENTO'}
)

# Deletar emergência
deleted = await emergency_service.delete_emergency(emergency_id)
```

### TicketService

**Funções avançadas para integração:**

```python
from api.entities_service import ticket_service

# Criar ticket e emergência simultaneamente
backend_data = {
    'success': True,
    'emergency_type': ['bombeiros', 'samu'],
    'urgency_level': 5,
    'situation': 'Incêndio em prédio residencial com vítimas presas',
    'confidence_score': 0.95,
    'location': 'Rua das Flores, 123 - Centro',
    'victim': 'Família de 4 pessoas',
    'reporter': 'João Silva'
}

# Cria ticket e emergência em uma única operação
result = await ticket_service.create_ticket_and_emergency(backend_data)
ticket = result['ticket']
emergency = result['emergency']
```

**Funções básicas do CRUD:**

```python
# Criar um ticket
ticket_data = {
    'success': True,
    'emergency_type': ['bombeiros', 'samu'],
    'urgency_level': 5,
    'situation': 'Incêndio em prédio residencial com vítimas presas',
    'confidence_score': 0.95,
    'location': 'Rua das Flores, 123 - Centro',
    'victim': 'Família de 4 pessoas',
    'reporter': 'João Silva'
}

ticket = await ticket_service.create_ticket(ticket_data)

# Buscar ticket por ID
ticket = await ticket_service.get_ticket_by_id(ticket_id)

# Listar todos os tickets
tickets = await ticket_service.get_all_tickets()

# Listar com filtros
tickets = await ticket_service.get_all_tickets(
    filters={'urgency_level': 5, 'emergency_type': 'bombeiros'}
)

# Atualizar ticket
updated = await ticket_service.update_ticket(
    ticket_id, 
    {'urgency_level': 4}
)

# Deletar ticket
deleted = await ticket_service.delete_ticket(ticket_id)
```

## 🔧 Recursos Implementados

### Funcionalidades Automáticas
- **Auto-incremento de IDs**: Usando UUIDs para garantir unicidade
- **Timestamps automáticos**: `created_at` e `updated_at` são gerenciados automaticamente
- **Triggers**: Atualização automática de `updated_at` ao modificar registros

### Validações
- **Nível de urgência**: Aceita apenas valores de 1 a 5
- **Confidence score**: Aceita apenas valores entre 0 e 1
- **Enums**: Validação de status e níveis através de tipos ENUM

### Índices para Performance
- Índices em campos frequentemente consultados
- Índice GIN para busca em arrays (emergency_type)

### Filtros Disponíveis

**Emergency:**
- `status`: 'ATIVO', 'EM_ANDAMENTO', 'RESOLVIDO', 'FINALIZADO'
- `level`: 'CRÍTICO', 'ALTO', 'MÉDIO', 'BAIXO'
- `responsible`: Busca parcial (ILIKE)
- `location`: Busca parcial (ILIKE)

**Ticket:**
- `urgency_level`: 1-5
- `emergency_type`: Busca em array
- `location`: Busca parcial (ILIKE)

## 🐳 Docker

O sistema está configurado para usar o PostgreSQL do Docker Compose:

```bash
docker-compose up -d postgres
```

## 📝 Exemplos e Testes

### Script de Compatibilidade com Frontend

Execute o teste de compatibilidade com TypeScript:

```bash
python test_frontend_compatibility.py
```

Este script testa:
- Funções compatíveis com o frontend TypeScript
- Conversão de dados BackendEmergency -> Emergency
- Filtros e estrutura de dados
- Serialização JSON
- Dados mock para desenvolvimento

### Script de Setup do Banco

Execute o setup interativo do banco:

```bash
python setup_database.py
```

Este script:
- Testa a conexão com o banco
- Verifica se as tabelas existem
- Inicializa o banco se necessário
- Confirma se tudo foi criado corretamente

### Funções Disponíveis

**Compatibilidade com Frontend TypeScript:**
- `emergency_service.get_emergencies()` - equivalente a `EmergencyService.getEmergencies()`
- `emergency_service.update_emergency_status()` - equivalente a `EmergencyService.updateEmergencyStatus()`
- `emergency_service.get_mock_emergencies()` - equivalente a `EmergencyService.getMockEmergencies()`
- `backend_to_emergency()` - equivalente a `backendToEmergency()`

**Funções de Integração:**
- `emergency_service.create_emergency_from_backend()` - cria Emergency a partir de BackendEmergency
- `ticket_service.create_ticket_and_emergency()` - cria ambos simultaneamente

## 🛠️ Troubleshooting

### Erro de Conexão
1. Verifique se o PostgreSQL está executando
2. Confirme as variáveis de ambiente
3. Teste a conexão manualmente

### Tabelas não encontradas
1. Execute o script `init_db.py`
2. Verifique se o seed.sql foi executado corretamente

### Erro de dependências
1. Instale as dependências: `pip install -r requirements.txt`
2. Certifique-se de que `asyncpg` está instalado 