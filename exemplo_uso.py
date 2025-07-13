"""
Exemplo de uso do sistema de classificação de urgência de emergências 911.
Demonstra como inicializar e utilizar o agente de IA para classificar ocorrências.
"""

import os
from agentes.urgency_classifier import UrgencyClassifier

from dotenv import load_dotenv

load_dotenv()

def exemplo_basico():
    """Exemplo básico de uso do classificador."""
    
    print("🚨 SISTEMA DE CLASSIFICAÇÃO DE EMERGÊNCIAS 911 🚨\n")
    
    # Configura API key (substitua pela sua chave)
    # os.environ["OPENAI_API_KEY"] = "sua_chave_openai_aqui"
    
    try:
        # Inicializa o classificador
        print("Inicializando sistema...")
        classifier = UrgencyClassifier()
        
        # Verifica status do sistema
        status = classifier.get_system_status()
        print(f"✅ Sistema inicializado - Modelo: {status['llm_model']}")
        
        # Exemplos de ocorrências para teste
        ocorrencias_exemplo = [
            "Minha casa está pegando fogo! Tem muita fumaça e as chamas estão altas!",
            "Um homem caiu da escada e está inconsciente, tem muito sangue na cabeça",
            "Tem dois homens brigando na rua com facas, um deles está ferido",
            "Meu carro bateu em outro na esquina, ninguém se machucou mas não conseguimos sair",
            "Tem um vazamento de gás no prédio, o cheiro está muito forte",
            "Uma senhora passou mal no shopping, está com dificuldade para respirar",
            "Vi um homem roubando uma bolsa e correndo pela praça",
            "Tem uma árvore que caiu na rua e está bloqueando o trânsito"
        ]
        
        print("\n" + "="*60)
        print("PROCESSANDO OCORRÊNCIAS DE EXEMPLO")
        print("="*60)
        
        # Processa cada ocorrência
        for i, ocorrencia in enumerate(ocorrencias_exemplo, 1):
            print(f"\n🔍 OCORRÊNCIA {i}:")
            print(f"Relato: '{ocorrencia}'")
            print("-" * 50)
            
            # Classifica a ocorrência
            resultado = classifier.classify_emergency(ocorrencia)
            
            # Mostra resultado formatado
            print(classifier.get_classification_summary(resultado))
            
            print("-" * 50)
        
        print("\n✅ Processamento concluído!")
        
    except Exception as e:
        print(f"❌ Erro no exemplo: {e}")
        print("Verifique se:")
        print("1. A API key da OpenAI está configurada")
        print("2. O Docker com Chroma está rodando (docker-compose up -d)")
        print("3. As dependências estão instaladas (pip install -r requirements.txt)")

def exemplo_uso_personalizado():
    """Exemplo de uso com conhecimento personalizado."""
    
    print("\n🔧 EXEMPLO COM CONHECIMENTO PERSONALIZADO\n")
    
    try:
        classifier = UrgencyClassifier()
        
        # Adiciona conhecimento personalizado
        documentos_personalizados = [
            """
            PROTOCOLO ESPECIAL PARA ANIMAIS:
            - Animais feridos em via pública: Nível 3, Canal: bombeiros
            - Animais atacando pessoas: Nível 4, Canal: policia + bombeiros
            - Animais presos em locais altos: Nível 2, Canal: bombeiros
            - Animais mortos causando problemas sanitários: Nível 2, Canal: defesa_civil
            """,
            """
            PROTOCOLO PARA EVENTOS CLIMÁTICOS:
            - Enchentes em andamento: Nível 4, Canal: defesa_civil
            - Vendaval com destelhamentos: Nível 3, Canal: defesa_civil
            - Granizo causando ferimentos: Nível 4, Canal: saude + defesa_civil
            - Raios causando incêndios: Nível 5, Canal: bombeiros
            """
        ]
        
        categorias = ["animais", "clima"]
        
        print("Adicionando conhecimento personalizado...")
        success = classifier.add_knowledge(documentos_personalizados, categorias)
        
        if success:
            print("✅ Conhecimento personalizado adicionado!")
            
            # Testa com casos específicos
            casos_especiais = [
                "Tem um cachorro ferido no meio da rua, ele foi atropelado",
                "Está chovendo muito forte e minha rua está alagando",
                "Um gato está preso no telhado há 2 dias",
                "O vento arrancou o telhado da casa do vizinho"
            ]
            
            print("\nTestando casos com conhecimento personalizado:")
            for caso in casos_especiais:
                resultado = classifier.classify_emergency(caso)
                print(f"\n📋 Caso: {caso}")
                print(f"➡️ Canal: {resultado.canal} | Urgência: {resultado.nivel_urgencia}")
        
    except Exception as e:
        print(f"❌ Erro no exemplo personalizado: {e}")

def exemplo_lote():
    """Exemplo de processamento em lote."""
    
    print("\n📦 EXEMPLO DE PROCESSAMENTO EM LOTE\n")
    
    try:
        classifier = UrgencyClassifier()
        
        # Lista de ocorrências para processar em lote
        lote_ocorrencias = [
            "Incêndio em prédio comercial",
            "Acidente de carro com feridos",
            "Roubo em andamento no banco",
            "Pessoa passando mal na rua",
            "Cachorro atacando crianças"
        ]
        
        print("Processando lote de ocorrências...")
        resultados = classifier.classify_batch(lote_ocorrencias)
        
        # Estatísticas do lote
        canais = {}
        urgencias = {}
        
        for resultado in resultados:
            canais[resultado.canal] = canais.get(resultado.canal, 0) + 1
            urgencias[resultado.nivel_urgencia] = urgencias.get(resultado.nivel_urgencia, 0) + 1
        
        print(f"\n📊 ESTATÍSTICAS DO LOTE ({len(resultados)} ocorrências):")
        print("\nDistribuição por canal:")
        for canal, count in canais.items():
            print(f"  {canal}: {count} ocorrência(s)")
        
        print("\nDistribuição por urgência:")
        for nivel, count in sorted(urgencias.items()):
            print(f"  Nível {nivel}: {count} ocorrência(s)")
        
    except Exception as e:
        print(f"❌ Erro no processamento em lote: {e}")

def main():
    """Função principal com menu de exemplos."""
    
    print("Escolha um exemplo para executar:")
    print("1. Exemplo básico")
    print("2. Exemplo com conhecimento personalizado") 
    print("3. Exemplo de processamento em lote")
    print("4. Executar todos os exemplos")
    print("0. Sair")
    
    while True:
        try:
            opcao = input("\nDigite sua opção (0-4): ").strip()
            
            if opcao == "0":
                print("👋 Até logo!")
                break
            elif opcao == "1":
                exemplo_basico()
            elif opcao == "2":
                exemplo_uso_personalizado()
            elif opcao == "3":
                exemplo_lote()
            elif opcao == "4":
                exemplo_basico()
                exemplo_uso_personalizado()
                exemplo_lote()
            else:
                print("❌ Opção inválida. Tente novamente.")
                
        except KeyboardInterrupt:
            print("\n👋 Interrompido pelo usuário. Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main() 