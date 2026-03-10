import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request
import re
from io import BytesIO
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors


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

ARQUIVO_BASE = "base_clientes_segmentada_EXECUTIVO.xlsx"

# =========================
# CARREGAR BASE CLIENTES
# =========================

@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO_BASE, sheet_name=0)
    df.columns = df.columns.str.strip().str.upper()
    return df

df = carregar_dados()

# =========================
# CARREGAR BASE VENDAS
# =========================

@st.cache_data
def carregar_vendas():

    try:

        vendas = pd.read_excel(ARQUIVO_BASE, sheet_name=1)

        vendas.columns = vendas.columns.str.strip().str.upper()

        vendas["CNPJ_LIMPO"] = vendas["CNPJ"].astype(str).str.replace(r"\D", "", regex=True)

        vendas["QTDE"] = pd.to_numeric(vendas["QTDE"], errors="coerce").fillna(0)

        vendas["VALOR"] = (
            vendas["VALOR"]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )

        vendas["VALOR"] = pd.to_numeric(vendas["VALOR"], errors="coerce").fillna(0)

        return vendas

    except:

        return pd.DataFrame()

df_vendas = carregar_vendas()

# =========================
# DEFINIR COLUNAS
# =========================

col_razao = "RAZÃO SOCIAL"
col_fantasia = "NOME FANTASIA"
col_uf = "UF"
col_cidade = "CIDADE"
col_bairro = "BAIRRO"
col_cnpj = "CNPJ"
col_telefone = "TELEFONE"
col_email = "E-MAIL"
col_vendedor = "VENDEDOR"
col_categoria = "CATEGORIA"
col_faturamento = "FATURAMENTO ÚLTIMOS 6 MESES"

# =========================
# LIMPAR CNPJ
# =========================

def limpar_cnpj(cnpj):

    if pd.isna(cnpj):
        return ""

    return re.sub(r"\D", "", str(cnpj))

df["CNPJ_LIMPO"] = df[col_cnpj].apply(limpar_cnpj)

# =========================
# LIMPAR TELEFONE
# =========================

def limpar_telefone(tel):

    if pd.isna(tel):
        return ""

    return re.sub(r"\D", "", str(tel))

df["TEL_LIMPO"] = df[col_telefone].apply(limpar_telefone)

# =========================
# TRATAR FATURAMENTO
# =========================

df[col_faturamento] = pd.to_numeric(df[col_faturamento], errors="coerce").fillna(0)

bins = [0, 5000, 20000, 50000, 100000, float("inf")]

labels = [
    "Até 5 mil",
    "5 mil – 20 mil",
    "20 mil – 50 mil",
    "50 mil – 100 mil",
    "Acima de 100 mil"
]

df["FAIXA_FATURAMENTO"] = pd.cut(df[col_faturamento], bins=bins, labels=labels)

# =========================
# GERAR PDF
# =========================

def gerar_pdf_cliente(cliente, vendas_cliente):

    buffer = BytesIO()

    styles = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph("Relatório de Cliente - PAPAPÁ", styles["Title"])
    data = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"])

    elementos.append(titulo)
    elementos.append(data)
    elementos.append(Spacer(1,20))

    dados_cliente = [

        ["Razão Social", cliente[col_razao]],
        ["Nome Fantasia", cliente[col_fantasia]],
        ["CNPJ", cliente[col_cnpj]],
        ["Telefone", cliente[col_telefone]],
        ["Email", cliente[col_email]],
        ["Cidade", f"{cliente[col_cidade]} - {cliente[col_uf]}"],
        ["Vendedor", cliente[col_vendedor]],
        ["Categoria", cliente[col_categoria]],
        ["Faturamento 6M", f"R$ {cliente[col_faturamento]:,.2f}"],
        ["Faixa", str(cliente["FAIXA_FATURAMENTO"])]

    ]

    tabela_cliente = Table(dados_cliente, colWidths=[6*cm,10*cm])

    tabela_cliente.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(1,0),colors.whitesmoke),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey)
    ]))

    elementos.append(tabela_cliente)

    elementos.append(Spacer(1,30))

    elementos.append(Paragraph("Histórico de Compras", styles["Heading2"]))

    if len(vendas_cliente) > 0:

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

        resumo_comercial = [

            ["Total SKUs Comprados", total_skus],
            ["Total Unidades", int(total_qtd)],
            ["Valor Total Comprado", f"R$ {total_valor:,.2f}"]

        ]

        elementos.append(Spacer(1,10))

        tabela_resumo = Table(resumo_comercial)

        elementos.append(tabela_resumo)

        elementos.append(Spacer(1,20))

        dados_produtos = [["Produto","Linha","Quantidade","Valor"]]

        for _,row in resumo.iterrows():

            dados_produtos.append([

                row["DESC PRODUTO"],
                row["LINHA"],
                int(row["QTDE"]),
                f"R$ {row['VALOR']:,.2f}"

            ])

        tabela_produtos = Table(dados_produtos)

        tabela_produtos.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey)
        ]))

        elementos.append(tabela_produtos)

    else:

        elementos.append(Paragraph("Nenhum histórico de compra encontrado.", styles["Normal"]))

    doc = SimpleDocTemplate(buffer, pagesize=A4)

    doc.build(elementos)

    buffer.seek(0)

    return buffer

