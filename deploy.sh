#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# e-Registro Brasil — Script de Deploy na VPS Hostinger
# ─────────────────────────────────────────────────────────────────────────────
set -e

REPO_URL="https://github.com/SEU_USUARIO/eregistro-brasil.git"  # ← ajuste
APP_DIR="/opt/eregistro-brasil"
DOMAIN="eregistrobrasil.com.br"

# ── Cores ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

info()  { echo -e "${GREEN}==> $1${NC}"; }
warn()  { echo -e "${YELLOW}[!] $1${NC}"; }
error() { echo -e "${RED}[ERRO] $1${NC}"; exit 1; }

# ── Detectar versão do Docker Compose ───────────────────────────────────────
if docker compose version &>/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose &>/dev/null; then
  DC="docker-compose"
else
  error "Docker Compose não encontrado. Instale com: apt install docker-compose-plugin -y"
fi
info "Usando: $DC"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   e-Registro Brasil — Deploy VPS Hostinger       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. Pré-requisitos ────────────────────────────────────────────────────────
info "Verificando pré-requisitos..."

command -v docker  &>/dev/null || error "Docker não encontrado. Instale com: curl -fsSL https://get.docker.com | sh"
command -v git     &>/dev/null || error "Git não encontrado. Instale com: apt install git -y"
command -v openssl &>/dev/null || error "OpenSSL não encontrado. Instale com: apt install openssl -y"
command -v nginx   &>/dev/null || error "Nginx não encontrado. Instale com: apt install nginx -y"

# ── 2. Clonar ou atualizar repositório ──────────────────────────────────────
if [ ! -d "$APP_DIR" ]; then
  info "Clonando repositório em $APP_DIR..."
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
else
  cd "$APP_DIR"
  info "Atualizando repositório..."
  DEFAULT_BRANCH=$(git remote show origin | awk '/HEAD branch/ {print $NF}')
  git pull origin "$DEFAULT_BRANCH"
fi

# Re-executa o script com a versão atualizada do disco (evita rodar código antigo pós-pull)
if [ "$1" != "--updated" ]; then
  exec bash "$APP_DIR/deploy.sh" --updated
fi

# ── 3. Arquivo .env ──────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  warn "Arquivo .env não encontrado."
  info "Copiando .env.example para .env..."
  cp .env.example .env
  echo ""
  warn "ATENÇÃO: Edite o arquivo .env antes de continuar!"
  warn "  nano $APP_DIR/.env"
  echo ""
  warn "Variáveis obrigatórias a preencher:"
  warn "  SECRET_KEY, DB_PASSWORD, REDIS_PASSWORD, MP_ACCESS_TOKEN, EMAIL_HOST_*"
  echo ""
  read -rp "Pressione ENTER após editar o .env para continuar..."
fi

# Validar variáveis críticas do .env
source .env 2>/dev/null || true
[ -z "$SECRET_KEY" ]    && error "SECRET_KEY não definida no .env"
[ -z "$DB_PASSWORD" ]   && error "DB_PASSWORD não definida no .env"
[ -z "$REDIS_PASSWORD" ] && error "REDIS_PASSWORD não definida no .env"

# ── 4. Gerar SECRET_KEY se for o valor padrão ────────────────────────────────
if echo "$SECRET_KEY" | grep -q "substitua-por"; then
  info "Gerando SECRET_KEY segura..."
  NEW_KEY=$(openssl rand -base64 50 | tr -d '\n')
  sed -i "s|SECRET_KEY=.*|SECRET_KEY=$NEW_KEY|" .env
  info "SECRET_KEY gerada e salva no .env."
fi

# ── 5. Build das imagens ─────────────────────────────────────────────────────
info "Construindo imagens Docker..."
$DC build

# ── 6. Configurar vhost no nginx do sistema ──────────────────────────────────
VHOST_DEST="/etc/nginx/sites-available/eregistrobrasil.com.br"
VHOST_LINK="/etc/nginx/sites-enabled/eregistrobrasil.com.br"

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  # Certificado ainda não existe: instala vhost HTTP simples para o certbot poder rodar
  info "Instalando vhost HTTP temporário (pré-SSL)..."
  cat > "$VHOST_DEST" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass         http://127.0.0.1:8001;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
    }
}
EOF
else
  # Certificado já existe: instala o vhost completo com HTTPS
  info "Instalando vhost completo (HTTPS)..."
  cp "$APP_DIR/nginx/nginx.conf" "$VHOST_DEST"
fi

if [ ! -L "$VHOST_LINK" ]; then
  ln -s "$VHOST_DEST" "$VHOST_LINK"
fi

nginx -t || error "Configuração do nginx inválida. Verifique $VHOST_DEST"
nginx -s reload
info "Nginx recarregado."

# ── 7. SSL via certbot do sistema ────────────────────────────────────────────
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  info "Obtendo certificado SSL via certbot..."

  if ! command -v certbot &>/dev/null; then
    info "Instalando certbot..."
    apt-get install -y certbot python3-certbot-nginx
  fi

  # Subir os containers para o Django responder no 8001
  info "Subindo containers antes do SSL..."
  $DC up -d

  # Aguarda o container web estar respondendo
  echo "   Aguardando Gunicorn ficar disponível..."
  for i in $(seq 1 30); do
    curl -sf http://127.0.0.1:8001 > /dev/null 2>&1 && break
    sleep 3
  done

  certbot --nginx \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --non-interactive \
    --agree-tos \
    -m "ti@eregistrobrasil.com.br" \
    --redirect

  # Após o certbot, substituir o vhost pelo nosso completo (com cabeçalhos de segurança)
  info "Aplicando vhost definitivo com cabeçalhos de segurança..."
  cp "$APP_DIR/nginx/nginx.conf" "$VHOST_DEST"
  nginx -t && nginx -s reload
else
  info "Certificado SSL já existe. Pulando emissão."
  nginx -s reload
fi

# ── 8. Subir todos os serviços (garante que estão rodando) ───────────────────
info "Iniciando todos os serviços..."
$DC up -d

# ── 9. Status ────────────────────────────────────────────────────────────────
echo ""
info "Status dos containers:"
$DC ps

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Deploy concluído!                              ║${NC}"
echo -e "${GREEN}║   https://$DOMAIN  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo "Comandos úteis:"
echo "  Logs em tempo real : $DC logs -f"
echo "  Reiniciar serviço  : $DC restart web"
echo "  Parar tudo         : $DC down"
echo "  Criar superusuário : $DC exec web python manage.py createsuperuser"
