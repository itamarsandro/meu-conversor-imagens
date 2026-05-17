from celery import Celery
from PIL import Image
import os

# Configura a string de conexão de transporte com o serviço Redis da rede isolada
REDIS_URL = os.getenv("REDIS_URL", "redis://fila-redis:6379/0")
app_celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

# Força o uso de apenas 1 tarefa concorrente simultânea para proteção de CPU Core do host
app_celery.conf.worker_concurrency = 1

@app_celery.task
def processar_imagem(caminho_original, formato_saida, largura=None):
    try:
        # Carrega o arquivo gráfico através do volume compartilhado
        img = Image.open(caminho_original)
        
        # === CORREÇÃO DE CORES PARA EXPORTAÇÃO (Evita erro "Mode P" ou Transparência) ===
        formato_normalizado = formato_saida.lower()
        
        # Se o usuário pediu JPEG, precisamos remover qualquer transparência ou paleta (Mode P)
        if formato_normalizado in ['jpeg', 'jpg']:
            if img.mode in ('RGBA', 'P', 'LA'):
                # Primeiro, converte a Paleta (P) para RGBA para podermos isolar a transparência
                if img.mode == 'P':
                    img = img.convert('RGBA')
                
                # Cria uma "tela" em branco puro do mesmo tamanho da imagem
                fundo_branco = Image.new('RGB', img.size, (255, 255, 255))
                
                # Cola a imagem transparente por cima do fundo branco
                if img.mode in ('RGBA', 'LA'):
                    fundo_branco.paste(img, mask=img.split()[-1])
                else:
                    fundo_branco.paste(img)
                
                # A imagem oficial passa a ser essa composição sólida
                img = fundo_branco
            else:
                # Se não for transparente, apenas garante que é RGB puro
                img = img.convert('RGB')
                
        # Se não for JPEG, mas ainda for Modo P (ex: indo para WEBP ou PNG), converte para RGBA seguro
        elif img.mode == 'P':
            img = img.convert('RGBA')
        # ==============================================================================

        # Executa o cálculo de proporção matemática e redimensionamento proporcional se necessário
        if largura:
            # Transforma a largura que veio como string/int em float para o cálculo
            largura_int = int(largura)
            porcentagem = (largura_int / float(img.size[0]))
            altura = int((float(img.size[1]) * float(porcentagem)))
            img = img.resize((largura_int, altura), Image.Resampling.LANCZOS)
        
        # Altera o nome final adicionando o sufixo necessário para download seguro
        caminho_saida = caminho_original.rsplit(".", 1)[0] + f"_final.{formato_saida}"
        
        # Salva aplicando algoritmos de compressão de matriz e otimização de metadados
        img.save(caminho_saida, format=formato_saida.upper(), quality=80, optimize=True)
        
        # Remove IMEDIATAMENTE a imagem temporária original enviada pelo usuário para poupar espaço
        if os.path.exists(caminho_original):
            os.remove(caminho_original)
        
        return {"url_download": f"/uploads/{os.path.basename(caminho_saida)}", "sucesso": True}
    except Exception as e:
        return {"erro": str(e), "sucesso": False}
