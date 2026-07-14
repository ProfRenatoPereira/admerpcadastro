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

    # Tabela de Estoque de Produtos Acabados (Página 8)
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

    # Tabela do Sequenciamento de Produção do PCP (Página 9)
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
# --- ROTAS DAS PÁGINAS 7 E 8: VENDAS E ESTOQUE ---
@app.route('/vendas')
def vendas():
    conn = get_db_connection()
    # Carrega produtos que já possuem preço final de venda configurado
    produtos = conn.execute('''
        SELECT p.id, p.codigo_produto, p.nome_produto, fp.preco_venda_final, 
               COALESCE(e.quantidade_disponivel, 0) AS estoque_atual
        FROM produtos p
        JOIN formacao_precos fp ON p.id = fp.produto_id
        LEFT JOIN estoque_produtos e ON p.id = e.produto_id
    ''').fetchall()
    
    pedidos = conn.execute('''
        SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final,
               fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal
        FROM pedidos_vendas pv
        JOIN produtos p ON pv.produto_id = p.id
        JOIN formacao_precos fp ON p.id = fp.produto_id
        ORDER BY pv.id DESC
    ''').fetchall()
    conn.close()
    return render_template('vendas.html', produtos=produtos, pedidos=pedidos)

@app.route('/estoque')
def estoque():
    conn = get_db_connection()
    estoque_itens = conn.execute('''
        SELECT ep.*, p.codigo_produto, p.nome_produto 
        FROM estoque_produtos ep
        JOIN produtos p ON ep.produto_id = p.id
    ''').fetchall()
    conn.close()
    return render_template('estoque.html', estoque_itens=estoque_itens)
@app.route('/lancar_venda', methods=['POST'])
def lancar_venda():
    prod_id = int(request.form['produto_id'])
    qtd = int(request.form['quantidade'])
    desconto = float(request.form['desconto_percentual'] or 0)
    obs = request.form['observacoes']
    
    conn = get_db_connection()
    # Verifica disponibilidade em estoque
    est = conn.execute('SELECT quantidade_disponivel FROM estoque_produtos WHERE produto_id = ?', (prod_id,)).fetchone()
    estoque_atual = est['quantidade_disponivel'] if est else 0
    
    if estoque_atual < qtd:
        conn.close()
        return "Erro Pedagógico: Saldo de estoque insuficiente para realizar esta venda! Abasteça o estoque primeiro."
    
    # Executa a baixa no estoque e insere o pedido de venda
    conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel - ? WHERE produto_id = ?', (qtd, prod_id))
    conn.execute('''
        INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes)
        VALUES (?, ?, ?, ?)
    ''', (prod_id, qtd, descuento, obs))
    conn.commit()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/deletar_venda/<int:id>', methods=['POST'])
