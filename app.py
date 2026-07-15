import os
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Cria todas as tabelas do sistema de forma robusta e integrada"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, aprovado INTEGER DEFAULT 0)')

    # Tabela imobiliaria atualizada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investimentos_imobiliarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            turma_nome TEXT NOT NULL, 
            cidade_regiao TEXT NOT NULL,
            bairro_imovel TEXT NOT NULL,
            area_imovel REAL NOT NULL,
            taxa_selic REAL NOT NULL, 
            valor_imovel_estimado REAL NOT NULL,
            aluguel_regional REAL NOT NULL,
            perc_acionistas REAL NOT NULL
        )
    ''')

    cursor.execute('CREATE TABLE IF NOT EXISTS maquinas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_equipamento TEXT NOT NULL, potencia REAL NOT NULL, consumo_eletrico REAL NOT NULL, velocidade TEXT, avanco TEXT, comprimento_max REAL, diametro_max REAL, frequencia_manutencao INTEGER NOT NULL, horas_trabalhadas INTEGER DEFAULT 0, preco_compra REAL NOT NULL, depreciacao_mensal REAL NOT NULL, valor_venda_final REAL NOT NULL, custo_minuto_maquina REAL NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS materiais (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_material TEXT UNIQUE NOT NULL, nome_material TEXT NOT NULL, preco_unidade REAL NOT NULL, dimensoes TEXT, volume_disponivel REAL NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS requisicoes_compras (id INTEGER PRIMARY KEY AUTOINCREMENT, equipamento_tipo TEXT NOT NULL, especificacao_desejada TEXT NOT NULL, quantidade INTEGER DEFAULT 1, status TEXT DEFAULT "Pendente em Cotação", preco_cotado REAL DEFAULT 0, potencia_cotada REAL DEFAULT 0, depreciacao_sugerida REAL DEFAULT 0, data_requisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_produto TEXT UNIQUE NOT NULL, nome_produto TEXT NOT NULL, custo_total_fabricacao REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS estrutura_produto (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL, maquina_id INTEGER, material_id INTEGER, tempo_processo_min REAL DEFAULT 0, quantidade_material REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS formacao_precos (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER UNIQUE NOT NULL, imposto_municipal REAL DEFAULT 0, imposto_estadual REAL DEFAULT 0, imposto_federal REAL DEFAULT 0, margem_lucro REAL DEFAULT 0, preco_venda_final REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS estoque_produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER UNIQUE NOT NULL, quantidade_disponivel REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS pedidos_vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, desconto_percentual REAL DEFAULT 0, observacoes TEXT, data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS ordens_processo (id INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id INTEGER NOT NULL, numero_operacao TEXT NOT NULL, maquina_nome TEXT NOT NULL, codigo_produto TEXT NOT NULL, nome_produto TEXT NOT NULL, data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tempo_estimado_min REAL NOT NULL, data_saida TEXT DEFAULT "Aguardando", operador_nome TEXT DEFAULT "Pendente", status TEXT DEFAULT "Na Fila", FOREIGN KEY(pedido_id) REFERENCES pedidos_vendas(id))')
    
    conn.commit()
    conn.close()

if not os.path.exists(DATABASE):
    init_db()

@app.route('/')
def index():
    return redirect(url_for('estrutura'))

@app.route('/login', methods=['POST'])
def login():
    return redirect(url_for('estrutura'))

@app.route('/cadastrar_usuario', methods=['POST'])
def cadastrar_usuario():
    return redirect(url_for('estrutura'))
# --- ROTAS DA PÁGINA 2: INVESTIMENTOS IMOBILIÁRIOS MODIFICADAS ---
@app.route('/estrutura')
def estrutura():
    conn = get_db_connection()
    registros = conn.execute('SELECT * FROM investimentos_imobiliarios').fetchall()
    conn.close()
    return render_template('estrutura.html', taxa_atual=11.39, registros=registros)

@app.route('/salvar_estrutura', methods=['POST'])
def salvar_estrutura():
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO investimentos_imobiliarios 
        (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        request.form['turma_nome'], request.form['cidade_regiao'], request.form['bairro_imovel'],
        float(request.form['area_imovel']), float(request.form['taxa_selic']),
        float(request.form['valor_imovel_estimado']), float(request.form['aluguel_regional']),
        float(request.form['perc_acionistas'])
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/alterar_estrutura/<int:id>', methods=['POST'])
def alterar_estrutura(id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE investimentos_imobiliarios 
        SET turma_nome=?, cidade_regiao=?, bairro_imovel=?, area_imovel=?, taxa_selic=?, valor_imovel_estimado=?, aluguel_regional=?, perc_acionistas=? 
        WHERE id=?
    ''', (
        request.form['turma_nome'], request.form['cidade_regiao'], request.form['bairro_imovel'],
        float(request.form['area_imovel']), float(request.form['taxa_selic']),
        float(request.form['valor_imovel_estimado']), float(request.form['aluguel_regional']),
        float(request.form['perc_acionistas']), id
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/deletar_estrutura/<int:id>', methods=['POST'])
def deletar_estrutura(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM investimentos_imobiliarios WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))
# --- ROTAS DA PÁGINA 3: MAQUINÁRIOS ---
@app.route('/maquinas')
def maquinas():
    conn = get_db_connection()
    m_dados = conn.execute('SELECT * FROM maquinas').fetchall()
    ult = conn.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    base = ult['aluguel_regional'] if ult else 0
    return render_template('maquinas.html', maquinas=m_dados, custo_minuto_estrutural=base/(176*60) if base > 0 else 0)

