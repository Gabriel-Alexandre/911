import os
from typing import Dict, Any, List
from enum import Enum
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

load_dotenv()


class EmergencyType(str, Enum):
    """Tipos de emergência disponíveis"""
    SAMU = "samu"
    POLICIA = "policia"
    BOMBEIRO = "bombeiro"


class EmergencyClassification(BaseModel):
    """Modelo para a classificação de emergência"""
    tipos_emergencia: List[EmergencyType] = Field(
        description="Lista dos tipos de emergência identificados (pode ser múltiplos)"
    )
    justificativa: str = Field(
        description="Justificativa detalhada para a classificação"
    )

    confianca: float = Field(
        description="Nível de confiança da classificação (0.0 a 1.0)"
    )


class EmergencyClassifierAgent:
    """Agente para classificação de emergências"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicializa o agente classificador de emergências
        
        Args:
            openai_api_key: Chave da API do OpenAI (opcional, pode vir do ambiente)
        """
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
        # Verificar se a chave da API está configurada
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY não encontrada. Configure: export OPENAI_API_KEY='sua_chave'")
            
        # Modelo pode ser configurado via variável de ambiente
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        self.llm = ChatOpenAI(
            temperature=0.1,  # Baixa temperatura para respostas mais consistentes
            max_tokens=1000,
            model_name=model_name
        )
        
        # Parser para estruturar a saída
        self.output_parser = PydanticOutputParser(pydantic_object=EmergencyClassification)
        
        # Template do prompt detalhado
        self.prompt_template = PromptTemplate(
            input_variables=["texto_emergencia"],
            template=self._create_detailed_prompt(),
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
    
    def _create_detailed_prompt(self) -> str:
        """Cria um prompt detalhado para classificação de emergências"""
        return """
Você é um especialista em triagem de emergências do Brasil. Sua função é analisar descrições de situações e classificar quais serviços de emergência devem ser acionados.

IMPORTANTE: Você DEVE escolher um ou mais dos serviços abaixo. SEMPRE retorne pelo menos um serviço.
Para situações complexas, escolha MÚLTIPLOS serviços quando apropriado.

SERVIÇOS DISPONÍVEIS:
- SAMU: Emergências médicas, acidentes com feridos, problemas de saúde graves
- POLICIA: Crimes em andamento, violência, roubos, situações de segurança pública  
- BOMBEIRO: Incêndios, resgates, acidentes graves, vazamentos, pessoas presas

CRITÉRIOS DE CLASSIFICAÇÃO:

SAMU:
- Pessoa inconsciente ou com dificuldade respiratória
- Dor no peito/suspeita de infarto
- Acidentes com ferimentos graves
- Overdose de drogas/intoxicação
- Tentativa de suicídio
- Complicações na gravidez/parto
- Queimaduras graves
- Fraturas expostas
- Emergências médicas em geral

POLICIA:
- Assalto em andamento
- Violência doméstica
- Briga com armas
- Sequestro
- Tráfico de drogas flagrante
- Perturbação grave da ordem
- Pessoa armada ameaçando
- Crimes em flagrante

BOMBEIRO:
- Incêndio de qualquer tipo
- Pessoa presa em elevador/local fechado
- Acidentes de trânsito com vítimas presas
- Vazamento de gás
- Animais peçonhentos
- Alagamentos/enchentes
- Queda de árvores/postes
- Resgates em altura
- Emergências estruturais

SITUAÇÕES MÚLTIPLAS (escolha mais de um):
- Acidente grave com crime: POLICIA + SAMU + BOMBEIRO
- Incêndio em prédio com feridos: BOMBEIRO + SAMU
- Assalto com feridos: POLICIA + SAMU
- Acidente com vítima presa: BOMBEIRO + SAMU

INSTRUÇÕES:
1. Analise cuidadosamente o texto fornecido
2. Identifique palavras-chave e contexto da situação
3. Considere a urgência e gravidade
4. SEMPRE escolha pelo menos um serviço
5. Para situações complexas, escolha múltiplos serviços
6. Forneça justificativa clara
7. Avalie sua confiança na classificação

TEXTO DA EMERGÊNCIA: {texto_emergencia}

{format_instructions}

Responda APENAS com o JSON estruturado conforme solicitado.
"""
    
    def classify_emergency(self, texto: str) -> Dict[str, Any]:
        """
        Classifica um texto de emergência
        
        Args:
            texto: Descrição da situação de emergência
            
        Returns:
            Dicionário com a classificação estruturada
        """
        try:
            # Gera o prompt com o texto fornecido
            prompt = self.prompt_template.format(texto_emergencia=texto)
            
            # Processa com o LLM
            response = self.llm.invoke(prompt)
            
            # Parse da resposta estruturada
            parsed_response = self.output_parser.parse(response.content)
            
            # Converte para dicionário - múltiplos tipos suportados
            result = {
                "tipos_emergencia": [tipo.value for tipo in parsed_response.tipos_emergencia],
                "justificativa": parsed_response.justificativa,
                "confianca": parsed_response.confianca,
                "status": "sucesso"
            }
            
            return result
            
        except Exception as e:
            return {
                "status": "erro",
                "erro": str(e),
                "tipos_emergencia": ["samu"],  # Default para emergência médica
                "justificativa": f"Erro ao processar: {str(e)}. Classificação padrão: SAMU por segurança.",
                "confianca": 0.0
            }
    
    def get_contact_info(self, emergency_types: List[str]) -> List[Dict[str, str]]:
        """
        Retorna informações de contato para os tipos de emergência
        
        Args:
            emergency_types: Lista de tipos de emergência (samu, policia, bombeiro)
            
        Returns:
            Lista de dicionários com informações de contato
        """
        contacts = {
            "samu": {
                "telefone": "192",
                "nome": "SAMU - Serviço de Atendimento Móvel de Urgência",
                "tipo": "Emergências médicas"
            },
            "policia": {
                "telefone": "190",
                "nome": "Polícia Militar",
                "tipo": "Segurança pública e crimes"
            },
            "bombeiro": {
                "telefone": "193",
                "nome": "Corpo de Bombeiros",
                "tipo": "Incêndios, resgates e acidentes"
            }
        }
        
        return [contacts.get(emergency_type, contacts["samu"]) for emergency_type in emergency_types]


def test_classifier():
    """Função de teste para o classificador de emergências."""
    # Exemplos de teste - incluindo casos de múltiplos tipos
    test_cases = [
        "Tem fogo na casa do vizinho, muita fumaça!",
        "Meu pai teve um infarto, não está respirando bem",
        "Tem um homem armado na praça ameaçando as pessoas",
        "Batida de carro na esquina, um ferido consciente",
        "Vazamento de gás no prédio, cheiro forte",
        "Assalto em andamento no banco, ladrão armado e tem feridos",
        "Pessoa presa no elevador há 2 horas",
        "Criança engasgada, não consegue respirar",
        "Briga de vizinhos com facas, tem sangue",
        "Árvore caiu na rua bloqueando a passagem",
        "Incêndio no prédio com pessoas presas nos andares superiores",
        "Acidente de carro com vítima presa nas ferragens e inconsciente",
        "Assalto à mão armada com vítima baleada",
        "Explosão em posto de gasolina com feridos e fogo"
    ]
    
    print("🧪 Iniciando testes do classificador de emergências...")
    
    try:
        classifier = EmergencyClassifierAgent()
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- TESTE {i} ---")
            print(f"Relato: {case}")
            
            result = classifier.classify_emergency(case)
            tipos_str = ", ".join(result['tipos_emergencia']).upper()
            print(f"Tipos: {tipos_str}")
            print(f"Confiança: {result['confianca']:.1%}")
            print(f"Status: {result['status']}")
            print(f"Justificativa: {result['justificativa']}")
            
            # Verifica se retornou múltiplos tipos
            if len(result['tipos_emergencia']) > 1:
                print("✅ MÚLTIPLOS TIPOS DETECTADOS!")
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")


if __name__ == "__main__":
    test_classifier()
