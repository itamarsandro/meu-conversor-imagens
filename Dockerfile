FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Garante a existência da pasta de uploads no contexto interno
RUN mkdir -p uploads

# Expõe a porta de comunicação interna para o proxy reverso do Easypanel
EXPOSE 80

# Comando para inicialização do Uvicorn em escuta de porta padrão HTTP
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
