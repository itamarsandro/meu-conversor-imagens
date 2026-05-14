FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Criar pastas necessárias
RUN mkdir -p uploads

# Expõe a porta 443 para o Easypanel
EXPOSE 443

# Comando padrão
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9999"]
