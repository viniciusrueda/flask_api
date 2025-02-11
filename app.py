import os
import requests
import pandas as pd
from flask import Flask, request, jsonify, send_file
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://portifoliovinicius.com.br"}})

# Pasta para salvar arquivos temporários
TEMP_FOLDER = "static"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Variáveis de ambiente para autenticação no Spotify
refresh_token = os.getenv("REFRESH_TOKEN")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Função para renovar o token de acesso do Spotify
def refresh_access_token(refresh_token):
    url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id ,
        'client_secret': client_secret
    }
    response = requests.post(url, data=payload)
    data = response.json()

    if 'access_token' in data:
        return data['access_token']
    else:
        print("Erro ao gerar novo token:", data)
        return None

# Rota principal
@app.route('/')
def home():
    return "API Flask Rodando!"

# Rota para executar códigos específicos
@app.route('/executar_codigo', methods=['GET'])
def executar_codigo():
    tipo = request.args.get('tipo', '')

    if not tipo:
        return jsonify({"erro": "Tipo de código não informado!"}), 400

    try:
        if tipo == "api_spotify":
            arquivo = buscar_musicas()
        elif tipo == "Web_Scrapping_":
            arquivo = fazer_scraping()
        else:
            return jsonify({"erro": "Tipo inválido!"}), 400

        return send_file(arquivo, as_attachment=True)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Função para buscar músicas no Spotify
def buscar_musicas():
    access_token = refresh_access_token(refresh_token)
    
    if not access_token:
        return jsonify({"erro": "Falha ao obter token de acesso do Spotify!"}), 500

    genres = ['rock', 'rap', 'pop', 'samba', 'electronic', 'mpb', 'sertanejo']
    all_track_data = []

    for genre in genres:
        url = f'https://api.spotify.com/v1/search?q=genre:{genre}&type=track&limit=1'
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            tracks = data.get('tracks', {}).get('items', [])
            for track in tracks:
                all_track_data.append({
                    'Gênero': genre,
                    'Nome': track['name'],
                    'Popularidade': track['popularity'],
                    'Link': track['external_urls']['spotify']
                })

    df = pd.DataFrame(all_track_data)
    file_path = os.path.join(TEMP_FOLDER, "api_spotify_resultado.xlsx")
    df.to_excel(file_path, index=False, engine="openpyxl")

    return file_path  # Retorna o caminho do arquivo gerado

# Função para fazer web scraping
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

        return file_path  # Retorna o caminho do arquivo gerado

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))  # Usa a variável de ambiente ou padrão 8000
    app.run(host='0.0.0.0', port=port)

