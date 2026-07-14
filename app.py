import os
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'

# Caminho para o banco de dados SQLite
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
            frequencia_manutencao INTEGER NOT NULL,
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

    # Tabela União/Roteiro (Página 5)
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

    # Tabela de Formação de Preços (Página 6)
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

    # Tabela de Estoque (Página 8)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque_produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER UNIQUE NOT NULL,
            quantidade_disponivel REAL DEFAULT 0,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    ''')

    # Tabela de Pedidos de Vendas (Página 7)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos_vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            desconto_percentual REAL DEFAULT 0,
            observacoes TEXT,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    ''')

    # Tabela do PCP (Página 9)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordens_processo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            numero_operacao TEXT NOT NULL,
            maquina_nome TEXT NOT NULL,
            codigo_produto TEXT NOT NULL,
            nome_produto TEXT NOT NULL,
            data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tempo_estimado_min REAL NOT NULL,
            data_saida TEXT DEFAULT 'Aguardando',
            operador_nome TEXT DEFAULT 'Pendente',
            status TEXT DEFAULT 'Na Fila',
            FOREIGN KEY(pedido_id) REFERENCES pedidos_vendas(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Executa a criação do banco de dados se ele não existir
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
        return "Usuário aguardando aprovação do administrador/professor."
    return "Usuário ou senha incorretos."

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    usuario = request.form['usuario']
    senha = request.form['senha']
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (usuario, presidential, aprovado) VALUES (?, ?, 0)', (usuario, senha))
        conn.commit()
        conn.close()
        return "Cadastro realizado com sucesso! Aguarde a aprovação do professor."
    except sqlite3.IntegrityError:
        return "Este nome de usuário já existe."

# --- ROTAS DA PÁGINA 2: INVESTIMENTOS IMOBILIÁRIOS ---
@app.route('/estrutura')
def estrutura():
    conn = get_db_connection()
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
# --- ROTAS DA PÁGINA 3: MAQUINÁRIOS ---
@app.route('/maquinas')
def maquinas():
    conn = get_db_connection()
    maquinas_dados = conn.execute('SELECT * FROM maquinas').fetchall()
    ultimo_imovel = conn.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    aluguel_base = ultimo_imovel['aluguel_regional'] if ultimo_imovel else 0
    custo_minuto_estrutural = aluguel_base / (176 * 60) if aluguel_base > 0 else 0
    return render_template('maquinas.html', maquinas=maquinas_dados, custo_minuto_estrutural=custo_minuto_estrutural)

@app.route('/salvar_maquina', methods=['POST'])
def salvar_maquina():
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (request.form['nome_equipamento'], float(request.form['potencia']), float(request.form['consumo_eletrico']), request.form['velocidade'], request.form['avanco'], float(request.form['comprimento_max'] or 0), float(request.form['diametro_max'] or 0), int(request.form['frequencia_manutencao']), int(request.form['horas_trabalhadas'] or 0), float(request.form['preco_compra']), float(request.form['depreciacao_mensal']), float(request.form['valor_venda_final']), float(request.form['custo_minuto_maquina'])))
    conn.commit(); conn.close()
    return redirect(url_for('maquinas'))

