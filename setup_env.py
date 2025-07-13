#!/usr/bin/env python3
"""
Script para configurar o arquivo .env automaticamente
"""

import os
import shutil

def setup_environment():
    """Configura o arquivo .env baseado no config_completo.txt"""
    
    print("🚀 Configurando ambiente do Sistema 911...")
    print("=" * 50)
    
    # Verificar se config_completo.txt existe
    if not os.path.exists("config_completo.txt"):
        print("❌ Arquivo config_completo.txt não encontrado!")
        return False
    
    # Verificar se .env já existe
    if os.path.exists(".env"):
        response = input("⚠️  Arquivo .env já existe. Deseja sobrescrever? (s/N): ")
        if response.lower() != 's':
            print("✅ Configuração cancelada. Arquivo .env mantido.")
            return True
    
    try:
        # Copiar config_completo.txt para .env
        shutil.copy("config_completo.txt", ".env")
        print("✅ Arquivo .env criado com sucesso!")
        print("📝 Edite o arquivo .env e configure as variáveis obrigatórias:")
        print("   - EV_API_KEY: Chave da API da Evolution API")
        print("   - EV_INSTANCE: Nome da instância da Evolution API")
        print("   - WEBHOOK_URL: URL do webhook")
        print("   - OPENAI_API_KEY: Chave da API OpenAI")
        print("\n🔧 Para executar o servidor: python app.py")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar arquivo .env: {e}")
        return False

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("\n📦 Verificando dependências...")
    
    try:
        import fastapi
        import uvicorn
        import httpx
        import openai
        print("✅ Todas as dependências estão instaladas!")
        return True
    except ImportError as e:
        print(f"❌ Dependência não encontrada: {e}")
        print("\n💡 Para instalar as dependências:")
        print("   1. Crie um ambiente virtual: python3 -m venv venv")
        print("   2. Ative o ambiente: source venv/bin/activate")
        print("   3. Instale as dependências: pip install -r requirements.txt")
        print("\n📚 Consulte o INSTALACAO.md para mais detalhes")
        return False

def main():
    """Função principal"""
    print("🔧 Setup do Sistema de Emergência 911")
    print("=" * 50)
    
    # Configurar ambiente
    if not setup_environment():
        return
    
    # Verificar dependências
    check_dependencies()
    
    print("\n🎉 Setup concluído!")
    print("📚 Consulte o README_webhook.md para mais informações.")

if __name__ == "__main__":
    main() 
