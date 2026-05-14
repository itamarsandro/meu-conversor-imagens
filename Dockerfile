FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Criar pastas necessárias
RUN mkdir -p uploads
# Comando padrão (será substituído pelo docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
