"""
Agente de IA para classificação de urgência de ocorrências de emergência 911.
Utiliza LangChain, OpenAI e RAG para classificar e direcionar emergências.
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseOutputParser
from langchain.schema.output_parser import OutputParserException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List

# Importação robusta que funciona tanto em execução direta quanto como módulo
try:
    from .rag_service import RAGService
except ImportError:
    from rag_service import RAGService

load_dotenv()

@dataclass
class EmergencyClassification:
    """Estrutura para resultado da classificação de emergência."""
    canal: List[str]
    nivel_urgencia: int
    justificativa: str
    confidence_score: float

class EmergencyOutputParser(BaseOutputParser[EmergencyClassification]):
    """Parser personalizado para saída estruturada do LLM."""
    
    def parse(self, text: str) -> EmergencyClassification:
        """
        Parseia a resposta do LLM para EmergencyClassification.
        
        Args:
            text: Resposta do LLM em formato JSON
            
        Returns:
            EmergencyClassification: Objeto estruturado com a classificação
        """
        try:
            # Tenta extrair JSON da resposta
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise OutputParserException("JSON não encontrado na resposta")
            
            json_str = text[start_idx:end_idx]
            data = json.loads(json_str)
            
            # Valida campos obrigatórios
            required_fields = ["canal", "nivel_urgencia", "justificativa"]
            for field in required_fields:
                if field not in data:
                    raise OutputParserException(f"Campo obrigatório '{field}' não encontrado")
            
            return EmergencyClassification(
                canal=data["canal"] if isinstance(data["canal"], list) else [data["canal"]],
                nivel_urgencia=int(data["nivel_urgencia"]),
                justificativa=data["justificativa"],
                confidence_score=float(data.get("confidence_score", 0.8))
            )
            
        except json.JSONDecodeError as e:
            raise OutputParserException(f"Erro ao parsear JSON: {e}")
        except Exception as e:
            raise OutputParserException(f"Erro no parse: {e}")
    
    def get_format_instructions(self) -> str:
        """Retorna instruções de formatação para o LLM."""
        return """
IMPORTANTE: Responda APENAS com um JSON válido no seguinte formato:

{
    "canal": ["bombeiros"] | ["saude"] | ["policia"] | ["defesa_civil"] | ["transito"] | ["bombeiros", "saude"] (lista de canais),
    "nivel_urgencia": 1-5 (1=mínima, 2=baixa, 3=média, 4=alta, 5=crítica),
    "justificativa": "Explicação detalhada da classificação",
    "confidence_score": 0.0-1.0
}

NÃO inclua texto adicional fora do JSON.
"""

class UrgencyClassifier:
    """Agente principal para classificação de urgência de emergências."""
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4.1-mini"):
        """
        Inicializa o classificador de urgência.
        
        Args:
            openai_api_key: Chave da API OpenAI
            model: Modelo OpenAI a ser usado
        """
        # Configura API key
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Inicializa LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.1,  # Baixa criatividade para consistência
            max_tokens=1000
        )
        
        # Inicializa serviço RAG
        self.rag_service = RAGService()
        
        # Inicializa parser de saída
        self.output_parser = EmergencyOutputParser()
        
        # Cria prompt template
        self._create_prompt_template()
        
        # Popula base de conhecimento se estiver vazia
        self._ensure_knowledge_base()
    
    def _create_prompt_template(self) -> None:
        """Cria o template de prompt para classificação."""
        
        system_message = SystemMessagePromptTemplate.from_template("""
Você é um agente especialista em classificação de emergências para o sistema 911.
Sua função é analisar relatos de ocorrências e determinar:
1. Canal(is) apropriado(s) (bombeiros, saúde, polícia, defesa_civil, transito)
2. Nível de urgência (1-5)
3. Justificativa detalhada da classificação

IMPORTANTE: Se houver uma CLASSIFICAÇÃO PRÉVIA no contexto, use-a como referência adicional para:
- Confirmar ou refinar a identificação dos canais
- Ajustar o nível de urgência com base na análise prévia
- Incorporar insights da justificativa prévia em sua análise

DIRETRIZES DE CLASSIFICAÇÃO:

