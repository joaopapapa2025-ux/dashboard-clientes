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

import json
import os

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

if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False

if not st.session_state.acesso_liberado:

    st.title("Acesso restrito")

    codigo_digitado = st.text_input(
        "Digite o código de acesso",
        type="password"
    )

    if st.button("Entrar"):

        if codigo_digitado == CODIGO_ACESSO:
            st.session_state.acesso_liberado = True
            st.rerun()

        else:
            st.error("Código incorreto")

    st.stop()

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
# TRATAR FATURAMENTO
# =========================

# Converte para numérico garantindo que a nova coluna de 9 meses seja lida corretamente
df[COL_T_U_9_M] = pd.to_numeric(df[COL_T_U_9_M], errors="coerce").fillna(0)

bins = [0, 5000, 20000, 50000, 100000, float("inf")]

labels = [
    "Até 5 mil",
    "5 mil – 20 mil",
    "20 mil – 50 mil",
    "50 mil – 100 mil",
    "Acima de 100 mil"
]

# Cria a faixa baseada no faturamento acumulado da nova planilha
df["FAIXA_FATURAMENTO"] = pd.cut(df[COL_T_U_9_M], bins=bins, labels=labels)

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
# FUNÇÃO GERAR PDF
# =========================

def gerar_pdf_cliente(cliente, vendas_cliente):

    buffer = BytesIO()
    styles = getSampleStyleSheet()

    style_tabela = styles["BodyText"]
    style_tabela.leading = 14

    elementos = []

    titulo = Paragraph("Relatório de Cliente - PAPAPÁ", styles["Title"])
    data = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"])

    elementos.append(titulo)
    elementos.append(data)
    elementos.append(Spacer(1,20))

    # Tabela de dados cadastrais usando o novo mapeamento
    dados_cliente = [
        ["Razão Social", str(cliente[COL_RAZAO])],
        ["CNPJ", str(cliente[COL_CNPJ])],
        ["Telefone", str(cliente[COL_TELEFONE])],
        ["Email", str(cliente[COL_EMAIL])],
        ["Cidade", f"{cliente[COL_CIDADE]} - {cliente[COL_UF]}"],
        ["Vendedor", str(cliente[COL_VENDEDOR])],
        ["Segmento", str(cliente[COL_SEGMENTO])], # Ajustado para SEGMENTO
        ["Faturamento 9M", f"R$ {cliente[COL_T_U_9_M]:,.2f}"],
        ["Faixa", str(cliente["FAIXA_FATURAMENTO"])]
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
        # Agrupamento baseado nas colunas da aba MIX da nova planilha
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

        # Verifica se as colunas de NF e Data existem no Mix para os cálculos
        if "NUMERO NF" in vendas_cliente.columns:
            total_pedidos = vendas_cliente["NUMERO NF"].nunique()
            if total_pedidos > 0:
                ticket_medio = total_valor / total_pedidos

        if "DATA PEDIDO" in vendas_cliente.columns:
            data_max = vendas_cliente["DATA PEDIDO"].max()
            if pd.notna(data_max):
                ultima_compra = pd.to_datetime(data_max).strftime("%d/%m/%Y")

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
        elementos.append(Spacer(1,25))

        # HISTÓRICO POR PEDIDO
        elementos.append(Paragraph("Histórico por Pedido", styles["Heading3"]))

        # Agrupamento por Nota Fiscal usando as colunas da aba MIX
        pedidos = (
            vendas_cliente
            .groupby(["DATA PEDIDO", "NUMERO NF"])["VALOR"]
            .sum()
            .reset_index()
            .sort_values("DATA PEDIDO", ascending=False)
        )

        dados_pedidos = [["Data", "NF", "Valor Pedido"]]

        for _, row in pedidos.iterrows():
            data_str = ""
            if not pd.isna(row["DATA PEDIDO"]):
                # Garante conversão para datetime antes de formatar
                data_str = pd.to_datetime(row["DATA PEDIDO"]).strftime("%d/%m/%Y")

            nf = str(row["NUMERO NF"])
            valor = f"R$ {row['VALOR']:,.2f}"

            dados_pedidos.append([data_str, nf, valor])

        tabela_pedidos = Table(
            dados_pedidos,
            colWidths=[4*cm, 4*cm, 4*cm],
            repeatRows=1
        )

        tabela_pedidos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))

        elementos.append(tabela_pedidos)
        elementos.append(Spacer(1, 25))

        # TOP PRODUTOS
        elementos.append(Paragraph("Top Produtos Comprados", styles["Heading3"]))

        # Pega os 5 produtos de maior valor (usando o 'resumo' calculado na parte 2)
        top_produtos = resumo.head(5)

        dados_top = [["Produto", "Linha", "Qtd", "Valor"]]

        for _, row in top_produtos.iterrows():
            dados_top.append([
                Paragraph(str(row["DESC PRODUTO"]), style_tabela),
                Paragraph(str(row["LINHA"]), style_tabela),
                int(row["QTDE"]),
                f"R$ {row['VALOR']:,.2f}"
            ])

        tabela_top = Table(
            dados_top,
            colWidths=[8*cm, 3.5*cm, 2*cm, 2.5*cm],
            repeatRows=1
        )

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

        # HISTÓRICO DETALHADO POR PRODUTO
        elementos.append(Paragraph("Histórico Detalhado de Compras", styles["Heading3"]))

        dados_produtos = [
            ["Data", "NF", "Produto", "Linha", "Qtd", "Valor"]
        ]

        # Itera sobre os itens individuais da venda
        for _, row in vendas_cliente.iterrows():
            data_item = ""
            if not pd.isna(row["DATA PEDIDO"]):
                data_item = pd.to_datetime(row["DATA PEDIDO"]).strftime("%d/%m/%Y")

            nf_item = str(row["NUMERO NF"]) if not pd.isna(row["NUMERO NF"]) else ""
            prod_item = Paragraph(str(row["DESC PRODUTO"]), style_tabela)
            lin_item = Paragraph(str(row["LINHA"]), style_tabela)
            
            # Tratamento para quantidade e valor nulos
            qtd_item = int(row["QTDE"]) if pd.notna(row["QTDE"]) else 0
            val_item = f"R$ {row['VALOR']:,.2f}" if pd.notna(row["VALOR"]) else "R$ 0.00"

            dados_produtos.append([
                data_item,
                nf_item,
                prod_item,
                lin_item,
                qtd_item,
                val_item
            ])

        tabela_produtos = Table(
            dados_produtos,
            colWidths=[2.5*cm, 2.5*cm, 7*cm, 3.5*cm, 2*cm, 2.5*cm],
            repeatRows=1
        )

        tabela_produtos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (4, 1), (4, -1), "CENTER"),
            ("ALIGN", (5, 1), (5, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8), # Fonte menor para caber mais itens
        ]))

        elementos.append(tabela_produtos)

    else:
        elementos.append(Paragraph("Nenhum histórico de compra encontrado no período.", styles["Normal"]))

    # Finalização do Documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=18
    )

    doc.build(elementos)
    buffer.seek(0)
    return buffer
    
