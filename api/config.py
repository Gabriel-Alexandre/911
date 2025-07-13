"""
Configurações do módulo API
"""

import os
from typing import Optional
from dotenv import load_dotenv
import asyncpg
from contextlib import asynccontextmanager

# Carregar variáveis de ambiente
load_dotenv()

class APIConfig:
    """Configurações da API"""
    
    # Configurações da Evolution API
    EV_URL: str = os.getenv("EV_URL", "http://localhost:8080")
    EV_API_KEY: Optional[str] = os.getenv("EV_API_KEY")
    EV_INSTANCE: Optional[str] = os.getenv("EV_INSTANCE")
    
    # Configuração OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Configurações do PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "evolution")
    DB_USER: str = os.getenv("DB_USER", "evolution")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "examplepassword")
    
    # Configurações do servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    @classmethod
    def get_database_url(cls) -> str:
        """Retorna a URL de conexão com o banco de dados"""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def validate(cls) -> bool:
        """Valida se todas as variáveis obrigatórias estão configuradas"""
        
        missing_vars = []
        for var_name, var_value in [
            ("EV_API_KEY", cls.EV_API_KEY),
            ("EV_INSTANCE", cls.EV_INSTANCE),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY)
        ]:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente obrigatórias não configuradas: {', '.join(missing_vars)}")
                
        return True
    
    @classmethod
    def get_server_config(cls) -> dict:
        """Retorna configuração do servidor"""
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "reload": cls.RELOAD,
            "log_level": cls.LOG_LEVEL
        }


class DatabaseClient:
    """Cliente para conexão com PostgreSQL"""
    
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Conecta ao banco de dados"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=APIConfig.DB_HOST,
                port=APIConfig.DB_PORT,
                user=APIConfig.DB_USER,
                password=APIConfig.DB_PASSWORD,
                database=APIConfig.DB_NAME,
                min_size=1,
                max_size=10
            )
    
    async def disconnect(self):
        """Desconecta do banco de dados"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Context manager para obter conexão do pool"""
        if self.pool is None:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_query(self, query: str, *args):
        """Executa uma query e retorna os resultados"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args):
        """Executa um comando (INSERT, UPDATE, DELETE)"""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def fetchone(self, query: str, *args):
        """Executa uma query e retorna apenas um resultado"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def init_database(self):
        """Inicializa o banco de dados executando o seed.sql"""
        try:
            # Conectar ao banco
            await self.connect()
            
            # Ler o arquivo seed.sql
            seed_file_path = os.path.join('entities', 'seed.sql')
            
            if not os.path.exists(seed_file_path):
                raise FileNotFoundError(f"Arquivo seed.sql não encontrado em: {seed_file_path}")
            
            with open(seed_file_path, 'r', encoding='utf-8') as f:
                seed_sql = f.read()
            
            # Executar o SQL
            async with self.get_connection() as conn:
                await conn.execute(seed_sql)
            
            print("✅ Banco de dados inicializado com sucesso!")
            print("📋 Tabelas criadas:")
            print("   - ocorrencias")
            print("🔧 Funções e triggers criados para atualização automática de timestamps")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar o banco de dados: {str(e)}")
            raise
    
    async def test_connection(self):
        """Testa a conexão com o banco de dados"""
        try:
            await self.connect()
            async with self.get_connection() as conn:
                result = await conn.fetchrow("SELECT 1 as test")
                if result and result['test'] == 1:
                    print("✅ Conexão com banco de dados estabelecida com sucesso!")
                    return True
                else:
                    print("❌ Falha no teste de conexão")
                    return False
        except Exception as e:
            print(f"❌ Erro ao testar conexão: {str(e)}")
            return False
    
    async def check_tables_exist(self):
        """Verifica se a tabela ocorrencias existe"""
        try:
            await self.connect()
            async with self.get_connection() as conn:
                result = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'ocorrencias'
                """)
                
                if result:
                    print("✅ Tabela 'ocorrencias' existe no banco de dados")
                    return True
                else:
                    print("❌ Tabela 'ocorrencias' não encontrada")
                    return False
                    
        except Exception as e:
            print(f"❌ Erro ao verificar tabela: {str(e)}")
            return False


# Instância global do cliente de banco
db_client = DatabaseClient()

# Funções auxiliares para facilitar o uso
async def init_database():
    """Função auxiliar para inicializar o banco de dados"""
    await db_client.init_database()

async def test_database_connection():
    """Função auxiliar para testar conexão com o banco"""
    return await db_client.test_connection()

async def check_database_tables():
    """Função auxiliar para verificar se as tabelas existem"""
    return await db_client.check_tables_exist() 
