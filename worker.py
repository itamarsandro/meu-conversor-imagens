from celery import Celery
from PIL import Image
import os

# Configura a conexão com o Redis (Fila)
REDIS_URL = os.getenv("REDIS_URL", "redis://fila-redis:6379/0")
app_celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# Força o uso de apenas 1 tarefa por vez para não sobrecarregar seu servidor
app_celery.conf.worker_concurrency = 1

@app_celery.task
def processar_imagem(caminho_original, formato_saida, largura=None):
    try:
        # Abre a imagem da pasta compartilhada
        img = Image.open(caminho_original)
        
        # Redimensiona mantendo a proporção se a largura foi informada
        if largura:
            porcentagem = (largura / float(img.size[0]))
            altura = int((float(img.size[1]) * float(porcentagem)))
            img = img.resize((largura, altura), Image.Resampling.LANCZOS)
        
        # Define o nome do arquivo de saída
        caminho_saida = caminho_original.rsplit(".", 1)[0] + f"_final.{formato_saida}"
        
        # Salva no novo formato aplicando compressão e otimização de matriz
        img.save(caminho_saida, format=formato_saida.upper(), quality=80, optimize=True)
        
        # Remove o arquivo original enviado para liberar espaço em disco
        os.remove(caminho_original)
        
        return {"url_download": f"/{caminho_saida}", "sucesso": True}
    except Exception as e:
        return {"erro": str(e), "sucesso": False}
