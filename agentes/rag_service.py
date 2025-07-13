"""
Serviço RAG (Retrieval-Augmented Generation) para sistema de emergência 911.
Fornece funções utilitárias para busca de contexto e gestão de conhecimento.
"""

import os
import pandas as pd
import PyPDF2
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

# Import do FAISS para vector store
from langchain_community.vectorstores import FAISS

# Importação robusta que funciona tanto em execução direta quanto como módulo
try:
    from .vectordb_config import VectorDBConfig
except ImportError:
    from vectordb_config import VectorDBConfig

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
            print("🔗 Vector store FAISS inicializado")
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
                # Salva o índice FAISS após adicionar documentos
                self.db_config.save_vector_store(self.vector_store)
                print(f"📝 {len(doc_objects)} chunks adicionados e salvos")
                return True
            else:
                print("❌ Vector store não inicializado.")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao adicionar documentos: {e}")
            return False
    
    def search_relevant_context(self, query: str, top_k: int = 5, score_threshold: float = 1.5) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante na base de conhecimento.
        
        Args:
            query: Consulta de busca
            top_k: Número máximo de resultados
            score_threshold: Threshold máximo de distância (valores menores = mais similar)
            
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
            
            # DEBUG: Mostra os scores retornados
            # print(f"🔍 DEBUG - Scores brutos do Chroma para '{query}':")
            # for i, (doc, score) in enumerate(results):
            #     print(f"   {i+1}. Score: {score:.4f} | Conteúdo: {doc.page_content[:50]}...")
            
            # Filtra por threshold e formata resultados
            relevant_contexts = []
            for doc, score in results:
                # Chroma usa distância (menor = mais similar)
                # Aceita scores menores que o threshold
                if score <= score_threshold:
                    relevant_contexts.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": max(0, 1 - (score / 2))  # Normaliza para 0-1
                    })
            
            print(f"📚 {len(relevant_contexts)} contextos relevantes")
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
    
    def load_database_files_to_knowledge_base(self) -> bool:
        """
        Carrega todos os arquivos das pastas database/Bombeiros, database/Policia e database/Saude
        para a base de conhecimento vetorial.
        
        Returns:
            bool: True se carregamento foi bem-sucedido
        """
        try:
            # Obtém o diretório base do projeto
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)  # Sobe um nível para sair da pasta agentes
            
            # Diretórios a serem processados
            database_dirs = {
                "bombeiros": os.path.join(project_root, "database", "Bombeiros"),
                "policia": os.path.join(project_root, "database", "Policia"), 
                "saude": os.path.join(project_root, "database", "Saude")
            }
            
            total_files_processed = 0
            total_chunks_added = 0
            
            for category, dir_path in database_dirs.items():
                print(f"📁 Processando arquivos da categoria: {category.upper()}")
                
                # Verifica se diretório existe
                if not os.path.exists(dir_path):
                    print(f"⚠️  Diretório não encontrado: {dir_path}")
                    continue
                
                # Percorre todos os arquivos do diretório
                for file_path in Path(dir_path).rglob("*"):
                    if file_path.is_file():
                        try:
                            file_extension = file_path.suffix.lower()
                            file_name = file_path.name
                            
                            print(f"📄 Processando arquivo: {file_name}")
                            
                            # Extrai conteúdo baseado na extensão
                            content = ""
                            if file_extension == ".pdf":
                                content = self._extract_pdf_content(str(file_path))
                            elif file_extension == ".csv":
                                content = self._extract_csv_content(str(file_path))
                            elif file_extension == ".xlsx":
                                content = self._extract_xlsx_content(str(file_path))
                            elif file_extension == ".txt":
                                content = self._extract_txt_content(str(file_path))
                            else:
                                print(f"⚠️  Tipo de arquivo não suportado: {file_extension}")
                                continue
                            
                            if content:
                                # Prepara metadados
                                metadata = {
                                    "category": category,
                                    "filename": file_name,
                                    "file_path": str(file_path),
                                    "file_type": file_extension,
                                    "source": f"{category}_{file_name}"
                                }
                                
                                # Adiciona à base de conhecimento
                                if self.add_documents_to_knowledge_base([content], [metadata]):
                                    total_files_processed += 1
                                    # Estima chunks (aproximado)
                                    estimated_chunks = len(content) // 1000
                                    total_chunks_added += estimated_chunks
                                    print(f"✅ Arquivo processado com sucesso!")
                                else:
                                    print(f"❌ Falha ao processar arquivo: {file_name}")
                            else:
                                print(f"⚠️  Conteúdo vazio ou erro na extração: {file_name}")
                                
                        except Exception as e:
                            print(f"❌ Erro ao processar arquivo {file_path}: {e}")
                            continue
            
            print(f"\n📊 RESUMO DO CARREGAMENTO:")
            print(f"   - Arquivos processados: {total_files_processed}")
            print(f"   - Chunks estimados: {total_chunks_added}")
            print(f"   - Status: {'✅ Sucesso' if total_files_processed > 0 else '❌ Nenhum arquivo processado'}")
            
            return total_files_processed > 0
            
        except Exception as e:
            print(f"❌ Erro geral no carregamento da base: {e}")
            return False
    
    def _extract_pdf_content(self, pdf_path: str) -> str:
        """
        Extrai conteúdo de texto de um arquivo PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            str: Conteúdo extraído do PDF
        """
        try:
            content = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    content += page.extract_text() + "\n"
            
            return content.strip()
            
        except Exception as e:
            print(f"❌ Erro ao extrair PDF {pdf_path}: {e}")
            return ""
    
    def _extract_csv_content(self, csv_path: str) -> str:
        """
        Extrai conteúdo de um arquivo CSV e converte para texto estruturado.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            str: Conteúdo estruturado do CSV
        """
        try:
            # Tenta múltiplas codificações para CSVs brasileiros
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
            
            df = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    if "codec" not in str(e).lower():
                        print(f"❌ Erro não relacionado à codificação no CSV {csv_path}: {e}")
                        continue
            
            if df is None:
                print(f"⚠️  Não foi possível decodificar o CSV {csv_path} com nenhuma codificação")
                return ""
            
            # Converte para texto estruturado
            content = f"DADOS DO ARQUIVO: {os.path.basename(csv_path)}\n"
            content += f"CODIFICAÇÃO USADA: {used_encoding}\n\n"
            
            # Adiciona informações sobre colunas
            content += f"COLUNAS: {', '.join(df.columns.tolist())}\n\n"
            
            # Adiciona algumas estatísticas básicas
            content += f"TOTAL DE REGISTROS: {len(df)}\n\n"
            
            # Adiciona dados (limitando para não ficar muito grande)
            content += "DADOS:\n"
            for index, row in df.head(100).iterrows():  # Limita a 100 linhas
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                content += f"{row_text}\n"
            
            if len(df) > 100:
                content += f"\n... (exibindo apenas primeiras 100 linhas de {len(df)} registros)"
            
            return content
            
        except Exception as e:
            print(f"❌ Erro ao extrair CSV {csv_path}: {e}")
            return ""
    
    def _extract_xlsx_content(self, xlsx_path: str) -> str:
        """
        Extrai conteúdo de um arquivo XLSX e converte para texto estruturado.
        
        Args:
            xlsx_path: Caminho para o arquivo XLSX
            
        Returns:
            str: Conteúdo estruturado do XLSX
        """
        try:
            # Lê o arquivo Excel
            excel_file = pd.ExcelFile(xlsx_path)
            content = f"DADOS DO ARQUIVO EXCEL: {os.path.basename(xlsx_path)}\n\n"
            
            # Processa cada planilha
            for sheet_name in excel_file.sheet_names:
                content += f"PLANILHA: {sheet_name}\n"
                content += "=" * 50 + "\n"
                
                # Lê os dados da planilha
                df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
                
                # Adiciona informações sobre colunas
                content += f"COLUNAS: {', '.join(df.columns.tolist())}\n\n"
                
                # Adiciona estatísticas básicas
                content += f"TOTAL DE REGISTROS: {len(df)}\n\n"
                
                # Adiciona dados (limitando para não ficar muito grande)
                content += "DADOS:\n"
                for index, row in df.head(50).iterrows():  # Limita a 50 linhas por planilha
                    row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
                    content += f"{row_text}\n"
                
                if len(df) > 50:
                    content += f"\n... (exibindo apenas primeiras 50 linhas de {len(df)} registros)\n"
                
                content += "\n" + "=" * 50 + "\n\n"
            
            return content
            
        except Exception as e:
            print(f"❌ Erro ao extrair XLSX {xlsx_path}: {e}")
            return ""
    
    def _extract_txt_content(self, txt_path: str) -> str:
        """
        Extrai conteúdo de um arquivo TXT.
        
        Args:
            txt_path: Caminho para o arquivo TXT
            
        Returns:
            str: Conteúdo do arquivo TXT
        """
        try:
            # Tenta diferentes codificações
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(txt_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        
                    # Adiciona cabeçalho com informações do arquivo
                    header = f"ARQUIVO DE TEXTO: {os.path.basename(txt_path)}\n"
                    header += f"CODIFICAÇÃO: {encoding}\n"
                    header += "=" * 50 + "\n\n"
                    
                    return header + content.strip()
                    
                except UnicodeDecodeError:
                    continue
            
            # Se nenhuma codificação funcionou
            print(f"⚠️  Não foi possível decodificar o arquivo {txt_path}")
            return ""
            
        except Exception as e:
            print(f"❌ Erro ao extrair TXT {txt_path}: {e}")
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da base de conhecimento.
        
        Returns:
            Dict: Estatísticas da base
        """
        try:
            if not self.vector_store:
                return {"error": "Vector store não inicializado"}
            
            # Obtém estatísticas do índice FAISS
            index_stats = self.db_config.get_index_stats()
            
            return {
                "vector_store_initialized": self.vector_store is not None,
                "index_stats": index_stats,
                "database_type": "FAISS"
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
            # Reseta o índice FAISS
            if self.db_config.reset_index():
                # Reinicializa o vector store
                self._initialize_vector_store()
                print("✅ Base de conhecimento limpa com sucesso!")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Erro ao limpar base de conhecimento: {e}")
            return False


if __name__ == "__main__":
    rag_service = RAGService()
    rag_service.load_database_files_to_knowledge_base()