# =========================
# SIDEBAR
# =========================

# --- ADICIONE ESTE BLOCO LOGO APÓS CARREGAR O DF ---
# Garante que a coluna de telefone seja tratada e limpa para a busca
if COL_TELEFONE in df.columns:
    df["TEL_LIMPO"] = df[COL_TELEFONE].astype(str).str.replace(r'\D', '', regex=True)
else:
    # Caso a coluna não exista, cria uma vazia para não dar erro no filtro
    df["TEL_LIMPO"] = ""
# --------------------------------------------------

st.sidebar.title("Filtros")

# Inicialização de estados caso não existam (evita erros no primeiro carregamento)
if "busca_cnpj" not in st.session_state: st.session_state["busca_cnpj"] = ""
if "busca_nome" not in st.session_state: st.session_state["busca_nome"] = ""

if st.sidebar.button("Limpar filtros"):

    st.session_state["busca_cnpj"] = ""
    st.session_state["busca_nome"] = ""
    st.session_state["busca_email"] = ""
    st.session_state["busca_tel"] = ""

    st.session_state["filtro_vendedor"] = []
    st.session_state["filtro_uf"] = []
    st.session_state["filtro_cidade"] = []
    st.session_state["filtro_bairro"] = []
    st.session_state["filtro_categoria"] = [] # Internamente mapeado para SEGMENTO
    st.session_state["filtro_faturamento"] = []

    st.rerun()

