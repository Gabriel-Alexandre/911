#!/usr/bin/env python3
"""
Script para forçar a recriação das tabelas do banco de dados
Execute: python force_setup_database.py
"""

import asyncio
import sys
from api.config import init_database, test_database_connection

async def main():
    """Função principal para recriar o banco de dados"""
    print("🚀 Forçando recriação do banco de dados...")
    
    try:
        # Primeiro, testar a conexão
        print("\n1. Testando conexão com o banco...")
        connection_ok = await test_database_connection()
        
        if not connection_ok:
            print("❌ Erro na conexão. Verifique se o PostgreSQL está rodando e as configurações estão corretas.")
            sys.exit(1)
        
        print("✅ Conexão estabelecida!")
        
        # Forçar inicialização do banco de dados (recria as tabelas)
        print("\n2. Recriando tabelas...")
        await init_database()
        
        print("\n🎉 Banco de dados recriado com sucesso!")
        print("Todas as tabelas foram recriadas.")
            
    except Exception as e:
        print(f"\n❌ Erro durante a reconfiguração: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 