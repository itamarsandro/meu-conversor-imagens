from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from worker import processar_imagem
from celery.result import AsyncResult
import uuid
import os

app = FastAPI(title="Fábrica de Imagens")

# Pasta para salvar os arquivos temporários
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# NECESSÁRIO: Permitir que as imagens processadas sejam baixadas pelo navegador
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/upload")
async def upload_imagem(
    arquivo: UploadFile = File(...), 
    formato: str = Form("webp"), 
    largura: int = Form(None)
):
    # Gera um nome único para o arquivo
    ext = arquivo.filename.split(".")[-1]
    id_unico = str(uuid.uuid4())
    caminho_entrada = os.path.join(UPLOAD_DIR, f"{id_unico}.{ext}")
    
    # Salva o arquivo enviado no disco
    with open(caminho_entrada, "wb") as buffer:
        buffer.write(await arquivo.read())
    
    # Envia para a fila do Celery (Worker)
    tarefa = processar_imagem.delay(caminho_entrada, formato, largura)
    
    return {"id_tarefa": tarefa.id, "status": "Processando"}

@app.get("/status/{tarefa_id}")
async def ver_status(tarefa_id: str):
    resultado = AsyncResult(tarefa_id)
    if resultado.ready():
        return {"status": "Concluído", "resultado": resultado.result}
    return {"status": "Processando..."}
