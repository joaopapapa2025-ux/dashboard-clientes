import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request
import re
from io import BytesIO
from datetime import datetime, timedelta

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")

    st.markdown("---")
    st.info("📍 **Menu de Navegação**")

    # Botão Home
    if st.button("📊 Dashboard Principal", use_container_width=True):
        st.rerun()
        
    # Em vez de st.button + st.switch_page, vamos usar um link direto
    # O Streamlit Cloud gera a URL da página seguindo o nome do arquivo
    st.markdown("""
        <a href="/Playbook_de_Vendas" target="_self" style="text-decoration: none;">
            <div style="
                background-color: #f0f2f6;
                color: #31333F;
                padding: 10px;
                text-align: center;
                border-radius: 5px;
                border: 1px solid #d3d3d3;
                margin-bottom: 10px;
                font-weight: bold;
            ">
                📖 Playbook de Vendas
            </div>
        </a>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
import json
import os

def categorizar_produto_papapa(row):
    # 1. Pega os dados brutos e limpa
    l = str(row.get('LINHA', '')).upper().strip()
    p = str(row.get('DESC PRODUTO', '')).upper().strip()
    
    # --- REGRA 1: YOGUZINHO (PRIORIDADE ABSOLUTA) ---
    if "IOGURTE" in p or "YOGU" in p:
        return "YOGUZINHO"

    # --- REGRA 2: LA CHEF (IDENTIFICAÇÃO POR PALAVRA-CHAVE DO PRODUTO) ---
    # Se no nome do produto tiver Lentilha, Risotinho ou Caseirinho, 
    # vira LA CHEF na hora, não importa o que diz a coluna LINHA.
    palavras_la_chef = ["LENTILHA", "RISOTINHO", "CASEIRINHO", "180G"]
    if any(x in p for x in palavras_la_chef):
        return "LA CHEF"

    # --- REGRA 3: SOPINHAS (APENAS SE NÃO FOR LA CHEF) ---
    if "SOPINHA" in p or "SOPINHA" in l:
        return "SOPINHAS"

    # --- REGRA 4: PAPINHAS SALGADAS (120G) ---
    if "120G" in p or "CARNE" in l or "SALGADA" in l or "FRANGO" in p:
        return "PAPINHAS SALGADAS"
    
    # --- REGRA 5: PAPINHAS DE FRUTAS / OUTROS ---
    if "FRUTA" in l or "ORG" in l: return "PAPINHAS DE FRUTAS"
    if "CERAL" in l or "AVEIA" in l: return "CEREAIS"
    if "DENTI" in l: return "DENTIÇÃO"
    
    return l if l != "" else "OUTROS"

# Nome do arquivo de banco de dados
ARQUIVO_DATABASE = "database_comentarios.json"

# Função para garantir que o arquivo exista e carregar os dados
def carregar_comentarios():
    if os.path.exists(ARQUIVO_DATABASE):
        try:
            with open(ARQUIVO_DATABASE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    else:
        # Se não existe, cria um arquivo JSON vazio {}
        with open(ARQUIVO_DATABASE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}

def salvar_comentarios(dados):
    with open(ARQUIVO_DATABASE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Inicializa a variável comentários
comentarios = carregar_comentarios()

def limpar_telefone(tel):
    """Remove caracteres não numéricos do telefone."""
    if pd.isna(tel) or tel == "":
        return ""
    # Mantém apenas os números
    return "".join(filter(str.isdigit, str(tel)))

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="Dashboard Inside Sales - PAPAPÁ",
    layout="wide"
)

# =========================
# PROTEÇÃO DE ACESSO
# =========================
CODIGO_ACESSO = "amamosnossosclientes"

# Inicializa o estado de acesso se não existir
if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False

# Se não estiver liberado, mostra a tela de login
if not st.session_state.acesso_liberado:
    st.title("🔒 Acesso Restrito - Papapá")
    codigo_digitado = st.text_input("Digite o código de acesso", type="password")
    
    if st.button("Entrar"):
        if codigo_digitado == CODIGO_ACESSO:
            st.session_state.acesso_liberado = True
            st.rerun()
        else:
            st.error("Código incorreto")
    st.stop() # Trava o resto da página

# ==========================================
# 📝 AJUSTE MANUAL DIÁRIO (MARÇO 2026)
# ==========================================

# --- AJUSTE MANUAL DIÁRIO (MARÇO 2026) ---
meta_marco = 872507.00
faturado_marco = 577852.00
digitado_marco = 61020.00

# --- CÁLCULOS AUTOMÁTICOS ---
total_geral = faturado_marco + digitado_marco
falta_r_cifra = meta_marco - total_geral

# Cálculo de Dias Úteis (Segunda a Sexta)
hoje = datetime.now()
ultimo_dia_mes = datetime(2026, 3, 31)
dias_uteis_restantes = len(pd.date_range(hoje, ultimo_dia_mes, freq='B'))

# Ritmo Diário necessário
ritmo = falta_r_cifra / dias_uteis_restantes if dias_uteis_restantes > 0 else 0
ritmo_final = max(ritmo, 0)

# --- EXIBIÇÃO DE ALERTAS ---
if falta_r_cifra <= 0:
    st.balloons()
    st.success("🏆 **META BATIDA!** Parabéns time Papapá!")
elif ritmo_final > 60000:
    st.error(f"⚠️ **ALERTA DE RITMO:** Precisamos de R$ {ritmo_final:,.0f} por dia útil!".replace(",", "."))

# --- EXIBIÇÃO NO TOPO ---
st.subheader("📊 Performance Diária - Inside Sales (D -1)")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("🎯 Meta", f"R$ {meta_marco:,.0f}".replace(",", "."))

with col2:
    st.metric("✅ Faturado", f"R$ {faturado_marco:,.0f}".replace(",", "."))

with col3:
    st.metric("📝 Digitado", f"R$ {digitado_marco:,.0f}".replace(",", "."))

with col4:
    # Mostra quanto falta ou quanto sobrou
    label_gap = "🚩 Falta (Gap)" if falta_r_cifra > 0 else "🏆 Superavit"
    st.metric(label_gap, f"R$ {abs(falta_r_cifra):,.0f}".replace(",", "."), 
              delta_color="inverse")

with col5:
    percentual = (total_geral / meta_marco) * 100
    st.metric("🔥 Total (Fat+Dig)", f"R$ {total_geral:,.0f}".replace(",", "."), 
              delta=f"{percentual:.1f}%")

with col6:
    # Mostra os dias úteis e o valor diário necessário no delta
    st.metric("📅 Ritmo Diário", f"{dias_uteis_restantes} d.ú.", 
              delta=f"R$ {ritmo_final:,.0f}/dia", delta_color="inverse")

st.markdown("---")

# =========================
# ARQUIVO BASE
# =========================

ARQUIVO_BASE = "Base Dashboard Inside Sales.xlsx"

# =========================
# MAPEAMENTO DA NOVA PLANILHA (Constantes)
# =========================
# Definido antes do carregamento para ser usado nas funções
COL_CODIGO   = "CÓDIGO"
COL_CNPJ     = "CNPJ"
COL_RAZAO    = "RAZÃO SOCIAL"
COL_TIER     = "TIER"
COL_ESTRATEG = "ESTRATÉGIA"
COL_UF       = "UF"
COL_CIDADE   = "CIDADE"
COL_BAIRRO   = "BAIRRO"
COL_TELEFONE = "TELEFONE"
COL_EMAIL    = "E-MAIL"
COL_VENDEDOR = "VENDEDOR"
COL_GRUPO_EC = "GRUPO ECONÔMICO"
COL_ULT_COMP = "ÚLTIMA COMPRA"
COL_TABELA   = "TABELA"
COL_SEGMENTO = "SEGMENTO"
COL_T_U_9_M  = "TOTAL ÚLTIMO 9 MESES"

# Meses para o Sistema de Farol
COL_MES_ATUAL = "FEV/26" 
COL_MES_ANT   = "JAN/26"

# =========================
# CARREGAR BASE CLIENTES
# =========================

@st.cache_data
def carregar_dados():
    # Carrega a aba correta 'BASE COMPLETA'
    df = pd.read_excel(ARQUIVO_BASE, sheet_name="BASE COMPLETA")
    df.columns = df.columns.str.strip() # Limpa espaços nos nomes das colunas
    return df

df = carregar_dados()

# =========================
# CARREGAR BASE PRODUTOS (MIX)
# =========================

@st.cache_data
def carregar_vendas():
    try:
        # Carrega a aba MIX
        vendas = pd.read_excel(ARQUIVO_BASE, sheet_name="MIX")
        vendas.columns = vendas.columns.str.strip()
        # Cria ID de busca por CNPJ limpo
        vendas["CNPJ_LIMPO"] = vendas["CNPJ"].astype(str).str.replace(r"\D", "", regex=True)
        return vendas
    except:
        return pd.DataFrame()

df_vendas = carregar_vendas()

# =========================
# GARANTIR COLUNAS E LIMPEZA
# =========================

def limpar_cnpj(cnpj):
    if pd.isna(cnpj):
        return ""
    return re.sub(r"\D", "", str(cnpj))

# Garante que colunas essenciais existam para não quebrar o código lá na frente
colunas_obrigatorias = [COL_RAZAO, COL_UF, COL_CIDADE, COL_CNPJ, COL_VENDEDOR, COL_SEGMENTO, COL_T_U_9_M]
for col in colunas_obrigatorias:
    if col not in df.columns:
        df[col] = ""

df["CNPJ_LIMPO"] = df[COL_CNPJ].apply(limpar_cnpj)

# =========================
# FUNÇÃO DO SISTEMA DE FAROL
# =========================
def calcular_status_farol(row):
    # Converte para numérico para evitar erro de comparação de texto
    fat_atual = pd.to_numeric(row.get(COL_MES_ATUAL, 0), errors='coerce')
    fat_ant   = pd.to_numeric(row.get(COL_MES_ANT, 0), errors='coerce')
    
    if pd.isna(fat_atual): fat_atual = 0
    if pd.isna(fat_ant): fat_ant = 0
    
    if fat_atual > 0:
        return "🟢 ATIVO", "#27AE60"
    elif fat_ant > 0:
        return "🟡 ALERTA", "#F1C40F"
    else:
        return "🔴 REATIVAÇÃO", "#E74C3C"

# =========================
# TRATAR FATURAMENTO (RESOLVIDO)
# =========================

# 1. Função para limpar R$, pontos de milhar e converter vírgula em ponto
def limpar_valor_comercial(valor):
    if pd.isna(valor) or valor == "": 
        return 0.0
    if isinstance(valor, (int, float)): 
        return float(valor)
    
    # Remove R$, espaços, pontos de milhar e troca a vírgula decimal por ponto
    texto_limpo = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(texto_limpo)
    except:
        return 0.0

# 2. Aplicamos a limpeza pesada na coluna original
df[COL_T_U_9_M] = df[COL_T_U_9_M].apply(limpar_valor_comercial)

# 3. Definimos os limites (bins) garantindo que o zero seja uma categoria separada
# O primeiro bin começa abaixo de zero para capturar o 0 exato
bins = [-float("inf"), 0.01, 5000, 20000, 50000, 100000, float("inf")]

labels = [
    "Sem Faturamento",
    "Até 5 mil",
    "5 mil – 20 mil",
    "20 mil – 50 mil",
    "50 mil – 100 mil",
    "Acima de 100 mil"
]

# 4. Criamos a coluna de faixas oficial
df["FAIXA_FATURAMENTO"] = pd.cut(df[COL_T_U_9_M], bins=bins, labels=labels, include_lowest=True)

# =========================
# COMENTÁRIOS POR CLIENTE
# =========================

ARQUIVO_COMENTARIOS = "comentarios_clientes.json"

def carregar_comentarios():
    try:
        # Garante a leitura com encoding utf-8 para não quebrar acentos
        if os.path.exists(ARQUIVO_COMENTARIOS):
            with open(ARQUIVO_COMENTARIOS, "r", encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def salvar_comentarios(comentarios):
    with open(ARQUIVO_COMENTARIOS, "w", encoding='utf-8') as f:
        json.dump(comentarios, f, indent=4, ensure_ascii=False)

# carregar comentários existentes
comentarios = carregar_comentarios()

# =========================
# FUNÇÃO GERAR PDF (CORRIGIDA - FATURAMENTO REAL)
# =========================

def gerar_pdf_cliente(cliente, vendas_cliente):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    
    # --- FUNÇÃO INTERNA DE LIMPEZA DE LINHA ---
    def normalizar_nome_linha(linha_bruta):
        l = str(linha_bruta).upper().strip()
        if "CARNE" in l or "SALGADA" in l: return "PAPINHAS SALGADAS"
        if "FRUTA" in l or "ORG" in l: return "PAPINHAS DE FRUTAS"
        if "CERAL" in l or "AVEIA" in l: return "CEREAIS" 
        if "DENTI" in l: return "DENTIÇÃO"
        if "YOGU" in l or "IOGURTE" in l: return "YOGUZINHO"
        return l 

    # Aplicar a normalização no DataFrame de vendas
    if not vendas_cliente.empty:
        vendas_cliente = vendas_cliente.copy()
        vendas_cliente["LINHA"] = vendas_cliente["LINHA"].apply(normalizar_nome_linha)

    # --- CÁLCULO DO FATURAMENTO REAL (Obrigatório estar aqui em cima) ---
    faturamento_real = 0
    if not vendas_cliente.empty:
        faturamento_real = vendas_cliente["VALOR"].sum()

    style_tabela = styles["BodyText"]
    style_tabela.leading = 14
    elementos = []

    titulo = Paragraph("Relatório de Cliente - PAPAPÁ", styles["Title"])
    data_geracao = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"])

    elementos.append(titulo)
    elementos.append(data_geracao)
    elementos.append(Spacer(1,20))

    # Tabela de dados cadastrais (AGORA COM faturamento_real DEFINIDO)
    dados_cliente = [
        ["Razão Social", str(cliente[COL_RAZAO])],
        ["CNPJ", str(cliente[COL_CNPJ])],
        ["Telefone", str(cliente[COL_TELEFONE])],
        ["Email", str(cliente[COL_EMAIL])],
        ["Cidade", f"{cliente[COL_CIDADE]} - {cliente[COL_UF]}"],
        ["Vendedor", str(cliente[COL_VENDEDOR])],
        ["Segmento", str(cliente[COL_SEGMENTO])],
        ["Faturamento Total", f"R$ {faturamento_real:,.2f}"],
    ]

    tabela_cliente = Table(dados_cliente, colWidths=[6*cm,10*cm])
    tabela_cliente.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
    ]))
    elementos.append(tabela_cliente)
    elementos.append(Spacer(1,20))

    elementos.append(Paragraph("Histórico de Compras (Mix)", styles["Heading2"]))

    if not vendas_cliente.empty:
        # Agrupamento para cálculos gerais
        resumo = (
            vendas_cliente
            .groupby(["DESC PRODUTO","LINHA"])[["QTDE","VALOR"]]
            .sum()
            .reset_index()
            .sort_values("VALOR", ascending=False)
        )

        total_valor = resumo["VALOR"].sum()
        total_qtd = resumo["QTDE"].sum()
        total_skus = resumo["DESC PRODUTO"].nunique()
        ticket_medio = 0
        ultima_compra = ""

        if "NUMERO NF" in vendas_cliente.columns:
            total_pedidos = vendas_cliente["NUMERO NF"].nunique()
            if total_pedidos > 0: ticket_medio = total_valor / total_pedidos

        if "DATA PEDIDO" in vendas_cliente.columns:
            data_max = vendas_cliente["DATA PEDIDO"].max()
            if pd.notna(data_max):
                ultima_compra = pd.to_datetime(data_max).strftime("%d/%m/%Y")

        # TABELA 1: RESUMO COMERCIAL
        resumo_comercial = [
            ["Total de SKUs Comprados", total_skus],
            ["Total de Unidades (Volume)", int(total_qtd)],
            ["Valor Total Acumulado", f"R$ {total_valor:,.2f}"],
            ["Ticket Médio por NF", f"R$ {ticket_medio:,.2f}"],
            ["Data da Última Compra", ultima_compra]
        ]

        tabela_resumo = Table(resumo_comercial, colWidths=[8*cm,8*cm])
        tabela_resumo.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
            ("FONTSIZE", (0,0), (-1,-1), 10),
        ]))
        elementos.append(Spacer(1,10))
        elementos.append(tabela_resumo)
        elementos.append(Spacer(1,20))

        # TABELA 2: RESUMO POR PEDIDO
        elementos.append(Paragraph("Resumo por Pedido (NF)", styles["Heading3"]))
        resumo_nfs = (
            vendas_cliente
            .groupby([vendas_cliente["DATA PEDIDO"].dt.strftime('%d/%m/%Y'), "NUMERO NF"])["VALOR"]
            .sum()
            .reset_index()
        )
        resumo_nfs.columns = ["DATA_PED", "NF_PED", "VALOR_PED"]
        resumo_nfs = resumo_nfs.sort_values("NF_PED", ascending=False)
        
        dados_nfs = [["DATA", "NÚMERO DA NF", "VALOR DO PEDIDO"]]
        for _, row in resumo_nfs.iterrows():
            dados_nfs.append([str(row["DATA_PED"]), str(row["NF_PED"]), f"R$ {row['VALOR_PED']:,.2f}"])

        tabela_nfs = Table(dados_nfs, colWidths=[5.3*cm, 5.3*cm, 5.4*cm])
        tabela_nfs.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tabela_nfs)
        elementos.append(Spacer(1, 25))

        # TOP PRODUTOS
        elementos.append(Paragraph("Top Produtos Comprados", styles["Heading3"]))
        top_produtos = resumo.head(5)
        dados_top = [["Produto", "Linha", "Qtd", "Valor"]]
        for _, row in top_produtos.iterrows():
            dados_top.append([
                Paragraph(str(row["DESC PRODUTO"]), style_tabela),
                Paragraph(str(row["LINHA"]), style_tabela),
                int(row["QTDE"]),
                f"R$ {row['VALOR']:,.2f}"
            ])

        tabela_top = Table(dados_top, colWidths=[8*cm, 3.5*cm, 2*cm, 2.5*cm], repeatRows=1)
        tabela_top.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tabela_top)
        elementos.append(Spacer(1, 25))

        # HISTÓRICO DETALHADO
        elementos.append(Paragraph("Histórico Detalhado de Compras", styles["Heading3"]))
        dados_produtos = [["Data", "NF", "Produto", "Linha", "Qtd", "Valor"]]
        for _, row in vendas_cliente.iterrows():
            data_item = pd.to_datetime(row["DATA PEDIDO"]).strftime("%d/%m/%Y") if pd.notna(row["DATA PEDIDO"]) else ""
            dados_produtos.append([
                data_item,
                str(row["NUMERO NF"]) if pd.notna(row["NUMERO NF"]) else "",
                Paragraph(str(row["DESC PRODUTO"]), style_tabela),
                Paragraph(str(row["LINHA"]), style_tabela),
                int(row["QTDE"]) if pd.notna(row["QTDE"]) else 0,
                f"R$ {row['VALOR']:,.2f}"
            ])

        tabela_produtos = Table(dados_produtos, colWidths=[2.5*cm, 2.5*cm, 7*cm, 3.5*cm, 1.5*cm, 2.5*cm], repeatRows=1)
        tabela_produtos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (4, 1), (4, -1), "CENTER"),
            ("ALIGN", (5, 1), (5, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elementos.append(tabela_produtos)
    else:
        elementos.append(Paragraph("Nenhum histórico de compra encontrado.", styles["Normal"]))

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    doc.build(elementos)
    buffer.seek(0)
    return buffer
    
# ==========================================
# SIDEBAR - VERSÃO FINAL (FIX RANKING + SEM DUPLICATAS)
# ==========================================

# --- TRATAMENTO DE DADOS ---
COL_DATA_ULTIMA_COMPRA = "ÚLTIMA COMPRA"
if COL_TELEFONE in df.columns:
    df["TEL_LIMPO"] = df[COL_TELEFONE].astype(str).str.replace(r'\D', '', regex=True)
else:
    df["TEL_LIMPO"] = ""

if COL_DATA_ULTIMA_COMPRA in df.columns:
    df[COL_DATA_ULTIMA_COMPRA] = pd.to_datetime(df[COL_DATA_ULTIMA_COMPRA], errors='coerce')
    df["MES_REF"] = df[COL_DATA_ULTIMA_COMPRA].dt.strftime('%m/%Y')
else:
    df["MES_REF"] = "Sem Data"

st.sidebar.title("Filtros")

# BOTÃO LIMPAR - Reseta as chaves novas e as antigas (para garantir o ranking)
if st.sidebar.button("Limpar todos os filtros"):
    chaves = ["b_cnpj", "b_razao", "b_email", "b_tel", "f_mes", "f_vend", "f_uf", "f_cid", "f_bair", "f_seg", "f_fat", "filtro_mes"]
    for c in chaves:
        if c in st.session_state:
            st.session_state[c] = [] if isinstance(st.session_state[c], list) else ""
    st.rerun()

df_filtrado = df.copy()

# ==========================================
# 1. BUSCAS POR TEXTO (TOPO)
# ==========================================
b_cnpj = st.sidebar.text_input("Buscar por CNPJ", key="b_cnpj")
if b_cnpj:
    cnpj_l = "".join(filter(str.isdigit, b_cnpj)) 
    if "CNPJ_LIMPO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_l, na=False)]

# RAZÃO SOCIAL DINÂMICA (PLACEHOLDER)
placeholder_razao = st.sidebar.empty()

b_email = st.sidebar.text_input("Buscar por E-mail", key="b_email")
if b_email:
    df_filtrado = df_filtrado[df_filtrado[COL_EMAIL].str.contains(b_email, case=False, na=False)]

b_tel = st.sidebar.text_input("Buscar por Telefone", key="b_tel")
if b_tel:
    t_l = "".join(filter(str.isdigit, b_tel))
    if "TEL_LIMPO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["TEL_LIMPO"].str.contains(t_l, na=False)]

# ==========================================
# 2. FILTROS DE SEGMENTAÇÃO (COMPLETO + FATURAMENTO REAL)
# ==========================================

# --- PASSO 0: LIMPEZA E CÁLCULO DE FATURAMENTO REAL ---

def limpar_cnpj(cnpj):
    return "".join(filter(str.isdigit, str(cnpj)))

# Garantimos que a base de vendas e a de filtros usem CNPJs apenas numéricos para o cruzamento
df_vendas_limpo = df_vendas.copy()
df_vendas_limpo[COL_CNPJ] = df_vendas_limpo[COL_CNPJ].apply(limpar_cnpj)
df_filtrado[COL_CNPJ + "_LIMPO"] = df_filtrado[COL_CNPJ].apply(limpar_cnpj)

# Soma das vendas reais
faturamento_total_base = df_vendas_limpo.groupby(COL_CNPJ)["VALOR"].sum()
df_filtrado["FAT_REAL"] = df_filtrado[COL_CNPJ + "_LIMPO"].map(faturamento_total_base).fillna(0)

def definir_faixa_real(v):
    if v <= 0: return "Sem Faturamento"
    elif v <= 5000: return "Até R$ 5k"
    elif v <= 20000: return "R$ 5k - 20k"
    elif v <= 50000: return "R$ 20k - 50k"
    else: return "Acima de R$ 50k"

df_filtrado["FAIXA_REAL"] = df_filtrado["FAT_REAL"].apply(definir_faixa_real)

# --- AGORA OS FILTROS DA SIDEBAR (ORDEM COMPLETA) ---

# 1. Filtro de Mês
m_lista = sorted(df_filtrado["MES_REF"].dropna().unique().tolist(), key=lambda x: pd.to_datetime(x, format='%m/%Y'), reverse=True)
mes_sel = st.sidebar.multiselect("Mês da Última Compra", m_lista, key="f_mes")
st.session_state["filtro_mes"] = mes_sel 
if mes_sel:
    df_filtrado = df_filtrado[df_filtrado["MES_REF"].isin(mes_sel)]

# 2. Filtro de Vendedor
v_lista = sorted(df_filtrado[COL_VENDEDOR].dropna().unique().tolist())
vendedor_sel = st.sidebar.multiselect("Vendedor", v_lista, key="f_vend")
if vendedor_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_VENDEDOR].isin(vendedor_sel)]

# 3. Filtro de Estado (UF)
u_lista = sorted(df_filtrado[COL_UF].dropna().unique().tolist())
uf_sel = st.sidebar.multiselect("Estado (UF)", u_lista, key="f_uf")
if uf_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_UF].isin(uf_sel)]

# 4. Filtro de Cidade
c_lista = sorted(df_filtrado[COL_CIDADE].dropna().unique().tolist())
cidade_sel = st.sidebar.multiselect("Cidade", c_lista, key="f_cid")
if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_CIDADE].isin(cidade_sel)]

# 5. Filtro de Bairro
b_lista = sorted(df_filtrado[COL_BAIRRO].dropna().unique().tolist())
bairro_sel = st.sidebar.multiselect("Bairro", b_lista, key="f_bair")
if bairro_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_BAIRRO].isin(bairro_sel)]

# 6. Filtro de Segmento
if COL_SEGMENTO in df_filtrado.columns:
    s_lista = sorted(df_filtrado[COL_SEGMENTO].dropna().unique().tolist())
    seg_sel = st.sidebar.multiselect("Segmento", s_lista, key="f_seg")
    if seg_sel:
        df_filtrado = df_filtrado[df_filtrado[COL_SEGMENTO].isin(seg_sel)]

# 7. Filtro de Faixa de Faturamento
ordem_f = ["Sem Faturamento", "Até R$ 5k", "R$ 5k - 20k", "R$ 20k - 50k", "Acima de R$ 50k"]
opcoes_f = [f for f in ordem_f if f in df_filtrado["FAIXA_REAL"].unique()]

fat_sel = st.sidebar.multiselect("Faixa de Faturamento (Real)", options=opcoes_f, key="f_fat_v_final")

if fat_sel:
    df_filtrado = df_filtrado[df_filtrado["FAIXA_REAL"].isin(fat_sel)]

# ==========================================
# 3. RAZÃO SOCIAL (CASCATA ATIVA)
# ==========================================
lista_clientes = [""] + sorted(df_filtrado[COL_RAZAO].dropna().unique().tolist())
cliente_sel = placeholder_razao.selectbox("Buscar Razão Social", options=lista_clientes, key="b_razao")
if cliente_sel != "":
    df_filtrado = df_filtrado[df_filtrado[COL_RAZAO] == cliente_sel]
    
# =========================
# TÍTULO
# =========================

st.title("Dashboard Inside Sales - PAPAPÁ")

# =========================
# KPIs (Sempre visíveis no topo do Dashboard Geral)
# =========================

st.divider()
k1, k2, k3, k4 = st.columns(4)

# KPIs baseados no df_filtrado (resultado dos filtros da sidebar)
k1.metric("Total Clientes", len(df_filtrado))
k2.metric("Estados Ativos", df_filtrado[COL_UF].nunique())
k3.metric("Segmentos", df_filtrado[COL_SEGMENTO].nunique())
k4.metric("Vendedores", df_filtrado[COL_VENDEDOR].nunique())

# =========================
# CARD CLIENTE + CRM (COMENTÁRIOS)
# =========================

vendas_cliente = pd.DataFrame()

if len(df_filtrado) == 1:
    cliente = df_filtrado.iloc[0]
    id_cliente = cliente["CNPJ_LIMPO"]
    
    # CHAMA O FAROL (Calculado na Parte 1)
    status_txt, status_cor = calcular_status_farol(cliente)

    st.markdown("### 🏢 Informações do Cliente")
    
    col_info, col_crm = st.columns([1, 1])

    with col_info:
        # 1. BUSCA DO LEAD TIME (Logística)
        prazo_html = ""
        try:
            # Lendo a aba do arquivo de lead time que você enviou
            # Nota: Certifique-se que o nome do arquivo está exato como abaixo
            df_lt = pd.read_excel("Tabela lead time operacao e comercial.xlsx", sheet_name="tabela de lead time")
            df_lt = df_lt.iloc[:, [0, 1, 2]] # Pega Cidade, UF e Prazo
            df_lt.columns = ['Cidade_Base', 'UF_Base', 'Prazo_Base']
            
            def normalizar_texto(txt):
                import unicodedata
                if pd.isna(txt): return ""
                return "".join(c for c in unicodedata.normalize('NFD', str(txt).upper().strip())
                               if unicodedata.category(c) != 'Mn')

            cidade_alvo = normalizar_texto(cliente[COL_CIDADE])
            uf_alvo = normalizar_texto(cliente[COL_UF])
            
            df_lt['Cid_Norm'] = df_lt['Cidade_Base'].apply(normalizar_texto)
            df_lt['UF_Norm'] = df_lt['UF_Base'].apply(normalizar_texto)
            
            busca_lt = df_lt[(df_lt['Cid_Norm'] == cidade_alvo) & (df_lt['UF_Norm'] == uf_alvo)]
            
            if not busca_lt.empty:
                v_prazo = busca_lt['Prazo_Base'].values[0]
                if pd.notna(v_prazo):
                    prazo_num = int(v_prazo)
                    if prazo_num == 0:
                        prazo_html = f"<br><b style='color:#27AE60;'>🚚 Entrega Imediata (CD Local)</b>"
                    else:
                        prazo_html = f"<br><b style='color:#E67E22;'>🚚 Prazo de Entrega: {prazo_num} dias úteis</b>"
                else:
                    prazo_html = "<br><i style='color:gray;'>📍 Prazo não preenchido no Excel</i>"
            else:
                prazo_html = f"<br><i style='color:gray; font-size:11px;'>📍 Logística não mapeada ({cidade_alvo})</i>"
        except:
            prazo_html = "<br><i style='color:red; font-size:11px;'>⚠️ Erro ao carregar Tabela de Lead Time</i>"

        # 2. REGRAS DE PRAZO DE PAGAMENTO
        uf_pagto = str(cliente[COL_UF]).upper().strip()
        if uf_pagto in ['RS', 'SC', 'PR', 'SP']:
            tabela_prazos = """
            <table style='width:100%; font-size:11px; border-collapse: collapse; margin-top:10px;'>
                <tr style='background-color:#eee;'><th>Valor Pedido</th><th>Prazo Boleto</th></tr>
                <tr><td>Até R$ 1.000</td><td>1x - 30 dias</td></tr>
                <tr><td>R$ 1.000 a R$ 2.000</td><td>2x - 30/45 dias</td></tr>
                <tr><td>Acima de R$ 2.000</td><td>3x - 30/45/60 dias</td></tr>
            </table>"""
        else:
            tabela_prazos = """
            <table style='width:100%; font-size:11px; border-collapse: collapse; margin-top:10px;'>
                <tr style='background-color:#eee;'><th>Valor Pedido</th><th>Prazo Boleto</th></tr>
                <tr><td>Até R$ 1.000</td><td>1x - 45 dias</td></tr>
                <tr><td>R$ 1.000 a R$ 2.000</td><td>2x - 45/60 dias</td></tr>
                <tr><td>Acima de R$ 2.000</td><td>3x - 40/50/60 dias</td></tr>
            </table>"""

        # TRATAMENTO DA DATA ÚLTIMA COMPRA
        data_bruta = cliente['ÚLTIMA COMPRA']
        if pd.notnull(data_bruta) and hasattr(data_bruta, 'strftime'):
            data_formatada = data_bruta.strftime('%d/%m/%Y')
        else:
            data_formatada = "Sem registro"

        # 3. QUADRO INFORMATIVO PRINCIPAL (CARD)
        st.markdown(
            f"""
            <div style="padding:20px; border-radius:10px; background-color:#f6f6f6; border-left: 8px solid {status_cor}; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="color:#333; margin:0;">{cliente[COL_RAZAO]}</h3>
                    <span style="background-color:{status_cor}; color:white; padding:5px 12px; border-radius:15px; font-weight:bold; font-size:12px;">
                        {status_txt}
                    </span>
                </div>
                <hr style='opacity:0.2; margin:10px 0;'>
                <b>Vendedor:</b> <span style="color:#1f77b4">{cliente[COL_VENDEDOR]}</span><br>
                <b>Última Compra:</b> {data_formatada}<br>
                <b>CNPJ:</b> {cliente[COL_CNPJ]}<br>
                <b>Segmento:</b> {cliente[COL_SEGMENTO]}<br>
                <b>Telefone:</b> {cliente[COL_TELEFONE]}<br>
                <b>E-mail:</b> {cliente[COL_EMAIL]}<br>
                <b>Cidade:</b> {cliente[COL_CIDADE]} - {cliente[COL_UF]}
                {prazo_html}
                <hr style='opacity:0.2; margin:10px 0;'>
                <b>💳 Condições Sugeridas:</b>
                {tabela_prazos}
                <p style='font-size:10px; color:gray; margin-top:5px;'>*Prazos padrão PAPAPÁ para esta região.</p>
            </div>
            """, unsafe_allow_html=True
        )

        # 4. BOTÕES DE AÇÃO (WhatsApp e PDF)
        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            tel_wpp = limpar_telefone(cliente[COL_TELEFONE])
            if tel_wpp:
                st.link_button("💬 WhatsApp", f"https://wa.me/55{tel_wpp}", use_container_width=True)
        
        with col_btn2:
            # Filtra vendas do cliente na aba MIX
            if not df_vendas.empty:
                v_cli = df_vendas[df_vendas["CNPJ_LIMPO"] == id_cliente]
                pdf_arq = gerar_pdf_cliente(cliente, v_cli)
                st.download_button("📄 Baixar Relatório PDF", data=pdf_arq, 
                                 file_name=f"relatorio_{id_cliente}.pdf", 
                                 mime="application/pdf", use_container_width=True)

# ... (Final do seu código de CRM aqui) ...
        
    # --- SAINDO DAS COLUNAS (Largura Total) ---
        
    # 2. GRÁFICO EM PÁGINA INTEIRA (Full Width)
    if not df_vendas.empty:
        id_cliente_str = str(id_cliente).strip()
        vendas_hist = df_vendas[df_vendas["CNPJ_LIMPO"] == id_cliente_str].copy()

        if not vendas_hist.empty:
            st.markdown("---")
            st.subheader("📈 Histórico Mensal de Compras")
            
            vendas_hist['DATA PEDIDO'] = pd.to_datetime(vendas_hist['DATA PEDIDO'], errors='coerce')
            vendas_hist = vendas_hist.dropna(subset=['DATA PEDIDO'])
            vendas_hist['MES_ANO'] = vendas_hist['DATA PEDIDO'].dt.strftime('%Y-%m')
            
            hist_mensal = vendas_hist.groupby('MES_ANO')['VALOR'].sum().reset_index()
            hist_mensal = hist_mensal.sort_values("MES_ANO")

            fig_hist_cli = px.bar(
                hist_mensal,
                x="MES_ANO",
                y="VALOR",
                text_auto='.2s',
                title="Evolução de Pedidos (R$)",
                color_discrete_sequence=["#E74C3C"]
            )
            
            # Força o gráfico a usar toda a largura disponível
            st.plotly_chart(fig_hist_cli, use_container_width=True)

    # --- COLUNA DIREITA: CRM ---
# ==========================================
# BLOCO CRM - SÓ APARECE COM 1 CLIENTE
# ==========================================

if len(df_filtrado) == 1:
    with col_crm:
        st.subheader("📝 Notas e Histórico")
        
        # 1. Seletor de usuário
        lista_pessoas = ["João Tadra", "Ana", "Pedro", "João Paulo", "Bernardo", "Thiago"]
        quem_comentou = st.selectbox("Quem está comentando?", lista_pessoas)

        # 2. Função disparada pelo botão
        def clicar_salvar():
            # Acessa o dicionário global de comentários
            global comentarios
            
            # Pega o texto da área de texto via session_state
            texto_digitado = st.session_state.get("txt_area_crm", "")
            
            if texto_digitado.strip():
                # Data e Hora (Brasília)
                agora = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M")
                texto_final = f"[{quem_comentou}] {texto_digitado.strip()}"
                
                # Garante que a chave do cliente existe
                id_cliente_str = str(id_cliente)
                if id_cliente_str not in comentarios:
                    comentarios[id_cliente_str] = []
                
                # Adiciona o novo comentário no topo da lista
                comentarios[id_cliente_str].insert(0, {"texto": texto_final, "data": agora})
                
                # SALVAMENTO FÍSICO
                salvar_comentarios(comentarios)
                
                # Limpa o campo para o próximo uso
                st.session_state["txt_area_crm"] = ""
                st.toast("✅ Nota salva com sucesso!")
            else:
                st.warning("O campo está vazio.")

        # 3. Campo de entrada de texto
        st.text_area(
            "Novo registro:", 
            placeholder="Descreva a conversa...", 
            key="txt_area_crm",
            height=120
        )
        
        # 4. Botão de Salvar
        st.button("Salvar Comentário", on_click=clicar_salvar, use_container_width=True)
        
        st.divider()

        # 5. Listagem do Histórico
        id_cliente_str = str(id_cliente)
        if id_cliente_str in comentarios and len(comentarios[id_cliente_str]) > 0:
            for idx, item in enumerate(comentarios[id_cliente_str]):
                with st.container():
                    col_txt, col_del = st.columns([0.85, 0.15])
                    
                    with col_txt:
                        st.caption(f"📅 {item['data']}")
                        st.write(item['texto'])
                    
                    with col_del:
                        if st.button("🗑️", key=f"btn_del_{id_cliente_str}_{idx}"):
                            comentarios[id_cliente_str].pop(idx)
                            salvar_comentarios(comentarios)
                            st.rerun()
                    
                    st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        else:
            st.info("Sem histórico para este cliente.")
else:
    # Mensagem amigável quando os filtros estão abertos (mais de 1 cliente)
    st.info("💡 Selecione um cliente específico nos filtros ao lado para visualizar mais detalhes sobre o cliente.")

# ==========================================
# CÁLCULO E EXIBIÇÃO DE LEAD TIME POR CLIENTE
# ==========================================

# 1. Carregamento da base de Lead Time
@st.cache_data
def carregar_lead_time():
    try:
        caminho = "Tabela lead time operacao e comercial.xlsx"
        # Lendo a aba 'base' (índice 2) que contém o detalhamento por transportador
        # Ajustamos skiprows=2 pois o cabeçalho real começa na linha 3
        df_lt = pd.read_excel(caminho, sheet_name="base", skiprows=2)
        
        # Selecionando: Cidade, UF, Lead Time Total, Transportador (ou Lead Time Transp se houver)
        # Baseado no seu arquivo: Coluna 3 (Cidade), 4 (UF), 5 (Lead Time)
        df_lt = df_lt.iloc[:, [3, 4, 5]] 
        df_lt.columns = ['Cidade', 'UF', 'Lead_Time_Total']
        
        return df_lt.dropna(subset=['Cidade', 'UF'])
    except Exception as e:
        st.error(f"Erro ao carregar detalhamento de Lead Time: {e}")
        return pd.DataFrame()

df_lead_time_detalhado = carregar_lead_time()

# 2. Exibição Detalhada
if 'id_cliente' in locals() and id_cliente:
    try:
        # Recupera dados do cliente selecionado
        dados_cadastrais = df_filtrado[df_filtrado["CNPJ_LIMPO"] == id_cliente].iloc[0]
        
        def normalizar_lt(txt):
            import unicodedata
            if pd.isna(txt): return ""
            return "".join(c for c in unicodedata.normalize('NFD', str(txt).upper().strip())
                           if unicodedata.category(c) != 'Mn')

        cidade_alvo = normalizar_lt(dados_cadastrais[COL_CIDADE])
        uf_alvo = normalizar_lt(dados_cadastrais[COL_UF])

        if not df_lead_time_detalhado.empty:
            # Normaliza a base de busca para garantir o cruzamento
            df_lt_copy = df_lead_time_detalhado.copy()
            df_lt_copy['Cid_Norm'] = df_lt_copy['Cidade'].apply(normalizar_lt)
            df_lt_copy['UF_Norm'] = df_lt_copy['UF'].apply(normalizar_lt)

            busca = df_lt_copy[
                (df_lt_copy['Cid_Norm'] == cidade_alvo) & 
                (df_lt_copy['UF_Norm'] == uf_alvo)
            ]

            if not busca.empty:
                lt_total = busca['Lead_Time_Total'].values[0]
                
                # Regra de negócio: Se o total é 7 dias, assumimos 2 de processamento e 5 de transporte
                # Ou conforme sua necessidade de cálculo interno:
                try:
                    total_dias = int(lt_total)
                    transp_estimado = max(1, total_dias - 2)
                    proc_interno = total_dias - transp_estimado
                except:
                    total_dias, transp_estimado, proc_interno = 0, 0, 0
            
            else:
                # Caso não encontre na aba 'base', o card anterior (Parte 6) já mostra o erro simplificado
                pass
    except Exception as e:
        # Silencioso para não poluir o Dashboard se o ID não estiver pronto
        pass

# ==========================================
# ANÁLISE DE COMPRAS (DENTRO DO IF DO CLIENTE ÚNICO)
# ==========================================

if not vendas_cliente.empty:
    st.divider()
    st.subheader("📊 Análise de Performance e Mix")

    # Garantir que a data está em formato datetime para ordenação correta nos gráficos
    vendas_cliente["DATA PEDIDO"] = pd.to_datetime(vendas_cliente["DATA PEDIDO"])

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        # MIX POR LINHA
        mix_linha = (
            vendas_cliente
            .groupby("LINHA")["VALOR"]
            .sum()
            .reset_index()
            .sort_values("VALOR", ascending=False)
        )
        fig_mix = px.pie(
            mix_linha,
            names="LINHA",
            values="VALOR",
            title="Distribuição por Linha de Produto",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_mix.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_mix, use_container_width=True)

    with col_graf2:
        # TOP PRODUTOS (Gráfico de Barras Horizontal)
        top_produtos = (
            vendas_cliente
            .groupby("DESC PRODUTO")["VALOR"]
            .sum()
            .reset_index()
            .sort_values("VALOR", ascending=True) # Ascending True para o maior ficar no topo da barra horizontal
            .tail(10)
        )
        fig_top = px.bar(
            top_produtos,
            x="VALOR",
            y="DESC PRODUTO",
            orientation="h",
            title="Top 10 Produtos (Valor Total)",
            labels={"VALOR": "Total Gasto (R$)", "DESC PRODUTO": "Produto"},
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_top, use_container_width=True)

    # EVOLUÇÃO DE COMPRAS (Agrupado por Mês para reduzir ruído)
    evolucao = (
        vendas_cliente
        .set_index("DATA PEDIDO")
        .resample('MS')["VALOR"] # MS = Month Start
        .sum()
        .reset_index()
    )
    
    fig_evolucao = px.area(
        evolucao,
        x="DATA PEDIDO",
        y="VALOR",
        title="Histórico de Volume de Compras Mensal",
        labels={"VALOR": "Total Mensal (R$)", "DATA PEDIDO": "Mês"},
        line_shape="spline"
    )
    fig_evolucao.update_traces(fillcolor="rgba(255, 75, 75, 0.2)", line_color="#FF4B4B")
    st.plotly_chart(fig_evolucao, use_container_width=True)

# ==========================================
# 🚀 INTELIGÊNCIA DE MERCADO - VERSÃO FINAL (SEM ERROS DE NOME OU INDENTAÇÃO)
# ==========================================
if len(df_filtrado) == 1:
    cliente = df_filtrado.iloc[0]
    id_cnpj = cliente["CNPJ_LIMPO"]
    
    vendas_cliente_atual = df_vendas[df_vendas["CNPJ_LIMPO"] == str(id_cnpj).strip()].copy()

    if not vendas_cliente_atual.empty:
        import unicodedata
        def limpar(t): 
            return "".join(c for c in unicodedata.normalize('NFD', str(t)) if unicodedata.category(c) != 'Mn').upper().strip()

        vendas_nomes = [limpar(n) for n in vendas_cliente_atual["DESC PRODUTO"].unique()]

        # --- PASSO 1: IDENTIFICADORES DE LINHA (DNA) ---
        # Definimos quem o cliente REALMENTE já compra para separar Salgada de Fruta
        ja_compra_salgada = any(("120G" in n or "SALGADA" in n) and not any(x in n for x in ["FRUTA", "DOCE", "MACA", "BANANA", "MANGA", "PERA", "AMEIXA", "MIRTILO"]) for n in vendas_nomes)
        ja_compra_palitinho = any("PALITINHO" in n for n in vendas_nomes)
        ja_compra_fruta = any(("100G" in n or "FRUTA" in n) and "PAPINHA" in n for n in vendas_nomes)
        
        catalogo_dna = {
            "LA CHEF": ["180G", "LENTILHA", "RISOTINHO", "CASEIRINHO"],
            "CEREAIS": ["CEREAL", "AVEIA", "MULTICEREAIS"],
            "SOPINHAS": ["SOPINHA", "240G"],
            "YOGUZINHO": ["YOGU", "IOGURTE"],
            "BISCOTTI": ["BISCOTTI"],
            "DENTIÇÃO": ["DENTICAO"],
            "MACARRÃO": ["MACARRAO", "ELBOW", "FUSILLI"]
        }

        # --- PASSO 2: CATÁLOGO COMPLETO (MANTIDO 100%) ---
        catalogo_papapa = {
            "LA CHEF": {
                "Lentilha Carne Legumes 180g": ["LENTILHA"],
                "Risotinho Arroz Quinoa Frango 180g": ["RISOTINHO"],
                "Caseirinho Arroz Feijão Carne Leg. 180g": ["CASEIRINHO"]
            },
            "SOPINHAS": {
                "Sopinha Frango Arroz Legumes 240g": ["SOPINHA", "FRANGO"],
                "Sopinha Carne Macarrao Legumes 240g": ["SOPINHA", "MACARRAO"],
                "Sopinha Carne Mandioquinha Leg 240g": ["SOPINHA", "MANDIOQ"],
                "Sopinha Feijão Carne Leg 240g": ["SOPINHA", "FEIJAO"]
            },
            "YOGUZINHO": {
                "Iogurte Frutas Amarelas e Banana 100g": ["IOGURTE", "AMARELAS"],
                "Iogurte Frutas Vermelhas e Banana 100g": ["IOGURTE", "VERMELHAS"]
            },
            "PAPINHAS SALGADAS": {
                "Papinha Carne Arroz Legumes 120g": ["CARNE", "120G"],
                "Papinha Frango Grão Vegetais 120g": ["FRANGO", "120G"]
            },
            "PAPINHAS DE FRUTAS": {
                "Papinha Org Maçã Ameixa 100g": ["MACA", "AMEIXA"],
                "Papinha Org Banana Mirtilo Quinoa 100g": ["BANANA", "MIRTILO"],
                "Papinha Org Manga 100g": ["MANGA"],
                "Papinha Org Pera Espinafre Abobrinha 100g": ["PERA", "ESPINA"],
                "Papinha Org Maçã B. Doce Cenoura 100g": ["DOCE", "CENOURA"],
                "Papinha Org Morango Maçã 100g": ["MORANGO", "MACA"]
            },
            "BISCOTTI": {
                "Biscotti Laranja e Cenoura 60g": ["BISCOTTI", "LARANJ"],
                "Biscotti Maçã e Canela 60g": ["BISCOTTI", "MAC", "CANEL"],
                "Biscotti Banana e Cacau 60g": ["BISCOTTI", "CACAU"],
                "Biscotti Goiaba 60g": ["BISCOTTI", "GOIAB"],
                "Biscotti Maracujá e Camomila 60g": ["BISCOTTI", "MARACUJ"] 
            },
            "PALITINHOS": {
                "Palitinho Org. Beterraba 20g": ["PALITINHO", "BETERRABA"],
                "Palitinho Org. Cenoura 20g": ["PALITINHO", "CENOURA"],
                "Palitinho Org. Tomate/Manjericão 20g": ["PALITINHO", "TOMATE"]
            },
            "DENTIÇÃO": {
                "Biscoito de Dentição Maçã e Abóbora": ["DENTICAO", "ABOBORA"],
                "Biscoito de Dentição Vegetais": ["DENTICAO", "VEGETAIS"]
            },
            "MACARRÃO": {
                "Macarrão Inf. Elbow Quinoa 200g": ["ELBOW", "QUINOA"],
                "Macarrão Inf. Fusilli Vegetais 200g": ["FUSILLI", "VEGETAIS"]
            },
            "CEREAIS": {
                "Cereal Multicereais 170g": ["CEREAL", "MULTI", "170G"],
                "Cereal Multicereais 500g": ["CEREAL", "MULTI", "500G"],
                "Cereal Aveia Morango e Beterraba 170g": ["AVEIA", "MORANGO"],
                "Cereal Aveia Banana e Ameixa 170g": ["AVEIA", "BANANA"]
            }
        }

        gap_mix = []
        cross_sell = []

        # --- PASSO 3: LÓGICA DE SEPARAÇÃO ---
        for linha, skus_dict in catalogo_papapa.items():
            # Define se o cliente já trabalha a linha
            if linha == "PAPINHAS SALGADAS":
                trabalha_a_linha = ja_compra_salgada
            elif linha == "PALITINHOS":
                trabalha_a_linha = ja_compra_palitinho
            elif linha == "PAPINHAS DE FRUTAS":
                trabalha_a_linha = ja_compra_fruta
            else:
                ids_dna = catalogo_dna.get(linha, [])
                trabalha_a_linha = any(any(id_dna in n for id_dna in ids_dna) for n in vendas_nomes)

            # Valida cada SKU dentro da linha
            for nome_exibicao, keywords in skus_dict.items():
                ja_tem_sku = any(all(limpar(k) in n for k in keywords) for n in vendas_nomes)

                if not ja_tem_sku:
                    item = {"Linha": linha, "Produto": nome_exibicao}
                    if trabalha_a_linha:
                        gap_mix.append(item)
                    else:
                        cross_sell.append(item)

        # --- PASSO 4: EXIBIÇÃO NO DASHBOARD ---
        st.subheader("📦 Análise Geral de Mix e Produtos")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🚨 Gap de Mix")
            if gap_mix:
                st.dataframe(pd.DataFrame(gap_mix), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Mix completo nas categorias atuais!")
        with c2:
            st.markdown("#### 📦 Cross-sell")
            if cross_sell:
                st.dataframe(pd.DataFrame(cross_sell), use_container_width=True, hide_index=True)
            else:
                st.info("💡 Já compra todas as linhas!")
                
# ==========================================

st.subheader("📦 Análise Geral de Mix e Produtos")

if not df_vendas.empty:
    # 1. Filtro de Segurança: Analisar apenas vendas dos clientes visíveis na sidebar
    cnpjs_visiveis = df_filtrado["CNPJ_LIMPO"].unique()
    vendas_geral = df_vendas[df_vendas["CNPJ_LIMPO"].isin(cnpjs_visiveis)].copy()
    
    # Limpeza de ruído (Blacklist)
    blacklist_geral = ["CONFERIDO", "AJUSTE", "TESTE", "FRETE"]
    regex_geral = "|".join(blacklist_geral)
    vendas_geral = vendas_geral[~vendas_geral["DESC PRODUTO"].str.upper().str.contains(regex_geral, na=False)]

    if not vendas_geral.empty:
        # 2. MAPEAMENTO INTELIGENTE (Categorização PAPAPÁ)
        
        def mapear_catalogo_detalhado(nome):
            nome = str(nome).upper()
            # Dicionário baseado nas linhas oficiais que você passou
            catalogo = {
                "LA CHEF": ["LENTILHA", "RISOTINHO", "CASEIRINHO"],
                "SOPINHAS": ["SOPINHA"],
                "YOGUZINHO": ["IOGURTE", "YOGUZINHO"],
                "PAPINHAS SALGADAS": ["CARNE", "ARROZ", "120G", "GRAO"],
                "PAPINHAS DE FRUTAS": ["MACA", "AMEIXA", "BANANA", "MIRTILO", "MANGA", "PERA", "ESPINA", "DOCE", "CENOURA", "MORANGO"],
                "BISCOTTI": ["LARANJ", "MAC", "CANEL", "CACAU", "GOIAB", "MARACUJ", "BISCOTTI"],
                "PALITINHOS": ["PALIT"],
                "DENTIÇÃO": ["DENTICAO"],
                "MACARRÃO": ["ELBOW", "FUSILLI", "MASSA", "LETRE"],
                "CEREAIS": ["CEREAL", "AVEIA"]
            }
            for linha, keywords in catalogo.items():
                if any(key in nome for key in keywords):
                    return linha
            

        def mapear_sabor(nome):
            nome = str(nome).upper()
            doces = ["FRUTA", "BANANA", "MAÇÃ", "MAMAO", "AMEIXA", "DOCE", "CACAU", "LARANJA", "MORANGO", "MANGA", "PERA", "IOGURTE", "YOGUZINHO"]
            return "Doce" if any(x in nome for x in doces) else "Salgado"

        def mapear_idade(nome):
            nome = str(nome).upper()
            if "12" in nome or "CEREAL" in nome or "PALIT" in nome: return "12 meses+"
            if any(x in nome for x in ["MACARRÃO", "MASSA", "LETRE", "ELBOW", "FUSILLI"]): return "8 meses+"
            return "6 meses+"

        # Aplicando as novas classificações
        vendas_geral["CAT_CATALOGO"] = vendas_geral["DESC PRODUTO"].apply(mapear_catalogo_detalhado)
        vendas_geral["SABOR"] = vendas_geral["DESC PRODUTO"].apply(mapear_sabor)
        vendas_geral["IDADE"] = vendas_geral["DESC PRODUTO"].apply(mapear_idade)

        # 3. LINHA 1 DE GRÁFICOS (Mix por Linha e Sabores)
        c1, c2 = st.columns(2)
        with c1:
            mix_cat = vendas_geral.groupby("CAT_CATALOGO")["VALOR"].sum().reset_index()
            fig_mix_cat = px.pie(mix_cat, names="CAT_CATALOGO", values="VALOR", 
                                title="Mix por Linha de Produto", hole=0.4, 
                                color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_mix_cat.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_mix_cat, use_container_width=True)
            
        with c2:
            mix_sabor = vendas_geral.groupby("SABOR")["VALOR"].sum().reset_index()
            fig_sabor = px.pie(mix_sabor, names="SABOR", values="VALOR", 
                               title="Divisão Doce vs Salgado", 
                               color_discrete_map={"Doce":"#FFB6C1","Salgado":"#90EE90"})
            fig_sabor.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_sabor, use_container_width=True)

        # 4. LINHA 2 DE GRÁFICOS (Idade e Top 10)
        c3, c4 = st.columns(2)
        with c3:
            # Ordenação lógica das idades
            vendas_geral["IDADE"] = pd.Categorical(vendas_geral["IDADE"], categories=["6 meses+", "8 meses+", "12 meses+"], ordered=True)
            mix_idade = vendas_geral.groupby("IDADE", observed=True)["VALOR"].sum().reset_index()
            
            fig_idade = px.bar(mix_idade, x="IDADE", y="VALOR", color="IDADE", 
                               title="Vendas por Faixa Etária",
                               color_discrete_sequence=px.colors.qualitative.Safe)
            fig_idade.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_idade, use_container_width=True)
            
        with c4:
            top_10_geral = (vendas_geral.groupby("DESC PRODUTO")["VALOR"].sum()
                            .reset_index().sort_values("VALOR", ascending=True).tail(10))
            fig_top_geral = px.bar(top_10_geral, x="VALOR", y="DESC PRODUTO", orientation="h", 
                                   title="Top 10 Produtos Mais Vendidos",
                                   color="VALOR", color_continuous_scale="Reds")
            fig_top_geral.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_top_geral, use_container_width=True)

else:
    st.warning("Base de vendas não encontrada. Verifique o arquivo de dados.")
    
# ==========================================
# 🏆 PERFORMANCE POR LINHA (VISÃO DETALHADA)
# ==========================================

# 1. Só aparece se houver exatamente 1 cliente selecionado
if len(df_filtrado) == 1:
    # 2. Só aparece se a variável de vendas existir (evita o NameError)
    if 'vendas_cliente_atual' in locals() and not vendas_cliente_atual.empty:
        st.markdown("---")
        st.markdown("#### 🏆 Performance por Linha de Produto")
        
        # Usamos as categorias oficiais da Papapá
        linhas_papapa = [
            "PAPINHAS SALGADAS", "YOGUZINHO", "PAPINHAS DE FRUTAS", 
            "PALITINHOS", "DENTIÇÃO", "MACARRÃO", "LA CHEF", 
            "CEREAIS", "BISCOTTI", "SOPINHAS"
        ]
        
        linha_selecionada = st.selectbox("Selecione uma linha para análise:", options=linhas_papapa)

        # Filtro de dados para a linha escolhida
        df_detalhe_linha = vendas_cliente_atual[vendas_cliente_atual["LINHA"] == linha_selecionada]
        
        if not df_detalhe_linha.empty:
            # Agrupar performance por SKU (usando VALOR TOTAL ou VALOR dependendo da sua coluna)
            col_valor = "VALOR TOTAL" if "VALOR TOTAL" in df_detalhe_linha.columns else "VALOR"
            col_qtd = "QTD" if "QTD" in df_detalhe_linha.columns else "QTDE"

            performance_sku = df_detalhe_linha.groupby("DESC PRODUTO")[col_valor].sum().sort_values(ascending=False).reset_index()
            
            c_top, c_vol = st.columns(2)
            
            with c_top:
                st.success(f"⭐ **Mais Comprados: {linha_selecionada}**")
                df_top_sku = performance_sku.head(5).copy()
                df_top_sku[col_valor] = df_top_sku[col_valor].apply(lambda x: f"R$ {x:,.2f}")
                st.table(df_top_sku.rename(columns={"DESC PRODUTO": "Produto", col_valor: "Total Gasto"}))
                
            with c_vol:
                total_linha = df_detalhe_linha[col_valor].sum()
                qtd_total = df_detalhe_linha[col_qtd].sum()
                
                st.metric(label=f"Investimento Total em {linha_selecionada}", value=f"R$ {total_linha:,.2f}")
                st.metric(label="Volume Total (Unidades)", value=int(qtd_total))
                
                # Gráfico de barras lateral
                fig_bar_linha = px.bar(
                    performance_sku.head(5), 
                    x=col_valor, 
                    y="DESC PRODUTO", 
                    orientation='h',
                    title="Top 5 SKUs por Valor",
                    labels={col_valor: "Valor (R$)", "DESC PRODUTO": "Produto"},
                    color_discrete_sequence=["#00CC96"]
                )
                fig_bar_linha.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_bar_linha, use_container_width=True)
        else:
            st.warning(f"O cliente ainda não realizou compras na linha '{linha_selecionada}'.")
            st.info(f"💡 Dica: Verifique os itens de {linha_selecionada} no **Cross-sell** acima!")
    else:
        st.info("ℹ️ Selecione um cliente com histórico de vendas para ver a performance por linha.")
        
# ==========================================
# 📊 DISTRIBUIÇÃO CADASTRAL (CORREÇÃO COLUNA FATURAMENTO)
# ==========================================

if len(df_filtrado) > 1:
    st.markdown("---")
    st.subheader("📊 Distribuição Cadastral")
    
    col1, col2 = st.columns(2)

    with col1:
        resumo_seg = df_filtrado[COL_SEGMENTO].value_counts().reset_index()
        resumo_seg.columns = ["Segmento", "Quantidade"]
        
        fig_seg = px.bar(
            resumo_seg, x="Quantidade", y="Segmento", orientation="h",
            title="Distribuição por Segmento",
            color="Quantidade", color_continuous_scale="Reds"
        )
        fig_seg.update_layout(margin=dict(l=150, r=20, t=50, b=20), height=450, showlegend=False)
        st.plotly_chart(fig_seg, use_container_width=True)

    with col2:
        # 1. Identificamos a coluna correta que você mencionou
        col_faturamento_real = "TOTAL ÚLTIMOS 9 MESES"
        
        if col_faturamento_real in df_filtrado.columns:
            # 2. Criamos as faixas de faturamento (ajuste os valores se precisar)
            def categorizar_faturamento(valor):
                try:
                    v = float(valor)
                    if v <= 5000: return "Até R$ 5k"
                    elif v <= 20000: return "R$ 5k - 20k"
                    elif v <= 50000: return "R$ 20k - 50k"
                    else: return "Acima de R$ 50k"
                except:
                    return "Não Identificado"

            # Criamos uma coluna temporária para o gráfico
            temp_df = df_filtrado.copy()
            temp_df["FAIXA_TEMP"] = temp_df[col_faturamento_real].apply(categorizar_faturamento)
            
            resumo_fat = temp_df["FAIXA_TEMP"].value_counts().reset_index()
            resumo_fat.columns = ["Faixa", "Quantidade"]

            fig_fat = px.pie(
                resumo_fat, names="Faixa", values="Quantidade",
                title="Distribuição por Faturamento (9 Meses)",
                hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r
            )
            fig_fat.update_layout(
                margin=dict(l=20, r=20, t=50, b=20),
                height=450,
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_fat, use_container_width=True)
        else:
            st.error(f"⚠️ Coluna '{col_faturamento_real}' não encontrada na planilha.")
    
    st.divider()

    # ==========================================
    # 🗺️ PRESENÇA GEOGRÁFICA
    # ==========================================
    st.subheader("🗺️ Presença Geográfica")

    resumo_estado = df_filtrado[COL_UF].value_counts().reset_index()
    resumo_estado.columns = ["UF", "Quantidade"]

    url_geojson = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

    try:
        import urllib.request, json
        with urllib.request.urlopen(url_geojson) as response:
            geojson_br = json.load(response)

        fig_mapa = px.choropleth(
            resumo_estado,
            geojson=geojson_br,
            locations="UF",
            featureidkey="properties.sigla",
            color="Quantidade",
            color_continuous_scale="Reds",
            title="Concentração de Clientes por Estado",
            scope="south america",
            labels={"Quantidade": "Nº de Clientes"}
        )

        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

        st.plotly_chart(fig_mapa, use_container_width=True)
    except:
        st.warning("⚠️ Não foi possível carregar o mapa. Verificando conexão...")
        st.bar_chart(resumo_estado.set_index("UF"))

    st.divider()

# ==========================================
# 🏆 RESULTADO FINANCEIRO E RANKING (VISUAL PREMIUM)
# ==========================================

st.markdown("### 💰 Resultado Financeiro e Ranking")

if not df_filtrado.empty:
    meses_selecionados = st.session_state.get("filtro_mes", [])

    if not meses_selecionados:
        st.info("💡 Selecione um ou mais meses no filtro lateral para visualizar o faturamento e o ranking.")
    else:
        # 1. Tradutor de Meses (Filtro -> Planilha)
        tradutor_meses = {
            "01": "JAN", "02": "FEV", "03": "MAR", "04": "ABR",
            "05": "MAI", "06": "JUN", "07": "JUL", "08": "AGO",
            "09": "SET", "10": "OUT", "11": "NOV", "12": "DEZ"
        }

        colunas_reais = []
        for m in meses_selecionados:
            try:
                mes_num, ano_num = m.split("/")
                nome_coluna = f"{tradutor_meses[mes_num]}/{ano_num[2:]}"
                if nome_coluna in df_filtrado.columns:
                    colunas_reais.append(nome_coluna)
            except: continue

        if not colunas_reais:
            st.warning("⚠️ Nenhuma coluna de faturamento encontrada para este período.")
        else:
            # 2. Cálculos
            df_calc = df_filtrado.copy()
            for col in colunas_reais:
                df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)

            df_calc["TOTAL_VENDAS"] = df_calc[colunas_reais].sum(axis=1)
            total_periodo = df_calc["TOTAL_VENDAS"].sum()
            qtd_clientes = df_filtrado[COL_RAZAO].nunique()
            
            ranking = df_calc.groupby(COL_VENDEDOR)["TOTAL_VENDAS"].sum().sort_values(ascending=False).reset_index()

            # 3. ESTILIZAÇÃO DOS CARDS (KPIs)
            st.markdown("---")
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7bcf;">
                        <p style="color: #555; margin-bottom: 5px; font-size: 14px; font-weight: bold;">FATURAMENTO TOTAL ({', '.join(colunas_reais)})</p>
                        <h2 style="color: #1f77b4; margin: 0;">R$ {total_periodo:,.2f}</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
                        <p style="color: #555; margin-bottom: 5px; font-size: 14px; font-weight: bold;">CLIENTES ATENDIDOS</p>
                        <h2 style="color: #ff4b4b; margin: 0;">{qtd_clientes}</h2>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 4. RANKING ESTILIZADO EM TABELA LIMPA
            st.markdown("#### 🥇 Ranking de Performance")
            
            # Criando uma visualização de ranking mais elegante
            for i, row in ranking.iterrows():
                valor = f"R$ {row['TOTAL_VENDAS']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                # Cores e ícones por posição
                cor_fundo = "#fffdf0" if i == 0 else "#f8f9fa"
                emoji = "🏆" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
                
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; 
                                background-color: {cor_fundo}; padding: 10px 15px; border-radius: 8px; 
                                margin-bottom: 5px; border: 1px solid #eee;">
                        <span style="font-weight: bold; color: #333;">{i+1}º {emoji} {row[COL_VENDEDOR]}</span>
                        <span style="font-family: monospace; font-weight: bold; color: #2e7bcf;">{valor}</span>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================
# 📂 EXPORTAÇÃO E LISTAGEM (MANTIDOS)
# ==========================================
st.markdown("---")
if not df_filtrado.empty:
    def gerar_excel(df_exp):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            cols_excluir = ["MES_REF", "CONTATO", "TEL_LIMPO", "CNPJ_LIMPO", "TOTAL_VENDAS"]
            df_exp.drop(columns=[c for c in cols_excluir if c in df_exp.columns]).to_excel(writer, index=False)
        return buffer.getvalue()

    st.download_button(label="📥 Baixar Base Completa", data=gerar_excel(df_filtrado), 
                       file_name="vendas_papapa.xlsx", use_container_width=True)

st.subheader("📋 Listagem Detalhada")

# WhatsApp e Tabela (Sua lógica que já funciona)
def criar_link_whatsapp(tel):
    if not tel or pd.isna(tel): return None
    num = "".join(filter(str.isdigit, str(tel)))
    if len(num) > 0 and not num.startswith("55"): num = "55" + num
    return f"https://wa.me/{num}"

df_filtrado["CONTATO"] = df_filtrado["TELEFONE"].apply(criar_link_whatsapp)
cols = list(df_filtrado.columns)
if "TELEFONE" in cols and "CONTATO" in cols:
    idx = cols.index("TELEFONE")
    cols.insert(idx + 1, cols.pop(cols.index("CONTATO")))
    df_filtrado = df_filtrado[cols]

# Configurações de exibição
colunas_meses = [c for c in df_filtrado.columns if "/" in c and len(c) == 6]
config_moeda = {c: st.column_config.NumberColumn(c, format="R$ %.2f") for c in colunas_meses}

st.dataframe(
    df_filtrado,
    column_config={
        "CONTATO": st.column_config.LinkColumn("WhatsApp", display_text="💬 Chamar"),
        "ÚLTIMA COMPRA": st.column_config.DateColumn("Última Compra", format="DD/MM/YYYY"),
        **config_moeda,
        **{c: None for c in ["CNPJ_LIMPO", "TEL_LIMPO", "MES_REF", "TOTAL_VENDAS"] if c in df_filtrado.columns}
    },
    use_container_width=True, hide_index=True
)

st.markdown("<div style='text-align: center; color: #888; font-size: 12px; margin-top: 50px;'>Dashboard Inside Sales Papapá © 2026 - v1.2</div>", unsafe_allow_html=True)






























































































