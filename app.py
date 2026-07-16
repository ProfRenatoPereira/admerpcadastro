import os
import sqlite3
import datetime
import math
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Cria todas as tabelas do sistema de forma robusta e integrada no banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, aprovado INTEGER DEFAULT 0)')

    # Tabela imobiliaria (Página 2)
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

    # Tabela de Máquinas Robustecida com Operador CLT e Custos de Folha (Página 3)
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
            custo_minuto_maquina REAL NOT NULL,
            operador_nome TEXT DEFAULT 'Posto Vago - Aguardando MOD',
            custo_minuto_operador REAL DEFAULT 0.0,
            salario_base REAL DEFAULT 0.0,
            valor_adicionais REAL DEFAULT 0.0,
            turno_trabalho TEXT DEFAULT 'Diurno',
            dia_semana TEXT DEFAULT 'Regular'
        )
    ''')

    cursor.execute('CREATE TABLE IF NOT EXISTS materiais (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_material TEXT UNIQUE NOT NULL, nome_material TEXT NOT NULL, preco_unidade REAL NOT NULL, dimensoes TEXT, volume_disponivel REAL NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS requisicoes_compras (id INTEGER PRIMARY KEY AUTOINCREMENT, equipamento_tipo TEXT NOT NULL, especificacao_desejada TEXT NOT NULL, quantidade INTEGER DEFAULT 1, status TEXT DEFAULT "Pendente em Cotação", preco_cotado REAL DEFAULT 0, potencia_cotada REAL DEFAULT 0, depreciacao_sugerida REAL DEFAULT 0, data_requisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_produto TEXT UNIQUE NOT NULL, nome_produto TEXT NOT NULL, custo_total_fabricacao REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS estrutura_produto (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL, maquina_id INTEGER, material_id INTEGER, tempo_processo_min REAL DEFAULT 0, quantidade_material REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS formacao_precos (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER UNIQUE NOT NULL, imposto_municipal REAL DEFAULT 0, imposto_estadual REAL DEFAULT 0, imposto_federal REAL DEFAULT 0, margem_lucro REAL DEFAULT 0, preco_venda_final REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS estoque_produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER UNIQUE NOT NULL, quantidade_disponivel REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS pedidos_vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, desconto_percentual REAL DEFAULT 0, observacoes TEXT, data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    
    # Tabela do Sequenciamento PCP atualizada com custos e encadeamento temporal (Página 12)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordens_processo (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            pedido_id INTEGER NOT NULL, 
            numero_operacao TEXT NOT NULL, 
            maquina_name TEXT NOT NULL, 
            codigo_produto TEXT NOT NULL, 
            nome_produto TEXT NOT NULL, 
            data_entrada TEXT NOT NULL, 
            tempo_estimado_min REAL NOT NULL, 
            data_saida TEXT NOT NULL, 
            operador_nome TEXT DEFAULT 'Pendente', 
            status TEXT DEFAULT 'Na Fila',
            custo_operacao REAL DEFAULT 0.0,
            FOREIGN KEY(pedido_id) REFERENCES pedidos_vendas(id)
        )
    ''')
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

# --- ROTAS DA PÁGINA 2: INVESTIMENTOS IMOBILIÁRIOS ---
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
        INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (request.form['nome_equipamento'], float(request.form['potencia']), float(request.form['consumo_eletrico']), request.form['velocidade'], request.form['avanco'], float(request.form['comprimento_max'] or 0), float(request.form['diametro_max'] or 0), int(request.form['frequencia_manutencao']), int(request.form['horas_trabalhadas'] or 0), float(request.form['preco_compra']), float(request.form['depreciacao_mensal']), float(request.form['valor_venda_final']), float(request.form['custo_minuto_maquina']), request.form.get('operador_nome', 'Posto Vago - Aguardando MOD'), float(request.form.get('custo_minuto_operador', 0.0)), float(request.form.get('salario_base', 0.0)), float(request.form.get('valor_adicionais', 0.0)), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular')))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/alterar_maquina/<int:id>', methods=['POST'])
