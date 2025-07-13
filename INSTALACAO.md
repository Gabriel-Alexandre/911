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

## 🎯 Configuração Rápida

### 1. Setup Automático

```bash
# Executar script de configuração
python3 setup_env.py
```

### 2. Configuração Manual

```bash
# Copiar arquivo de configuração
cp config_completo.txt .env

# Editar variáveis obrigatórias
nano .env
```

### 3. Instalar Dependências

```bash
# Usar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Executar Servidor

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
WEBHOOK_URL=http://localhost:8000/webhook

# OpenAI
OPENAI_API_KEY=sua_chave_openai_aqui
```

## 🔍 Verificação

Teste se tudo está funcionando:

```bash
# Verificar configurações
python exemplo_uso_api.py

# Verificar dependências
python -c "import fastapi, uvicorn, httpx, openai; print('✅ Todas as dependências instaladas!')"
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

## 📚 Recursos Adicionais

- [Documentação Python](https://docs.python.org/3/)
- [Guia pip](https://pip.pypa.io/en/stable/)
- [Ambientes Virtuais](https://docs.python.org/3/tutorial/venv.html) 
