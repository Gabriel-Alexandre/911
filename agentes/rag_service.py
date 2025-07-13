"""
Serviço RAG (Retrieval-Augmented Generation) para sistema de emergência 911.
Fornece funções utilitárias para busca de contexto e gestão de conhecimento.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

# Importação robusta do Chroma
try:
    from langchain_chroma import Chroma
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError:
        from langchain.vectorstores import Chroma

from .vectordb_config import VectorDBConfig

class RAGService:
    """Serviço para operações de RAG (Retrieval-Augmented Generation)."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Inicializa o serviço RAG.
        
        Args:
            openai_api_key: Chave da API OpenAI (opcional, pode vir de variável de ambiente)
        """
        self.db_config = VectorDBConfig()
        
        # Configura API key da OpenAI
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Inicializa embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            chunk_size=1000
        )
        
        # Inicializa text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.vector_store = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self) -> None:
        """Inicializa o vector store."""
        try:
            self.vector_store = self.db_config.get_vector_store(self.embeddings)
            self.db_config.create_collection_if_not_exists()
            print("✅ Vector store inicializado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao inicializar vector store: {e}")
            raise
    
    def add_documents_to_knowledge_base(self, documents: List[str], metadatas: Optional[List[Dict]] = None) -> bool:
        """
        Adiciona documentos à base de conhecimento.
        
        Args:
            documents: Lista de textos a serem adicionados
            metadatas: Lista de metadados associados aos documentos
            
        Returns:
            bool: True se documentos foram adicionados com sucesso
        """
        try:
            if not documents:
                print("❌ Nenhum documento fornecido.")
                return False
            
            # Processa documentos
            doc_objects = []
            for i, doc_text in enumerate(documents):
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                metadata.update({"source": f"document_{i}", "doc_id": i})
                
                # Divide documento em chunks
                chunks = self.text_splitter.split_text(doc_text)
                
                for j, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({"chunk_id": j, "chunk_index": f"{i}_{j}"})
                    
                    doc_objects.append(Document(
                        page_content=chunk,
                        metadata=chunk_metadata
                    ))
            
            # Adiciona ao vector store
            if self.vector_store:
                self.vector_store.add_documents(doc_objects)
                print(f"✅ {len(doc_objects)} chunks adicionados à base de conhecimento.")
                return True
            else:
                print("❌ Vector store não inicializado.")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao adicionar documentos: {e}")
            return False
    
    def search_relevant_context(self, query: str, top_k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante na base de conhecimento.
        
        Args:
            query: Consulta de busca
            top_k: Número máximo de resultados
            score_threshold: Threshold mínimo de similaridade
            
        Returns:
            List[Dict]: Lista de contextos relevantes com metadados
        """
        try:
            if not self.vector_store:
                print("❌ Vector store não inicializado.")
                return []
            
            # Busca por similaridade com scores
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k
            )
            
            # Filtra por threshold e formata resultados
            relevant_contexts = []
            for doc, score in results:
                if score <= (1 - score_threshold):  # Chroma usa distância (menor = mais similar)
                    relevant_contexts.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": 1 - score  # Converte para similaridade
                    })
            
            print(f"✅ Encontrados {len(relevant_contexts)} contextos relevantes.")
            return relevant_contexts
            
        except Exception as e:
            print(f"❌ Erro na busca de contexto: {e}")
            return []
    
    def get_enhanced_context(self, query: str, max_context_length: int = 2000) -> str:
        """
        Busca e formata contexto para melhorar resposta do LLM.
        
        Args:
            query: Consulta original
            max_context_length: Tamanho máximo do contexto em caracteres
            
        Returns:
            str: Contexto formatado para o prompt
        """
        try:
            # Busca contextos relevantes
            contexts = self.search_relevant_context(query, top_k=10)
            
            if not contexts:
                return "Nenhum contexto específico encontrado na base de conhecimento."
            
            # Formata contexto
            formatted_context = "CONTEXTO RELEVANTE DA BASE DE CONHECIMENTO:\n\n"
            current_length = len(formatted_context)
            
            for i, ctx in enumerate(contexts, 1):
                context_piece = f"{i}. {ctx['content']}\n"
                
                if current_length + len(context_piece) > max_context_length:
                    break
                
                formatted_context += context_piece
                current_length += len(context_piece)
            
            return formatted_context.strip()
            
        except Exception as e:
            print(f"❌ Erro ao obter contexto: {e}")
            return "Erro ao acessar base de conhecimento."
    
    def populate_initial_knowledge_base(self) -> bool:
        """
        Popula a base de conhecimento com dados iniciais sobre emergências.
        
        Returns:
            bool: True se população foi bem-sucedida
        """
        initial_documents = [
            # Conhecimento sobre bombeiros
            """
            PROTOCOLO BOMBEIROS - NÍVEIS DE URGÊNCIA:
            
            URGÊNCIA CRÍTICA (Nível 5):
            - Incêndios em edifícios residenciais ou comerciais
            - Explosões com vítimas
            - Vazamentos de gás com risco de explosão
            - Desabamentos com pessoas presas
            - Acidentes com materiais perigosos
            
            URGÊNCIA ALTA (Nível 4):
            - Incêndios em vegetação próxima a residências
            - Vazamentos químicos sem vítimas
            - Acidentes de trânsito com vítimas presas
            
            URGÊNCIA MÉDIA (Nível 3):
            - Incêndios em áreas não habitadas
            - Animais em situação de risco
            - Quedas de árvores obstruindo vias
            
            URGÊNCIA BAIXA (Nível 2):
            - Vazamentos menores de água
            - Remoção de galhos
            
            URGÊNCIA MÍNIMA (Nível 1):
            - Informações gerais
            - Orientações preventivas
            """,
            
            # Conhecimento sobre saúde/SAMU
            """
            PROTOCOLO SAÚDE/SAMU - NÍVEIS DE URGÊNCIA:
            
            URGÊNCIA CRÍTICA (Nível 5):
            - Parada cardiorrespiratória
            - Traumatismo craniano grave
            - Hemorragias arteriais
            - Choque anafilático
            - Queimaduras extensas
            - Overdose/intoxicação grave
            
            URGÊNCIA ALTA (Nível 4):
            - Dificuldade respiratória severa
            - Dor torácica intensa
            - Traumas com fraturas expostas
            - Convulsões contínuas
            - Desmaios com sinais de gravidade
            
            URGÊNCIA MÉDIA (Nível 3):
            - Fraturas simples
            - Cortes profundos
            - Febre alta em crianças
            - Dores abdominais intensas
            
            URGÊNCIA BAIXA (Nível 2):
            - Mal-estar geral
            - Dores moderadas
            - Ferimentos superficiais
            
            URGÊNCIA MÍNIMA (Nível 1):
            - Orientações médicas
            - Informações sobre sintomas leves
            """,
            
            # Conhecimento sobre polícia
            """
            PROTOCOLO POLÍCIA - NÍVEIS DE URGÊNCIA:
            
            URGÊNCIA CRÍTICA (Nível 5):
            - Homicídios em andamento
            - Sequestros/cárcere privado
            - Roubos à mão armada em andamento
            - Tiroteios
            - Ameaças de bomba
            - Violência doméstica com arma
            
            URGÊNCIA ALTA (Nível 4):
            - Furtos em flagrante
            - Brigas com agressão física
            - Acidentes de trânsito com feridos
            - Ameaças verbais graves
            - Perturbação do sossego com violência
            
            URGÊNCIA MÉDIA (Nível 3):
            - Furtos consumados
            - Acidentes de trânsito sem feridos
            - Perturbação do sossego
            - Conflitos familiares
            
            URGÊNCIA BAIXA (Nível 2):
            - Boletins de ocorrência
            - Documentos perdidos
            - Orientações legais
            
            URGÊNCIA MÍNIMA (Nível 1):
            - Informações gerais
            - Denúncias não urgentes
            """,
            
            # Palavras-chave para classificação
            """
            PALAVRAS-CHAVE PARA CLASSIFICAÇÃO DE EMERGÊNCIAS:
            
            INDICADORES DE ALTA URGÊNCIA:
            - "não respira", "parou de respirar", "sem pulso"
            - "sangramento", "muito sangue", "hemorragia"
            - "inconsciente", "desmaiou", "não acorda"
            - "fogo", "incêndio", "fumaça", "chamas"
            - "explosão", "explodiu", "bomba"
            - "arma", "tiro", "disparo", "baleado"
            - "preso", "soterrado", "não consegue sair"
            
            INDICADORES DE URGÊNCIA MÉDIA:
            - "dor forte", "dor intensa", "não aguenta"
            - "acidente", "bateu", "colisão"
            - "quebrou", "fraturou", "machucou"
            - "caiu", "tropeçou", "escorregou"
            
            CANAIS ESPECÍFICOS:
            - Termos relacionados a fogo/explosão → Bombeiros
            - Termos relacionados a saúde/ferimentos → SAMU
            - Termos relacionados a crimes/violência → Polícia
            """
        ]
        
        metadatas = [
            {"category": "bombeiros", "protocol_type": "urgency_levels"},
            {"category": "saude", "protocol_type": "urgency_levels"},
            {"category": "policia", "protocol_type": "urgency_levels"},
            {"category": "keywords", "protocol_type": "classification_indicators"}
        ]
        
        return self.add_documents_to_knowledge_base(initial_documents, metadatas)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da base de conhecimento.
        
        Returns:
            Dict: Estatísticas da base
        """
        try:
            if not self.vector_store:
                return {"error": "Vector store não inicializado"}
            
            # Busca alguns documentos para contar
            sample_results = self.vector_store.similarity_search("", k=1000)  # Busca vazia para pegar tudo
            
            return {
                "total_documents": len(sample_results),
                "vector_store_initialized": self.vector_store is not None,
                "connection_info": self.db_config.get_connection_info()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_knowledge_base(self) -> bool:
        """
        Limpa toda a base de conhecimento.
        
        Returns:
            bool: True se limpeza foi bem-sucedida
        """
        try:
            if self.vector_store:
                # Reinicializa o vector store
                self._initialize_vector_store()
                print("✅ Base de conhecimento limpa com sucesso!")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Erro ao limpar base de conhecimento: {e}")
            return False
