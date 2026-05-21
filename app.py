import os
import requests
import pandas as pd
from flask import Flask, request, jsonify, send_file
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
# Mantém a permissão para o seu domínio no Hostinger
CORS(app, resources={r"/*": {"origins": "https://portifoliovinicius.com.br"}})

# Pasta para salvar arquivos temporários
TEMP_FOLDER = "static"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Variável de ambiente para o YouTube (Configurar no painel do Railway)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Rota principal
@app.route('/')
def home():
    return "API Flask Rodando com YouTube e Web Scraping!"

# Rota para executar códigos específicos
@app.route('/executar_codigo', methods=['GET'])
def ejecutar_codigo():
    tipo = request.args.get('tipo', '')

    if not tipo:
        return jsonify({"erro": "Tipo de código não informado!"}), 400

    try:
        # Mantive os mesmos termos de "tipo" para não quebrar o seu front-end
        if tipo == "api_spotify":
            arquivo = buscar_videos_youtube()
        elif tipo == "Web_Scrapping_":
            arquivo = fazer_scraping()
        else:
            return jsonify({"erro": "Tipo inválido!"}), 400

        return send_file(arquivo, as_attachment=True)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Nova função que substitui o Spotify consumindo a API do YouTube
def buscar_videos_youtube():
    if not YOUTUBE_API_KEY:
        raise Exception("Chave de API do YouTube (YOUTUBE_API_KEY) não configurada nas variáveis de ambiente.")

    url = 'https://www.googleapis.com/youtube/v3/videos'

    # Categorias de vídeos para popular a planilha de forma analítica
    categorias = {
        'Música': '10',
        'Games': '20',
        'Ciência e Tecnologia': '28',
        'Esportes': '17'
    }
    
    all_video_data = []

    for nome_categoria, id_categoria in categorias.items():
        payload = {
            'part': 'snippet,statistics',
            'chart': 'mostPopular',
            'videoCategoryId': id_categoria,
            'regionCode': 'BR',  # Focado nas tendências do Brasil
            'maxResults': 5,     # Coleta os 5 principais vídeos de cada categoria
            'key': YOUTUBE_API_KEY
        }
        
        response = requests.get(url, params=payload)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            for item in items:
                snippet = item.get('snippet', {})
                statistics = item.get('statistics', {})
                video_id = item.get('id', '')
                
                all_video_data.append({
                    'Categoria': nome_categoria,
                    'Título do Vídeo': snippet.get('title', ''),
                    'Canal': snippet.get('channelTitle', ''),
                    'Visualizações': int(statistics.get('viewCount', 0)),
                    'Likes': int(statistics.get('likeCount', 0)),
                    'Link': f'https://www.youtube.com/watch?v={video_id}'
                })
        else:
            raise Exception(f"Erro na API do YouTube (Status {response.status_code}): {response.text}")

    if all_video_data:
        df = pd.DataFrame(all_video_data)
        # Ordena o relatório por número de visualizações
        df = df.sort_values(by='Visualizações', ascending=False)
        
        # Mantém o mesmo nome de arquivo para o link de download do Hostinger continuar funcionando
        file_path = os.path.join(TEMP_FOLDER, "api_spotify_resultado.xlsx")
        df.to_excel(file_path, index=False, engine="openpyxl")
        
        return file_path
    else:
        raise Exception("Nenhum dado foi retornado pela API do YouTube.")

# Função de web scraping mantida intacta
def fazer_scraping():
    url = "https://www.ibyte.com.br/pcs-e-notebooks/computador"
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        produtos = []

        for produto in soup.find_all(
                "div",
                class_=
                "flex flex-row min-h-full relative w-full overflow-hidden bg-white shadow rounded transition-shadow h-full md:flex-col hover:shadow-md"
        ):
            try:
                nome = produto.find("h2", class_="text-gray-800").text.strip()
                preco = produto.find(
                    "span",
                    class_="text-verde-500 js-best-price").text.strip()
                desconto = produto.find("p",
                                        class_="flex flag js-discount-flag")
                desconto = desconto.text.strip(
                ) if desconto else "Sem desconto importante"

                produtos.append({
                    "Nome": nome,
                    "Preço": preco,
                    "Desconto": desconto
                })
            except AttributeError:
                continue

        df = pd.DataFrame(produtos)
        file_path = os.path.join(TEMP_FOLDER, "Web_Scrapping_resultado.xlsx")
        df.to_excel(file_path, index=False, engine="openpyxl")

        return file_path

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

