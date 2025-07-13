# 🚨 Sistema 911 - Classificação Inteligente de Emergências

## 📋 Sobre o Projeto

O **Sistema 911** é uma aplicação inteligente de **triagem e classificação de emergências** que utiliza Inteligência Artificial para analisar relatos de emergência em tempo real e direcioná-los automaticamente para os serviços apropriados (SAMU, Polícia Civil ou Bombeiros). O sistema atua como um **centro de triagem virtual**, processando chamadas via WhatsApp e priorizando atendimentos baseado na urgência e tipo da ocorrência.

### 🎯 Propósito

- **Classificação Automática**: Analisa relatos de emergência usando IA e direciona para o serviço correto
- **Análise de Urgência**: Determina o nível de urgência das ocorrências (1-5)
- **Resposta Rápida**: Fornece orientações imediatas baseadas no tipo de emergência
- **Integração WhatsApp**: Recebe e responde mensagens via WhatsApp através da Evolution API
- **Gestão de Ocorrências**: Sistema completo de tickets e acompanhamento de emergências

## 🛠️ Tecnologias e Ferramentas

### Backend e API
- **Python 3.11** - Linguagem principal
- **FastAPI** - Framework web para APIs REST
- **Uvicorn** - Servidor ASGI de alta performance
- **Pydantic** - Validação de dados e serialização

### Inteligência Artificial
- **OpenAI GPT** - Modelos de linguagem para classificação
- **LangChain** - Framework para aplicações de IA
- **FAISS** - Busca vetorial de alta performance
- **Sentence Transformers** - Embeddings de texto
- **RAG (Retrieval-Augmented Generation)** - Sistema de busca e geração de contexto

### Banco de Dados e Cache
- **PostgreSQL 15** - Banco de dados principal
- **Redis 7** - Cache e sessões
- **AsyncPG** - Driver assíncrono para PostgreSQL

### Integração e Comunicação
- **Evolution API** - Integração com WhatsApp
- **HTTPX** - Cliente HTTP assíncrono
- **Webhook** - Recebimento de mensagens em tempo real

### Infraestrutura
- **Docker & Docker Compose** - Containerização
- **Nginx** (opcional) - Proxy reverso
- **Criptografia AES** - Segurança de dados

### Processamento de Dados
- **Pandas** - Manipulação de dados
- **PyPDF2** - Processamento de documentos PDF
- **OpenPyXL** - Manipulação de planilhas Excel
- **Tiktoken** - Tokenização para modelos OpenAI

## 🏗️ Arquitetura do Sistema

```
📁 911/
├── 🤖 agentes/                    # Módulos de IA
│   ├── emergency_classifier.py   # Classificador de emergências
│   ├── urgency_classifier.py     # Analisador de urgência
│   ├── rag_service.py            # Serviço RAG
│   └── vectordb_config.py        # Configuração do banco vetorial
├── 🌐 api/                       # API REST
│   ├── main.py                   # Ponto de entrada
│   ├── server.py                 # Servidor FastAPI
│   ├── config.py                 # Configurações
│   └── entities_service.py       # Serviços de entidades
├── 🗄️ database/                  # Base de conhecimento
│   ├── Bombeiros/               # Manuais e documentos
│   ├── Policia/                 # Legislação e dados
│   └── Saude/                   # Dados de saúde
├── 🐳 docker-compose.yml         # Orquestração de serviços
├── 📄 Dockerfile                # Imagem da aplicação
└── 🔧 requirements.txt           # Dependências Python
```

## ⚙️ Funcionalidades Principais

### 🏥 Sistema de Triagem
- **Triagem Automática**: Classifica automaticamente a gravidade e tipo de emergência
- **Priorização Inteligente**: Organiza atendimentos por nível de urgência (1-5)
- **Direcionamento Correto**: Encaminha para o serviço apropriado (SAMU, Polícia, Bombeiros)
- **Tempo de Resposta Otimizado**: Reduz tempo entre relato e atendimento especializado

### 🎯 Classificação Inteligente
- **Análise de Texto**: Processa relatos em linguagem natural
- **Múltiplos Tipos**: Identifica emergências médicas, policiais e de bombeiros
- **Nível de Confiança**: Fornece score de certeza da classificação
- **Justificativa**: Explica o motivo da classificação

### 📞 Integração WhatsApp
- **Recebimento Automático**: Webhook para mensagens do WhatsApp
- **Processamento de Áudio**: Transcrição automática de mensagens de voz
- **Respostas Inteligentes**: Orientações baseadas no tipo de emergência
- **Informações de Contato**: Fornece dados dos serviços apropriados

### 🎫 Sistema de Tickets
- **Criação Automática**: Gera tickets para cada emergência
- **Acompanhamento**: Status e histórico das ocorrências
- **Filtros Avançados**: Busca por urgência, tipo, localização
- **API REST**: Endpoints para integração com frontends

### 🧠 Base de Conhecimento (RAG)
- **Documentos Oficiais**: Manuais de primeiros socorros, legislação
- **Busca Semântica**: Encontra contexto relevante automaticamente
- **Atualização Dinâmica**: Adiciona novos documentos à base
- **Múltiplos Formatos**: Suporte a PDF, CSV, XLSX, TXT

## 🚀 Como Executar

### Pré-requisitos
- **Python 3.11+**
- **Docker e Docker Compose**
- **Chave da API OpenAI** (para classificação inteligente)
- **Evolution API configurada** com:
  - Instance ativa do WhatsApp
  - Webhooks habilitados
  - Suporte a Base64 ativado
  - UpsertMessages configurado

