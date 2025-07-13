# 🚀 Guia de Instalação - Sistema 911

## Problema: "zsh: command not found: pip"

Este erro é comum em sistemas macOS com Python instalado via Homebrew. Aqui está como resolver:

## 🔧 Soluções

### Opção 1: Usar python3 -m pip (Recomendado)

```bash
# Em vez de: pip install -r requirements.txt
python3 -m pip install -r requirements.txt
```

### Opção 2: Ambiente Virtual (Mais Seguro)

```bash
# 1. Criar ambiente virtual
python3 -m venv venv

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar o servidor
python app.py

# 5. Desativar ambiente virtual (quando terminar)
deactivate
```

### Opção 3: Instalar pip via Homebrew

```bash
# Instalar pip via Homebrew
brew install pip

# Ou usar pipx para aplicações Python
brew install pipx
pipx install nome-da-aplicacao
```

## 🎯 Configuração

### 1. Configuração Manual

```bash
# Copiar arquivo de configuração
cp config_completo.txt .env

# Editar variáveis obrigatórias
nano .env
```

### 2. Instalar Dependências

```bash
# Usar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Executar Servidor

```bash
# Com ambiente virtual ativado
python app.py

# Ou diretamente
python3 app.py
```

## 📋 Variáveis Obrigatórias

Edite o arquivo `.env` e configure:

```bash
# Evolution API
EV_API_KEY=sua_api_key_evolution_aqui
EV_INSTANCE=sua_instancia_aqui

# OpenAI
OPENAI_API_KEY=sua_chave_openai_aqui
```

## 🆘 Troubleshooting

### Erro: "externally-managed-environment"
- Use ambiente virtual: `python3 -m venv venv`
- Ou use: `python3 -m pip install --user -r requirements.txt`

### Erro: "No module named 'pip'"
- Instale pip: `python3 -m ensurepip --upgrade`
- Ou use Homebrew: `brew install pip`

### Erro: "Permission denied"
- Use ambiente virtual
- Ou adicione `--user`: `python3 -m pip install --user -r requirements.txt`

## 🐳 Execução com Docker

### Comandos Docker

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Ver logs
docker-compose logs -f

# Ver status
docker-compose ps

# Reconstruir imagem
docker-compose build --no-cache

# Limpar tudo
docker-compose down -v
```

### Endpoints com Docker

- **ChromaDB**: http://localhost:8000
- **Server**: http://localhost:8001
- **Health Check**: http://localhost:8001/health
- **Webhook**: http://localhost:8001/webhook

## 📚 Recursos Adicionais

- [Documentação Python](https://docs.python.org/3/)
- [Guia pip](https://pip.pypa.io/en/stable/)
- [Ambientes Virtuais](https://docs.python.org/3/tutorial/venv.html)
- [Docker Compose](https://docs.docker.com/compose/) 
