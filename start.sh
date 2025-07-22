#!/bin/bash
set -e

echo "🚀 Iniciando aplicação 911..."

# Aguardar o PostgreSQL estar pronto
echo "⏳ Aguardando PostgreSQL..."
until nc -z postgres 5432; do
  echo "PostgreSQL ainda não está pronto. Aguardando..."
  sleep 2
done
echo "✅ PostgreSQL está pronto!"

# Aguardar um pouco mais para garantir que o banco esteja totalmente inicializado
sleep 5

# Executar setup do banco de dados
echo "🔧 Configurando banco de dados..."
if python setup_database.py; then
    echo "✅ Setup do banco concluído com sucesso!"
else
    echo "⚠️ Erro no setup do banco, mas continuando..."
fi

# Iniciar a aplicação
echo "🎯 Iniciando servidor..."
exec python app.py 