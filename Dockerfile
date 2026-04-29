# ─────────────────────────────────────────────
# e-Registro Brasil — Dockerfile (Django)
# ─────────────────────────────────────────────
FROM python:3.12-slim

# Variáveis de ambiente para evitar arquivos .pyc e buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar o código-fonte
COPY . .

# Copiar e tornar executável o entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Usuário não-root para o Gunicorn
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN mkdir -p /app/staticfiles /app/mediafiles && chown -R appuser:appgroup /app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
