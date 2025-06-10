from flask import Flask, request, redirect, render_template, session, url_for
from flask_session import Session
import random
import string
import json
import os

app = Flask(__name__)
app.secret_key = 'segredo-super-seguro'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

ARQUIVO = "urls.json"
USUARIO = "admin"
SENHA = "1234"

# Carrega links salvos
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r") as f:
        links = json.load(f)
else:
    links = {}

def gerar_codigo():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

@app.route('/')
def index():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario == USUARIO and senha == SENHA:
            session['logado'] = True
            return redirect(url_for('index'))
        else:
            return '''
                <p>Usuário ou senha inválidos.</p>
                <a href="/login">Tentar novamente</a>
            '''
    return '''
        <h2>Login</h2>
        <form method="post" action="/login">
            <input type="text" name="usuario" placeholder="Usuário" required><br><br>
            <input type="password" name="senha" placeholder="Senha" required><br><br>
            <button type="submit">Entrar</button>
        </form>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/encurtar', methods=['POST'])
def encurtar():
    if not session.get('logado'):
        return redirect(url_for('login'))

    url_original = request.form['url']
    titulo = request.form.get('titulo', '')
    descricao = request.form.get('descricao', '')
    codigo = gerar_codigo()

    links[codigo] = {
        "url": url_original,
        "titulo": titulo,
        "descricao": descricao
    }

    with open(ARQUIVO, "w") as f:
        json.dump(links, f, indent=4)

    return f"""
        <h2>Link encurtado:</h2>
        <p><a href="/{codigo}">http://localhost:5000/{codigo}</a></p>
        <p><strong>Título:</strong> {titulo}</p>
        <p><strong>Descrição:</strong> {descricao}</p>
        <p><a href="/">Voltar</a> | <a href="/logout">Sair</a></p>
    """

@app.route('/<codigo>')
def redirecionar(codigo):
    info = links.get(codigo)
    if info:
        return redirect(info["url"])
    else:
        return "Link não encontrado", 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)