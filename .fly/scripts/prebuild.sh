#!/bin/bash

# Solução principal: ativar compilação local
mise settings set python_compile 1

# Instalar dependências ESSENCIAIS para compilação
sudo apt-get update
sudo apt-get install -y build-essential zlib1g-dev libffi-dev libssl-dev libbz2-dev libreadline-dev libsqlite3-dev
# Configurar cache para compilações futuras
mkdir -p ~/.cache/pip
mkdir -p ~/.cache/mise