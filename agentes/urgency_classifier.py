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
from .rag_service import RAGService

@dataclass
class EmergencyClassification:
    """Estrutura para resultado da classificação de emergência."""
    canal: str
    nivel_urgencia: int
    justificativa: str
    acoes_recomendadas: list
    tempo_resposta_estimado: str
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
            required_fields = ["canal", "nivel_urgencia", "justificativa", "acoes_recomendadas", "tempo_resposta_estimado"]
            for field in required_fields:
                if field not in data:
                    raise OutputParserException(f"Campo obrigatório '{field}' não encontrado")
            
            return EmergencyClassification(
                canal=data["canal"],
                nivel_urgencia=int(data["nivel_urgencia"]),
                justificativa=data["justificativa"],
                acoes_recomendadas=data.get("acoes_recomendadas", []),
                tempo_resposta_estimado=data["tempo_resposta_estimado"],
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
    "canal": "bombeiros" | "saude" | "policia" | "defesa_civil" | "transito",
    "nivel_urgencia": 1-5 (1=mínima, 2=baixa, 3=média, 4=alta, 5=crítica),
    "justificativa": "Explicação detalhada da classificação",
    "acoes_recomendadas": ["ação1", "ação2", "ação3"],
    "tempo_resposta_estimado": "tempo estimado para atendimento",
    "confidence_score": 0.0-1.0
}

NÃO inclua texto adicional fora do JSON.
"""

class UrgencyClassifier:
    """Agente principal para classificação de urgência de emergências."""
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
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
        self.rag_service = RAGService(openai_api_key)
        
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
1. Canal apropriado (bombeiros, saúde, polícia, defesa_civil, transito)
2. Nível de urgência (1-5)
3. Ações recomendadas
4. Tempo de resposta estimado

DIRETRIZES DE CLASSIFICAÇÃO:

CANAIS:
- bombeiros: incêndios, explosões, vazamentos de gás, resgates, acidentes com materiais perigosos
- saúde: emergências médicas, ferimentos, doenças, overdoses, problemas respiratórios
- policia: crimes, violência, distúrbios, acidentes com aspectos criminais
- defesa_civil: desastres naturais, alagamentos, deslizamentos
- transito: acidentes de trânsito simples, congestionamentos, sinalização

NÍVEIS DE URGÊNCIA:
- 5 (CRÍTICA): Risco iminente de morte, grandes incêndios, crimes violentos em andamento
- 4 (ALTA): Ferimentos graves, incêndios menores, crimes sem violência iminente
- 3 (MÉDIA): Ferimentos moderados, situações de risco controlado
- 2 (BAIXA): Problemas menores, orientações
- 1 (MÍNIMA): Informações, prevenção

TEMPOS DE RESPOSTA TÍPICOS:
- Crítica: "Imediato (0-4 minutos)"
- Alta: "Urgente (5-10 minutos)"
- Média: "Moderado (11-20 minutos)"
- Baixa: "Normal (21-60 minutos)"
- Mínima: "Quando possível (1+ horas)"

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
                print("📚 Populando base de conhecimento inicial...")
                self.rag_service.populate_initial_knowledge_base()
        except Exception as e:
            print(f"⚠️ Aviso: Erro ao verificar base de conhecimento: {e}")
    
    def classify_emergency(self, relato_ocorrencia: str) -> EmergencyClassification:
        """
        Classifica uma ocorrência de emergência.
        
        Args:
            relato_ocorrencia: Descrição da ocorrência
            
        Returns:
            EmergencyClassification: Resultado estruturado da classificação
        """
        try:
            # Busca contexto relevante via RAG
            enhanced_context = self.rag_service.get_enhanced_context(relato_ocorrencia)
            
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
            
            print("✅ Classificação realizada com sucesso!")
            return classification
            
        except Exception as e:
            print(f"❌ Erro na classificação: {e}")
            # Retorna classificação de fallback
            return EmergencyClassification(
                canal="saude",  # Canal seguro por padrão
                nivel_urgencia=4,  # Alta urgência por segurança
                justificativa=f"Erro na classificação automática: {e}. Direcionado para avaliação manual urgente.",
                acoes_recomendadas=["Avaliação manual imediata", "Contato direto com operador"],
                tempo_resposta_estimado="Imediato (avaliação manual)",
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
        
        summary = f"""
🚨 CLASSIFICAÇÃO DE EMERGÊNCIA 🚨

📍 CANAL: {classification.canal.upper()}
🔥 URGÊNCIA: {urgency_labels[classification.nivel_urgencia]} (Nível {classification.nivel_urgencia})
⏰ TEMPO RESPOSTA: {classification.tempo_resposta_estimado}
🎯 CONFIANÇA: {classification.confidence_score:.1%}

📋 JUSTIFICATIVA:
{classification.justificativa}

✅ AÇÕES RECOMENDADAS:
{chr(10).join(f"• {acao}" for acao in classification.acoes_recomendadas)}
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
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- TESTE {i} ---")
            print(f"Relato: {case}")
            
            result = classifier.classify_emergency(case)
            print(classifier.get_classification_summary(result))
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")

if __name__ == "__main__":
    test_classifier()
