from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from worker import processar_imagem
from celery.result import AsyncResult
import uuid
import os

app = FastAPI(title="Fábrica de Imagens")

# Pasta para salvar os arquivos temporários e processados
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Permitir que as imagens processadas sejam baixadas pelo navegador
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/", response_class=HTMLResponse)
async def pagina_inicial():
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fábrica de Imagens - Otimizador Automático</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 font-sans min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-slate-800 p-8 rounded-2xl shadow-2xl border border-slate-700">
            <h1 class="text-3xl font-bold text-center mb-2 bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">Fábrica de Imagens</h1>
            <p class="text-slate-400 text-center text-sm mb-8">Converta e redimensione suas imagens instantaneamente usando filas assíncronas.</p>
            
            <form id="uploadForm" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2">Selecione a Imagem</label>
                    <input type="file" id="arquivo" name="arquivo" required class="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-emerald-500 file:text-slate-900 hover:file:bg-emerald-400 cursor-pointer bg-slate-900 p-3 rounded-xl border border-slate-700">
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">Formato de Saída</label>
                        <select id="formato" name="formato" class="w-full bg-slate-900 p-3 rounded-xl border border-slate-700 text-slate-200 focus:outline-none focus:border-emerald-500">
                            <option value="webp">WEBP (Recomendado)</option>
                            <option value="png">PNG</option>
                            <option value="jpeg">JPEG</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Largura (Opcional)</label>
                        <input type="number" id="largura" name="largura" placeholder="Ex: 800" class="w-full bg-slate-900 p-3 rounded-xl border border-slate-700 text-slate-200 focus:outline-none focus:border-emerald-500">
                    </div>
                </div>
                
                <button type="submit" class="w-full bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-900 font-bold py-3 px-4 rounded-xl hover:from-emerald-400 hover:to-teal-500 transition duration-200 shadow-lg cursor-pointer">
                    Processar Imagem
                </button>
            </form>
            
            <div id="statusContainer" class="hidden mt-8 p-4 bg-slate-900 rounded-xl border border-slate-700 text-center space-y-4">
                <div id="spinner" class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-500 border-t-transparent"></div>
                <p id="statusTexto" class="text-sm font-medium text-emerald-400">Enviando arquivo...</p>
                <div id="downloadContainer" class="hidden">
                    <a id="downloadLink" href="#" target="_blank" class="inline-block w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-xl transition duration-200 shadow-lg text-center">
                        Baixar Imagem Convertida
                    </a>
                </div>
            </div>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const form = document.getElementById('uploadForm');
                const statusContainer = document.getElementById('statusContainer');
                const statusTexto = document.getElementById('statusTexto');
                const spinner = document.getElementById('spinner');
                const downloadContainer = document.getElementById('downloadContainer');
                const downloadLink = document.getElementById('downloadLink');
                
                // Exibe o painel de status
                statusContainer.classList.remove('hidden');
                downloadContainer.classList.add('hidden');
                spinner.classList.remove('hidden');
                statusTexto.innerText = "Enviando imagem para o servidor...";
                
                const formData = new FormData();
                formData.append('arquivo', document.getElementById('arquivo').files[0]);
                formData.append('formato', document.getElementById('formato').value);
                
                const larguraVal = document.getElementById('largura').value;
                if(larguraVal) {
                    formData.append('largura', larguraVal);
                }
                
                try {
                    // 1. Envia a imagem para a API
                    const resposta = await fetch('/upload', { method: 'POST', body: formData });
                    const dados = await resposta.json();
                    
                    if (!dados.id_tarefa) {
                        throw new Error("Falha ao iniciar tarefa");
                    }
                    
                    const idTarefa = dados.id_tarefa;
                    statusTexto.innerText = "Imagem na fila. Processando...";
                    
                    // 2. Inicia a checagem automática (Polling) em segundo plano
                    const intervalo = setInterval(async () => {
                        const checarStatus = await fetch(`/status/${idTarefa}`);
                        const statusDados = await checarStatus.json();
                        
                        if (statusDados.status === "Concluído") {
                            clearInterval(intervalo);
                            spinner.classList.add('hidden');
                            
                            if (statusDados.resultado.sucesso) {
                                statusTexto.innerText = "Sucesso! Sua imagem está pronta.";
                                downloadLink.href = statusDados.resultado.url_download;
                                downloadContainer.classList.remove('hidden');
                            } else {
                                statusTexto.innerText = "Erro no processamento: " + statusDados.resultado.erro;
                            }
                        }
                    }, 1500); // Checa a cada 1.5 segundos
                    
                } catch (erro) {
                    spinner.classList.add('hidden');
                    statusTexto.innerText = "Ocorreu um erro: " + erro.message;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

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
