from flask import Flask, request, redirect, render_template, session, url_for
from flask_session import Session
import random
import string
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'segredo-super-seguro'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

ARQUIVO = "urls.json"
USUARIO = "admin"
SENHA = "1234"

# Carrega os dados salvos
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
            return render_template("login.html", erro="Usuário ou senha inválidos.")
    return render_template("login.html")

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
        "descricao": descricao,
        "cliques": 0,
        "criado_em": datetime.now().isoformat(),
        "acessos": []
    }

    with open(ARQUIVO, "w") as f:
        json.dump(links, f, indent=4)

    return f"""
        <h2>Link encurtado:</h2>
        <p><a href="/{codigo}">http://localhost:5000/{codigo}</a></p>
        <p><strong>Título:</strong> {titulo}</p>
        <p><strong>Descrição:</strong> {descricao}</p>
        <p><strong>Cliques:</strong> 0</p>
        <p><a href="/">Voltar</a> | <a href="/logout">Sair</a></p>
    """

@app.route('/<codigo>')
def redirecionar(codigo):
    info = links.get(codigo)
    if info:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', 'Desconhecido')
        now = datetime.now().isoformat()

        info['cliques'] = info.get('cliques', 0) + 1
        info['ultimo_acesso'] = now
        info.setdefault('acessos', []).append({
            "data": now,
            "ip": ip,
            "user_agent": user_agent
        })

        with open(ARQUIVO, "w") as f:
            json.dump(links, f, indent=4)

        return redirect(info["url"])
    else:
        return "Link não encontrado", 404

@app.route('/admin')
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))

    codigos = list(links.keys())
    cliques = [links[c].get("cliques", 0) for c in codigos]

    return render_template("admin.html", links=links, codigos=codigos, cliques=cliques)

@app.route('/analytics/<codigo>')
def analytics(codigo):
    if not session.get('logado'):
        return redirect(url_for('login'))

    info = links.get(codigo)
    if not info:
        return "Link não encontrado", 404

    acessos = info.get("acessos", [])
    datas = [a["data"] for a in acessos]

    return render_template("analytics.html", codigo=codigo, url=info.get("url", ""), datas=datas)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