# =========================
# SIDEBAR
# =========================

st.sidebar.title("Filtros")

df_filtrado = df.copy()

busca_cnpj = st.sidebar.text_input("Buscar por CNPJ")

if busca_cnpj:

    cnpj_limpo = limpar_cnpj(busca_cnpj)

    df_filtrado = df_filtrado[
        df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_limpo, na=False)
    ]

busca_nome = st.sidebar.text_input("Buscar Razão Social")

cliente_escolhido = None

if busca_nome:

    sugestoes = df[
        df[col_razao].str.contains(busca_nome, case=False, na=False)
    ][col_razao].drop_duplicates().head(50)

    if len(sugestoes) > 0:

        cliente_escolhido = st.sidebar.selectbox(
            "Selecione o cliente",
            sugestoes
        )

        df_filtrado = df_filtrado[
            df_filtrado[col_razao] == cliente_escolhido
        ]

st.title("Dashboard Inside Sales - PAPAPÁ")

# =========================
# CARD CLIENTE
# =========================

if len(df_filtrado) == 1:

    cliente = df_filtrado.iloc[0]

    st.markdown("### Cliente encontrado")

    st.markdown(
        f"""
        <div style="padding:20px;border-radius:10px;background-color:#f6f6f6">

        <h3 style="color:#FF4B4B">{cliente[col_razao]}</h3>

        <b>Vendedor:</b> <span style="color:#1f77b4">{cliente[col_vendedor]}</span><br><br>

        <b>CNPJ:</b> {cliente[col_cnpj]}<br>
        <b>Telefone:</b> {cliente[col_telefone]}<br>
        <b>E-mail:</b> {cliente[col_email]}<br>
        <b>Cidade:</b> {cliente[col_cidade]} - {cliente[col_uf]}<br>

        </div>
        """,
        unsafe_allow_html=True
    )

    telefone = limpar_telefone(cliente[col_telefone])

    if telefone:

        link_whatsapp = f"https://wa.me/55{telefone}"

        st.link_button(
            "💬 Chamar no WhatsApp",
            link_whatsapp
        )

    vendas_cliente = pd.DataFrame()

    if not df_vendas.empty:

        vendas_cliente = df_vendas[
            df_vendas["CNPJ_LIMPO"] == cliente["CNPJ_LIMPO"]
        ]

    pdf = gerar_pdf_cliente(cliente, vendas_cliente)

    st.download_button(
        "📄 Baixar relatório completo do cliente em PDF",
        data=pdf,
        file_name=f"relatorio_cliente_{cliente[col_razao]}.pdf",
        mime="application/pdf"
    )

# =========================
# KPIs
# =========================

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Clientes", len(df_filtrado))
k2.metric("Estados Ativos", df_filtrado[col_uf].nunique())
k3.metric("Categorias", df_filtrado[col_categoria].nunique())
k4.metric("Vendedores", df_filtrado[col_vendedor].nunique())

st.subheader("Base de Clientes")

st.dataframe(df_filtrado, use_container_width=True)