def deletar_venda(id):
    conn = get_db_connection()
    # Estorna a quantidade de volta para o estoque ao deletar o pedido
    pedido = conn.execute('SELECT produto_id, quantidade FROM pedidos_vendas WHERE id = ?', (id,)).fetchone()
    if pedido:
        conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + ? WHERE produto_id = ?', (pedido['quantidade'], pedido['produto_id']))
        conn.execute('DELETE FROM pedidos_vendas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('vendas'))
@app.route('/imprimir_nf/<int:pedido_id>')
def imprimir_nf(pedido_id):
    conn = get_db_connection()
    pedido = conn.execute('''
        SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final,
               fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal
        FROM pedidos_vendas pv
        JOIN produtos p ON pv.produto_id = p.id
        JOIN formacao_precos fp ON p.id = fp.produto_id
        WHERE pv.id = ?
    ''', (pedido_id,)).fetchone()
    conn.close()
    
    if not pedido:
        return "Nota Fiscal não encontrada."
        
    # Cálculos dinâmicos para exibição na NF
    subtotal = pedido['preco_venda_final'] * pedido['quantidade']
    v_desconto = subtotal * (pedido['desconto_percentual'] / 100)
    total_liquido = subtotal - v_desconto
    
    v_municipal = total_liquido * (pedido['imposto_municipal'] / 100)
    v_estadual = total_liquido * (pedido['imposto_estadual'] / 100)
    v_federal = total_liquido * (pedido['imposto_federal'] / 100)
    total_impostos = v_municipal + v_estadual + v_federal
    
    return render_template('nota_fiscal.html', p=pedido, subtotal=subtotal, v_desconto=v_desconto, 
                           total_liquido=total_liquido, v_municipal=v_municipal, v_estadual=v_estadual, 
                           v_federal=v_federal, total_impostos=total_impostos)
# --- ROTAS DA PÁGINA 9 E ROI: PCP E RETORNO DOS ACIONISTAS ---
@app.route('/pcp')
def pcp():
    conn = get_db_connection()
    # Verifica se há novas vendas faturadas que precisam entrar na fila do PCP
    novas_vendas = conn.execute('''
        SELECT pv.id AS pedido_id, pv.quantidade, p.codigo_produto, p.nome_produto, p.id AS prod_id
        FROM pedidos_vendas pv
        JOIN produtos p ON pv.produto_id = p.id
        WHERE pv.id NOT IN (SELECT DISTINCT pedido_id FROM ordens_processo)
    ''').fetchall()
    
    # Se houver novas vendas, gera automaticamente o roteiro no PCP baseado na Engenharia (BOM)
    for venda in novas_vendas:
        roteiros = conn.execute('''
            SELECT ep.*, m.nome_equipamento 
            FROM estrutura_produto ep
            LEFT JOIN maquinas m ON ep.maquina_id = m.id
            WHERE ep.produto_id = ?
        ''', (venda['prod_id'],)).fetchall()
        
        for idx, rot in enumerate(roteiros):
            tempo_total_lote = rot['tempo_processo_min'] * venda['quantidade']
            conn.execute('''
                INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_nome, codigo_produto, nome_produto, tempo_estimado_min)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (venda['pedido_id'], f"OP { (idx+1)*10 }", rot['nome_equipamento'] or 'Bancada Manual', 
                  venda['codigo_produto'], venda['nome_produto'], tempo_total_lote))
            
            # Alimenta o estoque de acabados inicialmente se não existir registro para o produto
            conn.execute('INSERT OR IGNORE INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES (?, 0)', (venda['prod_id'],))
            # O abastecimento do estoque ocorre quando a produção finaliza (simulado pedagogicamente na rota dar_baixa)
            conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + ? WHERE produto_id = ?', (venda['quantidade'], venda['prod_id']))
            
    conn.commit()
    ordens = conn.execute('SELECT * FROM ordens_processo ORDER BY id ASC').fetchall()
    conn.close()
    return render_template('pcp.html', ordens=ordens)

@app.route('/dar_baixa_op/<int:op_id>', methods=['POST'])
def dar_baixa_op(op_id):
    operador = request.form['operador_nome']
    import datetime
    data_agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE ordens_processo 
        SET data_saida = ?, operador_nome = ?, status = 'Finalizado'
        WHERE id = ?
    ''', (data_agora, operador, op_id))
    conn.commit()
    conn.close()
    return redirect(url_for('pcp'))

@app.route('/roi')
def roi():
    conn = get_db_connection()
    # Soma de todo o faturamento líquido (preço final com descontos)
    vendas_dados = conn.execute('''
        SELECT SUM((fp.preco_venda_final * pv.quantidade) * (1 - pv.desconto_percentual/100)) AS receita_bruta,
               SUM(pv.quantidade) AS total_pecas
        FROM pedidos_vendas pv
        JOIN formacao_precos fp ON pv.produto_id = fp.produto_id
    ''').fetchone()
    
    # Soma de investimentos iniciais da página 2
    investimentos = conn.execute('SELECT SUM(valor_terreno + valor_instalacoes) AS cap_imobilizado FROM investimentos_imobiliarios').fetchone()
    conn.close()
    
    receita = vendas_dados['receita_bruta'] if vendas_dados and vendas_dados['receita_bruta'] else 0
    pecas = vendas_dados['total_pecas'] if vendas_dados and vendas_dados['total_pecas'] else 0
    capital = investimentos['cap_imobilizado'] if investimentos and investimentos['cap_imobilizado'] else 0
    
    # Pedagogia: O lucro repassado aos acionistas é simulado em cima do ritmo operacional
    lucro_acionistas = receita * 0.15 # 15% de margem líquida direta distribuída
    payback_real = (capital / lucro_acionistas) if lucro_acionistas > 0 else 0
    
    return render_template('roi.html', receita=receita, pecas=pecas, capital=capital, lucro_acionistas=lucro_acionistas, payback_real=payback_real)
