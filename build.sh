#!/usr/bin/env bash

# Ativa o modo de saída em caso de erro
set -o errexit

# Instala as dependências
pip install -r requirements.txt

# Aplica as migrações
python manage.py migrate

# Coleta os arquivos estáticos
python manage.py collectstatic --noinput
