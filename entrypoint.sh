#!/bin/sh
# ─────────────────────────────────────────────
# e-Registro Brasil — entrypoint.sh
# ─────────────────────────────────────────────
set -e

# ── Função: aguardar PostgreSQL ──────────────
wait_for_db() {
  echo "==> Aguardando banco de dados..."
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
}

# ── Celery (worker ou beat): aguarda banco e executa ──
if [ "$1" = "celery" ]; then
  wait_for_db
  echo "==> Iniciando Celery: $*"
  exec gosu appuser "$@"
fi

# ── Servidor web: setup completo + Gunicorn ──
wait_for_db

echo "==> Criando migrações pendentes..."
python manage.py makemigrations --noinput

echo "==> Executando migrações..."
python manage.py migrate --noinput

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> Corrigindo permissões dos volumes..."
chown -R appuser:appgroup /app/staticfiles /app/mediafiles

echo "==> Populando estados brasileiros..."
python manage.py seed_states

echo "==> Sincronizando todos os serviços do sistema (idempotente)..."
python manage.py seed_all_services

# Se foram passados argumentos extras (ex: python manage.py migrate),
# executa o comando em vez do Gunicorn.
if [ $# -gt 0 ]; then
  exec gosu appuser "$@"
fi

echo "==> Iniciando servidor Gunicorn..."
exec gosu appuser gunicorn core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
