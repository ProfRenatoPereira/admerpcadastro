import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'

DATABASE = 'database.db'
    # Tabela de Máquinas e Equipamentos (Página 3)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_equipamento TEXT NOT NULL,
            potencia REAL NOT NULL,
            consumo_eletrico REAL NOT NULL,
            velocidade TEXT,
            avanco TEXT,
            comprimento_max REAL,
            diametro_max REAL,
            frequencia_manutencao INTEGER NOT NULL, -- em horas
            horas_trabalhadas INTEGER DEFAULT 0,
            preco_compra REAL NOT NULL,
            depreciacao_mensal REAL NOT NULL,
            valor_venda_final REAL NOT NULL,
            custo_minuto_maquina REAL NOT NULL
        )
    ''')
    # Tabela de Materiais e Insumos (Página 4)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_material TEXT UNIQUE NOT NULL,
            nome_material TEXT NOT NULL,
            preco_unidade REAL NOT NULL,
            dimensoes TEXT,
            volume_disponivel REAL NOT NULL
        )
    ''')


    # Tabela Principal do Produto (Página 5)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_produto TEXT UNIQUE NOT NULL,
            nome_produto TEXT NOT NULL,
            custo_total_fabricacao REAL DEFAULT 0
        )
    ''')

    # Tabela União/Roteiro: Vincula Máquinas e Materiais ao Produto (Página 5)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estrutura_produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            maquina_id INTEGER,
            material_id INTEGER,
            tempo_processo_min REAL DEFAULT 0,
            quantidade_material REAL DEFAULT 0,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    ''')

    # Tabela de Formação de Preços e Impostos (Página 6)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formacao_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER UNIQUE NOT NULL,
            imposto_municipal REAL DEFAULT 0,
            imposto_estadual REAL DEFAULT 0,
            imposto_federal REAL DEFAULT 0,
            margem_lucro REAL DEFAULT 0,
            preco_venda_final REAL DEFAULT 0,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    ''')




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


# --- ROTAS DA PÁGINA 3: MAQUINÁRIOS E EQUIPAMENTOS ---
@app.route('/maquinas')
def maquinas():
    conn = get_db_connection()
    maquinas = conn.execute('SELECT * FROM maquinas').fetchall()
    
    # Busca o último aluguel diluído salvo para usar no cálculo do minuto máquina estrutural
    # Se não houver registro, assume 0 como fallback pedagógico
    ultimo_imovel = conn.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    aluguel_base = ultimo_imovel['aluguel_regional'] if ultimo_imovel else 0
    minutos_no_mes = 176 * 60
    custo_minuto_estrutural = aluguel_base / minutos_no_mes if aluguel_base > 0 else 0
    
    return render_template('maquinas.html', maquinas=maquinas, custo_minuto_estrutural=custo_minuto_estrutural)

@app.route('/salvar_maquina', methods=['POST'])
def salvar_maquina():
    nome = request.form['nome_equipamento']
    potencia = float(request.form['potencia'])
    consumo = float(request.form['consumo_eletrico'])
    velocidade = request.form['velocidade']
    avanco = request.form['avanco']
    comp_max = float(request.form['comprimento_max'] or 0)
    diam_max = float(request.form['diametro_max'] or 0)
    manutencao = int(request.form['frequencia_manutencao'])
    horas_trab = int(request.form['horas_trabalhadas'] or 0)
    preco = float(request.form['preco_compra'])
    depreciacao = float(request.form['depreciacao_mensal'])
    venda = float(request.form['valor_venda_final'])
    c_mm = float(request.form['custo_minuto_maquina'])
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, 
                             comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas,
                             preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, potencia, consumo, velocidade, avanco, comp_max, diam_max, manutencao, horas_trab, preco, depreciacao, venda, c_mm))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/alterar_maquina/<int:id>', methods=['POST'])
def alterar_maquina(id):
    nome = request.form['nome_equipamento']
    potencia = float(request.form['potencia'])
    consumo = float(request.form['consumo_eletrico'])
    velocidade = request.form['velocidade']
    avanco = request.form['avanco']
    comp_max = float(request.form['comprimento_max'] or 0)
    diam_max = float(request.form['diametro_max'] or 0)
    manutencao = int(request.form['frequencia_manutencao'])
    horas_trab = int(request.form['horas_trabalhadas'] or 0)
    preco = float(request.form['preco_compra'])
    depreciacao = float(request.form['depreciacao_mensal'])
    venda = float(request.form['valor_venda_final'])
    c_mm = float(request.form['custo_minuto_maquina'])
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE maquinas SET nome_equipamento=?, potencia=?, consumo_eletrico=?, velocidade=?, avanco=?, 
                            comprimento_max=?, diametro_max=?, frequencia_manutencao=?, horas_trabalhadas=?,
                            preco_compra=?, depreciacao_mensal=?, valor_venda_final=?, custo_minuto_maquina=?
        WHERE id=?
    ''', (nome, potencia, consumo, velocidade, avanco, comp_max, diam_max, manutencao, horas_trab, preco, depreciacao, venda, c_mm, id))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/deletar_maquina/<int:id>', methods=['POST'])
def deletar_maquina(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM maquinas WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))