def alterar_maquina(id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE maquinas SET nome_equipamento=?, potencia=?, consumo_eletrico=?, velocidade=?, avanco=?, comprimento_max=?, diametro_max=?, frequencia_manutencao=?, horas_trabalhadas=?, preco_compra=?, depreciacao_mensal=?, valor_venda_final=?, custo_minuto_maquina=?, operador_nome=?, custo_minuto_operador=?, salario_base=?, valor_adicionais=?, turno_trabalho=?, dia_semana=? WHERE id=?''', 
        (request.form['nome_equipamento'], float(request.form['potencia']), float(request.form['consumo_eletrico']), request.form['velocidade'], request.form['avanco'], float(request.form['comprimento_max'] or 0), float(request.form['diametro_max'] or 0), int(request.form['frequencia_manutencao']), int(request.form['horas_trabalhadas'] or 0), float(request.form['preco_compra']), float(request.form['depreciacao_mensal']), float(request.form['valor_venda_final']), float(request.form['custo_minuto_maquina']), request.form['operador_nome'], float(request.form['custo_minuto_operador']), float(request.form['salario_base']), float(request.form['valor_adicionais']), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), id))
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
# --- GESTÃO DE RECURSOS HUMANOS ---
@app.route('/rh')
def rh():
    conn = get_db_connection()
    colaboradores = conn.execute("SELECT * FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''").fetchall()
    conn.close()
    return render_template('rh.html', colaboradores=colaboradores)

@app.route('/salvar_colaborador', methods=['POST'])
def salvar_colaborador():
    conn = get_db_connection()
    posto_vago = conn.execute("SELECT id FROM maquinas WHERE operador_nome = 'Posto Vago - Aguardando MOD' LIMIT 1").fetchone()
    
    if posto_vago:
        conn.execute('''
            UPDATE maquinas 
            SET operador_nome=?, salario_base=?, valor_adicionais=?, turno_trabalho=?, dia_semana=?, custo_minuto_operador=? 
            WHERE id=?
        ''', (
            request.form['nome_completo'], float(request.form['salario_base']),
            float(request.form['valor_adicionais']), request.form['turno'],
            request.form['dia_semana'], float(request.form['custo_minuto_operador']),
            posto_vago['id']
        ))
        conn.commit()
        flash('Profissional CLT contratado e alocado com sucesso em uma máquina ativa!', 'success')
    else:
        conn.execute('''
            INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana) 
            VALUES ('Posto de Apoio / Indireto', 0, 0, 'N/A', 'N/A', 0, 0, 9999, 0, 0, 0, 0, 0, ?, ?, ?, ?, ?, ?)''',
            (request.form['nome_completo'], float(request.form['custo_minuto_operador']), float(request.form['salario_base']), float(request.form['valor_adicionais']), request.form['turno'], request.form['dia_semana']))
        conn.commit()
        flash('Quadro Corporativo Expandido: Profissional contratado e alocado em Posto Geral de Apoio (Mão de Obra Indireta).', 'success')
        
    conn.close()
    return redirect(url_for('rh'))
@app.route('/imprimir_holerite/<int:id>/<string:tipo>')
def imprimir_holerite(id, tipo):
    conn = get_db_connection()
    col = conn.execute('SELECT * FROM maquinas WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not col or col['operador_nome'] == 'Posto Vago - Aguardando MOD':
        return "Colaborador ou posto operacional não localizado."
        
    salario_base = float(col['salario_base'] or 0.0)
    adicionais = float(col['valor_adicionais'] or 0.0)
    horas_extras_acumuladas = 1250.00 if col['dia_semana'] != 'Regular' else 0.0
    
    titulo_recibo = "RECIBO DE PAGAMENTO MENSAL"
    provento_principal_nome = "Salário Base Nominal"
    provento_principal_valor = salario_base
    
    if tipo == "ferias":
        titulo_recibo = "RECIBO DE PAGAMENTO DE FÉRIAS (CLT)"
        provento_principal_nome = "Férias Integrais Gozadas"
        provento_principal_valor = salario_base + (salario_base / 3)
    elif tipo == "decimo":
        titulo_recibo = "RECIBO DE DÉCIMO TERCEIRO SALÁRIO INTEGRAL"
        provento_principal_nome = "13º Salário Integral Adiantado"
        provento_principal_valor = salario_base

    total_proventos = provento_principal_valor + adicionais + horas_extras_acumuladas
    inss = total_proventos * 0.11
    irrf = (total_proventos * 0.075) if total_proventos > 2250 else 0.0
    vale_transporte = salario_base * 0.06 if col['turno_trabalho'] == 'Diurno' else 0.0
    total_descontos = inss + irrf + vale_transporte
    valor_liquido = total_proventos - total_descontos
    
    dados_holerite = {
        "tipo_recibo": titulo_recibo,
        "nome": col['operador_nome'],
        "cargo": f"CBO {col['id']} - Posto de Trabalho Ativo",
        "principal_nome": provento_principal_nome,
        "principal_valor": provento_principal_valor,
        "adicionais": adicionais,
        "he": horas_extras_acumuladas,
        "total_proventos": total_proventos,
        "inss": inss,
        "irrf": irrf,
        "vt": vale_transporte,
        "total_descontos": total_descontos,
        "liquido": valor_liquido
    }
    return render_template('recibo_trabalhista.html', h=dados_holerite)

@app.route('/calcular_rescisao/<int:id>/<string:tipo>', methods=['POST'])
def calcular_rescisao(id, tipo):
    conn = get_db_connection()
    col = conn.execute('SELECT * FROM maquinas WHERE id = ?', (id,)).fetchone()
    
    if col:
        base = float(col['salario_base'] or 1412.00)
        total_rescisao = 0.0
        motivo_str = ""
        
        if tipo == "justa_causa":
            total_rescisao = base * 0.5
            motivo_str = "Rescisão por Justa Causa Efetuada. Direitos retidos conforme Art. 482 da CLT."
        elif tipo == "voluntaria":
            total_rescisao = (base / 12 * 6) + (base / 12 * 6) + (base * 0.5)
            motivo_str = "Pedido de Demissão Voluntária homologado com aviso cumprido."
        elif tipo == "demissao":
            total_rescisao = base + (base / 12 * 6) + (base / 12 * 6) + (base * 1.40)
            motivo_str = "Dispensa Imotivada sem Justa Causa concretizada. Verbas rescisórias liberadas."
            
        conn.execute('UPDATE maquinas SET operador_nome = "Posto Vago - Aguardando MOD", custo_minuto_operador = 0.0, salario_base = 0.0, valor_adicionais = 0.0 WHERE id = ?', (id,))
        conn.commit()
        flash(f"Processamento Concluído: {motivo_str} Valor Líquido de Rescisão: R$ {total_rescisao:.2f}", "warning")
    else:
        flash("Colaborador operacional não localizado no chão de fábrica.", "danger")
    conn.close()
    return redirect(url_for('rh'))
# --- CENTRAL DE REQUISIÇÕES E SUPRIMENTOS ---
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
        if 'torno' in tipo or 'cnc' in tipo: preco, pot, dep = (480000, 22.0, 4000) if 'mazak' in esp else (250000, 15.0, 2100)
        elif 'fresa' in tipo: preco, pot, dep = (110000, 7.5, 900)
        elif 'serra' in tipo: preco, pot, dep = (22000, 2.2, 180)
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
        preco, pot, dep = float(request.form['preco_final']), float(request.form['potencia_final']), float(request.form['depreciacao_final'])
        c_mm = (dep / minutos_operacionais) + ((pot * 0.75) / 60) + custo_aluguel_minuto
        conn.execute('INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador) VALUES (?, ?, ?, "3000", "15000", 500, 300, 1000, 0, ?, ?, ?, ?, "Posto Vago - Aguardando MOD", 0.0)', (f"{req['equipamento_tipo']} - {req['especificacao_desejada']}", pot, pot * 0.7, preco, dep, preco * 0.2, c_mm))
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
# --- ALMOXARIFADO DE MATERIAIS ---
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
    except sqlite3.IntegrityError: return "Erro: Material duplicado!"
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

# --- ENGENHARIA DE PRODUTO (BOM) ---
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
    except sqlite3.IntegrityError: return "Erro: Produto duplicado."
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
    """Restaura a função que deleta insumos da Engenharia/BOM (Correção do Erro 404)"""
    conn = get_db_connection()
    conn.execute('DELETE FROM estrutura_produto WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('engenharia'))
# --- CONTROLADORIA E PRECIFICAÇÃO ---
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

# --- PAINEL DE VENDAS E ESTOQUE DE ACABADOS ---
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
    peds = conn.execute("SELECT pv.*, p.codigo_produto, p.nome_produto FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.observacoes LIKE '%SOB ENCOMENDA%' AND pv.id NOT IN (SELECT DISTINCT pedido_id FROM ordens_processo WHERE status='Finalizado e Armazenado')").fetchall()
    conn.close()
    return render_template('estoque.html', estoque_itens=itens, pedidos=peds)

@app.route('/lancar_venda', methods=['POST'])
def lancar_venda():
    prod_id = int(request.form['produto_id'])
    qtd = int(request.form['quantidade'])
    conn = get_db_connection()
    est = conn.execute('SELECT quantity_disponivel FROM estoque_produtos WHERE produto_id = ?'.replace('quantity', 'quantidade'), (prod_id,)).fetchone()
    estoque_atual = est['quantidade_disponivel'] if est else 0
    if estoque_atual >= qtd:
        conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel - ? WHERE produto_id = ?', (qtd, prod_id))
        conn.execute('INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES (?, ?, 0, "Pronta Entrega - Faturado")', (prod_id, qtd))
        conn.commit()
    else:
        conn.execute('INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES (?, ?, 0, "SOB ENCOMENDA - Fila PCP")', (prod_id, qtd))
        conn.commit()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/deletar_venda/<int:id>', methods=['POST'])
def deletar_venda(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM pedidos_vendas WHERE id=?', (id,))
    conn.execute('DELETE FROM ordens_processo WHERE pedido_id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('vendas'))
# --- SECÇÃO DO CHÃO DE FÁBRICA (PCP) ---
@app.route('/pcp')
def pcp():
    conn = get_db_connection()
    ords = conn.execute('SELECT * FROM ordens_processo ORDER BY pedido_id ASC, id ASC').fetchall()
    conn.close()
    return render_template('pcp.html', ordens=ords)

@app.route('/solicitar_producao_pcp/<int:pedido_id>', methods=['POST'])
def solicitar_producao_pcp(pedido_id):
    """Restaura a rota que gera o sequenciamento dinâmico em cascata (Correção do Erro 404)"""
    conn = get_db_connection()
    existe = conn.execute('SELECT id FROM ordens_processo WHERE pedido_id = ?', (pedido_id,)).fetchone()
    if not existe:
        ped = conn.execute('SELECT pv.*, p.codigo_produto, p.nome_produto FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.id = ?', (pedido_id,)).fetchone()
        if ped:
            rots = conn.execute('SELECT ep.*, m.nome_equipamento, m.custo_minuto_maquina, m.operador_nome FROM estrutura_produto ep LEFT JOIN maquinas m ON ep.maquina_id = m.id WHERE ep.produto_id = ? ORDER BY ep.id ASC', (ped['produto_id'],)).fetchall()
            ponteiro_tempo = datetime.datetime.now()
            for idx, r in enumerate(rots):
                tempo_lote_min = float(r['tempo_processo_min'] or 0) * int(ped['quantidade'])
                custo_total_operacao = tempo_lote_min * float(r['custo_minuto_maquina'] or 0.15)
                entrada_str = ponteiro_tempo.strftime("%d/%m/%Y %H:%M")
                saida_op = ponteiro_tempo + datetime.timedelta(minutes=tempo_lote_min)
                saida_str = saida_op.strftime("%d/%m/%Y %H:%M")
                conn.execute('INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_name, codigo_produto, nome_produto, data_entrada, tempo_estimado_min, data_saida, status, custo_operacao, operador_nome) VALUES (?, ?, ?, ?, ?, ?, ?, ?, "Na Fila", ?, ?)', (pedido_id, f"OP {(idx+1)*10}", r['nome_equipamento'] or 'Bancada Manual', ped['codigo_produto'], ped['nome_produto'], entrada_str, tempo_lote_min, saida_str, custo_total_operacao, r['operador_nome'] or 'Pendente'))
                ponteiro_tempo = saida_op
            conn.commit()
        flash('Ordem de Produção transmitida com sucesso para o painel do PCP!', 'success')
    else:
        flash('Este pedido já possui ordens de processo ativas.', 'info')
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/abastecer_estoque_pcp', methods=['POST'])
def abastecer_estoque_pcp():
    prod_id, pedido_id, qtd = int(request.form['produto_id']), int(request.form['pedido_id']), float(request.form['quantidade_abastecer'])
    conn = get_db_connection()
    ops_existentes = conn.execute('SELECT COUNT(*) as total FROM ordens_processo WHERE pedido_id = ?', (pedido_id,)).fetchone()['total']
    ops_pendentes = conn.execute("SELECT COUNT(*) as pendentes FROM ordens_processo WHERE pedido_id = ? AND status != 'Finalizado'", (pedido_id,)).fetchone()['pendentes']
    if ops_existentes == 0 or ops_pendentes > 0:
        conn.close()
        flash('Bloqueio de Qualidade: O Almoxarifado não pode receber este lote! Existem operações pendentes no PCP.', 'danger')
        return redirect(url_for('estoque'))
    est = conn.execute('SELECT * FROM estoque_produtos WHERE produto_id = ?', (prod_id,)).fetchone()
    if not est: conn.execute('INSERT INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES (?, ?)', (prod_id, qtd))
    else: conn.execute('UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + ? WHERE produto_id = ?', (qtd, prod_id))
    conn.execute("UPDATE ordens_processo SET status = 'Finalizado e Armazenado' WHERE pedido_id = ?", (pedido_id,))
    conn.commit()
    conn.close()
    flash('Recebimento efetuado e integrado com sucesso ao estoque disponível.', 'success')
    return redirect(url_for('estoque'))

@app.route('/dar_baixa_op/<int:id>', methods=['POST'])
def dar_baixa_op(id):
    conn = get_db_connection()
    conn.execute('UPDATE ordens_processo SET operador_nome = ?, status = "Finalizado" WHERE id = ?', (request.form['operador_nome'], id))
    conn.commit()
    conn.close()
    return redirect(url_for('pcp'))

# --- CONTROLADORIA FINANCEIRA (CAIXA E ROI) ---
@app.route('/financeiro')
def financeiro():
    conn = get_db_connection()
    faturamento_bruto = conn.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS total FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()['total']
    despesa_pessoal_bruta = conn.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) AS total FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''").fetchone()['total']
    conn.close()
    impostos_provisao = despesa_pessoal_bruta * 0.11
    caixa_liquido = faturamento_bruto - despesa_pessoal_bruta - impostos_provisao
    return render_template('financeiro.html', faturamento=faturamento_bruto, custo_pessoal=despesa_pessoal_bruta, impostos=impostos_provisao, saldo_liquido=caixa_liquido)

@app.route('/pagar_dividendos', methods=['POST'])
def pagar_dividendos():
    flash('Distribuição de dividendos processada! Enviado para o Livro Razão Contábil.', 'success')
    return redirect(url_for('financeiro'))

@app.route('/roi')
def roi():
    conn = get_db_connection()
    v_dados = conn.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS receita_bruta, COALESCE(SUM(pv.quantidade), 0) AS total_pecas FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()
    invs = conn.execute('SELECT COALESCE(SUM(valor_imovel_estimado), 0) AS capital_imobilizado FROM investimentos_imobiliarios').fetchone()
    conn.close()
    rec, pecas, cap = v_dados['receita_bruta'], v_dados['total_pecas'], invs['capital_imobilizado']
    roi_calculado = (rec / cap) * 100 if cap > 0 else 0.0
    return render_template('roi.html', receita=rec, total_pecas=pecas, capital=cap, roi=roi_calculado)

if __name__ == '__main__':
    app.run(debug=True)
