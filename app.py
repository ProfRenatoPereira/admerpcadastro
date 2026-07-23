import os
import sqlite3
import datetime
import math
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from whitenoise import WhiteNoise
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

DATABASE = 'database.db'

CATALOGO_MAQUINAS = {
    'cnc_romi': {'nome': 'Centro de Usinagem CNC ROMI 5X', 'pot': 22.0, 'cons': 15.4, 'vel': '8000', 'avan': '20000', 'comp': 1000, 'diam': 500, 'mnt': 1000, 'preco': 620000.0, 'dep': 5166.66, 'venda': 124000.0, 'operador': 'Carlos Souza (Técnico CNC)', 'custo_op': 0.45, 'salario': 3100.0, 'adic': 930.0, 'vida': 120},
    'prensa_100t': {'nome': 'Prensa Hidráulica Industrial 100T', 'pot': 15.0, 'cons': 10.5, 'vel': '60', 'avan': '1200', 'comp': 800, 'diam': 800, 'mnt': 1500, 'preco': 220000.0, 'dep': 1833.33, 'venda': 44000.0, 'operador': 'Marcos Lima (Meio Oficial)', 'custo_op': 0.22, 'salario': 1850.0, 'adic': 282.40, 'vida': 120},
    'forno_tempera': {'nome': 'Forno de Têmpera Contínua', 'pot': 45.0, 'cons': 38.0, 'vel': '1200°C', 'avan': 'Automático', 'comp': 1500, 'diam': 600, 'mnt': 800, 'preco': 180000.0, 'dep': 1500.0, 'venda': 36000.0, 'operador': 'Aline Dias (Tratadora Térmica)', 'custo_op': 0.40, 'salario': 2900.0, 'adic': 564.80, 'vida': 120},
    'forno_revenimento': {'nome': 'Forno de Revenimento Industrial', 'pot': 30.0, 'cons': 24.0, 'vel': '700°C', 'avan': 'Estático', 'comp': 1200, 'diam': 600, 'mnt': 800, 'preco': 120000.0, 'dep': 1000.0, 'venda': 24000.0, 'operador': 'Pedro Alves (Operador Forno)', 'custo_op': 0.35, 'salario': 2400.0, 'adic': 282.40, 'vida': 120},
    'solda_mig_tig': {'nome': 'Estação de Solda MIG/TIG Industrial', 'pot': 7.5, 'cons': 5.2, 'vel': 'N/A', 'avan': 'Manual', 'comp': 500, 'diam': 0, 'mnt': 300, 'preco': 15000.0, 'dep': 125.0, 'venda': 3000.0, 'operador': 'Bruno Silva (Soldador TIG)', 'custo_op': 0.38, 'salario': 2600.0, 'adic': 564.80, 'vida': 120},
    'compressor_parafuso': {'nome': 'Compressor de Ar de Parafuso', 'pot': 11.0, 'cons': 8.8, 'vel': '10 bar', 'avan': 'Contínuo', 'comp': 600, 'diam': 400, 'mnt': 600, 'preco': 35000.0, 'dep': 291.66, 'venda': 7000.0, 'operador': 'Posto de Apoio / Indireto', 'custo_op': 0.0, 'salario': 0.0, 'adic': 0.0, 'vida': 120},
    'jato_areia': {'nome': 'Jato de Areia Pressurizado', 'pot': 5.5, 'cons': 4.1, 'vel': 'N/A', 'avan': 'Manual', 'comp': 800, 'diam': 600, 'mnt': 400, 'preco': 28000.0, 'dep': 233.33, 'venda': 5600.0, 'operador': 'Auxiliar de Jateamento', 'custo_op': 0.20, 'salario': 1512.0, 'adic': 282.40, 'vida': 120}
}

