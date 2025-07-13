#!/usr/bin/env python3
"""
Script auxiliar para configurar o banco de dados
Execute na raiz do projeto: python setup_database.py
"""

import asyncio
import sys
from api.config import init_database, test_database_connection, check_database_tables

async def main():
    """Função principal para configurar o banco de dados"""
    print("🚀 Configurando banco de dados...")
    
    try:
        # Primeiro, testar a conexão
        print("\n1. Testando conexão com o banco...")
        connection_ok = await test_database_connection()
        
        if not connection_ok:
            print("❌ Erro na conexão. Verifique se o PostgreSQL está rodando e as configurações estão corretas.")
            sys.exit(1)
        
        # Verificar se as tabelas já existem
        print("\n2. Verificando se as tabelas existem...")
        tables_exist = await check_database_tables()
        
        if tables_exist:
            print("ℹ️  Tabelas já existem. Deseja recriar? (s/n)")
            response = input().lower()
            if response != 's':
                print("✅ Configuração concluída.")
                return
        
        # Inicializar o banco de dados
        print("\n3. Inicializando banco de dados...")
        await init_database()
        
        # Verificar novamente se as tabelas foram criadas
        print("\n4. Verificando se as tabelas foram criadas...")
        tables_created = await check_database_tables()
        
        if tables_created:
            print("\n🎉 Banco de dados configurado com sucesso!")
            print("Você pode agora usar o serviço de Ocorrências.")
        else:
            print("\n❌ Erro ao criar as tabelas.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Erro durante a configuração: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
