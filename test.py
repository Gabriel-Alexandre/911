import csv
import requests
import json
import ast
import statistics
from typing import List, Dict, Any, Tuple

# Configuração da API
API_URL = "http://localhost:8001/classify"

def normalize_emergency_types(types_str: str) -> List[str]:
    """
    Normaliza os tipos de emergência de diferentes formatos para uma lista padronizada
    """
    # Remove aspas duplas externas se existirem
    types_str = types_str.strip('"\'')
    
    # Tenta interpretar como lista Python
    try:
        if types_str.startswith('[') and types_str.endswith(']'):
            # É uma lista Python
            result = ast.literal_eval(types_str)
            if isinstance(result, list):
                return [item.strip() for item in result]
        else:
            # É um valor simples ou valores separados por vírgula
            if ',' in types_str:
                return [item.strip() for item in types_str.split(',')]
            else:
                return [types_str.strip()]
    except:
        # Se falhar, tenta separar por vírgula
        if ',' in types_str:
            return [item.strip() for item in types_str.split(',')]
        else:
            return [types_str.strip()]

def normalize_urgency_level(level_str: str) -> int:
    """
    Normaliza o nível de urgência para inteiro
    """
    try:
        return int(level_str.strip())
    except:
        return 0

def load_test_cases(filename: str) -> List[Dict[str, Any]]:
    """
    Carrega os casos de teste do arquivo CSV
    """
    test_cases = []
    
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        
        for row_num, row in enumerate(reader, 1):
            if len(row) >= 3:
                relato = row[0].strip('"\'')
                expected_types = normalize_emergency_types(row[1])
                expected_urgency = normalize_urgency_level(row[2])
                
                test_cases.append({
                    'row_number': row_num,
                    'relato': relato,
                    'expected_types': expected_types,
                    'expected_urgency': expected_urgency
                })
    
    return test_cases

def call_classify_api(relato: str) -> Dict[str, Any]:
    """
    Chama a API de classificação
    """
    try:
        response = requests.post(
            API_URL,
            json={"relato": relato},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Status {response.status_code}: {response.text}",
                "success": False
            }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def compare_emergency_types(actual: List[str], expected: List[str]) -> bool:
    """
    Compara os tipos de emergência (considerando mapeamentos)
    """
    # Normalizar nomes para comparação
    type_mapping = {
        'bombeiro': 'bombeiro',
        'bombeiros': 'bombeiro',
        'samu': 'samu',
        'policia': 'policia',
        'polícia': 'policia'
    }
    
    # Normalizar listas
    actual_normalized = [type_mapping.get(t.lower(), t.lower()) for t in actual]
    expected_normalized = [type_mapping.get(t.lower(), t.lower()) for t in expected]
    
    # Comparar conjuntos (ordem não importa)
    return set(actual_normalized) == set(expected_normalized)