CATALOGO_MATERIAIS = {
    'tub_mec': {'cod': 'TUB-MEC-ST52', 'nome': 'Tubo Mecânico de Alta Resistência ST52', 'preco': 45.50, 'dim': 'Ø 3 pol x 2000mm', 'vol': 150.0},
    'tar_aco': {'cod': 'TAR-ACO-4140', 'nome': 'Tarugo Redondo Aço Liga SAE 4140', 'preco': 28.90, 'dim': 'Ø 2 pol x 1000mm', 'vol': 300.0},
    'bar_lat': {'cod': 'BAR-LAT-CLA', 'nome': 'Barra de Latão de Fácil Usinagem CLA', 'preco': 55.20, 'dim': 'Ø 1 pol x 3000mm', 'vol': 80.0},
    'chapa_a36': {'cod': 'CHA-ACO-A36', 'nome': 'Chapa de Aço Carbono ASTM A36 3mm', 'preco': 18.50, 'dim': '1000x2000mm', 'vol': 200.0},
    'gas_mig': {'cod': 'INS-GAS-MIG', 'nome': 'Cilindro Mistura Gás Solda Argônio/CO2', 'preco': 120.00, 'dim': 'Cilindro 50L', 'vol': 15.0}
}

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(db_url)
        conn.cursor_factory = DictCursor
        return conn  # <--- Corrigido: Agora retorna a conexão do Postgres corretamente
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Detecta se a conexão atual é PostgreSQL (Neon) ou SQLite local
    is_postgres = hasattr(conn, 'cursor_factory')

    # Altera dinamicamente o incremento de ID baseado no banco conectado
    id_syntax = "id SERIAL PRIMARY KEY" if is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    timestamp_syntax = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_postgres else "TEXT DEFAULT CURRENT_TIMESTAMP"

    # Criação das tabelas com a sintaxe corrigida para ambos os bancos
    cursor.execute(f'CREATE TABLE IF NOT EXISTS usuarios ({id_syntax}, usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, aprovado INTEGER DEFAULT 0)')
    
    cursor.execute(f'CREATE TABLE IF NOT EXISTS investimentos_imobiliarios ({id_syntax}, turma_nome TEXT NOT NULL, cidade_regiao TEXT NOT NULL, bairro_imovel TEXT NOT NULL, area_imovel REAL NOT NULL, taxa_selic REAL NOT NULL, valor_imovel_estimado REAL NOT NULL, aluguel_regional REAL NOT NULL, perc_acionistas REAL NOT NULL, capital_inicial_negocio REAL DEFAULT 0.0)')
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS maquinas (
            {id_syntax}, 
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
    """)
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS materiais ({id_syntax}, codigo_material TEXT UNIQUE NOT NULL, nome_material TEXT NOT NULL, preco_unidade REAL NOT NULL, dimensoes TEXT, volume_disponivel REAL NOT NULL)")
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS requisicoes_compras ({id_syntax}, equipamento_tipo TEXT NOT NULL, especificacao_desejada TEXT NOT NULL, quantidade INTEGER DEFAULT 1, status TEXT DEFAULT 'Pendente em Cotação', preco_cotado REAL DEFAULT 0, potencia_cotada REAL DEFAULT 0, depreciacao_sugerida REAL DEFAULT 0, vida_util_sugerida INTEGER DEFAULT 120, data_requisicao {timestamp_syntax})")
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS produtos ({id_syntax}, codigo_produto TEXT UNIQUE NOT NULL, nome_produto TEXT NOT NULL, custo_total_fabricacao REAL DEFAULT 0)")
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS estrutura_produto ({id_syntax}, produto_id INTEGER NOT NULL, maquina_id INTEGER, material_id INTEGER, tempo_processo_min REAL DEFAULT 0, quantidade_material REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))")
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS formacao_precos ({id_syntax}, produto_id INTEGER UNIQUE NOT NULL, imposto_municipal REAL DEFAULT 0, imposto_estadual REAL DEFAULT 0, imposto_federal REAL DEFAULT 0, margem_lucro REAL DEFAULT 0, preco_venda_final REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))")
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS estoque_produtos ({id_syntax}, produto_id INTEGER UNIQUE NOT NULL, quantidade_disponivel REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))")
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS pedidos_vendas ({id_syntax}, produto_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, desconto_percentual REAL DEFAULT 0, observacoes TEXT, data_pedido {timestamp_syntax}, FOREIGN KEY(produto_id) REFERENCES produtos(id))")
    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS ordens_processo ({id_syntax}, pedido_id INTEGER NOT NULL, numero_operacao TEXT NOT NULL, maquina_name TEXT NOT NULL, codigo_produto TEXT NOT NULL, nome_produto TEXT NOT NULL, data_entrada TEXT NOT NULL, tempo_estimado_min REAL NOT NULL, data_saida TEXT NOT NULL, operador_nome TEXT DEFAULT 'Pendente', status TEXT DEFAULT 'Na Fila', custo_operacao REAL DEFAULT 0.0, FOREIGN KEY(pedido_id) REFERENCES pedidos_vendas(id))")
    
    conn.commit()

    # Executa a checagem de dados iniciais de forma compatível
    cursor.execute('SELECT COUNT(*) AS total FROM investimentos_imobiliarios')
    check = cursor.fetchone()
    
    total_registros = check['total'] if (is_postgres and isinstance(check, dict)) or hasattr(check, 'keys') else check

    if total_registros == 0:
        cursor.execute('''
            INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio)
            VALUES ('Metalúrgica Modelo S/A - Cenário Base', 'Curitiba CIC', 'CIC (Distrito Industrial)', 450.00, 11.39, 3825000.00, 13500.00, 25.0, 500000.00)
        ''')
        conn.commit()

    cursor.close()
    conn.close()

# Correção: Inicializa o banco de forma independente do arquivo físico para funcionar no Neon
init_db()

def calcular_caixa_disponivel(conn):
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'cursor_factory')

    # Correção: Usa o cursor para executar as consultas (obrigatório no PostgreSQL)
    cursor.execute('SELECT capital_inicial_negocio, aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ult_imovel = cursor.fetchone()
    
    if not ult_imovel: 
        cursor.close()
        return 0.0, 0.0
        
    capital_inicial = float(ult_imovel['capital_inicial_negocio'] or 0.0)
    aluguel_fixo = float(ult_imovel['aluguel_regional'] or 0.0)
    
    cursor.execute('SELECT COALESCE(SUM(preco_compra), 0) AS total FROM maquinas')
    investido_maquinas = cursor.fetchone()['total']
    
    cursor.execute('SELECT COALESCE(SUM(preco_unidade * volume_disponivel), 0) AS total FROM materiais')
    comprado_materiais = cursor.fetchone()['total']
    
    cursor.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS total FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    faturamento = cursor.fetchone()['total']
    
    # Correção: Ajuste de aspas simples para compatibilidade estrita com o PostgreSQL
    cursor.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) AS total FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    folha_rh = cursor.fetchone()['total']
    
    caixa_atual = capital_inicial - float(investido_maquinas) - float(comprado_materiais) + float(faturamento) - float(folha_rh) - aluguel_fixo
    
    cursor.close()  # Fecha o cursor de forma segura para não estourar conexões no Neon
    return caixa_atual, capital_inicial

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login_validar', methods=['POST'])
def login_validar():
    user_input = request.form.get('username')
    pass_input = request.form.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define dinamicamente o placeholder (? para SQLite, %s para Postgres)
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT * FROM usuarios WHERE usuario = {query_param}', (user_input,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user and check_password_hash(user['senha'], pass_input):
        session['logado'] = True
        session['usuario_equipe'] = user_input
        flash('Acesso concedido com sucesso!', 'success')
    else:
        flash('Usuário ou senha inválidos.', 'danger')
    return redirect(url_for('index'))

@app.route('/professor_painel_secreto')
def professor_painel():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, usuario FROM usuarios')
    todas_equipes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('professor.html', usuarios=todas_equipes)

@app.route('/professor/resetar', methods=['POST'])
def professor_resetar():
    user_aluno = request.form.get('username')
    nova_senha = request.form.get('nova_senha')
    novo_hash = generate_password_hash(nova_senha)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'UPDATE usuarios SET senha = {query_param} WHERE usuario = {query_param}', (novo_hash, user_aluno))
    conn.commit()
    
    cursor.close()
    conn.close()
    flash(f"Sucesso! A senha da equipe '{user_aluno}' foi alterada para '{nova_senha}'.", 'success')
    return redirect(url_for('professor_painel'))

@app.route('/professor/cadastrar', methods=['POST'])
def professor_cadastrar():
    novo_user = request.form.get('novo_user').strip().lower().replace(" ", "")
    senha_inicial = request.form.get('senha_inicial')
    hash_senha = generate_password_hash(senha_inicial)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    try:
        cursor.execute(f'INSERT INTO usuarios (usuario, senha) VALUES ({query_param}, {query_param})', (novo_user, hash_senha))
        conn.commit()
        flash(f"Equipe '{novo_user}' registrada com sucesso!", 'success')
    except Exception:  # Captura erros de integridade tanto do SQLite quanto do Neon (PostgreSQL)
        flash("Erro: Essa equipe já está cadastrada.", 'danger')
        
    cursor.close()
    conn.close()
    return redirect(url_for('professor_painel'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Desconectado com sucesso.', 'success')
    return redirect(url_for('index'))

@app.route('/estrutura', methods=['GET'])
def estrutura():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM investimentos_imobiliarios')
    registros = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    
    cursor.close()
    conn.close()
    return render_template('estrutura.html', taxa_atual=11.39, registros=registros, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/inicializar_simulador', methods=['POST'])
def inicializar_simulador():
    nome_empresa = request.form.get('nome_empresa', 'Empresa Simulada S/A')
    try: 
        capital_inicial = float(request.form.get('capital_inicial', 0))
    except ValueError: 
        capital_inicial = 0.0
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Executa a limpeza preventiva de forma segura (ignora tabelas que porventura não existam)
    cursor.execute('DROP TABLE IF EXISTS investimentos_imobiliarios, maquinas, materiais, produtos, estrutura_produto, formacao_precos, estoque_produtos, pedidos_vendas, ordens_processo, requisicoes_compras CASCADE')
    conn.commit()
    cursor.close()
    conn.close()
    
    # Força a reconstrução completa e correta das tabelas no Neon
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    # Correção: Inserindo em cidade_regiao de forma compatível
    cursor.execute(f'''
        INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio)
        VALUES ({query_param}, 'Não Definido', 'Não Definido', 0.0, 11.39, 0.0, 0.0, 0.0, {query_param})
    ''', (nome_empresa, capital_inicial))
    conn.commit()
    
    cursor.close()
    conn.close()
    flash(f'Empresa {nome_empresa} inicializada com sucesso!', 'success')
    return redirect(url_for('estrutura'))

@app.route('/salvar_estrutura', methods=['POST'])
def salvar_estrutura():
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT capital_inicial_negocio FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ultimo_registro = cursor.fetchone()
    
    capital_fixado = float(ultimo_registro['capital_inicial_negocio']) if ultimo_registro else 0.0
    
    cursor.execute(f'''
        INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio) 
        VALUES ({query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param})
    ''', (request.form.get('turma_nome', 'Grupo Geral'), request.form.get('cidade_regiao', 'Curitiba'), request.form.get('bairro_imovel', 'Centro'), float(request.form.get('area_imovel') or 0), float(request.form.get('taxa_selic') or 11.39), float(request.form.get('valor_imovel_estimado') or 0), float(request.form.get('aluguel_regional') or 0), float(request.form.get('perc_acionistas') or 0), capital_fixado))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/alterar_estrutura/<int:id>', methods=['POST'])
def alterar_estrutura(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT capital_inicial_negocio FROM investimentos_imobiliarios WHERE id={query_param}', (id,))
    ultimo_registro = cursor.fetchone()
    
    capital_fixado = float(ultimo_registro['capital_inicial_negocio']) if ultimo_registro else 0.0
    
    cursor.execute(f'''
        UPDATE investimentos_imobiliarios SET turma_nome={query_param}, cidade_regiao={query_param}, bairro_imovel={query_param}, area_imovel={query_param}, taxa_selic={query_param}, valor_imovel_estimado={query_param}, aluguel_regional={query_param}, perc_acionistas={query_param}, capital_inicial_negocio={query_param} WHERE id={query_param}
    ''', (request.form.get('turma_nome', 'Grupo Geral'), request.form.get('cidade_regiao', 'Curitiba'), request.form.get('bairro_imovel', 'Centro'), float(request.form.get('area_imovel') or 0), float(request.form.get('taxa_selic') or 11.39), float(request.form.get('valor_imovel_estimado') or 0), float(request.form.get('aluguel_regional') or 0), float(request.form.get('perc_acionistas') or 0), capital_fixado, id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/deletar_estrutura/<int:id>', methods=['POST'])
def deletar_estrutura(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'DELETE FROM investimentos_imobiliarios WHERE id={query_param}', (id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/maquinas')
def maquinas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM maquinas')
    m_dados = cursor.fetchall()
    
    cursor.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ult = cursor.fetchone()
    
    caixa, total = calcular_caixa_disponivel(conn)
    
    cursor.close()
    conn.close()
    
    base = ult['aluguel_regional'] if ult else 0
    minutos_padrao_mes = 44 * 4.33 * 60
    return render_template('maquinas.html', maquinas=m_dados, custo_minuto_estrutural=base/minutos_padrao_mes if base > 0 else 0, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_maquina', methods=['POST'])
def salvar_maquina():
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'''
        INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana, vida_util_meses) 
        VALUES ({query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param})''', 
        (request.form.get('nome_equipamento', 'Equipamento'), float(request.form.get('potencia') or 0), float(request.form.get('consumo_eletrico') or 0), request.form.get('velocidade', 'N/A'), request.form.get('avanco', 'N/A'), float(request.form.get('comprimento_max') or 0), float(request.form.get('diametro_max') or 0), int(request.form.get('frequencia_manutencao') or 500), int(request.form.get('horas_trabalhadas') or 0), float(request.form.get('preco_compra') or 0), float(request.form.get('depreciacao_mensal') or 0), float(request.form.get('valor_venda_final') or 0), float(request.form.get('custo_minuto_maquina') or 0), request.form.get('operador_nome', 'Posto Vago - Aguardando MOD'), float(request.form.get('custo_minuto_operador') or 0.0), float(request.form.get('salario_base') or 0.0), float(request.form.get('valor_adicionais') or 0.0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), int(request.form.get('vida_util_meses') or 120)))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/alterar_maquina/<int:id>', methods=['POST'])
def alterar_maquina(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'''
        UPDATE maquinas SET nome_equipamento={query_param}, potencia={query_param}, consumo_eletrico={query_param}, velocidade={query_param}, avanco={query_param}, comprimento_max={query_param}, diametro_max={query_param}, frequencia_manutencao={query_param}, horas_trabalhadas={query_param}, preco_compra={query_param}, depreciacao_mensal={query_param}, valor_venda_final={query_param}, custo_minuto_maquina={query_param}, operador_nome={query_param}, custo_minuto_operador={query_param}, salario_base={query_param}, valor_adicionais={query_param}, turno_trabalho={query_param}, dia_semana={query_param}, vida_util_meses={query_param} WHERE id={query_param}
    ''', (request.form.get('nome_equipamento', 'Equipamento'), float(request.form.get('potencia') or 0), float(request.form.get('consumo_eletrico') or 0), request.form.get('velocidade', 'N/A'), request.form.get('avanco', 'N/A'), float(request.form.get('comprimento_max') or 0), float(request.form.get('diametro_max') or 0), int(request.form.get('frequencia_manutencao') or 500), int(request.form.get('horas_trabalhadas') or 0), float(request.form.get('preco_compra') or 0), float(request.form.get('depreciacao_mensal') or 0), float(request.form.get('valor_venda_final') or 0), float(request.form.get('custo_minuto_maquina') or 0), request.form.get('operador_nome', 'Posto Vago - Aguardando MOD'), float(request.form.get('custo_minuto_operador') or 0.0), float(request.form.get('salario_base') or 0.0), float(request.form.get('valor_adicionais') or 0.0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), int(request.form.get('vida_util_meses') or 120), id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/deletar_maquina/<int:id>', methods=['POST'])
def deletar_maquina(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'DELETE FROM maquinas WHERE id={query_param}', (id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/rh')
def rh():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    colaboradores = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('rh.html', colaboradores=colaboradores, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_colaborador', methods=['POST'])
def salvar_colaborador():
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f"SELECT id FROM maquinas WHERE operador_nome = 'Posto Vago - Aguardando MOD' LIMIT 1")
    posto_vago = cursor.fetchone()
    
    if posto_vago:
        # Correção: Adicionado o '= ?' / '= %s' que faltava na coluna custo_minuto_operador
        cursor.execute(f'UPDATE maquinas SET operador_nome={query_param}, salario_base={query_param}, valor_adicionais={query_param}, turno_trabalho={query_param}, dia_semana={query_param}, custo_minuto_operador={query_param} WHERE id={query_param}', 
                       (request.form.get('nome_completo', 'Colaborador'), float(request.form.get('salario_base') or 0), float(request.form.get('valor_adicionais') or 0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), float(request.form.get('custo_minuto_operador') or 0), posto_vago['id']))
        conn.commit()
        flash('MOD Alocado com sucesso!', 'success')
    else:
        cursor.execute(f"INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana) VALUES ('Posto de Apoio / Indireto', 0, 0, 'N/A', 'N/A', 0, 0, 9999, 0, 0, 0, 0, 0, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param})", 
                       (request.form.get('nome_completo', 'Colaborador'), float(request.form.get('custo_minuto_operador') or 0), float(request.form.get('salario_base') or 0), float(request.form.get('valor_adicionais') or 0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular')))
        conn.commit()
        flash('Mão de Obra Indireta alocada.', 'success')
        
    cursor.close()
    conn.close()
    return redirect(url_for('rh'))

@app.route('/imprimir_holerite/<int:id>/<string:tipo>')
def imprimir_holerite(id, tipo):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT * FROM maquinas WHERE id = {query_param}', (id,))
    col = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not col or col['operador_nome'] == 'Posto Vago - Aguardando MOD': 
        return "Colaborador não localizado."
        
    salario_base = float(col['salario_base'] or 0.0)
    adicionais = float(col['valor_adicionais'] or 0.0)
    horas_extras_acumuladas = 1250.00 if col['dia_semana'] != 'Regular' else 0.0
    titulo_recibo = "RECIBO DE PAGAMENTO MENSAL"
    provento_principal_nome = "Salário Base Nominal"
    provento_principal_valor = salario_base
    
    if tipo == "ferias":
        titulo_recibo = "RECIBO DE PAGAMENTO DE FÉRIAS (CLT)"
        provento_principal_nome = "Férias Integrais"
        provento_principal_valor = salario_base + (salario_base / 3)
    elif tipo == "decimo":
        titulo_recibo = "RECIBO DE DÉCIMO TERCEIRO SALÁRIO"
        provento_principal_nome = "13º Salário Integral"
        provento_principal_valor = salario_base
        
    total_proventos = provento_principal_valor + adicionais + horas_extras_acumuladas
    inss = total_proventos * 0.075 if total_proventos <= 1518.00 else ((total_proventos * 0.09) - 22.77 if total_proventos <= 2793.88 else ((total_proventos * 0.12) - 106.59 if total_proventos <= 4190.83 else ((total_proventos * 0.14) - 190.40 if total_proventos <= 8157.41 else 951.64)))
    base_irrf = total_proventos - inss
    irrf = 0.0 if base_irrf <= 2259.20 else ((base_irrf * 0.075) - 169.44 if base_irrf <= 2826.65 else ((base_irrf * 0.15) - 381.44 if base_irrf <= 3751.05 else ((base_irrf * 0.225) - 662.77 if base_irrf <= 4664.68 else (base_irrf * 0.275) - 896.00)))
    vale_transporte = salario_base * 0.06 if col['turno_trabalho'] == 'Diurno' else 0.0
    total_descontos = inss + irrf + vale_transporte
    valor_liquido = total_proventos - total_descontos
    dados_holerite = {"tipo_recibo": titulo_recibo, "nome": col['operador_nome'], "cargo": f"CBO {col['id']} - Ativo", "principal_nome": provento_principal_nome, "principal_valor": provento_principal_valor, "adicionais": adicionais, "horas_extras": horas_extras_acumuladas, "total_proventos": total_proventos, "inss": inss, "irrf": irrf, "vt": vale_transporte, "total_descontos": total_descontos, "liquido": valor_liquido}
    return render_template('holerite.html', h=dados_holerite)

@app.route('/orcamentos')
def orcamentos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas')
    maqs = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('orcamentos.html', maquinas=maqs, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_orcamento_calculado', methods=['POST'])
def salvar_orcamento_calculado():
    tipo = request.form.get('tipo_produto')
    nome_item = request.form.get('nome_item')
    lote = int(request.form.get('lote') or 1)
    preco_final = float(request.form.get('preco_final_calculado') or 0.0)
    sku = f"ORC-{tipo.upper()}-{int(preco_final)%1000}"
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    try:
        cursor.execute(f'INSERT INTO produtos (codigo_produto, nome_produto) VALUES ({query_param}, {query_param})', (sku, nome_item))
        
        cursor.execute(f'SELECT id FROM produtos WHERE codigo_produto = {query_param}', (sku,))
        prod_id = cursor.fetchone()['id']
        
        cursor.execute(f'INSERT INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES ({query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param})', 
                       (prod_id, float(request.form.get('iss') or 5), float(request.form.get('icms') or 18), float(request.form.get('federal') or 9.25), float(request.form.get('margem') or 25), preco_final / lote))
        
        cursor.execute(f'INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES ({query_param}, {query_param}, 0, \'SOB ENCOMENDA - Fila PCP\')', (prod_id, lote))
        conn.commit()
        flash('Orçamento integrado à carteira de demandas comerciais!', 'success')
    except Exception: # Correção: Captura genérica adaptada para o PostgreSQL/Neon
        flash('Erro no processamento comercial.', 'danger')
        
    cursor.close()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/requisicoes')
def requisicoes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM requisicoes_compras ORDER BY id DESC')
    reqs = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('requisicoes.html', requisicoes=reqs, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/compras')
def compras():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requisicoes_compras WHERE status LIKE 'Cotado%' ORDER BY id DESC")
    cotadas = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('compras.html', requisicoes_cotadas=cotadas, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_requisicao', methods=['POST'])
def salvar_requisicao():
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'INSERT INTO requisicoes_compras (equipamento_tipo, especificacao_desejada, quantidade) VALUES ({query_param}, {query_param}, {query_param})', 
                   (request.form.get('equipamento_tipo', 'Equipamento'), request.form.get('especificacao_desejada', 'N/A'), int(request.form.get('quantidade') or 1)))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/cotar_internet/<int:id>', methods=['POST'])
def cotar_internet(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT * FROM requisicoes_compras WHERE id = {query_param}', (id,))
    req = cursor.fetchone()
    
    if req:
        tipo = req['equipamento_tipo'].lower()
        esp = req['especificacao_desejada'].lower()
        preco, pot, dep = 45000.0, 5.5, 375.0
        if 'torno' in tipo or 'cnc' in tipo or 'centro' in tipo: 
            preco, pot, dep = (620000.0, 35.0, 5100.0) if '5 eixos' in esp else (290000.0, 18.0, 2400.0)
        elif 'forno' in tipo: 
            preco, pot, dep = (180000.0, 45.0, 1500.0)
        elif 'prensa' in tipo: 
            preco, pot, dep = (220000.0, 22.0, 1800.0)
        elif 'solda' in tipo: 
            preco, pot, dep = (15000.0, 7.5, 125.0)
        elif 'material' in tipo or 'insumo' in tipo: 
            preco, pot, dep = (2500.0 if 'tubo' in esp else 850.0), 0.0, 0.0
            
        cursor.execute(f'UPDATE requisicoes_compras SET preco_cotado={query_param}, potencia_cotada={query_param}, depreciacao_sugerida={query_param}, status=\'Cotado - Aguardando Confirmação\' WHERE id={query_param}', 
                       (preco, pot, dep, id))
        conn.commit()
        
    cursor.close()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/efetivar_compra/<int:id>', methods=['POST'])
def efetivar_compra(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'cursor_factory')
    query_param = "%s" if is_postgres else "?"
    
    cursor.execute(f'SELECT * FROM requisicoes_compras WHERE id = {query_param}', (id,))
    req = cursor.fetchone()
    
    cursor.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ult_imovel = cursor.fetchone()
    
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
            cursor.execute(f'INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, vida_util_meses) VALUES ({query_param}, {query_param}, {query_param}, \'3000\', \'15000\', 1000, 500, 1000, 0, {query_param}, {query_param}, {query_param}, {query_param}, \'Posto Vago - Aguardando MOD\', 0.0, {query_param})', 
                           (f"{req['especificacao_desejada']}", pot, pot * 0.7, preco, dep, preco * 0.2, c_mm, vida))
        else:
            sku_gerado = f"SKU-{req['id']}"
            preco_unidade_calc = preco / float(req['quantidade'])
            volume_calc = float(req['quantidade'])
            
            # Correção: O PostgreSQL não aceita 'INSERT OR REPLACE'. Usamos Upsert dinâmico baseado no driver ativo.
            if is_postgres:
                cursor.execute(f'''
                    INSERT INTO materiais (codigo_material, nome_material, preco_unitario, unidade_medida, estoque_atual, estoque_minimo) 
                    VALUES (%s, %s, %s, 'Lote', %s, 0.0)
                    ON CONFLICT (codigo_material) 
                    DO UPDATE SET preco_unitario = EXCLUDED.preco_unitario, estoque_atual = EXCLUDED.estoque_atual
                ''', (sku_gerado, req['especificacao_desejada'], preco_unidade_calc, volume_calc))
            else:
                cursor.execute("INSERT OR REPLACE INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (?, ?, ?, 'Lote', ?)", 
                               (sku_gerado, req['especificacao_desejada'], preco_unidade_calc, volume_calc))
                               
        cursor.execute(f'UPDATE requisicoes_compras SET status = \'Comprado e Ativado\' WHERE id = {query_param}', (id,))
        conn.commit()
        
    cursor.close()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/deletar_requisicao/<int:id>', methods=['POST'])
def deletar_requisicao(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'DELETE FROM requisicoes_compras WHERE id={query_param}', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/inventario')
@app.route('/materiais')
def materiais():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM materiais')
    mats = cursor.fetchall()
    
    cursor.execute('SELECT p.id, p.codigo_produto, p.nome_produto, COALESCE(ep.quantidade_disponivel, 0) AS quantidade_disponivel FROM produtos p LEFT JOIN estoque_produtos ep ON p.id = ep.produto_id')
    itens_acabados = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('materiais.html', materiais=mats, estoque_itens=itens_acabados, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_material', methods=['POST'])
def salvar_material():
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    try:
        cursor.execute(f'INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES ({query_param}, {query_param}, {query_param}, {query_param}, {query_param})', 
                       (request.form.get('codigo_material', 'SKU').strip(), request.form.get('nome_material', 'Insumo').strip(), float(request.form.get('preco_unidade') or 0), request.form.get('dimensoes', 'N/A'), float(request.form.get('volume_disponivel') or 0)))
        conn.commit()
    except Exception: # Correção: Captura genérica para barrar erros de restrição de unicidade (SKU) do Neon
        cursor.close()
        conn.close()
        return "Erro: SKU duplicado!"
        
    cursor.close()
    conn.close()
    return redirect(url_for('materiais'))

@app.route('/alterar_material/<int:id>', methods=['POST'])
def alterar_material(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'UPDATE materiais SET codigo_material={query_param}, nome_material={query_param}, preco_unidade={query_param}, dimensoes={query_param}, volume_disponivel={query_param} WHERE id={query_param}', 
                   (request.form.get('codigo_material', 'SKU').strip(), request.form.get('nome_material', 'Insumo').strip(), float(request.form.get('preco_unidade') or 0), request.form.get('dimensoes', 'N/A'), float(request.form.get('volume_disponivel') or 0), id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('materiais'))

@app.route('/deletar_material/<int:id>', methods=['POST'])
def deletar_material(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'DELETE FROM materiais WHERE id={query_param}', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('materiais'))

@app.route('/engenharia')
def engenharia():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM produtos')
    prods = cursor.fetchall()
    
    cursor.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas')
    maqs = cursor.fetchall()
    
    cursor.execute('SELECT id, nome_material, preco_unidade FROM materiais')
    mats = cursor.fetchall()
    
    cursor.execute('SELECT ep.*, p.nome_produto, p.codigo_produto, m.nome_equipamento, mat.nome_material FROM estrutura_produto ep JOIN produtos p ON ep.produto_id = p.id LEFT JOIN maquinas m ON ep.maquina_id = m.id LEFT JOIN materiais mat ON ep.material_id = mat.id')
    comps = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('engenharia.html', produtos=prods, maquinas=maqs, materiais=mats, composicoes=comps, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    try:
        cursor.execute(f'INSERT INTO produtos (codigo_produto, nome_produto) VALUES ({query_param}, {query_param})', 
                       (request.form.get('codigo_produto', 'PROD').strip(), request.form.get('nome_produto', 'Acabado').strip()))
        conn.commit()
    except Exception: # Correção: Captura genérica adaptada ao PostgreSQL do Neon
        cursor.close()
        conn.close()
        return "Erro: Produto duplicado."
        
    cursor.close()
    conn.close()
    return redirect(url_for('engenharia'))

@app.route('/vincular_estrutura', methods=['POST'])
def vincular_estrutura():
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    maquina_id = request.form.get('maquina_id')
    material_id = request.form.get('material_id')
    
    cursor.execute(f'INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material) VALUES ({query_param}, {query_param}, {query_param}, {query_param}, {query_param})', 
                   (int(request.form.get('produto_id') or 0), int(maquina_id) if maquina_id and maquina_id.isdigit() else None, int(material_id) if material_id and material_id.isdigit() else None, float(request.form.get('tempo_processo_min') or 0), float(request.form.get('quantidade_material') or 0)))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('engenharia'))

@app.route('/deletar_item_estrutura/<int:id>', methods=['POST'])
def deletar_item_estrutura(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'DELETE FROM estrutura_produto WHERE id={query_param}', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('engenharia'))

@app.route('/precificacao')
def precificacao():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Correção: Inclusão de todas as colunas do SELECT na cláusula GROUP BY para atender ao padrão ANSI/PostgreSQL do Neon
    cursor.execute('SELECT p.id, p.codigo_produto, p.nome_produto, COALESCE(SUM(ep.tempo_processo_min * mq.custo_minuto_maquina), 0) + COALESCE(SUM(ep.quantidade_material * mt.preco_unidade), 0) AS custo_fabricacao FROM produtos p LEFT JOIN estrutura_produto ep ON p.id = ep.produto_id LEFT JOIN maquinas mq ON ep.maquina_id = mq.id LEFT JOIN materiais mt ON ep.material_id = mt.id GROUP BY p.id, p.codigo_produto, p.nome_produto')
    prods = cursor.fetchall()
    
    cursor.execute('SELECT fp.*, p.codigo_produto, p.nome_produto FROM formacao_precos fp JOIN produtos p ON fp.produto_id = p.id')
    salvos = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('precificacao.html', produtos=prods, precos_salvos=salvos, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_preco', methods=['POST'])
def salvar_preco():
    conn = get_db_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'cursor_factory')
    
    prod_id = int(request.form.get('produto_id') or 0)
    imp_mun = float(request.form.get('imposto_municipal') or 0)
    imp_est = float(request.form.get('imposto_estadual') or 0)
    imp_fed = float(request.form.get('imposto_federal') or 0)
    margem = float(request.form.get('margem_lucro') or 0)
    preco_vf = float(request.form.get('preco_venda_final') or 0)

    # Correção: Desvio de sintaxe para o Upsert do PostgreSQL (Neon) em substituição do INSERT OR REPLACE
    if is_postgres:
        cursor.execute('''
            INSERT INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (produto_id) 
            DO UPDATE SET imposto_municipal = EXCLUDED.imposto_municipal, imposto_estadual = EXCLUDED.imposto_estadual, imposto_federal = EXCLUDED.imposto_federal, margem_lucro = EXCLUDED.margem_lucro, preco_venda_final = EXCLUDED.preco_venda_final
        ''', (prod_id, imp_mun, imp_est, imp_fed, margem, preco_vf))
    else:
        cursor.execute('INSERT OR REPLACE INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (?, ?, ?, ?, ?, ?)', 
                       (prod_id, imp_mun, imp_est, imp_fed, margem, preco_vf))
                       
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('precificacao'))

@app.route('/vendas')
def vendas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT p.id, p.codigo_produto, p.nome_produto, fp.preco_venda_final, COALESCE(e.quantidade_disponivel, 0) AS estoque_atual FROM produtos p JOIN formacao_precos fp ON p.id = fp.produto_id LEFT JOIN estoque_produtos e ON p.id = e.produto_id')
    prods = cursor.fetchall()
    
    cursor.execute('SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id ORDER BY pv.id DESC')
    peds = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('vendas.html', produtos=prods, pedidos=peds, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/estoque')
def estoque():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT p.id AS produto_id, p.codigo_produto, p.nome_produto, COALESCE(ep.quantidade_disponivel, 0) AS quantidade_disponivel FROM produtos p LEFT JOIN estoque_produtos ep ON p.id = ep.produto_id')
    itens = cursor.fetchall()
    
    cursor.execute("SELECT pv.*, p.codigo_produto, p.nome_produto FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.observacoes LIKE '%SOB ENCOMENDA%' AND pv.id NOT IN (SELECT DISTINCT pedido_id FROM ordens_processo WHERE status='Finalizado e Armazenado')")
    peds = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('estoque.html', estoque_itens=itens, pedidos=peds, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/lancar_venda', methods=['POST'])
def lancar_venda():
    prod_id = int(request.form.get('produto_id') or 0)
    qtd = int(request.form.get('quantidade') or 1)
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT quantidade_disponivel FROM estoque_produtos WHERE produto_id = {query_param}', (prod_id,))
    est = cursor.fetchone()
    estoque_atual = est['quantidade_disponivel'] if est else 0
    
    if estoque_atual >= qtd:
        cursor.execute(f'UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel - {query_param} WHERE produto_id = {query_param}', (qtd, prod_id))
        cursor.execute(f'INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES ({query_param}, {query_param}, 0, \'Pronta Entrega - Faturado\')', (prod_id, qtd))
    else:
        cursor.execute(f'INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES ({query_param}, {query_param}, 0, \'SOB ENCOMENDA - Fila PCP\')', (prod_id, qtd))
        
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/deletar_venda/<int:id>', methods=['POST'])
def deletar_venda(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'DELETE FROM pedidos_vendas WHERE id={query_param}', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/pcp')
def pcp():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens_processo ORDER BY pedido_id ASC, id ASC')
    ords = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    cursor.close()
    conn.close()
    return render_template('pcp.html', ordens=ords, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/solicitar_producao_pcp/<int:pedido_id>', methods=['POST'])
def solicitar_producao_pcp(pedido_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT id FROM ordens_processo WHERE pedido_id = {query_param}', (pedido_id,))
    existe = cursor.fetchone()
    
    if not existe:
        cursor.execute(f'SELECT pv.*, p.codigo_produto, p.nome_produto FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.id = {query_param}', (pedido_id,))
        ped = cursor.fetchone()
        
        if ped:
            cursor.execute(f'SELECT ep.*, m.nome_equipamento, m.custo_minuto_maquina, m.operador_nome FROM estrutura_produto ep LEFT JOIN maquinas m ON ep.maquina_id = m.id WHERE ep.produto_id = {query_param} ORDER BY ep.id ASC', (ped['produto_id'],))
            rots = cursor.fetchall()
            
            ponteiro_tempo = datetime.datetime.now()
            tempo_setup_fixo = 15
            
            for idx, r in enumerate(rots):
                tempo_lote_min = (float(r['tempo_processo_min'] or 0) * int(ped['quantidade'])) + tempo_setup_fixo
                custo_total_operacao = tempo_lote_min * float(r['custo_minuto_maquina'] or 0.15)
                status_inicial = "Na Fila [GARGALO OPERACIONAL]" if tempo_lote_min > 480 else "Na Fila"
                entrada_str = ponteiro_tempo.strftime("%d/%m/%Y %H:%M")
                saida_op = ponteiro_tempo + datetime.timedelta(minutes=tempo_lote_min)
                saida_str = saida_op.strftime("%d/%m/%Y %H:%M")
                
                cursor.execute(f'INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_name, codigo_produto, nome_produto, data_entrada, tempo_estimado_min, data_saida, status, custo_operacao, operador_nome) VALUES ({query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param}, {query_param})', 
                               (pedido_id, f"OP {(idx+1)*10}", r['nome_equipamento'] or 'Bancada Manual', ped['codigo_produto'], ped['nome_produto'], entrada_str, tempo_lote_min, saida_str, status_inicial, custo_total_operacao, r['operador_nome'] or 'Pendente'))
                ponteiro_tempo = saida_op
            conn.commit()
        flash('Ordem de Produção transmitida com sucesso para o painel do PCP!', 'success')
        
    cursor.close()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/abastecer_estoque_pcp', methods=['POST'])
def abastecer_estoque_pcp():
    prod_id = int(request.form.get('produto_id') or 0)
    pedido_id = int(request.form.get('pedido_id') or 0)
    qtd = float(request.form.get('quantidade_abastecer') or 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    # Busca a contagem usando o cursor corrigido
    cursor.execute(f'SELECT COUNT(*) as total FROM ordens_processo WHERE pedido_id = {query_param}', (pedido_id,))
    ops_existentes = cursor.fetchone()['total']
    
    cursor.execute(f"SELECT COUNT(*) as pendentes FROM ordens_processo WHERE pedido_id = {query_param} AND status NOT LIKE 'Finalizado%'", (pedido_id,))
    ops_pendentes = cursor.fetchone()['pendentes']
    
    if ops_existentes == 0 or ops_pendentes > 0:
        cursor.close()
        conn.close()
        flash('Bloqueio de Qualidade: O Almoxarifado não pode receber este lote! Existem operações pendentes no PCP.', 'danger')
        return redirect(url_for('estoque'))
        
    cursor.execute(f'SELECT * FROM estoque_produtos WHERE produto_id = {query_param}', (prod_id,))
    est = cursor.fetchone()
    
    if not est: 
        cursor.execute(f'INSERT INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES ({query_param}, {query_param})', (prod_id, qtd))
    else: 
        cursor.execute(f'UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + {query_param} WHERE produto_id = {query_param}', (qtd, prod_id))
        
    cursor.execute(f"UPDATE ordens_processo SET status = 'Finalizado e Armazenado' WHERE pedido_id = {query_param}", (pedido_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    flash('Recebimento efetuado e integrado com sucesso ao estoque disponível.', 'success')
    return redirect(url_for('estoque'))
        
    cursor.execute(f'SELECT * FROM estoque_produtos WHERE produto_id = {query_param}', (prod_id,))
    est = cursor.fetchone()
    
    if not est: 
        cursor.execute(f'INSERT INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES ({query_param}, {query_param})', (prod_id, qtd))
    else: 
        cursor.execute(f'UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + {query_param} WHERE produto_id = {query_param}', (qtd, prod_id))
        
    cursor.execute(f"UPDATE ordens_processo SET status = 'Finalizado e Armazenado' WHERE pedido_id = {query_param}", (pedido_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    flash('Recebimento efetuado e integrado com sucesso ao estoque disponível.', 'success')
    return redirect(url_for('estoque'))

@app.route('/dar_baixa_op/<int:id>', methods=['POST'])
def dar_baixa_op(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define o placeholder correto (%s para o Neon, ? para o SQLite local)
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    # Atualiza o status da OP usando o cursor de forma compatível
    cursor.execute(f'UPDATE ordens_processo SET operador_nome = {query_param}, status = \'Finalizado\' WHERE id = {query_param}', 
                   (request.form.get('operador_nome', 'Operador'), id))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('pcp'))

@app.route('/imprimir_nf/<int:pedido_id>')
def imprimir_nf(pedido_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query_param = "%s" if hasattr(conn, 'cursor_factory') else "?"
    
    cursor.execute(f'SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id WHERE pv.id = {query_param}', (pedido_id,))
    ped = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not ped: 
        return "Nota Fiscal não encontrada."
        
    sub = ped['preco_venda_final'] * ped['quantidade']
    v_desc = sub * (ped['desconto_percentual'] / 100.0)
    liq = sub - v_desc
    v_mun = liq * (ped['imposto_municipal'] / 100.0)
    v_est = liq * (ped['imposto_estadual'] / 100.0)
    v_fed = liq * (ped['imposto_federal'] / 100.0)
    return render_template('nota_fiscal.html', p=ped, subtotal=sub, v_desconto=v_desc, total_liquido=liq, v_municipal=v_mun, v_estadual=v_est, v_federal=v_fed, total_impostos=v_mun+v_est+v_fed)

@app.route('/financeiro')
def financeiro():
    if not session.get('logado'):
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS total FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    faturamento_bruto = cursor.fetchone()['total']
    
    cursor.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) AS total FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    despesa_pessoal_bruta = cursor.fetchone()['total']
    
    cursor.execute('SELECT COALESCE(SUM((fp.preco_venda_final * pv.quantidade) * ((fp.imposto_municipal + fp.imposto_estadual + fp.imposto_federal) / 100.0)), 0) AS total FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    impostos_vendas = cursor.fetchone()['total']
    
    caixa, total = calcular_caixa_disponivel(conn)
    
    cursor.close()
    conn.close()
    
    total_encargos = impostos_vendas + (despesa_pessoal_bruta * 0.20)
    return render_template('financeiro.html', faturamento=faturamento_bruto, custo_pessoal=despesa_pessoal_bruta, impostos=total_encargos, saldo_liquido=caixa, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/pagar_dividendos', methods=['POST'])
def pagar_dividendos():
    if not session.get('logado'):
        return redirect(url_for('index'))
    percentual = float(request.form.get('percentual_lucro') or 25)
    flash(f'Distribuição de {percentual}% dos dividendos processada!', 'success')
    return redirect(url_for('financeiro'))

@app.route('/roi')
def roi():
    if not session.get('logado'):
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS receita_bruta, COALESCE(SUM(pv.quantidade), 0) AS total_pecas FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    v_dados = cursor.fetchone()
    
    cursor.execute('SELECT COALESCE(SUM(valor_imovel_estimado + capital_inicial_negocio), 0) AS capital_total, COALESCE(SUM(aluguel_regional), 0) AS aluguel FROM investimentos_imobiliarios')
    invs = cursor.fetchone()
    
    cursor.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) AS total FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    despesa_pessoal = cursor.fetchone()['total']
    
    caixa, total = calcular_caixa_disponivel(conn)
    
    cursor.close()
    conn.close()
    
    rec, pecas, cap, aluguel = v_dados['receita_bruta'], v_dados['total_pecas'], invs['capital_total'], invs['aluguel']
    sobra = rec - despesa_pessoal - aluguel
    payback_meses = (cap / sobra) if sobra > 0 else 0.0
    return render_template('roi.html', receita=rec, total_pecas=pecas, capital=cap, payback_real=payback_meses, lucro_acionistas=rec*0.25, caixa_disponivel=caixa, capital_inicial=total)

if __name__ == '__main__':
    app.run(debug=True)
