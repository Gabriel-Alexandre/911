# 🚨 Agente Classificador de Emergências

Agente que classifica situações de emergência e indica qual serviço chamar (SAMU, Polícia ou Bombeiros).

## 🚀 Configuração Rápida

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Configurar OpenAI:**
```powershell
$env:OPENAI_API_KEY="sua_chave_aqui"
```

3. **Testar:**
```bash
python teste_agente.py
```

## 📋 Uso

```python
from agentes import EmergencyClassifierAgent

agent = EmergencyClassifierAgent()
resultado = agent.classify_emergency("Incêndio no prédio!")

print(resultado['tipos_emergencia'])  # ['bombeiro']
```

## 🔧 Configurações Opcionais

```powershell
# Para usar GPT-4 (melhor qualidade)
$env:OPENAI_MODEL="gpt-4.1"

# Para usar GPT-3.5 (padrão, mais barato)
$env:OPENAI_MODEL="gpt-3.5-turbo"
```