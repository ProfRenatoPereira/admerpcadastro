import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Cria as tabelas iniciais se elas não existirem"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Usuários (Página 1)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            aprovado INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela de Investimentos Imobiliários (Página 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investimentos_imobiliarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turma_nome TEXT NOT NULL,
            valor_terreno REAL NOT NULL,
            valor_instalacoes REAL NOT NULL,
            taxa_selic REAL NOT NULL,
            aluguel_regional REAL NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializa o banco de dados ao rodar o app
if not os.path.exists(DATABASE):
    init_db()

# --- ROTAS DA PÁGINA 1: LOGIN E ADMINISTRAÇÃO ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    senha = request.form['senha']
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE usuario = ? AND senha = ?', (usuario, senha)).fetchone()
    conn.close()
    
    if user:
        if user['aprovado'] == 1 or user['usuario'] == 'admin':
            return redirect(url_for('estrutura'))
        else:
            return "Usuário aguardando aprovação do administrador/professor."
    return "Usuário ou senha incorretos."

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    usuario = request.form['usuario']
    senha = request.form['senha']
    
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (usuario, senha, aprovado) VALUES (?, ?, 0)', (usuario, senha))
        conn.commit()
        conn.close()
        return "Cadastro realizado com sucesso! Aguarde a aprovação do professor."
    except sqlite3.IntegrityError:
        return "Este nome de usuário já existe."

# --- ROTAS DA PÁGINA 2: INVESTIMENTOS IMOBILIÁRIOS (CRUD COMPLETO) ---
@app.route('/estrutura')
def estrutura():
    conn = get_db_connection()
    # Simulando a taxa Selic média de mercado atual (2026) que o Python pode buscar ou fixar
    taxa_atual = 11.39 
    registros = conn.execute('SELECT * FROM investimentos_imobiliarios').fetchall()
    conn.close()
    return render_template('estrutura.html', taxa_atual=taxa_atual, registros=registros)

@app.route('/salvar_estrutura', methods=['POST'])
def salvar_estrutura():
    turma = request.form['turma_nome']
    terreno = float(request.form['valor_terreno'])
    instalacoes = float(request.form['valor_instalacoes'])
    taxa = float(request.form['taxa_selic'])
    aluguel = float(request.form['aluguel_regional'])
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO investimentos_imobiliarios (turma_nome, valor_terreno, valor_instalacoes, taxa_selic, aluguel_regional)
        VALUES (?, ?, ?, ?, ?)
    ''', (turma, terreno, instalacoes, taxa, aluguel))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/alterar_estrutura/<int:id>', methods=['POST'])
def alterar_estrutura(id):
    turma = request.form['turma_nome']
    terreno = float(request.form['valor_terreno'])
    instalacoes = float(request.form['valor_instalacoes'])
    taxa = float(request.form['taxa_selic'])
    aluguel = float(request.form['aluguel_regional'])
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE investimentos_imobiliarios 
        SET turma_nome = ?, valor_terreno = ?, valor_instalacoes = ?, taxa_selic = ?, aluguel_regional = ?
        WHERE id = ?
    ''', (turma, terreno, instalacoes, taxa, aluguel, id))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/deletar_estrutura/<int:id>', methods=['POST'])
def deletar_estrutura(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM investimentos_imobiliarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

if __name__ == '__main__':
    app.run(debug=True)
