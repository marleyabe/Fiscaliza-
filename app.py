from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import sqlite3
import os
import base64
import google.generativeai as genai
import PIL.Image
import random

API_KEY = "AIzaSyANsuWiWwwzu8WPPEgC_6GNAl1MbgIurZM"
genai.configure(api_key=API_KEY)

app = Flask(__name__)
CORS(app)

DATABASE = 'denuncias.db'
UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
@app.route('/feed')
def feed():
    return render_template('feed.html')

@app.route('/add')
def add():
    return render_template('add.html')

@app.route('/mapa')
def map():
    return render_template('mapa.html')

@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Função para criar a tabela no banco de dados
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS denuncias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    descricao TEXT NOT NULL,
                    foto TEXT,
                    tags TEXT,
                    autor TEXT
                )''')
    conn.commit()
    conn.close()

# Inicializa o banco de dados ao iniciar a API
init_db()

# Criar uma nova denúncia
@app.route('/denuncias', methods=['POST'])
def create_denuncia():
    try:
        data = request.get_json()

        # Extrai os campos do JSON
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        tags = data.get('tags', None)
        autor = data.get('autor', None)
        image_data = data.get('image')

        if not latitude or not longitude or not image_data:
            return jsonify({'error': 'Campos latitude, longitude e image são obrigatórios!'}), 400

        # Decodifica a imagem Base64 e salva no servidor
        hash = random.getrandbits(128)
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        foto_filename = f"denuncia_{hash}_{latitude}_{longitude}.png".replace('.', '_')
        foto_path = os.path.join(UPLOAD_FOLDER, foto_filename)
        with open(foto_path, 'wb') as image_file:
            image_file.write(image_bytes)

        # Gera uma descrição automaticamente com o geminAI
        model = genai.GenerativeModel("gemini-1.5-flash")
        img = PIL.Image.open(foto_path)
        prompt = f"Me dê a resposta no seguinte formato, sem adicionar nenhuma palavra: ['Descrição em 2 a 4 palavras sobre a imagem', 'se ela é ou não uma imagem de um problema urbano. responda apenas sim ou não']"
        response = model.generate_content([prompt, img])

        
        response = response.text.replace('[','').replace(']','').replace('\'','').split(',')
        descricao = response[0]
        descricao = descricao.replace('\"','')
        publicar = response[1]

        print(descricao, publicar)

        if publicar.lower() != 'sim':
            os.remove(foto_path)
            return jsonify({'error': 'Imagem não é um problema urbano!'}), 400

        # Salva os dados no banco de dados
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO denuncias (latitude, longitude, descricao, foto, tags, autor) VALUES (?, ?, ?, ?, ?, ?)',
            (latitude, longitude, descricao, foto_filename, tags, autor)
        )
        conn.commit()
        conn.close()

        return jsonify({'message': 'Denúncia criada com sucesso!'}), 201

    except Exception as e:
        # Retorna JSON mesmo em caso de erro
        return jsonify({'error': f'Ocorreu um erro: {str(e)}'}), 500



# Ler todas as denúncias
@app.route('/denuncias', methods=['GET'])
def get_denuncias():
    conn = get_db_connection()
    denuncias = conn.execute('SELECT * FROM denuncias').fetchall()
    conn.close()

    return jsonify([dict(denuncia) for denuncia in denuncias])

# Ler uma denúncia específica por ID
@app.route('/denuncias/<int:id>', methods=['GET'])
def get_denuncia(id):
    conn = get_db_connection()
    denuncia = conn.execute('SELECT * FROM denuncias WHERE id = ?', (id,)).fetchone()
    conn.close()

    if denuncia is None:
        return jsonify({'error': 'Denúncia não encontrada!'}), 404

    return jsonify(dict(denuncia))

# Atualizar uma denúncia por ID
@app.route('/denuncias/<int:id>', methods=['PUT'])
def update_denuncia(id):
    conn = get_db_connection()
    denuncia = conn.execute('SELECT * FROM denuncias WHERE id = ?', (id,)).fetchone()
    if denuncia is None:
        conn.close()
        return jsonify({'error': 'Denúncia não encontrada!'}), 404

    # Verifica o Content-Type da requisição
    if 'multipart/form-data' in request.content_type:
        # Lida com multipart/form-data
        latitude = request.form.get('latitude', denuncia['latitude'])
        longitude = request.form.get('longitude', denuncia['longitude'])
        descricao = request.form.get('descricao', denuncia['descricao'])
        tags = request.form.get('tags', denuncia['tags'])
        autor = request.form.get('autor', denuncia['autor'])

        # Lida com o arquivo da imagem
        foto = request.files.get('foto')
        foto_path = denuncia['foto']  # Mantém a foto existente se nenhuma nova for enviada
        if foto:
            foto_path = os.path.join(UPLOAD_FOLDER, foto.filename)
            foto.save(foto_path)
    else:
        # Lida com application/json
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON não fornecidos ou mal formatados'}), 400

        latitude = data.get('latitude', denuncia['latitude'])
        longitude = data.get('longitude', denuncia['longitude'])
        descricao = data.get('descricao', denuncia['descricao'])
        tags = data.get('tags', denuncia['tags'])
        autor = data.get('autor', denuncia['autor'])
        foto_path = data.get('foto', denuncia['foto'])  # Mantém a foto existente se nenhuma nova for enviada

    # Atualiza o banco de dados
    conn.execute(
        'UPDATE denuncias SET latitude = ?, longitude = ?, descricao = ?, foto = ?, tags = ?, autor = ? WHERE id = ?',
        (latitude, longitude, descricao, foto_path, tags, autor, id)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Denúncia atualizada com sucesso!'})


# Excluir uma denúncia por ID
@app.route('/denuncias/<int:id>', methods=['DELETE'])
def delete_denuncia(id):
    conn = get_db_connection()
    denuncia = conn.execute('SELECT * FROM denuncias WHERE id = ?', (id,)).fetchone()
    if denuncia is None:
        conn.close()
        return jsonify({'error': 'Denúncia não encontrada!'}), 404

    conn.execute('DELETE FROM denuncias WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Denúncia excluída com sucesso!'})

if __name__ == '__main__':
    app.run(debug=True)