@app.route('/alterar_maquina/<int:id>', methods=['POST'])
def alterar_maquina(id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE maquinas SET nome_equipamento=?, potencia=?, consumo_eletrico=?, velocidade=?, avanco=?, comprimento_max=?, diametro_max=?, frequencia_manutencao=?, horas_trabalhadas=?, preco_compra=?, depreciacao_mensal=?, valor_venda_final=?, custo_minuto_maquina=? WHERE id=?
    ''', (request.form['nome_equipamento'], float(request.form['potencia']), float(request.form['consumo_eletrico']), request.form['velocidade'], request.form['avanco'], float(request.form['comprimento_max'] or 0), float(request.form['diametro_max'] or 0), int(request.form['frequencia_manutencao']), int(request.form['horas_trabalhadas'] or 0), float(request.form['preco_compra']), float(request.form['depreciacao_mensal']), float(request.form['valor_venda_final']), float(request.form['custo_minuto_maquina']), id))
    conn.commit(); conn.close()
    return redirect(url_for('maquinas'))

@app.route('/deletar_maquina/<int:id>', methods=['POST'])
def deletar_maquina(id):
    conn = get_db_connection(); conn.execute('DELETE FROM maquinas WHERE id=?', (id,)); conn.commit(); conn.close()
    return redirect(url_for('maquinas'))

# --- ROTAS DA PÁGINA 4: MATERIAIS ---
@app.route('/materiais')
def materiais():
    conn = get_db_connection(); mats = conn.execute('SELECT * FROM materiais').fetchall(); conn.close()
    return render_template('materiais.html', materiais=mats)

@app.route('/salvar_material', methods=['POST'])
def salvar_material():
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (?, ?, ?, ?, ?)', (request.form['codigo_material'], request.form['nome_material'], float(request.form['preco_unidade']), request.form['dimensoes'], float(request.form['volume_disponivel'])))
        conn.commit(); conn.close()
    except sqlite3.IntegrityError: return "Erro: Código duplicado."
    return redirect(url_for('materiais'))

@app.route('/alterar_material/<int:id>', methods=['POST'])
def alterar_material(id):
    conn = get_db_connection()
    conn.execute('UPDATE materiais SET codigo_material=?, nome_material=?, preco_unidade=?, dimensoes=?, volume_disponivel=? WHERE id=?', (request.form['codigo_material'], request.form['nome_material'], float(request.form['preco_unidade']), request.form['dimensoes'], float(request.form['volume_disponivel']), id))
    conn.commit(); conn.close()
    return redirect(url_for('materiais'))

@app.route('/deletar_material/<int:id>', methods=['POST'])
def deletar_material(id):
    conn = get_db_connection(); conn.execute('DELETE FROM materiais WHERE id=?', (id,)); conn.commit(); conn.close()
    return redirect(url_for('materiais'))

# --- ROTAS DA PÁGINA 5: ENGENHARIA DE PRODUTO ---
@app.route('/engenharia')
def engenharia():
    conn = get_db_connection()
    prods = conn.execute('SELECT * FROM produtos').fetchall()
    maqs = conn.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas').fetchall()
    mats = conn.execute('SELECT id, nome_material, preco_unidade FROM materiais').fetchall()
    comps = conn.execute('SELECT ep.*, p.nome_produto, p.codigo_produto, m.nome_equipamento, mat.nome_material FROM estrutura_produto ep JOIN produtos p ON ep.produto_id = p.id LEFT JOIN maquinas m ON ep.maquina_id = m.id LEFT JOIN materiais mat ON ep.material_id = mat.id').fetchall()
    conn.close()
    return render_template('engenharia.html', produtos=prods, maquinas=maqs, materiais=mats, composicoes=comps)

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    try:
        conn = get_db_connection(); conn.execute('INSERT INTO produtos (codigo_produto, nome_produto) VALUES (?, ?)', (request.form['codigo_produto'], request.form['nome_produto'])); conn.commit(); conn.close()
    except sqlite3.IntegrityError: return "Erro: Produto duplicado."
    return redirect(url_for('engenharia'))

@app.route('/vincular_estrutura', methods=['POST'])
def vincular_estrutura():
    conn = get_db_connection()
    conn.execute('INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material) VALUES (?, ?, ?, ?, ?)', (int(request.form['produto_id']), request.form['maquina_id'] or None, request.form['material_id'] or None, float(request.form['tempo_processo_min'] or 0), float(request.form['quantidade_material'] or 0)))
    conn.commit(); conn.close()
    return redirect(url_for('engenharia'))

@app.route('/deletar_item_estrutura/<int:id>', methods=['POST'])
def deletar_item_estrutura(id):
    conn = get_db_connection(); conn.execute('DELETE FROM estrutura_produto WHERE id=?', (id,)); conn.commit(); conn.close()
    return redirect(url_for('engenharia'))
# --- ROTAS DA PÁGINA 6: FORMAÇÃO DE PREÇOS ---
@app.route('/precificacao')
def precificacao():
    conn = get_db_connection()
    prods = conn.execute('SELECT p.id, p.codigo_produto, p.nome_produto, COALESCE(SUM(ep.tempo_processo_min * mq.custo_minuto_maquina), 0) + COALESCE(SUM(ep.quantidade_material * mt.preco_unidade), 0) AS custo_fabricacao FROM produtos p LEFT JOIN estrutura_produto ep ON p.id = ep.produto_id LEFT JOIN maquinas mq ON ep.maquina_id = mq.id LEFT JOIN materiais mt ON ep.material_id = mt.id GROUP BY p.id').fetchall()
    salvos = conn.execute('SELECT fp.*, p.codigo_produto, p.nome_produto FROM formacao_precos fp JOIN produtos p ON fp.produto_id = p.id').fetchall()
    conn.close()
    return render_template('precificacao.html', produtos=prods, precos_salvos=salvos)

@app.route('/salvar_preco', methods=['POST'])
def salvar_preco():
    conn = get_db_connection()
    conn.execute('INSERT OR REPLACE INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (?, ?, ?, ?, ?, ?)', (int(request.form['produto_id']), float(request.form['imposto_municipal'] or 0), float(request.form['imposto_estadual'] or 0), float(request.form['imposto_federal'] or 0), float(request.form['margem_lucro'] or 0), float(request.form['preco_venda_final'] or 0)))
    conn.commit(); conn.close()
    return redirect(url_for('precificacao'))

@app.route('/deletar_preco/<int:id>', methods=['POST'])
def deletar_preco(id):
    conn = get_db_connection(); conn.execute('DELETE FROM formacao_precos WHERE id=?', (id,)); conn.commit(); conn.close()
    return redirect(url_for('precificacao'))

# --- ROTAS DAS PÁGINAS 7 E 8: VENDAS E ESTOQUE ---
@app.route('/vendas')
def vendas():
    conn = get_db_connection()
    prods = conn.execute('SELECT p.id, p.codigo_produto, p.nome_produto, fp.preco_venda_final, COALESCE(e.quantidade_disponivel, 0) AS estoque_atual FROM produtos p JOIN formacao_precos fp ON p.id = fp.produto_id LEFT JOIN estoque_produtos e ON p.id = e.produto_id').fetchall()
    peds = conn.execute('SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id ORDER BY pv.id DESC').fetchall()
    conn.close()
    return render_template('vendas.html', produtos=prods, pedidos=peds)

@app.route('/estoque')
def estoque():
    conn = get_db_connection(); itens = conn.execute('SELECT ep.*, p.codigo_produto, p.nome_produto FROM estoque_produtos ep JOIN produtos p ON ep.produto_id = p.id').fetchall(); conn.close()
    return render_template('estoque.html', estoque_itens=itens)

@app.route('/lancar_venda', methods=['POST'])
def lancar_venda():
    prod_id = int(request.form['produto_id']); qtd = int(request.form['quantidade'])
    conn = get_db_connection()
    est = conn.execute('SELECT quantidade_disponivel FROM estoque_produtos WHERE produto_id = ?', (prod_id,)).fetchone()
    if not est or est['quantidade_disponivel'] < qtd:
        conn.close(); return "Erro Pedagógico: Saldo de estoque insuficiente!"
    conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel - ? WHERE produto_id = ?', (qtd, prod_id))
    conn.execute('INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES (?, ?, ?, ?)', (prod_id, qtd, float(request.form['desconto_percentual'] or 0), request.form['observacoes']))
    conn.commit(); conn.close()
    return redirect(url_for('vendas'))

@app.route('/deletar_venda/<int:id>', methods=['POST'])
def deletar_venda(id):
    conn = get_db_connection(); ped = conn.execute('SELECT produto_id, quantidade FROM pedidos_vendas WHERE id = ?', (id,)).fetchone()
    if ped:
        conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + ? WHERE produto_id = ?', (ped['quantidade'], ped['produto_id']))
        conn.execute('DELETE FROM pedidos_vendas WHERE id = ?', (id,))
    conn.commit(); conn.close()
    return redirect(url_for('vendas'))

@app.route('/imprimir_nf/<int:pedido_id>')
def imprimir_nf(pedido_id):
    conn = get_db_connection()
    ped = conn.execute('SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id WHERE pv.id = ?', (pedido_id,)).fetchone()
    conn.close()
    if not ped: return "Nota Fiscal não encontrada."
    sub = ped['preco_venda_final'] * ped['quantidade']
    v_desc = sub * (ped['desconto_percentual'] / 100)
    liq = sub - v_desc
    return render_template('nota_fiscal.html', p=ped, subtotal=sub, v_desconto=v_desc, total_liquido=liq, v_municipal=liq*(ped['imposto_municipal']/100), v_estadual=liq*(ped['imposto_estadual']/100), v_federal=liq*(ped['imposto_federal']/100), total_impostos=liq*((ped['imposto_municipal']+ped['imposto_estadual']+ped['imposto_federal'])/100))

# --- ROTAS DA PÁGINA 9 E ROI: PCP E RETORNO DOS ACIONISTAS ---
@app.route('/pcp')
def pcp():
    conn = get_db_connection()
    novas = conn.execute('SELECT pv.id AS pedido_id, pv.quantidade, p.codigo_produto, p.nome_produto, p.id AS prod_id FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.id NOT IN (SELECT DISTINCT pedido_id FROM ordens_processo)').fetchall()
    for v in novas:
        rots = conn.execute('SELECT ep.*, m.nome_equipamento FROM estrutura_produto ep LEFT JOIN maquinas m ON ep.maquina_id = m.id WHERE ep.produto_id = ?', (v['prod_id'],)).fetchall()
        for idx, r in enumerate(rots):
            conn.execute('INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_nome, codigo_produto, nome_produto, tempo_estimado_min) VALUES (?, ?, ?, ?, ?, ?)', (v['pedido_id'], f"OP {(idx+1)*10}", r['nome_equipamento'] or 'Bancada Manual', v['codigo_produto'], v['nome_produto'], r['tempo_processo_min'] * v['quantidade']))
        conn.execute('INSERT OR IGNORE INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES (?, 0)')
        conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + ? WHERE produto_id = ?', (v['quantidade'], v['prod_id']))
    conn.commit()
    ords = conn.execute('SELECT * FROM ordens_processo ORDER BY id ASC').fetchall(); conn.close()
    return render_template('pcp.html', ordens=ords)

@app.route('/dar_baixa_op/<int:op_id>', methods=['POST'])
def dar_baixa_op(op_id):
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    conn = get_db_connection(); conn.execute('UPDATE ordens_processo SET data_saida = ?, operador_nome = ?, status = "Finalizado" WHERE id = ?', (agora, request.form['operador_nome'], op_id)); conn.commit(); conn.close()
    return redirect(url_for('pcp'))

@app.route('/roi')
def roi():
    conn = get_db_connection()
    v_dados = conn.execute('SELECT SUM((fp.preco_venda_final * pv.quantidade) * (1 - pv.desconto_percentual/100)) AS receita_bruta, SUM(pv.quantidade) AS total_pecas FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()
    invs = conn.execute('SELECT SUM(valor_terreno + valor_instalacoes) AS cap_imobilizado FROM investimentos_imobiliarios').fetchone()
    conn.close()
    rec = v_dados['receita_bruta'] if v_dados and v_dados['receita_bruta'] else 0
    pecas = v_dados['total_pecas'] if v_dados and v_dados['total_pecas'] else 0
    cap = invs['cap_imobilizado'] if invs and invs['cap_imobilizado'] else 0
    lucro = rec * 0.15
    return render_template('roi.html', receita=rec, pecas=pecas, capital=cap, lucro_acionistas=lucro, payback_real=(cap / lucro) if lucro > 0 else 0)

if __name__ == '__main__':
    app.run(debug=True)