df_filtrado = df.copy()

# =========================
# BUSCA CNPJ
# =========================

busca_cnpj = st.sidebar.text_input("Buscar por CNPJ", key="busca_cnpj")

if busca_cnpj:
    # Usa a função limpar_cnpj que definimos na Parte 1
    cnpj_busca_limpo = limpar_cnpj(busca_cnpj)

    df_filtrado = df_filtrado[
        df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_busca_limpo, na=False)
    ]

# =========================
# BUSCA RAZÃO SOCIAL
# =========================

busca_nome = st.sidebar.text_input("Buscar Razão Social", key="busca_nome")

cliente_escolhido = None

if busca_nome:
    # Usa COL_RAZAO da nossa configuração
    sugestoes = df[
        df[COL_RAZAO].str.contains(busca_nome, case=False, na=False)
    ][COL_RAZAO].drop_duplicates().head(50)

    if len(sugestoes) > 0:

        cliente_escolhido = st.sidebar.selectbox(
            "Selecione o cliente",
            sugestoes
        )

        df_filtrado = df_filtrado[
            df_filtrado[COL_RAZAO] == cliente_escolhido
        ]
        
# =========================
# BUSCA EMAIL
# =========================

busca_email = st.sidebar.text_input("Buscar por E-mail", key="busca_email")

if busca_email:
    # Usa COL_EMAIL definido no bloco de mapeamento
    df_filtrado = df_filtrado[
        df_filtrado[COL_EMAIL].str.contains(busca_email, case=False, na=False)
    ]

# =========================
# BUSCA TELEFONE
# =========================

tel_busca = st.sidebar.text_input("Buscar por Telefone:")
# Limpa o que o usuário digitou (remove parênteses e traços)
tel_busca_limpo = "".join(filter(str.isdigit, tel_busca))

if tel_busca_limpo:
    df_filtrado = df_filtrado[df_filtrado["TEL_LIMPO"].str.contains(tel_busca_limpo, na=False)]

# =========================
# FILTROS MULTISELECT
# =========================

# Vendedor
vendedores = sorted(df_filtrado[COL_VENDEDOR].dropna().unique())
vendedor_sel = st.sidebar.multiselect("Vendedor", vendedores, key="filtro_vendedor")

if vendedor_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_VENDEDOR].isin(vendedor_sel)]

# UF (Estado)
ufs = sorted(df_filtrado[COL_UF].dropna().unique())
uf_sel = st.sidebar.multiselect("Estado (UF)", ufs, key="filtro_uf")

if uf_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_UF].isin(uf_sel)]

# Cidade
cidades = sorted(df_filtrado[COL_CIDADE].dropna().unique())
cidade_sel = st.sidebar.multiselect("Cidade", cidades, key="filtro_cidade")

if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_CIDADE].isin(cidade_sel)]

# Bairro
bairros = sorted(df_filtrado[COL_BAIRRO].dropna().unique())
bairro_sel = st.sidebar.multiselect("Bairro", bairros, key="filtro_bairro")

if bairro_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_BAIRRO].isin(bairro_sel)]

# Segmento (Antiga Categoria)
lista_segmentos = sorted(df_filtrado[COL_SEGMENTO].dropna().unique())
segmento_sel = st.sidebar.multiselect("Segmento", lista_segmentos, key="filtro_segmento")

