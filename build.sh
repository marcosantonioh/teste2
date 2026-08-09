#!/usr/bin/env bash
# Sair imediatamente em caso de erro
set -o errexit

# Instala as dependências (incluindo gunicorn e whitenoise)
pip install -r requirements.txt

# 1. Cria as tabelas primeiro (Crucial para evitar o erro de 'relation does not exist')
python manage.py migrate --no-input

# 2. Em bancos novos, inclui os módulos, seções, estações e exercícios iniciais.
# O comando é idempotente e não duplica a estação de demonstração.
python manage.py carregar_conteudo_inicial

# 3. Coleta os arquivos estáticos depois
python manage.py collectstatic --no-input
