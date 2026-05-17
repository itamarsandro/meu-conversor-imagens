FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Criar pastas necessárias internamente
RUN mkdir -p uploads

# Expõe a porta 80 para a rede interna do Easypanel
EXPOSE 80

# Comando padrão de inicialização
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