if segmento_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_SEGMENTO].isin(segmento_sel)]

# Faixa de Faturamento
faixas = sorted(df_filtrado["FAIXA_FATURAMENTO"].dropna().unique())
faixa_sel = st.sidebar.multiselect("Faixa de Faturamento", faixas, key="filtro_faturamento")

if faixa_sel:
    df_filtrado = df_filtrado[df_filtrado["FAIXA_FATURAMENTO"].isin(faixa_sel)]

# =========================
# TÍTULO
# =========================

st.title("Dashboard Inside Sales - PAPAPÁ")

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
    
    # 1. MOVER INDICADORES PARA CIMA
    st.markdown("---")
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    with col_met1:
        st.metric("Total Clientes", len(df_filtrado))
    with col_met2:
        # Exemplo de lógica para ativos (ajuste conforme sua coluna de status)
        st.metric("Clientes Ativos", "1") 
    with col_met3:
        st.metric("Segmentos", df_filtrado[COL_SEGMENTO].nunique())
    with col_met4:
        st.metric("Vendedores", df_filtrado[COL_VENDEDOR].nunique())

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
# ANÁLISE DE MIX COMPLETA (VISÃO GERAL)
# =========================

# ==========================================
# 🚀 CORREÇÃO DEFINITIVA: BUSCA POR PALAVRAS-CHAVE
# ==========================================
if len(df_filtrado) == 1:
    st.markdown("---")
    st.subheader("💡 Oportunidades de Crescimento")
    
    # Garantimos que o CNPJ do cliente está limpo para a busca
    id_cliente_atual = str(df_filtrado["CNPJ_LIMPO"].iloc[0]).strip()
    
    # Criamos a coluna CNPJ_LIMPO na df_vendas caso ela não exista
    if "CNPJ_LIMPO" not in df_vendas.columns:
        df_vendas["CNPJ_LIMPO"] = df_vendas["CNPJ"].astype(str).str.replace(r'[^0-9]', '', regex=True)

    # 1. MAPEAMENTO COM PALAVRAS-CHAVE (Keywords)
    # Se o sistema encontrar ESTAS palavras no histórico, ele considera o item como "Comprado"
    catalogo_v5 = {
        "PAPINHAS SALGADAS": {
            "Papinha Papapa Carne Arroz Legumes 120g": ["CARNE", "ARROZ", "120G"],
            "Papinha Papapa Frango Grão Vegetais 120g": ["FRANGO", "GRAO", "120G"]
        },
        "YOGUZINHO": {
            "Papinha Papapa Iogurte Frutas Amarelas e Banana 100g": ["IOGURTE", "AMARELAS"],
            "Papinha Papapa Iogurte Frutas Vermelhas e Banana 100g": ["IOGURTE", "VERMELHAS"]
        },
        "PAPINHAS DE FRUTAS": {
            "Papinha Papapá Org Maçã Ameixa 100g": ["MACA", "AMEIXA"],
            "Papinha Papapá Org Banana Mirtilo Quinoa 100g": ["BANANA", "MIRTILO"],
            "Papinha Papapá Org Manga 100g": ["MANGA"],
            "Papinha Papapá Org Pera Espinafre Abobrinha 100g": ["PERA", "ESPINA"],
            "Papinha Papapá Org Maçã B. Doce Cenoura 100g": ["MACA", "DOCE", "CENOURA"],
            "Papinha Papapá Org Morango Maçã 100g": ["MORANGO", "MACA"]
        },
        "PALITINHOS": {
            "Biscoito inf Papapá Palitinho de Vegetais org. Beterraba 20g": ["PALITINHO", "BETERRABA"],
            "Biscoito inf Papapá Palitinho de Vegetais org. Cenoura 20g": ["PALITINHO", "CENOURA"],
            "Biscoito inf Papapá Palitinho de Vegetais org. Tomate/Manjericão 20g": ["PALITINHO", "TOMATE"]
        },
        "DENTIÇÃO": {
            "Biscoito Inf Papapá dent. Maçã e Abóbora 36g": ["DENTICAO", "MACA", "ABOBORA"],
            "Biscoito Inf Papapá dent Vegetais 36g": ["DENTICAO", "VEGETAIS"]
        },
        "MACARRÃO": {
            "Macarrao Inf Papapá m. Elbow Quinoa 200g": ["ELBOW"],
            "Macarrao Inf Papapá m. Fusilli Vegetais 200g": ["FUSILLI"]
        },
        "LA CHEF": {
            "Sopinha Papapá org Lentinha Carne Legumes 180g": ["LENTILHA"],
            "Risotinho Papapá org Arroz quinoa frango 180g": ["RISOTINHO"],
            "Caseirinho Papapá org Arroz feijão carne leg. 180g": ["CASEIRINHO"]
        },
        "CEREAIS": {
            "Cereal Infantil Papapá Aveia - Morango e Beterraba 170g": ["CEREAL", "MORANGO"],
            "Cereal Infantil Papapá Aveia - Banana e Ameixa 170g": ["CEREAL", "BANANA"],
            "Cereal Infantil Papapá Aveia - Multicereais 170g": ["CEREAL", "MULTI", "170G"],
            "Cereal Infantil Papapá Aveia - Multicereais 500g": ["CEREAL", "MULTI", "500G"]
        },
        "BISCOTTI": {
            "Biscoito Infantil Papapá Biscotti com Laranja e Cenoura 60g": ["BISCOTTI", "LARANJA"],
            "Biscoito Infantil Papapá Biscotti com Maçã e Canela 60g": ["BISCOTTI", "CANELA"],
            "Biscoito Infantil Papapá Biscotti com Banana e Cacau 60g": ["BISCOTTI", "CACAU"],
            "Biscoito Infantil Papapá Biscotti Goiaba 60g": ["BISCOTTI", "GOIABA"],
            "Biscoito Infantil Papapá Biscotti com Maracujá e Camomila 60g": ["BISCOTTI", "MARACUJA"]
        },
        "SOPINHAS": {
            "Sopinha Papapá Frango Arroz Legumes 240g": ["SOPINHA", "FRANGO", "240G"],
            "Sopinha Papapá Carne Macarrao Legumes 240g": ["SOPINHA", "MACARRAO", "240G"],
            "Sopinha Papapá Carne Mandioquinha Leg 240g": ["SOPINHA", "MANDIOQ"],
            "Sopinha Papapá Feijão Carne Leg 240g": ["SOPINHA", "FEIJAO", "240G"]
        }
    }

    if not df_vendas.empty:
        # Pega o histórico desse cliente e transforma tudo em uma grande massa de texto limpo
        # Corrigido: usando .str.upper() para evitar o AttributeError
        vendas_cliente_nomes = " ".join(
            df_vendas[df_vendas["CNPJ_LIMPO"] == id_cliente_atual]["DESC PRODUTO"]
            .fillna("")
            .astype(str)
            .str.upper() # O erro estava aqui (faltava o .str)
            .unique()
        )
        
        # Identifica as categorias que o cliente já compra no histórico
        linhas_ativas = set(
            df_vendas[df_vendas["CNPJ_LIMPO"] == id_cliente_atual]["LINHA"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
            .unique()
        )
        
        gap_mix = []
        cross_sell = []

        for linha, produtos in catalogo_v5.items():
            for nome_bonito, keywords in produtos.items():
                # O item só é considerado "Já Comprou" se TODAS as palavras-chave baterem
                # Ex: "MACA" e "AMEIXA" devem estar presentes na mesma linha de compra
                ja_comprou = all(kw.upper() in vendas_cliente_nomes for kw in keywords)
                
                if not ja_comprou:
                    if linha.upper() in linhas_ativas:
                        gap_mix.append({"Linha": linha, "Produto": nome_bonito})
                    else:
                        # Se ele nunca comprou NADA dessa linha, vai para Cross-sell
                        cross_sell.append({"Linha": linha, "Produto": nome_bonito})

        # Exibição Final
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🚨 Gap de Mix")
            st.caption("Faltam nestas linhas que ela já compra:")
            if gap_mix:
                st.dataframe(pd.DataFrame(gap_mix), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Mix completo nas categorias ativas!")

        with c2:
            st.markdown("#### 📦 Cross-sell")
            st.caption("Categorias totalmente novas para ela:")
            if cross_sell:
                # Mostra apenas o nome do produto das categorias novas
                st.dataframe(pd.DataFrame(cross_sell), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Já compra de todas as linhas!")
                
# ==========================================

st.subheader("📦 Análise Geral de Mix e Produtos")

if not df_vendas.empty:
    # 1. Filtro de Segurança: Analisar apenas vendas dos clientes que estão no filtro da sidebar
    cnpjs_visiveis = df_filtrado["CNPJ_LIMPO"].unique()
    vendas_geral = df_vendas[df_vendas["CNPJ_LIMPO"].isin(cnpjs_visiveis)].copy()
    
    # Limpeza de ruído (itens administrativos ou de conferência)
    blacklist_geral = ["CONFERIDO", "AJUSTE", "TESTE", "FRETE"]
    regex_geral = "|".join(blacklist_geral)
    vendas_geral = vendas_geral[~vendas_geral["DESC PRODUTO"].str.upper().str.contains(regex_geral, na=False)]

    if not vendas_geral.empty:
        # 2. MAPEAMENTO INTELIGENTE (Categorização para o Catálogo PAPAPÁ)
        def mapear_catalogo(nome):
            nome = str(nome).upper()
            if any(x in nome for x in ["PAPINHA", "SOPINHA", "REFEIÇÃO", "COMIDINHA"]): return "Papinhas e Sopinhas"
            if any(x in nome for x in ["PUFFS", "BISCOITO", "SNACK", "PALITINHO", "MILHO", "DENTIÇÃO", "BISCOTTI"]): return "Snacks"
            if any(x in nome for x in ["MACARRÃO", "MASSA", "LETRE"]): return "Macarrões"
            if any(x in nome for x in ["CEREAL", "AVEIA", "MUCILON"]): return "Cereais"
            return "Outros"

        def mapear_sabor(nome):
            nome = str(nome).upper()
            doces = ["FRUTA", "BANANA", "MAÇÃ", "MAMAO", "AMEIXA", "DOCE", "CACAU", "LARANJA", "MORANGO", "MANGA", "PERA"]
            return "Doce" if any(x in nome for x in doces) else "Salgado"

        def mapear_idade(nome):
            nome = str(nome).upper()
            if "12" in nome or "CEREAL" in nome: return "12 meses+"
            if any(x in nome for x in ["MACARRÃO", "MASSA", "LETRE"]): return "8 meses+"
            return "6 meses+"

        vendas_geral["CAT_CATALOGO"] = vendas_geral["DESC PRODUTO"].apply(mapear_catalogo)
        vendas_geral["SABOR"] = vendas_geral["DESC PRODUTO"].apply(mapear_sabor)
        vendas_geral["IDADE"] = vendas_geral["DESC PRODUTO"].apply(mapear_idade)

        # 3. LINHA 1 DE GRÁFICOS (Mix e Sabores)
        c1, c2 = st.columns(2)
        with c1:
            mix_cat = vendas_geral.groupby("CAT_CATALOGO")["VALOR"].sum().reset_index()
            fig_mix_cat = px.pie(mix_cat, names="CAT_CATALOGO", values="VALOR", 
                                title="Mix por Categoria de Catálogo", hole=0.4, 
                                color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_mix_cat, use_container_width=True)
            
        with c2:
            mix_sabor = vendas_geral.groupby("SABOR")["VALOR"].sum().reset_index()
            fig_sabor = px.pie(mix_sabor, names="SABOR", values="VALOR", 
                               title="Divisão Doce vs Salgado", 
                               color_discrete_map={"Doce":"#FFB6C1","Salgado":"#90EE90"})
            st.plotly_chart(fig_sabor, use_container_width=True)

        # 4. LINHA 2 DE GRÁFICOS (Idade e Top 10)
        c3, c4 = st.columns(2)
        with c3:
            mix_idade = vendas_geral.groupby("IDADE")["VALOR"].sum().reset_index()
            fig_idade = px.bar(mix_idade, x="IDADE", y="VALOR", color="IDADE", 
                               title="Vendas por Faixa Etária Recomendada",
                               color_discrete_sequence=px.colors.qualitative.Safe)
            fig_idade.update_layout(showlegend=False)
            st.plotly_chart(fig_idade, use_container_width=True)
            
        with c4:
            top_10_geral = (vendas_geral.groupby("DESC PRODUTO")["VALOR"].sum()
                            .reset_index().sort_values("VALOR", ascending=True).tail(10))
            fig_top_geral = px.bar(top_10_geral, x="VALOR", y="DESC PRODUTO", orientation="h", 
                                   title="Top 10 Produtos (Base Geral Filtrada)",
                                   color_continuous_scale="Reds")
            st.plotly_chart(fig_top_geral, use_container_width=True)

# ==========================================
        # 5. PERFORMANCE POR LINHA PAPAPÁ (Deep Dive)
        # ==========================================
        st.markdown("---")
        st.markdown("#### 🏆 Performance por Linha de Produto")
        
        # Usamos as chaves do dicionário que criamos na Inteligência de Mercado
        linhas_papapa = [
            "PAPINHAS SALGADAS", "YOGUZINHO", "PAPINHAS DE FRUTAS", 
            "PALITINHOS", "DENTIÇÃO", "MACARRÃO", "LA CHEF", 
            "CEREAIS", "BISCOTTI", "SOPINHAS"
        ]
        
        linha_selecionada = st.selectbox("Selecione uma linha para detalhar a performance:", options=linhas_papapa)
        
        # Filtrar a base MIX pelo nome da linha (garantindo que esteja em maiúsculo)
        df_detalhe_linha = df_vendas[
            (df_vendas["CNPJ_LIMPO"] == id_cliente_atual) & 
            (df_vendas["LINHA"].str.upper().str.strip() == linha_selecionada)
        ]
        
        if not df_detalhe_linha.empty:
            # Agrupar performance por SKU dentro da linha selecionada
            performance_sku = df_detalhe_linha.groupby("DESC PRODUTO")["VALOR"].sum().sort_values(ascending=False).reset_index()
            
            c_top, c_vol = st.columns(2)
            
            with c_top:
                st.success(f"⭐ **Mais Comprados: {linha_selecionada}**")
                df_top_sku = performance_sku.head(5).copy()
                df_top_sku["VALOR"] = df_top_sku["VALOR"].apply(lambda x: f"R$ {x:,.2f}")
                st.table(df_top_sku.rename(columns={"DESC PRODUTO": "Produto", "VALOR": "Total Gasto"}))
                
            with c_vol:
                # Mostrar o volume total dessa categoria para o cliente
                total_linha = df_detalhe_linha["VALOR"].sum()
                qtd_total = df_detalhe_linha["QTDE"].sum()
                st.metric(label=f"Investimento Total em {linha_selecionada}", value=f"R$ {total_linha:,.2f}")
                st.metric(label="Volume Total (Unidades)", value=int(qtd_total))
                
                # Gráfico rápido de barras para a linha
                import plotly.express as px
                fig_bar_linha = px.bar(performance_sku.head(5), x="VALOR", y="DESC PRODUTO", orientation='h',
                                      title="Top 5 SKUs por Valor",
                                      labels={"VALOR": "Valor (R$)", "DESC PRODUTO": "Produto"},
                                      color_discrete_sequence=["#00CC96"])
                fig_bar_linha.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_bar_linha, use_container_width=True)
        else:
            st.warning(f"O cliente ainda não realizou compras na linha '{linha_selecionada}'.")
            st.info(f"💡 Dica: Veja os produtos desta linha na tabela de **Cross-sell** acima para oferecer!")
# =========================
# GRÁFICOS E MAPA (SÓ APARECEM SE HOUVER MAIS DE 1 CLIENTE)
# =========================

if len(df_filtrado) > 1:
    st.markdown("---")
    st.subheader("📊 Distribuição Cadastral")
    col_graf_cad1, col_graf_cad2 = st.columns(2)

    with col_graf_cad1:
        resumo_segmento = df_filtrado[COL_SEGMENTO].value_counts().reset_index()
        resumo_segmento.columns = ["Segmento", "Quantidade"]

        fig_seg = px.bar(
            resumo_segmento,
            x="Quantidade",
            y="Segmento",
            orientation="h",
            title="Distribuição por Segmento",
            color="Quantidade",
            color_continuous_scale="Reds"
        )
        fig_seg.update_layout(showlegend=False)
        st.plotly_chart(fig_seg, use_container_width=True)

    with col_graf_cad2:
        resumo_faturamento = df_filtrado["FAIXA_FATURAMENTO"].value_counts().reset_index()
        resumo_faturamento.columns = ["Faixa", "Quantidade"]

        fig_fat = px.pie(
            resumo_faturamento,
            names="Faixa",
            values="Quantidade",
            title="Distribuição por Faixa de Faturamento",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Reds_r 
        )
        st.plotly_chart(fig_fat, use_container_width=True)

    # MAPA DE CALOR (BRASIL)
    st.subheader("🗺️ Presença Geográfica")

    resumo_estado = df_filtrado[COL_UF].value_counts().reset_index()
    resumo_estado.columns = ["UF", "Quantidade"]

    url_geojson = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

    try:
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
        st.warning("⚠️ Não foi possível carregar o mapa. Verifique a conexão.")
        st.bar_chart(resumo_estado.set_index("UF"))

    st.divider()

# Caso tenha apenas 1 cliente, o código ignora tudo acima e segue adiante

# =========================
# DOWNLOAD DE DADOS (EXCEL)
# =========================

def gerar_excel(df):
    """Gera um arquivo Excel em memória para download."""
    buffer = BytesIO()
    # Usando xlsxwriter para garantir compatibilidade e formatação
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Clientes_Filtrados")
    return buffer.getvalue()

st.markdown("### 📂 Exportação e Dados")

# Criamos uma linha com colunas para o botão de download não ocupar a tela toda
col_down, col_spacer = st.columns([1, 3])

with col_down:
    if not df_filtrado.empty:
        # Geramos o arquivo apenas se houver dados
        excel_data = gerar_excel(df_filtrado)
        
        st.download_button(
            label="📥 Baixar Base Filtrada (Excel)",
            data=excel_data,
            file_name=f"clientes_papapa_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# =========================
# TABELA DE DADOS FINAL
# =========================

st.subheader("📋 Listagem Detalhada")
st.write(f"Exibindo **{len(df_filtrado)}** registros com base nos filtros aplicados:")

# Lista de colunas para exibir na tabela (ocultando colunas técnicas se desejar)
colunas_exibicao = [c for c in df_filtrado.columns if c not in ["CNPJ_LIMPO", "TEL_LIMPO", "FAIXA_FATURAMENTO"]]

st.dataframe(
    df_filtrado[colunas_exibicao], 
    use_container_width=True,
    hide_index=True
)

# Mensagem de rodapé
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px; margin-top: 50px;'>
        Dashboard Inside Sales Papapá © 2026 - v1.0
    </div>
    """, 
    unsafe_allow_html=True
)
































































