# --- ROTAS DA PÁGINA 4: CADASTRO DE MATERIAIS E INSUMOS ---
@app.route('/materiais')
def materiais():
    conn = get_db_connection()
    materiais = conn.execute('SELECT * FROM materiais').fetchall()
    conn.close()
    return render_template('materiais.html', materiais=materiais)

@app.route('/salvar_material', methods=['POST'])
def salvar_material():
    codigo = request.form['codigo_material']
    nome = request.form['nome_material']
    preco = float(request.form['preco_unidade'])
    dimensoes = request.form['dimensoes']
    volume = float(request.form['volume_disponivel'])
    
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel)
            VALUES (?, ?, ?, ?, ?)
        ''', (codigo, nome, preco, dimensoes, volume))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return "Erro: Já existe um material cadastrado com este código."
    return redirect(url_for('materiais'))


@app.route('/alterar_material/<int:id>', methods=['POST'])
def alterar_material(id):
    codigo = request.form['codigo_material']
    nome = request.form['nome_material']
    preco = float(request.form['preco_unidade'])
    dimensoes = request.form['dimensoes']
    volume = float(request.form['volume_disponivel'])
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE materiais 
        SET codigo_material=?, nome_material=?, preco_unidade=?, dimensoes=?, volume_disponivel=?
        WHERE id=?
    ''', (codigo, nome, preco, dimensoes, volume, id))
    conn.commit()
    conn.close()
    return redirect(url_for('materiais'))

@app.route('/deletar_material/<int:id>', methods=['POST'])
def deletar_material(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM materiais WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('materiais'))
# --- ROTAS DA PÁGINA 5: ENGENHARIA DE PRODUTO ---
@app.route('/engenharia')
def engenharia():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    maquinas = conn.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas').fetchall()
    materiais = conn.execute('SELECT id, nome_material, preco_unidade FROM materiais').fetchall()
    
    # Busca a árvore completa de composições detalhadas para exibir na tabela
    composicoes = conn.execute('''
        SELECT ep.*, p.nome_produto, p.codigo_produto, m.nome_equipamento, mat.nome_material 
        FROM estrutura_produto ep
        JOIN produtos p ON ep.produto_id = p.id
        LEFT JOIN maquinas m ON ep.maquina_id = m.id
        LEFT JOIN materiais mat ON ep.material_id = mat.id
    ''').fetchall()
    conn.close()
    
    return render_template('engenharia.html', produtos=produtos, maquinas=maquinas, materiais=materiais, composicoes=composicoes)

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    codigo = request.form['codigo_produto']
    nome = request.form['nome_produto']
    
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO produtos (codigo_produto, nome_produto) VALUES (?, ?)', (codigo, nome))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return "Erro: Código de produto já cadastrado."
    return redirect(url_for('engenharia'))
@app.route('/vincular_estrutura', methods=['POST'])
def vincular_estrutura():
    prod_id = int(request.form['produto_id'])
    maq_id = request.form['maquina_id'] or None
    mat_id = request.form['material_id'] or None
    tempo = float(request.form['tempo_processo_min'] or 0)
    qtd_mat = float(request.form['quantidade_material'] or 0)
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material)
        VALUES (?, ?, ?, ?, ?)
    ''', (prod_id, maq_id, mat_id, tempo, qtd_mat))
    conn.commit()
    conn.close()
    return redirect(url_for('engenharia'))

@app.route('/deletar_item_estrutura/<int:id>', methods=['POST'])
def deletar_item_estrutura(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM estrutura_produto WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('engenharia'))
# --- ROTAS DA PÁGINA 6: FORMAÇÃO DE PREÇOS ---
@app.route('/precificacao')
def precificacao():
    conn = get_db_connection()
    # Puxa produtos e calcula o custo total acumulado de cada um (máquina + material)
    produtos = conn.execute('''
        SELECT p.id, p.codigo_produto, p.nome_produto,
               COALESCE(SUM(ep.tempo_processo_min * mq.custo_minuto_maquina), 0) +
               COALESCE(SUM(ep.quantidade_material * mt.preco_unidade), 0) AS custo_fabricacao
        FROM produtos p
        LEFT JOIN estrutura_produto ep ON p.id = ep.produto_id
        LEFT JOIN maquinas mq ON ep.maquina_id = mq.id
        LEFT JOIN materiais mt ON ep.material_id = mt.id
        GROUP BY p.id
    ''').fetchall()
    
    precos_salvos = conn.execute('''
        SELECT fp.*, p.codigo_produto, p.nome_produto 
        FROM formacao_precos fp
        JOIN produtos p ON fp.produto_id = p.id
    ''').fetchall()
    conn.close()
    
    return render_template('precificacao.html', produtos=produtos, precos_salvos=precos_salvos)

@app.route('/salvar_preco', methods=['POST'])
def salvar_preco():
    prod_id = int(request.form['produto_id'])
    municipal = float(request.form['imposto_municipal'] or 0)
    estadual = float(request.form['imposto_estadual'] or 0)
    federal = float(request.form['imposto_federal'] or 0)
    margem = float(request.form['margem_lucro'] or 0)
    preco_final = float(request.form['preco_venda_final'] or 0)
    
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO formacao_precos 
        (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (prod_id, municipal, estadual, federal, margem, preco_final))
    conn.commit()
    conn.close()
    return redirect(url_for('precificacao'))
@app.route('/deletar_preco/<int:id>', methods=['POST'])
def deletar_preco(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM formacao_precos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('precificacao'))