@app.route('/salvar_maquina', methods=['POST'])
def salvar_maquina():
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (request.form['nome_equipamento'], float(request.form['potencia']), float(request.form['consumo_eletrico']), request.form['velocidade'], request.form['avanco'], float(request.form['comprimento_max'] or 0), float(request.form['diametro_max'] or 0), int(request.form['frequencia_manutencao']), int(request.form['horas_trabalhadas'] or 0), float(request.form['preco_compra']), float(request.form['depreciacao_mensal']), float(request.form['valor_venda_final']), float(request.form['custo_minuto_maquina'])))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/alterar_maquina/<int:id>', methods=['POST'])
def alterar_maquina(id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE maquinas SET nome_equipamento=?, potencia=?, consumo_eletrico=?, velocidade=?, avanco=?, comprimento_max=?, diametro_max=?, frequencia_manutencao=?, horas_trabalhadas=?, preco_compra=?, depreciacao_mensal=?, valor_venda_final=?, custo_minuto_maquina=? WHERE id=?''', 
        (request.form['nome_equipamento'], float(request.form['potencia']), float(request.form['consumo_eletrico']), request.form['velocidade'], request.form['avanco'], float(request.form['comprimento_max'] or 0), float(request.form['diametro_max'] or 0), int(request.form['frequencia_manutencao']), int(request.form['horas_trabalhadas'] or 0), float(request.form['preco_compra']), float(request.form['depreciacao_mensal']), float(request.form['valor_venda_final']), float(request.form['custo_minuto_maquina']), id))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/requisicoes')
def requisicoes():
    conn = get_db_connection()
    reqs = conn.execute('SELECT * FROM requisicoes_compras ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('requisicoes.html', requisicoes=reqs)

@app.route('/compras')
def compras():
    conn = get_db_connection()
    cotadas = conn.execute("SELECT * FROM requisicoes_compras WHERE status LIKE 'Cotado%' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('compras.html', requisicoes_cotadas=cotadas)

@app.route('/salvar_requisicao', methods=['POST'])
def salvar_requisicao():
    conn = get_db_connection()
    conn.execute('INSERT INTO requisicoes_compras (equipamento_tipo, especificacao_desejada, quantidade) VALUES (?, ?, ?)', (request.form['equipamento_tipo'], request.form['especificacao_desejada'], int(request.form['quantidade'])))
    conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/cotar_internet/<int:id>', methods=['POST'])
def cotar_internet(id):
    conn = get_db_connection()
    req = conn.execute('SELECT * FROM requisicoes_compras WHERE id = ?', (id,)).fetchone()
    if req:
        tipo = req['equipamento_tipo'].lower()
        esp = req['especificacao_desejada'].lower()
        preco, pot, dep = 45000, 5.5, 375
        if 'torno' in tipo or 'cnc' in tipo:
            preco, pot, dep = (480000, 22.0, 4000) if 'mazak' in esp else (250000, 15.0, 2100)
        elif 'fresa' in tipo:
            preco, pot, dep = (110000, 7.5, 900)
        elif 'serra' in tipo:
            preco, pot, dep = (22000, 2.2, 180)
        conn.execute('UPDATE requisicoes_compras SET preco_cotado=?, potencia_cotada=?, depreciacao_sugerida=?, status="Cotado - Aguardando Confirmação" WHERE id=?', (preco, pot, dep, id))
        conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/efetivar_compra/<int:id>', methods=['POST'])
def efetivar_compra(id):
    conn = get_db_connection()
    req = conn.execute('SELECT * FROM requisicoes_compras WHERE id = ?', (id,)).fetchone()
    ult_imovel = conn.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    aluguel_mensal = ult_imovel['aluguel_regional'] if ult_imovel else 0
    minutos_operacionais = 176 * 60
    custo_aluguel_minuto = aluguel_mensal / minutos_operacionais
    if req:
        preco = float(request.form['preco_final'])
        pot = float(request.form['potencia_final'])
        dep = float(request.form['depreciacao_final'])
        c_mm = (dep / minutos_operacionais) + ((pot * 0.75) / 60) + custo_aluguel_minuto
        conn.execute('INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina) VALUES (?, ?, ?, "3000", "15000", 500, 300, 1000, 0, ?, ?, ?, ?)', (f"{req['equipamento_tipo']} - {req['especificacao_desejada']}", pot, pot * 0.7, preco, dep, preco * 0.2, c_mm))
        conn.execute("UPDATE requisicoes_compras SET status = 'Comprado e Ativado' WHERE id = ?", (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/deletar_requisicao/<int:id>', methods=['POST'])
def deletar_requisicao(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM requisicoes_compras WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))
# --- ROTAS DA PÁGINA 4: MATERIAIS ---
@app.route('/materiais')
def materiais():
    conn = get_db_connection()
    mats = conn.execute('SELECT * FROM materiais').fetchall()
    conn.close()
    return render_template('materiais.html', materiais=mats)

@app.route('/salvar_material', methods=['POST'])
def salvar_material():
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (?, ?, ?, ?, ?)', (request.form['codigo_material'], request.form['nome_material'], float(request.form['preco_unidade']), request.form['dimensoes'], float(request.form['volume_disponivel'])))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError: 
        return "Erro Pedagógico: Material duplicado!"
    return redirect(url_for('materiais'))

@app.route('/alterar_material/<int:id>', methods=['POST'])
def alterar_material(id):
    conn = get_db_connection()
    conn.execute('UPDATE materiais SET codigo_material=?, nome_material=?, preco_unidade=?, dimensoes=?, volume_disponivel=? WHERE id=?', (request.form['codigo_material'], request.form['nome_material'], float(request.form['preco_unidade']), request.form['dimensoes'], float(request.form['volume_disponivel']), id))
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
    prods = conn.execute('SELECT * FROM produtos').fetchall()
    maqs = conn.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas').fetchall()
    mats = conn.execute('SELECT id, nome_material, preco_unidade FROM materiais').fetchall()
    comps = conn.execute('SELECT ep.*, p.nome_produto, p.codigo_produto, m.nome_equipamento, mat.nome_material FROM estrutura_produto ep JOIN produtos p ON ep.produto_id = p.id LEFT JOIN maquinas m ON ep.maquina_id = m.id LEFT JOIN materiais mat ON ep.material_id = mat.id').fetchall()
    conn.close()
    return render_template('engenharia.html', produtos=prods, maquinas=maqs, materiais=mats, composicoes=comps)

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO produtos (codigo_produto, nome_produto) VALUES (?, ?)', (request.form['codigo_produto'], request.form['nome_produto']))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError: 
        return "Erro: Produto duplicado."
    return redirect(url_for('engenharia'))

@app.route('/vincular_estrutura', methods=['POST'])
def vincular_estrutura():
    conn = get_db_connection()
    conn.execute('INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material) VALUES (?, ?, ?, ?, ?)', (int(request.form['produto_id']), request.form['maquina_id'] or None, request.form['material_id'] or None, float(request.form['tempo_processo_min'] or 0), float(request.form['quantidade_material'] or 0)))
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
    prods = conn.execute('SELECT p.id, p.codigo_produto, p.nome_produto, COALESCE(SUM(ep.tempo_processo_min * mq.custo_minuto_maquina), 0) + COALESCE(SUM(ep.quantidade_material * mt.preco_unidade), 0) AS custo_fabricacao FROM produtos p LEFT JOIN estrutura_produto ep ON p.id = ep.produto_id LEFT JOIN maquinas mq ON ep.maquina_id = mq.id LEFT JOIN materiais mt ON ep.material_id = mt.id GROUP BY p.id').fetchall()
    salvos = conn.execute('SELECT fp.*, p.codigo_produto, p.nome_produto FROM formacao_precos fp JOIN produtos p ON fp.produto_id = p.id').fetchall()
    conn.close()
    return render_template('precificacao.html', produtos=prods, precos_salvos=salvos)

@app.route('/salvar_preco', methods=['POST'])
def salvar_preco():
    conn = get_db_connection()
    conn.execute('INSERT OR REPLACE INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (?, ?, ?, ?, ?, ?)', (int(request.form['produto_id']), float(request.form['imposto_municipal'] or 0), float(request.form['imposto_estadual'] or 0), float(request.form['imposto_federal'] or 0), float(request.form['margem_lucro'] or 0), float(request.form['preco_venda_final'] or 0)))
    conn.commit()
    conn.close()
    return redirect(url_for('precificacao'))
# --- ROTAS DAS PÁGINAS 7 E 8: VENDAS E ESTOQUE BLINDADOS ---
@app.route('/vendas')
def vendas():
    conn = get_db_connection()
    prods = conn.execute('SELECT p.id, p.codigo_produto, p.nome_produto, fp.preco_venda_final, COALESCE(e.quantidade_disponivel, 0) AS estoque_atual FROM produtos p JOIN formacao_precos fp ON p.id = fp.produto_id LEFT JOIN estoque_produtos e ON p.id = e.produto_id').fetchall()
    peds = conn.execute('SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id ORDER BY pv.id DESC').fetchall()
    conn.close()
    return render_template('vendas.html', produtos=prods, pedidos=peds)

@app.route('/estoque')
def estoque():
    conn = get_db_connection()
    itens = conn.execute('SELECT p.id AS produto_id, p.codigo_produto, p.nome_produto, COALESCE(ep.quantidade_disponivel, 0) AS quantidade_disponivel FROM produtos p LEFT JOIN estoque_produtos ep ON p.id = ep.produto_id').fetchall()
    conn.close()
    return render_template('estoque.html', estoque_itens=itens)

@app.route('/abastecer_estoque', methods=['POST'])
def abastecer_estoque():
    prod_id = int(request.form['produto_id'])
    qtd = float(request.form['quantidade_abastecer'])
    conn = get_db_connection()
    est = conn.execute('SELECT * FROM estoque_produtos WHERE produto_id = ?', (prod_id,)).fetchone()
    if not est: 
        conn.execute('INSERT INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES (?, ?)', (prod_id, qtd))
    else: 
        conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + ? WHERE produto_id = ?', (qtd, prod_id))
    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/lancar_venda', methods=['POST'])
def lancar_venda():
    prod_id = int(request.form['produto_id'])
    qtd = int(request.form['quantidade'])
    conn = get_db_connection()
    est = conn.execute('SELECT quantidade_disponivel FROM estoque_produtos WHERE produto_id = ?', (prod_id,)).fetchone()
    estoque_atual = est['quantidade_disponivel'] if est else 0
    if estoque_atual < qtd:
        conn.close()
        return "Erro Pedagógico: Saldo de estoque insuficiente!"
    conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel - ? WHERE produto_id = ?', (qtd, prod_id))
    conn.execute('INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES (?, ?, ?, ?)', (prod_id, qtd, float(request.form['desconto_percentual'] or 0), request.form['observacoes']))
    conn.commit()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/deletar_venda/<int:id>', methods=['POST'])
def deletar_venda(id):
    conn = get_db_connection()
    ped = conn.execute('SELECT produto_id, quantidade FROM pedidos_vendas WHERE id = ?', (id,)).fetchone()
    if ped:
        conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + ? WHERE produto_id = ?', (ped['quantidade'], ped['produto_id']))
        conn.execute('DELETE FROM pedidos_vendas WHERE id = ?', (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/imprimir_nf/<int:pedido_id>')
def imprimir_nf(pedido_id):
    conn = get_db_connection()
    ped = conn.execute('SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id WHERE pv.id = ?', (pedido_id,)).fetchone()
    conn.close()
    if not ped: 
        return "Nota Fiscal não encontrada."
    sub = ped['preco_venda_final'] * ped['quantidade']
    v_desc = sub * (ped['desconto_percentual'] / 100)
    liq = sub - v_desc
    return render_template('nota_fiscal.html', p=ped, subtotal=sub, v_desconto=v_desc, total_liquido=liq, v_municipal=liq*(ped['imposto_municipal']/100), v_estadual=liq*(ped['imposto_estadual']/100), v_federal=liq*(ped['imposto_federal']/100), total_impostos=liq*((ped['imposto_municipal']+ped['imposto_estadual']+ped['imposto_federal'])/100))

@app.route('/pcp')
def pcp():
    conn = get_db_connection()
    novas = conn.execute('SELECT pv.id AS pedido_id, pv.quantidade, p.codigo_produto, p.nome_produto, p.id AS prod_id FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.id NOT IN (SELECT DISTINCT pedido_id FROM ordens_processo)').fetchall()
    for v in novas:
        rots = conn.execute('SELECT ep.*, m.nome_equipamento FROM estrutura_produto ep LEFT JOIN maquinas m ON ep.maquina_id = m.id WHERE ep.produto_id = ?', (v['prod_id'],)).fetchall()
        for idx, r in enumerate(rots):
            conn.execute('INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_nome, codigo_produto, nome_produto, tempo_estimado_min) VALUES (?, ?, ?, ?, ?, ?)', (v['pedido_id'], f"OP {(idx+1)*10}", r['nome_equipamento'] or 'Bancada Manual', v['codigo_produto'], v['nome_produto'], r['tempo_processo_min'] * v['quantidade']))
    ords = conn.execute('SELECT * FROM ordens_processo ORDER BY id ASC').fetchall()
    conn.close()
    return render_template('pcp.html', ordens=ords)

@app.route('/dar_baixa_op/<int:id>', methods=['POST'])
def dar_baixa_op(id):
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    conn = get_db_connection()
    conn.execute('UPDATE ordens_processo SET data_saida = ?, operador_nome = ?, status = "Finalizado" WHERE id = ?', (agora, request.form['operador_nome'], id))
    conn.commit()
    conn.close()
    return redirect(url_for('pcp'))

@app.route('/roi')
def roi():
    conn = get_db_connection()
    v_dados = conn.execute('SELECT COALESCE(SUM((fp.preco_venda_final * pv.quantidade) * (1 - pv.desconto_percentual/100)), 0) AS receita_bruta, COALESCE(SUM(pv.quantidade), 0) AS total_pecas FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()
    invs = conn.execute('SELECT COALESCE(SUM(valor_imovel_estimado), 0) AS cap_imobilizado FROM investimentos_imobiliarios').fetchone()
    conn.close()
    rec, pecas, cap = v_dados['receita_bruta'], v_dados['total_pecas'], invs['cap_imobilizado']
    roi_calculado = (rec / cap) * 100 if cap > 0 else 0.0
    return render_template('roi.html', receita=rec, total_pecas=pecas, capital=cap, roi=roi_calculado)

if __name__ == '__main__':
    app.run(debug=True)