CANAIS (pode ser um ou múltiplos):
- bombeiros: incêndios, explosões, vazamentos de gás, resgates, acidentes com materiais perigosos
- saude: emergências médicas, ferimentos, doenças, overdoses, problemas respiratórios
- policia: crimes, violência, distúrbios, acidentes com aspectos criminais
- defesa_civil: desastres naturais, alagamentos, deslizamentos
- transito: acidentes de trânsito simples, congestionamentos, sinalização

MÚLTIPLOS CANAIS podem ser necessários quando:
- Acidente com feridos (transito + saude)
- Incêndio criminoso (bombeiros + policia)
- Acidente com materiais perigosos (bombeiros + saude + defesa_civil)

NÍVEIS DE URGÊNCIA:
- 5 (CRÍTICA): Risco iminente de morte, grandes incêndios, crimes violentos em andamento
- 4 (ALTA): Ferimentos graves, incêndios menores, crimes sem violência iminente
- 3 (MÉDIA): Ferimentos moderados, situações de risco controlado
- 2 (BAIXA): Problemas menores, orientações
- 1 (MÍNIMA): Informações, prevenção

{context}

{format_instructions}
""")
        
        human_message = HumanMessagePromptTemplate.from_template("""
RELATO DA OCORRÊNCIA:
{ocorrencia}

Analise este relato e forneça a classificação estruturada conforme as diretrizes.
""")
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            system_message,
            human_message
        ])
    
    def _ensure_knowledge_base(self) -> None:
        """Garante que a base de conhecimento esteja populada."""
        try:
            stats = self.rag_service.get_stats()
            if stats.get("total_documents", 0) == 0:
                print("📚 Populando base de conhecimento...")
                self.rag_service.populate_initial_knowledge_base()
        except Exception as e:
            print(f"⚠️ Aviso: Erro ao verificar base de conhecimento: {e}")
    
    def classify_emergency(self, relato_ocorrencia: str, emergency_classification: Optional[Dict[str, Any]] = None) -> EmergencyClassification:
        """
        Classifica uma ocorrência de emergência.
        
        Args:
            relato_ocorrencia: Descrição da ocorrência
            emergency_classification: Resultado do emergency_classifier.py (opcional)
            
        Returns:
            EmergencyClassification: Resultado estruturado da classificação
        """
        try:
            # Busca contexto relevante via RAG
            enhanced_context = self.rag_service.get_enhanced_context(relato_ocorrencia)
            
            # Adiciona informações do emergency_classifier se disponível
            if emergency_classification:
                tipos_emergencia = emergency_classification.get("tipos_emergencia", [])
                justificativa_emergencia = emergency_classification.get("justificativa", "")
                confianca_emergencia = emergency_classification.get("confianca", 0.0)
                
                # Mapeia tipos do emergency_classifier para canais do urgency_classifier
                mapeamento_canais = {
                    "samu": "saude",
                    "policia": "policia", 
                    "bombeiro": "bombeiros"
                }
                
                canais_sugeridos = []
                for tipo in tipos_emergencia:
                    canal = mapeamento_canais.get(tipo, tipo)
                    canais_sugeridos.append(canal)
                
                classificacao_previa = f"""
CLASSIFICAÇÃO PRÉVIA DO EMERGENCY CLASSIFIER:
- Tipos identificados: {', '.join(tipos_emergencia).upper()}
- Canais sugeridos: {', '.join(canais_sugeridos)}
- Justificativa: {justificativa_emergencia}
- Confiança: {confianca_emergencia:.1%}