def run_tests():
    """
    Executa todos os testes e gera relatório
    """
    print("🚨 Iniciando validação dos casos de teste...")
    print("=" * 60)
    
    # Carregar casos de teste
    test_cases = load_test_cases('test_cases_classificados.csv')
    print(f"📋 Carregados {len(test_cases)} casos de teste")
    
    # Estatísticas
    total_tests = len(test_cases)
    emergency_correct = 0
    urgency_correct = 0
    both_correct = 0
    api_errors = 0
    
    # Listas para análise detalhada
    emergency_errors = []
    urgency_errors = []
    api_error_details = []
    
    print("\n🔍 Executando testes...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{total_tests}] Testando: {test_case['relato'][:50]}...")
        
        # Chamar API
        result = call_classify_api(test_case['relato'])
        
        # Verificar se houve erro na API
        if result.get('error') or not result.get('emergency_classification'):
            api_errors += 1
            api_error_details.append({
                'row': test_case['row_number'],
                'relato': test_case['relato'],
                'error': result.get('error', 'Resposta inválida da API')
            })
            continue
        
        # Extrair resultados da API
        actual_types = result.get('emergency_classification', [])
        actual_urgency = result.get('nivel_urgencia', 0)
        
        # Comparar tipos de emergência
        emergency_match = compare_emergency_types(actual_types, test_case['expected_types'])
        if emergency_match:
            emergency_correct += 1
        else:
            emergency_errors.append({
                'row': test_case['row_number'],
                'relato': test_case['relato'],
                'expected': test_case['expected_types'],
                'actual': actual_types
            })
        
        # Comparar urgência
        urgency_match = actual_urgency == test_case['expected_urgency']
        if urgency_match:
            urgency_correct += 1
        else:
            urgency_errors.append({
                'row': test_case['row_number'],
                'relato': test_case['relato'],
                'expected': test_case['expected_urgency'],
                'actual': actual_urgency
            })
        
        # Ambos corretos
        if emergency_match and urgency_match:
            both_correct += 1
        
        # Mostrar progresso
        if i % 10 == 0:
            print(f"   Progresso: {i}/{total_tests} ({(i/total_tests)*100:.1f}%)")
    
    # Gerar relatório
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    
    print(f"\n📈 ESTATÍSTICAS GERAIS:")
    print(f"   Total de testes: {total_tests}")
    print(f"   Erros de API: {api_errors}")
    print(f"   Testes válidos: {total_tests - api_errors}")
    
    if total_tests - api_errors > 0:
        valid_tests = total_tests - api_errors
        
        print(f"\n🎯 ACURÁCIA POR CATEGORIA:")
        print(f"   Classificação de Emergência: {emergency_correct}/{valid_tests} ({(emergency_correct/valid_tests)*100:.1f}%)")
        print(f"   Nível de Urgência: {urgency_correct}/{valid_tests} ({(urgency_correct/valid_tests)*100:.1f}%)")
        print(f"   Ambos Corretos: {both_correct}/{valid_tests} ({(both_correct/valid_tests)*100:.1f}%)")
        
        print(f"\n❌ ERROS POR CATEGORIA:")
        print(f"   Erros de Emergência: {len(emergency_errors)}")
        print(f"   Erros de Urgência: {len(urgency_errors)}")
        print(f"   Erros de API: {api_errors}")
    
    # Mostrar alguns exemplos de erros
    if emergency_errors:
        print(f"\n🔍 EXEMPLOS DE ERROS DE CLASSIFICAÇÃO DE EMERGÊNCIA (primeiros 5):")
        for error in emergency_errors[:5]:
            print(f"   Linha {error['row']}: {error['relato'][:40]}...")
            print(f"      Esperado: {error['expected']}")
            print(f"      Obtido: {error['actual']}")
            print()
    
    if urgency_errors:
        print(f"\n🔍 EXEMPLOS DE ERROS DE URGÊNCIA (primeiros 5):")
        for error in urgency_errors[:5]:
            print(f"   Linha {error['row']}: {error['relato'][:40]}...")
            print(f"      Esperado: {error['expected']}")
            print(f"      Obtido: {error['actual']}")
            print()
    
    if api_error_details:
        print(f"\n🔍 EXEMPLOS DE ERROS DE API (primeiros 3):")
        for error in api_error_details[:3]:
            print(f"   Linha {error['row']}: {error['relato'][:40]}...")
            print(f"      Erro: {error['error']}")
            print()
    
    # Salvar relatório detalhado
    save_detailed_report(test_cases, emergency_errors, urgency_errors, api_error_details)
    
    print("=" * 60)
    print("✅ Validação concluída!")
    print("📄 Relatório detalhado salvo em 'test_report.json'")

def save_detailed_report(test_cases, emergency_errors, urgency_errors, api_errors):
    """
    Salva relatório detalhado em JSON
    """
    report = {
        "summary": {
            "total_tests": len(test_cases),
            "emergency_correct": len(test_cases) - len(emergency_errors),
            "urgency_correct": len(test_cases) - len(urgency_errors),
            "api_errors": len(api_errors),
            "emergency_accuracy": ((len(test_cases) - len(emergency_errors) - len(api_errors)) / max(1, len(test_cases) - len(api_errors))) * 100,
            "urgency_accuracy": ((len(test_cases) - len(urgency_errors) - len(api_errors)) / max(1, len(test_cases) - len(api_errors))) * 100
        },
        "emergency_errors": emergency_errors,
        "urgency_errors": urgency_errors,
        "api_errors": api_errors
    }
    
    with open('test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    run_tests()
