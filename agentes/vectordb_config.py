"""
Configurações da base vetorial FAISS para sistema de emergência 911.
FAISS é um banco vetorial simples, rápido e confiável.
"""

import os
import pickle
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Importações do LangChain para FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

load_dotenv()

class VectorDBConfig:
    """Configurações para a base vetorial FAISS."""
    
    # Configurações via variáveis de ambiente
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_db")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "emergency_knowledge")
    
    def __init__(self):
        """Inicializa as configurações da base vetorial."""
        # Cria diretório se não existir
        os.makedirs(self.FAISS_INDEX_PATH, exist_ok=True)
        self.index_file = os.path.join(self.FAISS_INDEX_PATH, f"{self.COLLECTION_NAME}.faiss")
        self.pkl_file = os.path.join(self.FAISS_INDEX_PATH, f"{self.COLLECTION_NAME}.pkl")
        
    def get_embeddings(self) -> OpenAIEmbeddings:
        """
        Retorna o modelo de embeddings OpenAI.
        
        Returns:
            OpenAIEmbeddings: Modelo de embeddings configurado
        """
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            chunk_size=1000
        )
    
    def get_vector_store(self, embeddings: Optional[OpenAIEmbeddings] = None) -> FAISS:
        """
        Retorna o vector store FAISS configurado.
        
        Args:
            embeddings: Modelo de embeddings a ser usado (OpenAI por padrão)
            
        Returns:
            FAISS: Vector store configurado
        """
        if embeddings is None:
            embeddings = self.get_embeddings()
        
        # Verifica se já existe um índice salvo
        if os.path.exists(self.index_file) and os.path.exists(self.pkl_file):
            try:
                # Carrega índice existente
                vector_store = FAISS.load_local(
                    self.FAISS_INDEX_PATH, 
                    embeddings, 
                    self.COLLECTION_NAME,
                    allow_dangerous_deserialization=True
                )
                return vector_store
            except Exception as e:
                print(f"⚠️ Erro ao carregar índice existente: {e}")
                print("🔄 Criando novo índice...")
        
        # Cria novo índice vazio
        # Cria com um documento dummy para inicializar
        dummy_doc = Document(
            page_content="Documento inicial para configuração do sistema 911",
            metadata={"tipo": "sistema", "categoria": "inicial"}
        )
        
        vector_store = FAISS.from_documents([dummy_doc], embeddings)
        
        # Salva o índice
        self.save_vector_store(vector_store)
        
        return vector_store
    
    def save_vector_store(self, vector_store: FAISS) -> bool:
        """
        Salva o vector store no disco.
        
        Args:
            vector_store: Vector store a ser salvo
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            vector_store.save_local(self.FAISS_INDEX_PATH, self.COLLECTION_NAME)
            print(f"✅ Índice salvo em: {self.FAISS_INDEX_PATH}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar índice: {e}")
            return False
    
    def add_documents(self, documents: List[Document], vector_store: Optional[FAISS] = None) -> bool:
        """
        Adiciona documentos ao vector store.
        
        Args:
            documents: Lista de documentos a serem adicionados
            vector_store: Vector store existente (opcional)
            
        Returns:
            bool: True se adicionou com sucesso
        """
        try:
            if vector_store is None:
                vector_store = self.get_vector_store()
            
            # Adiciona documentos
            vector_store.add_documents(documents)
            
            # Salva alterações
            self.save_vector_store(vector_store)
            
            print(f"✅ {len(documents)} documentos adicionados com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar documentos: {e}")
            return False
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> bool:
        """
        Adiciona textos ao vector store.
        
        Args:
            texts: Lista de textos a serem adicionados
            metadatas: Lista de metadados (opcional)
            
        Returns:
            bool: True se adicionou com sucesso
        """
        try:
            vector_store = self.get_vector_store()
            
            # Adiciona textos
            vector_store.add_texts(texts, metadatas=metadatas)
            
            # Salva alterações
            self.save_vector_store(vector_store)
            
            print(f"✅ {len(texts)} textos adicionados com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar textos: {e}")
            return False
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        Busca documentos similares.
        
        Args:
            query: Texto de busca
            k: Número de documentos a retornar
            
        Returns:
            List[Document]: Lista de documentos encontrados
        """
        try:
            vector_store = self.get_vector_store()
            results = vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
    
    def search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """
        Busca documentos similares com pontuação.
        
        Args:
            query: Texto de busca
            k: Número de documentos a retornar
            
        Returns:
            List[tuple]: Lista de tuplas (documento, score)
        """
        try:
            vector_store = self.get_vector_store()
            results = vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            print(f"❌ Erro na busca com score: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do índice.
        
        Returns:
            Dict: Estatísticas do índice
        """
        try:
            vector_store = self.get_vector_store()
            
            # FAISS não tem método direto para contagem, mas podemos inferir
            stats = {
                "index_file_exists": os.path.exists(self.index_file),
                "pkl_file_exists": os.path.exists(self.pkl_file),
                "index_path": self.FAISS_INDEX_PATH,
                "collection_name": self.COLLECTION_NAME,
                "index_file_size": os.path.getsize(self.index_file) if os.path.exists(self.index_file) else 0,
                "pkl_file_size": os.path.getsize(self.pkl_file) if os.path.exists(self.pkl_file) else 0
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def reset_index(self) -> bool:
        """
        Reseta o índice, removendo todos os documentos.
        
        Returns:
            bool: True se resetou com sucesso
        """
        try:
            # Remove arquivos do índice
            if os.path.exists(self.index_file):
                os.remove(self.index_file)
            if os.path.exists(self.pkl_file):
                os.remove(self.pkl_file)
            
            print("✅ Índice resetado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao resetar índice: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com a base vetorial.
        
        Returns:
            bool: True se conexão bem-sucedida
        """
        try:
            # Testa criação do vector store
            vector_store = self.get_vector_store()
            
            # Testa busca simples
            results = vector_store.similarity_search("teste de conexão", k=1)
            
            print("✅ Conexão com FAISS estabelecida com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")
            return False
    
    def test_embeddings(self) -> bool:
        """
        Testa se os embeddings OpenAI estão funcionando.
        
        Returns:
            bool: True se embeddings estão funcionando
        """
        try:
            embeddings = self.get_embeddings()
            
            # Testa com um texto simples
            test_text = "Emergência médica: paciente com dor no peito"
            result = embeddings.embed_query(test_text)
            
            if result and len(result) > 0:
                print(f"✅ Embeddings funcionando! Dimensão: {len(result)}")
                return True
            else:
                print("❌ Embeddings não retornaram resultado válido")
                return False
                
        except Exception as e:
            print(f"❌ Erro nos embeddings: {e}")
            return False
    
    def test_vector_store_operations(self) -> bool:
        """
        Testa operações básicas do vector store (inserção e busca).
        
        Returns:
            bool: True se todas as operações funcionaram
        """
        try:
            # Dados de teste
            test_texts = [
                "Emergência médica: paciente com dor no peito aguda",
                "Incêndio em residência: bombeiros necessários urgentemente",
                "Acidente de trânsito: feridos graves na rodovia",
                "Assalto em andamento: suspeito armado"
            ]
            
            test_metadatas = [
                {"categoria": "medica", "prioridade": "alta"},
                {"categoria": "incendio", "prioridade": "alta"},
                {"categoria": "transito", "prioridade": "media"},
                {"categoria": "criminal", "prioridade": "alta"}
            ]
            
            # Obtém o vector store
            vector_store = self.get_vector_store()
            
            # Testa inserção
            print("🔄 Testando inserção de textos...")
            vector_store.add_texts(texts=test_texts, metadatas=test_metadatas)
            self.save_vector_store(vector_store)
            print("✅ Textos inseridos com sucesso!")
            
            # Testa busca
            print("🔄 Testando busca de documentos...")
            results = vector_store.similarity_search(query="dor no peito", k=2)
            
            if results and len(results) > 0:
                print(f"✅ Busca funcionando! Encontrados {len(results)} documentos")
                for i, doc in enumerate(results):
                    print(f"   {i+1}. {doc.page_content[:50]}...")
                return True
            else:
                print("❌ Busca não retornou resultados")
                return False
                
        except Exception as e:
            print(f"❌ Erro nas operações: {e}")
            return False
    
    def run_full_test_suite(self) -> bool:
        """
        Executa suite completa de testes para verificar se tudo está funcionando.
        
        Returns:
            bool: True se todos os testes passaram
        """
        print("🚀 Iniciando suite completa de testes do FAISS...")
        print("=" * 60)
        
        # Lista de testes
        tests = [
            ("Teste de embeddings OpenAI", self.test_embeddings),
            ("Teste de conexão FAISS", self.test_connection),
            ("Teste de operações do vector store", self.test_vector_store_operations),
            ("Verificação de estatísticas", self.get_index_stats)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🔍 Executando teste: {test_name}")
            print("-" * 40)
            
            start_time = time.time()
            try:
                if test_name == "Verificação de estatísticas":
                    result = test_func()
                    success = bool(result)
                    if success:
                        print("✅ Estatísticas obtidas:")
                        for key, value in result.items():
                            print(f"   {key}: {value}")
                else:
                    success = test_func()
                
                elapsed_time = time.time() - start_time
                
                if success:
                    print(f"✅ {test_name} - PASSOU ({elapsed_time:.2f}s)")
                else:
                    print(f"❌ {test_name} - FALHOU ({elapsed_time:.2f}s)")
                
                results.append((test_name, success, elapsed_time))
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"❌ {test_name} - ERRO: {e} ({elapsed_time:.2f}s)")
                results.append((test_name, False, elapsed_time))
        
        # Resumo final
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES")
        print("=" * 60)
        
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        
        for test_name, result, elapsed_time in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{status:<12} {test_name:<35} ({elapsed_time:.2f}s)")
        
        print("-" * 60)
        print(f"Resultados: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 Todos os testes passaram! FAISS funcionando corretamente.")
            return True
        else:
            print("⚠️  Alguns testes falharam. Verifique as configurações.")
            self.provide_troubleshooting_tips()
            return False
    
    def provide_troubleshooting_tips(self) -> None:
        """
        Fornece dicas de solução de problemas se os testes falharem.
        """
        print("\n🔧 DICAS DE SOLUÇÃO DE PROBLEMAS:")
        print("=" * 50)
        
        print("\n1. 📦 Instalar dependências:")
        print("   pip install faiss-cpu langchain-openai langchain-community")
        
        print("\n2. 🔑 Verificar variáveis de ambiente:")
        print("   OPENAI_API_KEY deve estar definida")
        print("   export OPENAI_API_KEY='sua-chave-aqui'")
        
        print("\n3. 🗂️ Verificar permissões de diretório:")
        print(f"   Diretório: {self.FAISS_INDEX_PATH}")
        print("   Certifique-se de que o diretório tem permissões de escrita")
        
        print("\n4. 🧹 Resetar índice (se necessário):")
        print("   config.reset_index()")
        
        print("\n5. 📊 Verificar estatísticas:")
        print("   config.get_index_stats()")
        
        print("\n💡 FAISS é mais simples que ChromaDB - menos problemas!")

# Função utilitária para execução rápida
def test_vectordb_quick():
    """
    Função utilitária para teste rápido da base vetorial.
    """
    config = VectorDBConfig()
    return config.run_full_test_suite()

# Função para migração de dados do ChromaDB (se necessário)
def migrate_from_chromadb():
    """
    Função para migrar dados do ChromaDB para FAISS (se necessário).
    """
    print("🔄 Migração do ChromaDB para FAISS não implementada")
    print("💡 FAISS é um novo começo - mais simples e confiável!")
    print("📝 Recarregue seus dados usando config.add_texts() ou config.add_documents()")

if __name__ == "__main__":
    # Executa testes quando o arquivo é executado diretamente
    success = test_vectordb_quick()
    
    if success:
        print("\n🎉 FAISS funcionando perfeitamente!")
    else:
        print("\n❌ Alguns testes falharam. Verifique as configurações.")
