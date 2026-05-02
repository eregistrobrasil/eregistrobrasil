#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# e-Registro Brasil — Inicialização do SSL (Let's Encrypt)
# Execute UMA VEZ na primeira implantação para obter os certificados.
# ─────────────────────────────────────────────────────────────────────────────
set -e

DOMAIN="eregistrobrasil.com.br"
DOMAINS="-d eregistrobrasil.com.br -d www.eregistrobrasil.com.br"
EMAIL="ti@eregistrobrasil.com.br"   # ← altere para seu e-mail real
STAGING=0                            # 1 = modo teste (sem limite de requisições)

CERT_PATH="./certbot/conf/live/$DOMAIN"

# ── Verificar se já existem certificados válidos ─────────────────────────────
if [ -d "$CERT_PATH" ] && [ "$(ls -A $CERT_PATH)" ]; then
  echo "==> Certificados já existem em $CERT_PATH. Pulando emissão."
  echo "    Para renovar manualmente: docker compose run --rm certbot renew"
  exit 0
fi

echo "╔══════════════════════════════════════════════════╗"
echo "║   e-Registro Brasil — Configuração SSL/HTTPS     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Domínio : $DOMAIN"
echo "  E-mail  : $EMAIL"
echo ""

# ── Criar diretórios necessários ─────────────────────────────────────────────
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# ── Baixar parâmetros TLS recomendados pelo Certbot ──────────────────────────
if [ ! -f "./certbot/conf/options-ssl-nginx.conf" ]; then
  echo "==> Baixando options-ssl-nginx.conf..."
  curl -sSL \
    https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
    -o ./certbot/conf/options-ssl-nginx.conf
fi

if [ ! -f "./certbot/conf/ssl-dhparams.pem" ]; then
  echo "==> Baixando ssl-dhparams.pem..."
  curl -sSL \
    https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
    -o ./certbot/conf/ssl-dhparams.pem
fi

# ── Criar certificado dummy para que o nginx possa iniciar ───────────────────
echo "==> Criando certificado temporário (dummy)..."
mkdir -p "$CERT_PATH"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout "$CERT_PATH/privkey.pem" \
  -out    "$CERT_PATH/fullchain.pem" \
  -subj   "/CN=localhost" 2>/dev/null
# Certbot também espera chain.pem
cp "$CERT_PATH/fullchain.pem" "$CERT_PATH/chain.pem"

# ── Subir apenas o nginx para o desafio HTTP ─────────────────────────────────
echo "==> Iniciando nginx..."
docker compose up --force-recreate -d nginx
echo "   Aguardando nginx ficar pronto..."
sleep 3

# ── Solicitar certificado real ao Let's Encrypt ──────────────────────────────
STAGING_FLAG=""
if [ "$STAGING" = "1" ]; then
  STAGING_FLAG="--staging"
  echo "==> [MODO TESTE] Usando servidor staging do Let's Encrypt..."
fi

echo "==> Solicitando certificado Let's Encrypt para $DOMAIN..."
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  $STAGING_FLAG \
  $DOMAINS

# ── Recarregar nginx com certificado real ────────────────────────────────────
echo "==> Recarregando nginx com certificado real..."
docker compose exec nginx nginx -s reload

echo ""
echo "✓ SSL configurado com sucesso!"
echo "  Acesse: https://$DOMAIN"