### 📋 Instalação Rápida com Docker

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd 911
```

2. **Configure as variáveis de ambiente**
```bash
cp config_completo.txt .env
# Edite o arquivo .env com suas configurações
```

3. **Configure as variáveis obrigatórias no .env**
```bash
# OpenAI (obrigatório)
OPENAI_API_KEY=sua_chave_openai_aqui
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=1000

# Configurações RAG (opcional)
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONTEXT_LENGTH=2000

# URL da Evolution API
EV_URL=http://localhost:8080

# Chave da API da Evolution API (obrigatório)
EV_API_KEY=sua_api_key_evolution_aqui

# Nome da instância da Evolution API (obrigatório)
EV_INSTANCE=sua_instancia_aqui

# Servidor
HOST=0.0.0.0
PORT=8000
RELOAD=true
LOG_LEVEL=info

# Evolution API - Autenticação
AUTHENTICATION_API_KEY=sua_api_key_evolution_aqui
AUTH_STRATEGY=apikey
AUTH_ENABLED=true

# Database
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://evolution:examplepassword@postgres:5432/evolution?schema=public
DATABASE_CONNECTION_CLIENT_NAME=evolution_api

# Salvamento de dados
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=true
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
DATABASE_SAVE_DATA_LABELS=true
DATABASE_SAVE_DATA_HISTORIC=true

# Redis
CACHE_REDIS_ENABLED=true
CACHE_REDIS_URI=redis://redis:6379
CACHE_REDIS_PREFIX_KEY=evolution_api
CACHE_REDIS_SAVE_INSTANCES=false
CONFIG_SESSION_PHONE_VERSION=2.3000.1020885143
```

4. **Execute com Docker**
```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar se os serviços estão rodando
docker-compose ps

# Ver logs
docker-compose logs -f
```

5. **Configurar Evolution API**

⚠️ **IMPORTANTE**: Para o funcionamento correto do sistema de triagem, é necessário configurar a Evolution API com as seguintes configurações:

- **Ativar Webhooks**: Configure o webhook URL para `http://localhost:8000/webhook`
- **Ativar Base64**: Habilite o uso de Base64 para processamento de mídia
- **Ativar UpsertMessages**: Configure para sincronização de mensagens

Essas configurações são essenciais para que o sistema receba e processe mensagens do WhatsApp automaticamente.

6. **Verificar funcionamento**
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Documentação**: http://localhost:8000/docs
- **Evolution API**: http://localhost:8080

### 🔧 Instalação Manual (Desenvolvimento)

1. **Criar ambiente virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

2. **Instalar dependências**
```bash
pip install -r requirements.txt
```

3. **Configurar banco de dados**
```bash
# Certifique-se que PostgreSQL está rodando
python setup_database.py
```

4. **Executar aplicação**
```bash
python app.py
```

### 🔧 Configuração Detalhada da Evolution API

Para que o sistema de triagem funcione corretamente, configure sua instância da Evolution API:

1. **Acesse o painel da Evolution API**: http://localhost:8080
2. **Configure os Webhooks**:
   - URL: `http://localhost:8000/webhook`
   - Eventos: `messages.upsert`, `messages.update`
3. **Ative as configurações**:
   - ✅ **Base64**: Para processamento de áudios e mídias
   - ✅ **UpsertMessages**: Para sincronização de mensagens
   - ✅ **Webhooks**: Para recebimento em tempo real
4. **Teste a conexão**: Envie uma mensagem de teste para verificar se o webhook está funcionando

### 🔍 Comandos Úteis

```bash
# Parar serviços Docker
docker-compose down

# Reconstruir imagens
docker-compose build --no-cache

# Executar apenas o banco
docker-compose up postgres redis -d

# Limpar volumes (CUIDADO: apaga dados)
docker-compose down -v

# Executar shell no container
docker-compose exec server bash

# Ver logs específicos da Evolution API
docker-compose logs -f evolution-api

# Testar webhook manualmente
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook funcionando"}'
```

## 📡 Endpoints da API

### Classificação de Emergências
```bash
POST /classify
{
  "relato": "Minha mãe está com dor no peito e dificuldade para respirar"
}
```

### Webhook WhatsApp
```bash
POST /webhook
# Recebe mensagens da Evolution API automaticamente
```

### Gestão de Emergências
```bash
GET /api/emergencies          # Listar emergências
POST /api/emergencies         # Criar emergência
GET /api/emergencies/{id}     # Buscar por ID
PATCH /api/emergencies/{id}   # Atualizar status
```

### Sistema de Tickets
```bash
GET /api/tickets              # Listar tickets
POST /api/tickets             # Criar ticket
POST /api/tickets/with-emergency  # Criar ticket com emergência
```

## 🔐 Segurança

- **Criptografia AES**: Dados sensíveis são criptografados
- **Validação de Dados**: Pydantic para validação rigorosa
- **CORS Configurado**: Controle de acesso entre domínios
- **Environment Variables**: Credenciais via variáveis de ambiente
- **Logs Estruturados**: Rastreamento de operações

## 📊 Monitoramento

- **Health Check**: Endpoint `/health` para verificar status
- **Logs Detalhados**: Sistema de logging configurável
- **Métricas**: Estatísticas da base de conhecimento
- **Error Handling**: Tratamento robusto de erros

## 🤝 Como Contribuir

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob licença [especificar licença]. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no repositório
- Consulte a documentação em `/docs`
- Verifique os logs com `docker-compose logs -f`

---

**⚠️ Importante**: Este sistema processa emergências reais e funciona como um **centro de triagem virtual**. Sempre teste em ambiente de desenvolvimento antes de implementar em produção.

**🏥 Sobre a Triagem**: O sistema implementa protocolos de triagem baseados em IA para classificar automaticamente a gravidade das emergências, garantindo que casos críticos recebam prioridade máxima no atendimento.
