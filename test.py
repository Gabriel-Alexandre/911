import os
from dotenv import load_dotenv
from agentes.rag_service import RAGService

# Carrega variáveis de ambiente se existir arquivo .env
load_dotenv()

def test_database_loading():
    """Teste simples para verificar se o carregamento dos arquivos funciona"""
    
    print("🧪 INICIANDO TESTE DE CARREGAMENTO DE ARQUIVOS")
    print("=" * 50)
    
    try:
        # Inicializa o serviço RAG
        print("1. Inicializando RAGService...")
        rag_service = RAGService()
        print("✅ RAGService inicializado com sucesso!")
        
        # Carrega os arquivos das pastas database
        print("\n2. Carregando arquivos das pastas database...")
        success = rag_service.load_database_files_to_knowledge_base()
        
        if success:
            print("✅ Arquivos carregados com sucesso!")
            
            # Testa algumas buscas com diferentes thresholds
            print("\n3. Testando buscas com diferentes níveis de similaridade...")
            
            # Teste 1: Busca por primeiros socorros
            print("\n🔍 Teste 1: Buscando 'primeiros socorros'")
            for threshold in [0.8, 1.0, 1.2]:  # Ajustar para valores mais altos
                results = rag_service.search_relevant_context("primeiros socorros", top_k=3, score_threshold=threshold)
                print(f"   Threshold {threshold}: {len(results)} resultados")
            
            # Usar threshold mais alto que funciona
            results = rag_service.search_relevant_context("primeiros socorros", top_k=3, score_threshold=1.0)
            if results:
                print(f"📋 Mostrando resultados com threshold 0.3:")
                for i, result in enumerate(results[:2], 1):  # Mostra só 2 para não poluir
                    print(f"   {i}. Categoria: {result['metadata']['category']}")
                    print(f"      Arquivo: {result['metadata']['filename']}")
                    print(f"      Tipo: {result['metadata']['file_type']}")
                    print(f"      Similaridade: {result['similarity_score']:.2f}")
                    print(f"      Conteúdo: {result['content'][:150]}...")
                    print("-" * 40)
            
            # Teste 2: Busca por polícia
            print("\n🔍 Teste 2: Buscando 'polícia'")
            results = rag_service.search_relevant_context("polícia", top_k=2, score_threshold=1.0)
            if results:
                print(f"📋 Encontrados {len(results)} resultados:")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Arquivo: {result['metadata']['filename']}")
                    print(f"      Categoria: {result['metadata']['category']}")
                    print(f"      Similaridade: {result['similarity_score']:.2f}")
                    print("-" * 40)
            
            # Teste 3: Busca por saúde
            print("\n🔍 Teste 3: Buscando 'saúde'")
            results = rag_service.search_relevant_context("saúde", top_k=2, score_threshold=1.2)
            if results:
                print(f"📋 Encontrados {len(results)} resultados:")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Arquivo: {result['metadata']['filename']}")
                    print(f"      Categoria: {result['metadata']['category']}")
                    print(f"      Similaridade: {result['similarity_score']:.2f}")
                    print("-" * 40)
            
            # Teste 4: Busca por termos específicos dos CSVs
            print("\n🔍 Teste 4: Buscando 'médico' (dados CSV)")
            results = rag_service.search_relevant_context("médico", top_k=2, score_threshold=1.2)
            if results:
                print(f"📋 Encontrados {len(results)} resultados:")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Arquivo: {result['metadata']['filename']}")
                    print(f"      Categoria: {result['metadata']['category']}")
                    print(f"      Tipo: {result['metadata']['file_type']}")
                    print(f"      Similaridade: {result['similarity_score']:.2f}")
                    print("-" * 40)
            
            # Estatísticas gerais
            print("\n4. Estatísticas da base de conhecimento:")
            stats = rag_service.get_stats()
            print(f"📊 Total de documentos: {stats.get('total_documents', 'N/A')}")
            print(f"📊 Vector store ativo: {stats.get('vector_store_initialized', 'N/A')}")
            
            # Diagnóstico por categoria
            print("\n5. Diagnóstico por categoria:")
            thresholds = {
                'bombeiros': 1.0,
                'policia': 1.0, 
                'saude': 1.2  # Threshold mais alto para saúde
            }

            for category in ['bombeiros', 'policia', 'saude']:
                threshold = thresholds[category]
                results = rag_service.search_relevant_context(category, top_k=10, score_threshold=threshold)
                files_found = set()
                for result in results:
                    files_found.add(result['metadata']['filename'])  # Remove filtro por categoria
                print(f"   📁 {category.upper()}: {len(files_found)} arquivos únicos indexados (threshold: {threshold})")
            
        else:
            print("❌ Falha no carregamento dos arquivos")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("🎉 TESTE CONCLUÍDO!")
    return True

# Adicionar esta função após a função principal
def debug_search_test():
    """Teste específico para debugging da busca"""
    print("\n🔧 TESTE DE DEBUGGING DA BUSCA")
    print("=" * 50)
    
    try:
        rag_service = RAGService()
        
        # Testa busca sem threshold (aceita tudo)
        print("1. Buscando 'primeiros socorros' sem threshold...")
        results = rag_service.search_relevant_context("primeiros socorros", top_k=5, score_threshold=1.0)
        print(f"   Resultados sem threshold: {len(results)}")
        
        # Testa busca com threshold progressivo
        print("\n2. Testando thresholds progressivos...")
        for threshold in [0.8, 1.0, 1.2, 1.5]:  # Ajustar para valores mais altos
            results = rag_service.search_relevant_context("primeiros socorros", top_k=5, score_threshold=threshold)
            print(f"   Threshold {threshold}: {len(results)} resultados")
        
        # Testa busca simples
        results = rag_service.search_relevant_context("manual", top_k=5, score_threshold=1.6)
        if results:
            print(f"   Encontrados {len(results)} resultados para 'manual'")
            for result in results[:2]:
                print(f"   - Arquivo: {result['metadata']['filename']}")
                print(f"   - Similaridade: {result['similarity_score']:.2f}")
        
        # Testa busca por categoria
        results = rag_service.search_relevant_context("bombeiros", top_k=5, score_threshold=1.0)
        if results:
            print(f"   Encontrados {len(results)} resultados para 'bombeiros'")
    
    except Exception as e:
        print(f"❌ Erro no debugging: {e}")
        import traceback
        traceback.print_exc()

# Modificar a função principal para incluir o debugging
if __name__ == "__main__":
    # Verifica se a chave da OpenAI está configurada
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  ATENÇÃO: Variável OPENAI_API_KEY não encontrada!")
        print("   Configure sua chave da OpenAI no arquivo .env ou como variável de ambiente")
        print("   Exemplo: OPENAI_API_KEY=sua_chave_aqui")
        exit(1)
    
    test_database_loading()
    debug_search_test()
