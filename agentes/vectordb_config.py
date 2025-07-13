"""
Configurações da base vetorial Chroma para sistema de emergência 911.
Contém configurações hardcoded para conexão e inicialização.
"""

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
import os
from typing import Optional

# Importação robusta do Chroma
try:
    from langchain_chroma import Chroma
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError:
        from langchain.vectorstores import Chroma

class VectorDBConfig:
    """Configurações para conexão com a base vetorial Chroma."""
    
    # Configurações hardcoded
    CHROMA_HOST = "localhost"
    CHROMA_PORT = 8000
    CHROMA_DB_IMPL = "duckdb+parquet"
    CHROMA_PERSIST_DIRECTORY = "./chroma_db"
    COLLECTION_NAME = "emergency_knowledge"
    
    # URLs de conexão
    CHROMA_SERVER_URL = f"http://{CHROMA_HOST}:{CHROMA_PORT}"
    
    def __init__(self):
        """Inicializa as configurações da base vetorial."""
        self.settings = Settings(
            chroma_server_host=self.CHROMA_HOST,
            chroma_server_http_port=self.CHROMA_PORT,
            chroma_db_impl=self.CHROMA_DB_IMPL,
            persist_directory=self.CHROMA_PERSIST_DIRECTORY
        )
        
    def get_chroma_client(self) -> chromadb.Client:
        """
        Retorna cliente Chroma configurado.
        
        Returns:
            chromadb.Client: Cliente configurado para conexão com Chroma
        """
        try:
            # Tenta conectar ao servidor Chroma
            client = chromadb.HttpClient(
                host=self.CHROMA_HOST,
                port=self.CHROMA_PORT
            )
            # Teste a conexão
            client.heartbeat()
            return client
        except Exception:
            # Fallback para cliente local se servidor não estiver disponível
            return chromadb.PersistentClient(
                path=self.CHROMA_PERSIST_DIRECTORY,
                settings=self.settings
            )
    
    def get_vector_store(self, embeddings: Optional[OpenAIEmbeddings] = None) -> Chroma:
        """
        Retorna o vector store Chroma configurado.
        
        Args:
            embeddings: Modelo de embeddings a ser usado (OpenAI por padrão)
            
        Returns:
            Chroma: Vector store configurado
        """
        if embeddings is None:
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                chunk_size=1000
            )
        
        try:
            # Tenta usar servidor HTTP
            return Chroma(
                collection_name=self.COLLECTION_NAME,
                embedding_function=embeddings,
                client=chromadb.HttpClient(
                    host=self.CHROMA_HOST,
                    port=self.CHROMA_PORT
                )
            )
        except Exception:
            # Fallback para cliente persistente local
            return Chroma(
                collection_name=self.COLLECTION_NAME,
                embedding_function=embeddings,
                persist_directory=self.CHROMA_PERSIST_DIRECTORY
            )
    
    def create_collection_if_not_exists(self) -> bool:
        """
        Cria a coleção se ela não existir.
        
        Returns:
            bool: True se coleção foi criada ou já existe
        """
        try:
            client = self.get_chroma_client()
            
            # Verifica se coleção já existe
            collections = client.list_collections()
            collection_names = [col.name for col in collections]
            
            if self.COLLECTION_NAME not in collection_names:
                client.create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"description": "Base de conhecimento para emergências 911"}
                )
                print(f"Coleção '{self.COLLECTION_NAME}' criada com sucesso.")
            else:
                print(f"Coleção '{self.COLLECTION_NAME}' já existe.")
            
            return True
        except Exception as e:
            print(f"Erro ao criar coleção: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """
        Retorna informações de conexão para debug.
        
        Returns:
            dict: Informações de conexão
        """
        return {
            "host": self.CHROMA_HOST,
            "port": self.CHROMA_PORT,
            "server_url": self.CHROMA_SERVER_URL,
            "collection_name": self.COLLECTION_NAME,
            "persist_directory": self.CHROMA_PERSIST_DIRECTORY
        }
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com a base vetorial.
        
        Returns:
            bool: True se conexão bem-sucedida
        """
        try:
            client = self.get_chroma_client()
            client.heartbeat()
            print("✅ Conexão com Chroma estabelecida com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro na conexão com Chroma: {e}")
            return False
