# Use a imagem base oficial do Python
FROM python:3.10-slim-bullseye

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar apenas requirements primeiro para cache eficiente
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante da aplicação
COPY . .

# Expor a porta
EXPOSE 8080

# Comando de inicialização
CMD ["gunicorn", "app:app", "--workers", "2", "--bind", "0.0.0.0:8080"]