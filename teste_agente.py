#!/usr/bin/env python3
"""
Teste do Agente Classificador de Emergências

CONFIGURAÇÃO NECESSÁRIA:
export OPENAI_API_KEY="sua_chave_aqui"

OPCIONAL:
export OPENAI_MODEL="gpt-4"  # padrão: gpt-3.5-turbo
"""

import os
from dotenv import load_dotenv
from agentes import EmergencyClassifierAgent

load_dotenv()

def testar_agente():
    # Verificar configuração
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERRO: Configure sua chave da OpenAI primeiro!")
        print("No PowerShell: $env:OPENAI_API_KEY='sua_chave'")
        print("No CMD: set OPENAI_API_KEY=sua_chave")
        return
    
    print("🔑 Chave da API configurada ✅")
    print(f"🤖 Modelo: {os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}")
    print()
    
    # Inicializar agente
    try:
        agent = EmergencyClassifierAgent()
        print("🚨 Agente inicializado com sucesso!\n")
    except Exception as e:
        print(f"❌ Erro ao inicializar agente: {e}")
        return
    
    # Casos de teste
    casos = [
        "Incêndio no prédio com pessoas presas!",
        "Assalto à mão armada com feridos",
        "Pessoa tendo infarto",
        "Acidente grave com vítimas presas nas ferragens"
    ]
    
    for caso in casos:
        print(f"\n🚨 Situação: {caso}")
        resultado = agent.classify_emergency(caso)
        
        if resultado["status"] == "sucesso":
            tipos = resultado['tipos_emergencia']
            print(f"📋 Serviços: {', '.join(tipos).upper()}")
            
            # Contatos
            contatos = agent.get_contact_info(tipos)
            for contato in contatos:
                print(f"📞 {contato['telefone']} - {contato['nome']}")
        else:
            print(f"❌ Erro: {resultado['erro']}")

if __name__ == "__main__":
    testar_agente() 