Use esta informação como referência adicional para sua análise.
"""
                enhanced_context += f"\n\n{classificacao_previa}"
            
            # Prepara prompt
            formatted_prompt = self.prompt_template.format_messages(
                context=enhanced_context,
                ocorrencia=relato_ocorrencia,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Gera resposta
            response = self.llm.invoke(formatted_prompt)
            
            # Parseia resposta
            classification = self.output_parser.parse(response.content)
            
            print("📋 Classificação concluída")
            return classification
            
        except Exception as e:
            print(f"❌ Erro na classificação: {e}")
            # Retorna classificação de fallback
            return EmergencyClassification(
                canal=["saude"],  # Canal seguro por padrão
                nivel_urgencia=4,  # Alta urgência por segurança
                justificativa=f"Erro na classificação automática: {e}. Direcionado para avaliação manual urgente.",
                confidence_score=0.1
            )
    
    def classify_batch(self, relatos: list) -> list:
        """
        Classifica múltiplas ocorrências em lote.
        
        Args:
            relatos: Lista de descrições de ocorrências
            
        Returns:
            list: Lista de EmergencyClassification
        """
        results = []
        for i, relato in enumerate(relatos):
            print(f"Processando ocorrência {i+1}/{len(relatos)}...")
            result = self.classify_emergency(relato)
            results.append(result)
        
        return results
    
    def get_classification_summary(self, classification: EmergencyClassification) -> str:
        """
        Gera resumo textual da classificação.
        
        Args:
            classification: Resultado da classificação
            
        Returns:
            str: Resumo formatado
        """
        urgency_labels = {
            1: "MÍNIMA",
            2: "BAIXA", 
            3: "MÉDIA",
            4: "ALTA",
            5: "CRÍTICA"
        }
        
        # Formata os canais
        canais_str = ", ".join(canal.upper() for canal in classification.canal)
        
        summary = f"""
🚨 CLASSIFICAÇÃO DE EMERGÊNCIA 🚨

📍 CANAL(IS): {canais_str}
🔥 URGÊNCIA: {urgency_labels[classification.nivel_urgencia]} (Nível {classification.nivel_urgencia})
🎯 CONFIANÇA: {classification.confidence_score:.1%}

📋 JUSTIFICATIVA:
{classification.justificativa}
"""
        return summary.strip()
    
    def add_knowledge(self, documents: list, categories: list = None) -> bool:
        """
        Adiciona conhecimento personalizado à base.
        
        Args:
            documents: Lista de documentos/textos
            categories: Lista de categorias correspondentes
            
        Returns:
            bool: True se adicionado com sucesso
        """
        metadatas = []
        if categories:
            metadatas = [{"category": cat, "custom": True} for cat in categories]
        
        return self.rag_service.add_documents_to_knowledge_base(documents, metadatas)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Retorna status do sistema classificador.
        
        Returns:
            Dict: Status completo do sistema
        """
        return {
            "llm_model": self.llm.model_name,
            "rag_stats": self.rag_service.get_stats(),
            "vector_db_connection": self.rag_service.db_config.test_connection(),
            "system_ready": True
        }

def test_classifier():
    """Função de teste para o classificador."""
    # Exemplos de teste
    test_cases = [
        "Tem fogo na casa do vizinho, muita fumaça!",
        "Meu pai teve um infarto, não está respirando bem",
        "Tem um homem armado na praça ameaçando as pessoas",
        "Batida de carro na esquina, um ferido consciente",
        "Vazamento de gás no prédio, cheiro forte"
    ]
    
    print("🧪 Iniciando testes do classificador...")
    
    try:
        classifier = UrgencyClassifier()
        
        # Simula uso com emergency_classifier
        try:
            from .emergency_classifier import EmergencyClassifierAgent
            emergency_classifier = EmergencyClassifierAgent()
            use_emergency_classifier = True
            print("📋 Usando emergency_classifier como referência")
        except ImportError:
            try:
                from emergency_classifier import EmergencyClassifierAgent
                emergency_classifier = EmergencyClassifierAgent()
                use_emergency_classifier = True
                print("📋 Usando emergency_classifier como referência")
            except ImportError:
                use_emergency_classifier = False
                print("⚠️ emergency_classifier não disponível - usando apenas urgency_classifier")
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- TESTE {i} ---")
            print(f"Relato: {case}")
            
            # Usa emergency_classifier se disponível
            emergency_result = None
            if use_emergency_classifier:
                try:
                    emergency_result = emergency_classifier.classify_emergency(case)
                    print(f"Emergency Classifier: {', '.join(emergency_result['tipos_emergencia']).upper()}")
                except Exception as e:
                    print(f"⚠️ Erro no emergency_classifier: {e}")
                    emergency_result = None
            
            result = classifier.classify_emergency(case, emergency_result)
            print(classifier.get_classification_summary(result))
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")

if __name__ == "__main__":
    test_classifier()
