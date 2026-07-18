import os
import sqlite3
import datetime
import math
from flask import Flask, render_template, request, redirect, url_for, flash
from whitenoise import WhiteNoise

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

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

    # Módulo 1: Investimentos Imobiliários e Capital de Giro
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
            perc_acionistas REAL NOT NULL,
            capital_inicial_negocio REAL DEFAULT 0.0
        )
    ''')

    # Módulo 2: Engenharia de Ativos - Adicionado Vida Útil em Meses
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
            dia_semana TEXT DEFAULT 'Regular',
            vida_util_meses INTEGER DEFAULT 120
        )
    ''')


    # Módulo 4: Almoxarifado de Insumos e Matérias-Primas (Inventário Expandido)
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

    # Módulo 5: Central de Requisições de Compras - Corrigida a duplicidade de colunas do lote
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requisicoes_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            equipamento_tipo TEXT NOT NULL, 
            especificacao_desejada TEXT NOT NULL, 
            quantidade INTEGER DEFAULT 1, 
            status TEXT DEFAULT "Pendente em Cotação", 
            preco_cotado REAL DEFAULT 0, 
            potencia_cotada REAL DEFAULT 0, 
            depreciacao_sugerida REAL DEFAULT 0, 
            vida_util_sugerida INTEGER DEFAULT 120,
            data_requisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_produto TEXT UNIQUE NOT NULL, nome_produto TEXT NOT NULL, custo_total_fabricacao REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS estrutura_produto (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL, maquina_id INTEGER, material_id INTEGER, tempo_processo_min REAL DEFAULT 0, quantidade_material REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS formacao_precos (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER UNIQUE NOT NULL, imposto_municipal REAL DEFAULT 0, imposto_estadual REAL DEFAULT 0, imposto_federal REAL DEFAULT 0, margem_lucro REAL DEFAULT 0, preco_venda_final REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS estoque_produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER UNIQUE NOT NULL, quantidade_disponivel REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS pedidos_vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, desconto_percentual REAL DEFAULT 0, observacoes TEXT, data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS ordens_processo (id INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id INTEGER NOT NULL, numero_operacao TEXT NOT NULL, maquina_name TEXT NOT NULL, codigo_produto TEXT NOT NULL, nome_produto TEXT NOT NULL, data_entrada TEXT NOT NULL, tempo_estimado_min REAL NOT NULL, data_saida TEXT NOT NULL, operador_nome TEXT DEFAULT "Pendente", status TEXT DEFAULT "Na Fila", custo_operacao REAL DEFAULT 0.0, FOREIGN KEY(pedido_id) REFERENCES pedidos_vendas(id))')
    conn.commit()
    conn.close()

if not os.path.exists(DATABASE):
    init_db()

def calcular_caixa_disponivel(conn):
    """Função Contábil Interna para calcular o saldo dinâmico atualizado do Giro em todas as telas"""
    ult_imovel = conn.execute('SELECT capital_inicial_negocio, aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    if not ult_imovel: return 0.0, 0.0
    capital_inicial = float(ult_imovel['capital_inicial_negocio'])
    aluguel_fixo = float(ult_imovel['aluguel_regional'])
    investido_maquinas = conn.execute('SELECT COALESCE(SUM(preco_compra), 0) AS total FROM maquinas').fetchone()['total']
    comprado_materiais = conn.execute('SELECT COALESCE(SUM(preco_unidade * volume_disponivel), 0) AS total FROM materiais').fetchone()['total']
    faturamento = conn.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS total FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()['total']
    folha_rh = conn.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) AS total FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''").fetchone()['total']
    caixa_atual = capital_inicial - investido_maquinas - comprado_materiais + faturamento - folha_rh - aluguel_fixo
    return caixa_atual, capital_inicial
    




@app.route('/inicializar_simulador', methods=['POST'])
def inicializar_simulador():
    nome_empresa = request.form.get('nome_empresa', 'Empresa Simulada S/A')
    try: capital_inicial = float(request.form.get('capital_inicial', 0))
    except ValueError: capital_inicial = 0.0
    
    conn = get_db_connection()
    conn.execute('DELETE FROM investimentos_imobiliarios')
    conn.execute('DELETE FROM maquinas')
    conn.execute('DELETE FROM materiais')
    conn.execute('DELETE FROM produtos')
    conn.execute('DELETE FROM estrutura_produto')
    conn.execute('DELETE FROM formacao_precos')
    conn.execute('DELETE FROM estoque_produtos')
    conn.execute('DELETE FROM pedidos_vendas')
    conn.execute('DELETE FROM ordens_processo')
    conn.execute('DELETE FROM requisicoes_compras')
    
    # CORRIGIDO: Inseridos os campos obrigatórios NOT NULL com strings padrão para evitar estouro de restrição do SQLite
    conn.execute('''
        INSERT INTO investimentos_imobiliarios 
        (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio)
        VALUES (?, 'Não Definido', 'Não Definido', 0.0, 11.39, 0.0, 0.0, 0.0, ?)
    ''', (nome_empresa, capital_inicial))
    conn.commit()
    conn.close()
    
    flash(f'Empresa {nome_empresa} inicializada com orçamento de R$ {capital_inicial:,.2f}!', 'success')
    return redirect(url_for('estrutura'))


@app.route('/estrutura')
def estrutura():
    conn = get_db_connection()
    registros = conn.execute('SELECT * FROM investimentos_imobiliarios').fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('estrutura.html', taxa_atual=11.39, registros=registros, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_estrutura', methods=['POST'])
def salvar_estrutura():
    conn = get_db_connection()
    ultimo_registro = conn.execute('SELECT capital_inicial_negocio FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    capital_fixado = float(ultimo_registro['capital_inicial_negocio']) if ultimo_registro else 0.0
    conn.execute('''
        INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (request.form.get('turma_nome', 'Grupo Geral'), request.form.get('cidade_regiao', 'Curitiba'), request.form.get('bairro_imovel', 'Centro'), float(request.form.get('area_imovel') or 0), float(request.form.get('taxa_selic') or 11.39), float(request.form.get('valor_imovel_estimado') or 0), float(request.form.get('aluguel_regional') or 0), float(request.form.get('perc_acionistas') or 0), capital_fixado))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))
@app.route('/alterar_estrutura/<int:id>', methods=['POST'])
def alterar_estrutura(id):
    conn = get_db_connection()
    ultimo_registro = conn.execute('SELECT capital_inicial_negocio FROM investimentos_imobiliarios WHERE id=?', (id,)).fetchone()
    capital_fixado = float(ultimo_registro['capital_inicial_negocio']) if ultimo_registro else 0.0
    conn.execute('''
        UPDATE investimentos_imobiliarios SET turma_nome=?, cidade_regiao=?, bairro_imovel=?, area_imovel=?, taxa_selic=?, valor_imovel_estimado=?, aluguel_regional=?, perc_acionistas=?, capital_inicial_negocio=? WHERE id=?
    ''', (request.form.get('turma_nome', 'Grupo Geral'), request.form.get('cidade_regiao', 'Curitiba'), request.form.get('bairro_imovel', 'Centro'), float(request.form.get('area_imovel') or 0), float(request.form.get('taxa_selic') or 11.39), float(request.form.get('valor_imovel_estimado') or 0), float(request.form.get('aluguel_regional') or 0), float(request.form.get('perc_acionistas') or 0), capital_fixado, id))
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

@app.route('/maquinas')
def maquinas():
    conn = get_db_connection()
    m_dados = conn.execute('SELECT * FROM maquinas').fetchall()
    ult = conn.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    base = ult['aluguel_regional'] if ult else 0
    minutos_padrao_mes = 44 * 4.33 * 60
    return render_template('maquinas.html', maquinas=m_dados, custo_minuto_estrutural=base/minutos_padrao_mes if base > 0 else 0, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_maquina', methods=['POST'])
def salvar_maquina():
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana, vida_util_meses) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (request.form.get('nome_equipamento', 'Equipamento'), float(request.form.get('potencia') or 0), float(request.form.get('consumo_eletrico') or 0), request.form.get('velocidade', 'N/A'), request.form.get('avanco', 'N/A'), float(request.form.get('comprimento_max') or 0), float(request.form.get('diametro_max') or 0), int(request.form.get('frequencia_manutencao') or 500), int(request.form.get('horas_trabalhadas') or 0), float(request.form.get('preco_compra') or 0), float(request.form.get('depreciacao_mensal') or 0), float(request.form.get('valor_venda_final') or 0), float(request.form.get('custo_minuto_maquina') or 0), request.form.get('operador_nome', 'Posto Vago - Aguardando MOD'), float(request.form.get('custo_minuto_operador') or 0.0), float(request.form.get('salario_base') or 0.0), float(request.form.get('valor_adicionais') or 0.0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), int(request.form.get('vida_util_meses') or 120)))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))
@app.route('/alterar_maquina/<int:id>', methods=['POST'])
def alterar_maquina(id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE maquinas SET nome_equipamento=?, potencia=?, consumo_eletrico=?, velocidade=?, avanco=?, comprimento_max=?, diametro_max=?, frequencia_manutencao=?, horas_trabalhadas=?, preco_compra=?, depreciacao_mensal=?, valor_venda_final=?, custo_minuto_maquina=?, operador_nome=?, custo_minuto_operador=?, salario_base=?, valor_adicionais=?, turno_trabalho=?, dia_semana=?, vida_util_meses=? WHERE id=?
    ''', (request.form.get('nome_equipamento', 'Equipamento'), float(request.form.get('potencia') or 0), float(request.form.get('consumo_eletrico') or 0), request.form.get('velocidade', 'N/A'), request.form.get('avanco', 'N/A'), float(request.form.get('comprimento_max') or 0), float(request.form.get('diametro_max') or 0), int(request.form.get('frequencia_manutencao') or 500), int(request.form.get('horas_trabalhadas') or 0), float(request.form.get('preco_compra') or 0), float(request.form.get('depreciacao_mensal') or 0), float(request.form.get('valor_venda_final') or 0), float(request.form.get('custo_minuto_maquina') or 0), request.form.get('operador_nome', 'Posto Vago - Aguardando MOD'), float(request.form.get('custo_minuto_operador') or 0.0), float(request.form.get('salario_base') or 0.0), float(request.form.get('valor_adicionais') or 0.0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), int(request.form.get('vida_util_meses') or 120), id))
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

@app.route('/rh')
def rh():
    conn = get_db_connection()
    colaboradores = conn.execute("SELECT * FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''").fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('rh.html', colaboradores=colaboradores, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_colaborador', methods=['POST'])
def salvar_colaborador():
    conn = get_db_connection()
    posto_vago = conn.execute("SELECT id FROM maquinas WHERE operador_nome = 'Posto Vago - Aguardando MOD' LIMIT 1").fetchone()
    if posto_vago:
        conn.execute('UPDATE maquinas SET operador_nome=?, salario_base=?, valor_adicionais=?, turno_trabalho=?, dia_semana=?, custo_minuto_operador=? WHERE id=?', (request.form.get('nome_completo', 'Colaborador'), float(request.form.get('salario_base') or 0), float(request.form.get('valor_adicionais') or 0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), float(request.form.get('custo_minuto_operador') or 0), posto_vago['id']))
        conn.commit()
        flash('MOD Alocado na planta com sucesso!', 'success')
    else:
        conn.execute("INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana) VALUES ('Posto de Apoio / Indireto', 0, 0, 'N/A', 'N/A', 0, 0, 9999, 0, 0, 0, 0, 0, ?, ?, ?, ?, ?, ?)", (request.form.get('nome_completo', 'Colaborador'), float(request.form.get('custo_minuto_operador') or 0), float(request.form.get('salario_base') or 0), float(request.form.get('valor_adicionais') or 0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular')))
        conn.commit()
        flash('Quadro Expandido: Mão de Obra Indireta cadastrada.', 'success')
    conn.close()
    return redirect(url_for('rh'))
@app.route('/imprimir_holerite/<int:id>/<string:tipo>')
def imprimir_holerite(id, tipo):
    conn = get_db_connection()
    col = conn.execute('SELECT * FROM maquinas WHERE id = ?', (id,)).fetchone()
    conn.close()
    if not col or col['operador_nome'] == 'Posto Vago - Aguardando MOD': return "Colaborador não localizado."
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
    inss = 0.0
    if total_proventos <= 1518.00: inss = total_proventos * 0.075
    elif total_proventos <= 2793.88: inss = (total_proventos * 0.09) - 22.77
    elif total_proventos <= 4190.83: inss = (total_proventos * 0.12) - 106.59
    elif total_proventos <= 8157.41: inss = (total_proventos * 0.14) - 190.40
    else: inss = 951.64
    base_irrf = total_proventos - inss
    irrf = 0.0
    if base_irrf <= 2259.20: irrf = 0.0
    elif base_irrf <= 2826.65: irrf = (base_irrf * 0.075) - 169.44
    elif base_irrf <= 3751.05: irrf = (base_irrf * 0.15) - 381.44
    elif base_irrf <= 4664.68: irrf = (base_irrf * 0.225) - 662.77
    else: irrf = (base_irrf * 0.275) - 896.00
    vale_transporte = salario_base * 0.06 if col['turno_trabalho'] == 'Diurno' else 0.0
    total_descontos = inss + irrf + vale_transporte
    valor_liquido = total_proventos - total_descontos
    dados_holerite = {"tipo_recibo": titulo_recibo, "nome": col['operador_nome'], "cargo": f"CBO {col['id']} - Posto Ativo", "principal_nome": provento_principal_nome, "principal_valor": provento_principal_valor, "adicionais": adicionais, "he": horas_extras_acumuladas, "inss": inss, "irrf": irrf, "vt": vale_transporte, "total_proventos": total_proventos, "total_descontos": total_descontos, "liquido": valor_liquido}
    return render_template('imprimir_holerite.html', h=dados_holerite)

@app.route('/calcular_rescisao/<int:id>/<string:tipo>', methods=['POST'])
def calcular_rescisao(id, tipo):
    conn = get_db_connection()
    col = conn.execute('SELECT * FROM maquinas WHERE id = ?', (id,)).fetchone()
    if col:
        base = float(col['salario_base'] or 1412.00)
        total_rescisao = base * 0.5 if tipo == "justa_causa" else (base * 1.1 if tipo == "voluntaria" else base * 2.40)
        conn.execute('UPDATE maquinas SET operador_nome = "Posto Vago - Aguardando MOD", custo_minuto_operador = 0.0, salario_base = 0.0, valor_adicionais = 0.0 WHERE id = ?', (id,))
        conn.commit()
        flash(f"Rescisão Concluída. Valor Líquido Homologado: R$ {total_rescisao:,.2f}", "warning")
    conn.close()
    return redirect(url_for('rh'))

@app.route('/orcamentos')
def orcamentos():
    conn = get_db_connection()
    maqs = conn.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas').fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('orcamentos.html', maquinas=maqs, caixa_disponivel=caixa, capital_inicial=total)
@app.route('/salvar_orcamento_calculado', methods=['POST'])
def salvar_orcamento_calculado():
    tipo = request.form.get('tipo_produto')
    nome_item = request.form.get('nome_item')
    lote = int(request.form.get('lote') or 1)
    preco_final = float(request.form.get('preco_final_calculado') or 0.0)
    tempo_total = float(request.form.get('tempo_estimado_total') or 0.0)
    
    sku = f"ORC-{tipo.upper()}-{int(preco_final)%1000}"
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO produtos (codigo_produto, nome_produto) VALUES (?, ?)', (sku, nome_item))
        prod_id = conn.execute('SELECT id FROM produtos WHERE codigo_produto = ?', (sku,)).fetchone()['id']
        conn.execute('INSERT INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (?, ?, ?, ?, ?, ?)', (prod_id, float(request.form.get('iss') or 5), float(request.form.get('icms') or 18), float(request.form.get('federal') or 9.25), float(request.form.get('margem') or 25), preco_final / lote))
        conn.execute('INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES (?, ?, 0, "SOB ENCOMENDA - Fila PCP")', (prod_id, lote))
        conn.commit()
        flash('Orçamento validado! Engenharia e Demanda comercial inseridas no PCP.', 'success')
    except sqlite3.IntegrityError: flash('Erro: Orçamento já processado.', 'danger')
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/requisicoes')
def requisicoes():
    conn = get_db_connection()
    reqs = conn.execute('SELECT * FROM requisicoes_compras ORDER BY id DESC').fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('requisicoes.html', requisicoes=reqs, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/compras')
def compras():
    conn = get_db_connection()
    cotadas = conn.execute("SELECT * FROM requisicoes_compras WHERE status LIKE 'Cotado%' ORDER BY id DESC").fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('compras.html', requisicoes_cotadas=cotadas, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_requisicao', methods=['POST'])
def salvar_requisicao():
    conn = get_db_connection()
    conn.execute('INSERT INTO requisicoes_compras (equipamento_tipo, especificacao_desejada, quantidade) VALUES (?, ?, ?)', (request.form.get('equipamento_tipo', 'Equipamento'), request.form.get('especificacao_desejada', 'N/A'), int(request.form.get('quantidade') or 1)))
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
        preco, pot, dep = 45000.0, 5.5, 375.0
        
        # MEGA EXPANSÃO INTEGRAÇÃO MÁQUINAS SOLICITADAS
        if 'torno' in tipo or 'cnc' in tipo or 'centro de usinagem' in tipo: preco, pot, dep = (620000.0, 35.0, 5100.0) if '5 eixos' in esp else (290000.0, 18.0, 2400.0)
        elif 'forno' in tipo or 'têmpera' in tipo: preco, pot, dep = (180000.0, 45.0, 1500.0)
        elif 'prensa' in tipo: preco, pot, dep = (220000.0, 22.0, 1800.0)
        elif 'solda' in tipo: preco, pot, dep = (15000.0, 7.5, 125.0)
        elif 'compressor' in tipo: preco, pot, dep = (35000.0, 11.0, 290.0)
        elif 'jato' in tipo: preco, pot, dep = (28000.0, 5.5, 230.0)
        elif 'material' in tipo or 'insumo' in tipo: preco, pot, dep = (2500.0 if 'tubo' in esp else 850.0), 0.0, 0.0

        conn.execute('UPDATE requisicoes_compras SET preco_cotado=?, potencia_cotada=?, depreciacao_sugerida=?, status="Cotado - Aguardando Confirmação" WHERE id=?', (preco, pot, dep, id))
        conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/efetivar_compra/<int:id>', methods=['POST'])
def efetivar_compra(id):
    conn = get_db_connection()
    req = conn.execute('SELECT * FROM requisicoes_compras WHERE id = ?', (id,)).fetchone()
    ult_imovel = conn.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    aluguel_mensal = ult_imovel['aluguel_regional'] if ult_imovel else 0.0
    minutos_operacionais = 44 * 4.33 * 60
    custo_aluguel_minuto = aluguel_mensal / minutos_operacionais
    if req:
        preco = float(request.form.get('preco_final') or 0.0)
        pot = float(request.form.get('potencia_final') or 0.0)
        dep = float(request.form.get('depreciacao_final') or 0.0)
        vida = int(request.form.get('vida_util_meses') or 120)
        if "Máquina" in req['equipamento_tipo'] or "Ativo" in req['equipamento_tipo']:
            c_mm = (dep / minutos_operacionais) + ((pot * 0.75) / 60) + custo_aluguel_minuto
            conn.execute('INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, vida_util_meses) VALUES (?, ?, ?, "3000", "15000", 1000, 500, 1000, 0, ?, ?, ?, ?, "Posto Vago - Aguardando MOD", 0.0, ?)', (f"{req['especificacao_desejada']}", pot, pot * 0.7, preco, dep, preco * 0.2, c_mm, vida))
        else:
            sku_gerado = f"SKU-{req['id']}"
            conn.execute("INSERT OR REPLACE INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (?, ?, ?, 'Lote Adquirido', ?)", (sku_gerado, req['especificacao_desejada'], preco/float(req['quantidade']), float(req['quantidade'])))
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
@app.route('/inventario')
@app.route('/materiais')
def materiais():
    conn = get_db_connection()
    mats = conn.execute('SELECT * FROM materiais').fetchall()
    itens_acabados = conn.execute('SELECT p.id, p.codigo_produto, p.nome_produto, COALESCE(ep.quantidade_disponivel, 0) AS quantidade_disponivel FROM produtos p LEFT JOIN estoque_produtos ep ON p.id = ep.produto_id').fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('materiais.html', materiais=mats, estoque_itens=itens_acabados, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_material', methods=['POST'])
def salvar_material():
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (?, ?, ?, ?, ?)', (request.form.get('codigo_material', 'SKU').strip(), request.form.get('nome_material', 'Insumo').strip(), float(request.form.get('preco_unidade') or 0), request.form.get('dimensoes', 'N/A'), float(request.form.get('volume_disponivel') or 0)))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError: return "Erro: SKU duplicado!"
    return redirect(url_for('materiais'))

@app.route('/alterar_material/<int:id>', methods=['POST'])
def alterar_material(id):
    conn = get_db_connection()
    conn.execute('UPDATE materiais SET codigo_material=?, nome_material=?, preco_unidade=?, dimensoes=?, volume_disponivel=? WHERE id=?', (request.form.get('codigo_material', 'SKU').strip(), request.form.get('nome_material', 'Insumo').strip(), float(request.form.get('preco_unidade') or 0), request.form.get('dimensoes', 'N/A'), float(request.form.get('volume_disponivel') or 0), id))
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

@app.route('/engenharia')
def engenharia():
    conn = get_db_connection()
    prods = conn.execute('SELECT * FROM produtos').fetchall()
    maqs = conn.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas').fetchall()
    mats = conn.execute('SELECT id, nome_material, preco_unidade FROM materiais').fetchall()
    comps = conn.execute('SELECT ep.*, p.nome_produto, p.codigo_produto, m.nome_equipamento, mat.nome_material FROM estrutura_produto ep JOIN produtos p ON ep.produto_id = p.id LEFT JOIN maquinas m ON ep.maquina_id = m.id LEFT JOIN materiais mat ON ep.material_id = mat.id').fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('engenharia.html', produtos=prods, maquinas=maqs, materiais=mats, composicoes=comps, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO produtos (codigo_produto, nome_produto) VALUES (?, ?)', (request.form.get('codigo_produto', 'PROD').strip(), request.form.get('nome_produto', 'Acabado').strip()))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError: return "Erro: Produto duplicado."
    return redirect(url_for('engenharia'))

@app.route('/vincular_estrutura', methods=['POST'])
def vincular_estrutura():
    conn = get_db_connection()
    maquina_id = request.form.get('maquina_id')
    material_id = request.form.get('material_id')
    conn.execute('INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material) VALUES (?, ?, ?, ?, ?)', (int(request.form.get('produto_id') or 0), int(maquina_id) if maquina_id and maquina_id.isdigit() else None, int(material_id) if material_id and material_id.isdigit() else None, float(request.form.get('tempo_processo_min') or 0), float(request.form.get('quantidade_material') or 0)))
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
@app.route('/solicitar_producao_pcp/<int:pedido_id>', methods=['POST'])
def solicitar_producao_pcp(pedido_id):
    conn = get_db_connection()
    existe = conn.execute('SELECT id FROM ordens_processo WHERE pedido_id = ?', (pedido_id,)).fetchone()
    if not existe:
        ped = conn.execute('SELECT pv.*, p.codigo_produto, p.nome_produto FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.id = ?', (pedido_id,)).fetchone()
        if ped:
            rots = conn.execute('SELECT ep.*, m.nome_equipamento, m.custo_minuto_maquina, m.operador_nome FROM estrutura_produto ep LEFT JOIN maquinas m ON ep.maquina_id = m.id WHERE ep.produto_id = ? ORDER BY ep.id ASC', (ped['produto_id'],)).fetchall()
            ponteiro_tempo = datetime.datetime.now()
            tempo_setup_fixo = 15
            for idx, r in enumerate(rots):
                tempo_lote_min = (float(r['tempo_processo_min'] or 0) * int(ped['quantidade'])) + tempo_setup_fixo
                custo_total_operacao = tempo_lote_min * float(r['custo_minuto_maquina'] or 0.15)
                status_inicial = "Na Fila [GARGALO OPERACIONAL]" if tempo_lote_min > 480 else "Na Fila"
                entrada_str = ponteiro_tempo.strftime("%d/%m/%Y %H:%M")
                saida_op = ponteiro_tempo + datetime.timedelta(minutes=tempo_lote_min)
                saida_str = saida_op.strftime("%d/%m/%Y %H:%M")
                conn.execute('INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_name, codigo_produto, nome_produto, data_entrada, tempo_estimado_min, data_saida, status, custo_operacao, operador_nome) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (pedido_id, f"OP {(idx+1)*10}", r['nome_equipamento'] or 'Bancada Manual', ped['codigo_produto'], ped['nome_produto'], entrada_str, tempo_lote_min, saida_str, status_inicial, custo_total_operacao, r['operador_nome'] or 'Pendente'))
                ponteiro_tempo = saida_op
            conn.commit()
        flash('Ordem de Produção transmitida com sucesso para o painel do PCP!', 'success')
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/abastecer_estoque_pcp', methods=['POST'])
def abastecer_estoque_pcp():
    prod_id = int(request.form.get('produto_id') or 0)
    pedido_id = int(request.form.get('pedido_id') or 0)
    qtd = float(request.form.get('quantidade_abastecer') or 0)
    conn = get_db_connection()
    ops_existentes = conn.execute('SELECT COUNT(*) as total FROM ordens_processo WHERE pedido_id = ?', (pedido_id,)).fetchone()['total']
    ops_pendentes = conn.execute("SELECT COUNT(*) as pendentes FROM ordens_processo WHERE pedido_id = ? AND status NOT LIKE 'Finalizado%'", (pedido_id,)).fetchone()['pendentes']
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
    conn.execute('UPDATE ordens_processo SET operador_nome = ?, status = "Finalizado" WHERE id = ?', (request.form.get('operador_nome', 'Operador'), id))
    conn.commit()
    conn.close()
    return redirect(url_for('pcp'))

@app.route('/imprimir_nf/<int:pedido_id>')
def imprimir_nf(pedido_id):
    conn = get_db_connection()
    ped = conn.execute('SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id WHERE pv.id = ?', (pedido_id,)).fetchone()
    conn.close()
    if not ped: return "Nota Fiscal não encontrada."
    sub = ped['preco_venda_final'] * ped['quantidade']
    v_desc = sub * (ped['desconto_percentual'] / 100.0)
    liq = sub - v_desc
    v_mun = liq * (ped['imposto_municipal'] / 100.0)
    v_est = liq * (ped['imposto_estadual'] / 100.0)
    v_fed = liq * (ped['imposto_federal'] / 100.0)
    return render_template('nota_fiscal.html', p=ped, subtotal=sub, v_desconto=v_desc, total_liquido=liq, v_municipal=v_mun, v_estadual=v_est, v_federal=v_fed, total_impostos=v_mun+v_est+v_fed)
@app.route('/financeiro')
def financeiro():
    conn = get_db_connection()
    faturamento_bruto = conn.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS total FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()['total']
    despesa_pessoal_bruta = conn.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) AS total FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''").fetchone()['total']
    impostos_vendas = conn.execute('SELECT COALESCE(SUM((fp.preco_venda_final * pv.quantidade) * ((fp.imposto_municipal + fp.imposto_estadual + fp.imposto_federal) / 100.0)), 0) AS total FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()['total']
    ult_imovel = conn.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1').fetchone()
    custo_aluguel_fixo = ult_imovel['aluguel_regional'] if ult_imovel else 0.0
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    total_encargos = impostos_vendas + (despesa_pessoal_bruta * 0.20)
    return render_template('financeiro.html', faturamento=faturamento_bruto, custo_pessoal=despesa_pessoal_bruta, impostos=total_encargos, saldo_liquido=caixa, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/pagar_dividendos', methods=['POST'])
def pagar_dividendos():
    percentual = float(request.form.get('percentual_lucro' or 25))
    flash(f'Distribuição de {percentual}% dos dividendos processada!', 'success')
    return redirect(url_for('financeiro'))

@app.route('/roi')
def roi():
    conn = get_db_connection()
    v_dados = conn.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS receita_bruta, COALESCE(SUM(pv.quantidade), 0) AS total_pecas FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id').fetchone()
    invs = conn.execute('SELECT COALESCE(SUM(valor_imovel_estimado + capital_inicial_negocio), 0) AS capital_total, COALESCE(SUM(aluguel_regional), 0) AS aluguel FROM investimentos_imobiliarios').fetchone()
    despesa_pessoal = conn.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) AS total FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''").fetchone()['total']
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    rec, pecas, cap, aluguel = v_dados['receita_bruta'], v_dados['total_pecas'], invs['capital_total'], invs['aluguel']
    sobra = rec - despesa_pessoal - aluguel
    payback_meses = (cap / sobra) if sobra > 0 else 0.0
    return render_template('roi.html', receita=rec, total_pecas=pecas, capital=cap, payback_real=payback_meses, lucro_acionistas=rec*0.25, caixa_disponivel=caixa, capital_inicial=total)

if __name__ == '__main__':
    app.run(debug=True)
