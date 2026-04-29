#!/bin/sh
# ─────────────────────────────────────────────
# e-Registro Brasil — entrypoint.sh
# ─────────────────────────────────────────────
set -e

echo "==> Aguardando banco de dados..."
# Aguarda o PostgreSQL ficar disponível
until python -c "
import os, psycopg2
psycopg2.connect(
    dbname=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    host=os.environ['DB_HOST'],
    port=os.environ.get('DB_PORT', '5432'),
)
" 2>/dev/null; do
  echo "   PostgreSQL indisponível — aguardando..."
  sleep 2
done
echo "==> PostgreSQL pronto!"

echo "==> Criando migrações pendentes..."
python manage.py makemigrations --noinput

echo "==> Executando migrações..."
python manage.py migrate --noinput

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> Corrigindo permissões dos volumes..."
chown -R appuser:appgroup /app/staticfiles /app/mediafiles

echo "==> Populando produtos iniciais..."
python manage.py seed_products

echo "==> Iniciando servidor Gunicorn..."
exec gosu appuser gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
