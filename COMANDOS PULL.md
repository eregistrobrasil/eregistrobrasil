comandos quando troca apenas html e imagens


# Link SSH
ssh root@72.60.144.18
vetorialcontabilidade.com.br

# 1. Primeiro, vamos fazer o deploy das alterações nos templates
cd /root/contabilidade
git pull origin master

# 2. Copiar os arquivos de media do container para o host (se existirem no container)
docker cp vetorial_web:/app/media/. /root/contabilidade/media/

# 3. Ajustar permissões
chmod -R 755 /root/contabilidade/media/

# 4. Verificar se os arquivos foram copiados
ls -la /root/contabilidade/media/

# 5. Reiniciar o container web
docker-compose -f docker-compose.prod.yml restart web

# 6. Verificar se há imagens no container
docker-compose -f docker-compose.prod.yml exec web ls -la /app/media/

# 2. Coletar arquivos estáticos no container
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 3. Copiar os arquivos estáticos do container para o host (onde o Nginx serve)
docker cp vetorial_web:/app/staticfiles/. /root/contabilidade/staticfiles/

# 4. Ajustar permissões
chmod -R 755 /root/contabilidade/staticfiles/

# 5. Verificar se o logo.png foi copiado
ls -la /root/contabilidade/staticfiles/img/logo.png

# 6. Se necessário, reiniciar o Nginx
nginx -t && systemctl reload nginx



COMANDOS PARA FAZER O PULL COMPLETO

# 1. Fazer pull das alterações (se ainda não fez)
cd /root/vetorial
git pull origin master

# 2. Reconstruir a imagem com as novas dependências (mercadopago SDK)
docker-compose -f docker-compose.prod.yml build web

# 3. Aplicar as migrações do banco de dados
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 4. Coletar arquivos estáticos (templates novos)
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 5. Reiniciar os containers (web, celery_worker e celery_beat)
docker-compose -f docker-compose.prod.yml restart web
docker-compose -f docker-compose.prod.yml restart celery_worker
docker-compose -f docker-compose.prod.yml restart celery_beat

# 6. Verificar se está rodando
docker-compose -f docker-compose.prod.yml ps

# 7. Verificar logs (opcional)
docker-compose -f docker-compose.prod.yml logs --tail 50 web


# 8. Reconstruir a imagem 
docker-compose -f docker-compose.prod.yml build --no-cache

# Apagar containers orfãos
docker-compose -f docker-compose.prod.yml down --remove-orphans

# verificar se cairam
docker ps -a

# subir forçado
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate 

# 9. Subir os containers
docker-compose -f docker-compose.prod.yml up -d


docker cp ab45c8cf4c49_vetorial_web:/app/staticfiles/. /root/contabilidade/staticfiles/
docker cp ab45c8cf4c49_vetorial_web:/app/media/. /root/contabilidade/media/
chmod -R 755 /root/contabilidade/staticfiles/
chmod -R 755 /root/contabilidade/media/