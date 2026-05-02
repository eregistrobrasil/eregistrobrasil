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

# ── 2. Clonar ou atualizar repositório ──────────────────────────────────────
if [ ! -d "$APP_DIR" ]; then
  info "Clonando repositório em $APP_DIR..."
  git clone "$REPO_URL" "$APP_DIR"
else
  info "Atualizando repositório..."
  DEFAULT_BRANCH=$(git -C "$APP_DIR" remote show origin | awk '/HEAD branch/ {print $NF}')
  git -C "$APP_DIR" pull origin "$DEFAULT_BRANCH"
fi

cd "$APP_DIR"

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

# ── 6. SSL (Let's Encrypt) ───────────────────────────────────────────────────
if [ ! -d "./certbot/conf/live/$DOMAIN" ]; then
  info "Configurando certificado SSL (Let's Encrypt)..."
  bash init-letsencrypt.sh
else
  info "Certificado SSL já existe. Pulando emissão."
fi

# ── 7. Subir todos os serviços ───────────────────────────────────────────────
info "Iniciando todos os serviços..."
$DC up -d

# ── 8. Status ────────────────────────────────────────────────────────────────
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
