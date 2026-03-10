import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request
import re
from io import BytesIO
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

st.set_page_config(
    page_title="Dashboard Inside Sales - PAPAPÁ",
    layout="wide"
)

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

ARQUIVO_BASE = "base_clientes_segmentada_EXECUTIVO.xlsx"

@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO_BASE, sheet_name=0)
    df.columns = df.columns.str.strip().str.upper()
    return df

df = carregar_dados()

@st.cache_data
def carregar_vendas():
    try:

        vendas = pd.read_excel(ARQUIVO_BASE, sheet_name=1)

        vendas.columns = vendas.columns.str.strip().str.upper()

        vendas["CNPJ_LIMPO"] = vendas["CNPJ"].astype(str).str.replace(r"\D", "", regex=True)

        vendas["VALOR"] = (
            vendas["VALOR"]
            .astype(str)
            .str.replace("R$","", regex=False)
            .str.replace(".","", regex=False)
            .str.replace(",",".", regex=False)
        )

        vendas["VALOR"] = pd.to_numeric(vendas["VALOR"], errors="coerce").fillna(0)

        vendas["QTDE"] = pd.to_numeric(vendas["QTDE"], errors="coerce").fillna(0)

        vendas["DATA PEDIDO"] = pd.to_datetime(vendas["DATA PEDIDO"], errors="coerce")

        return vendas

    except:
        return pd.DataFrame()

df_vendas = carregar_vendas()

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

colunas_obrigatorias = [
    col_razao,
    col_fantasia,
    col_uf,
    col_cidade,
    col_bairro,
    col_cnpj,
    col_telefone,
    col_email,
    col_vendedor,
    col_categoria,
    col_faturamento
]

for col in colunas_obrigatorias:
    if col not in df.columns:
        df[col] = ""

def limpar_cnpj(cnpj):
    if pd.isna(cnpj):
        return ""
    return re.sub(r"\D", "", str(cnpj))

df["CNPJ_LIMPO"] = df[col_cnpj].apply(limpar_cnpj)

def limpar_telefone(tel):
    if pd.isna(tel):
        return ""
    return re.sub(r"\D", "", str(tel))

df["TEL_LIMPO"] = df[col_telefone].apply(limpar_telefone)

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

def gerar_pdf_cliente(cliente, vendas_cliente):

    buffer = BytesIO()
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Relatório Comercial do Cliente", styles["Title"]))
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
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
        ["Faturamento 6M", f"R$ {cliente[col_faturamento]:,.2f}"]

    ]

    tabela_cliente = Table(dados_cliente, colWidths=[6*cm,10*cm])

    tabela_cliente.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.grey)
    ]))

    elementos.append(tabela_cliente)
    elementos.append(Spacer(1,25))

    if len(vendas_cliente) > 0:

        total_valor = vendas_cliente["VALOR"].sum()
        total_qtde = vendas_cliente["QTDE"].sum()
        total_pedidos = vendas_cliente["NUMERO NF"].nunique()

        ticket = total_valor / total_pedidos if total_pedidos > 0 else 0

        primeira_compra = vendas_cliente["DATA PEDIDO"].min()
        ultima_compra = vendas_cliente["DATA PEDIDO"].max()

        resumo = [

            ["Valor total comprado", f"R$ {total_valor:,.2f}"],
            ["Total unidades", int(total_qtde)],
            ["Total pedidos", total_pedidos],
            ["Ticket médio", f"R$ {ticket:,.2f}"],
            ["Primeira compra", primeira_compra.strftime("%d/%m/%Y") if pd.notnull(primeira_compra) else ""],
            ["Última compra", ultima_compra.strftime("%d/%m/%Y") if pd.notnull(ultima_compra) else ""]
        ]

        elementos.append(Paragraph("Resumo Comercial", styles["Heading2"]))

        tabela_resumo = Table(resumo)

        tabela_resumo.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.5,colors.grey)
        ]))

        elementos.append(tabela_resumo)

        elementos.append(Spacer(1,25))

        top_produtos = (
            vendas_cliente
            .groupby("DESC PRODUTO")[["QTDE","VALOR"]]
            .sum()
            .reset_index()
            .sort_values("VALOR", ascending=False)
            .head(10)
        )

        dados_produtos = [["Produto","Qtde","Valor"]]

        for _,row in top_produtos.iterrows():

            dados_produtos.append([
                row["DESC PRODUTO"],
                int(row["QTDE"]),
                f"R$ {row['VALOR']:,.2f}"
            ])

        elementos.append(Paragraph("Top Produtos Comprados", styles["Heading2"]))

        tabela_produtos = Table(dados_produtos)

        tabela_produtos.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey)
        ]))

        elementos.append(tabela_produtos)

        elementos.append(Spacer(1,25))

        ultimos = vendas_cliente.sort_values("DATA PEDIDO", ascending=False).head(10)

        dados_pedidos = [["Data","NF","Produto","Qtde","Valor"]]

        for _,row in ultimos.iterrows():

            dados_pedidos.append([
                row["DATA PEDIDO"].strftime("%d/%m/%Y") if pd.notnull(row["DATA PEDIDO"]) else "",
                row["NUMERO NF"],
                row["DESC PRODUTO"],
                int(row["QTDE"]),
                f"R$ {row['VALOR']:,.2f}"
            ])

        elementos.append(Paragraph("Últimos Pedidos", styles["Heading2"]))

        tabela_pedidos = Table(dados_pedidos)

        tabela_pedidos.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey)
        ]))

        elementos.append(tabela_pedidos)

    doc = SimpleDocTemplate(buffer, pagesize=A4)

    doc.build(elementos)

    buffer.seek(0)

    return buffer

st.sidebar.title("Filtros")

if st.sidebar.button("Limpar filtros"):

    st.session_state["busca_cnpj"] = ""
    st.session_state["busca_nome"] = ""
    st.session_state["busca_email"] = ""
    st.session_state["busca_tel"] = ""

    st.session_state["filtro_vendedor"] = []
    st.session_state["filtro_uf"] = []
    st.session_state["filtro_cidade"] = []
    st.session_state["filtro_bairro"] = []
    st.session_state["filtro_categoria"] = []
    st.session_state["filtro_faturamento"] = []

    st.rerun()

df_filtrado = df.copy()

busca_cnpj = st.sidebar.text_input("Buscar por CNPJ", key="busca_cnpj")

if busca_cnpj:

    cnpj_limpo = limpar_cnpj(busca_cnpj)

    df_filtrado = df_filtrado[
        df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_limpo, na=False)
    ]

busca_nome = st.sidebar.text_input("Buscar Razão Social", key="busca_nome")

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

busca_email = st.sidebar.text_input("Buscar por E-mail", key="busca_email")

if busca_email:
    df_filtrado = df_filtrado[
        df_filtrado[col_email].str.contains(busca_email, case=False, na=False)
    ]

busca_tel = st.sidebar.text_input("Buscar por Telefone", key="busca_tel")

if busca_tel:

    tel_limpo = limpar_telefone(busca_tel)

    df_filtrado = df_filtrado[
        df_filtrado["TEL_LIMPO"].str.contains(tel_limpo, na=False)
    ]

vendedores = sorted(df_filtrado[col_vendedor].dropna().unique())

vendedor_sel = st.sidebar.multiselect("Vendedor", vendedores, key="filtro_vendedor")

if vendedor_sel:
    df_filtrado = df_filtrado[df_filtrado[col_vendedor].isin(vendedor_sel)]

ufs = sorted(df_filtrado[col_uf].dropna().unique())

uf_sel = st.sidebar.multiselect("Estado (UF)", ufs, key="filtro_uf")

if uf_sel:
    df_filtrado = df_filtrado[df_filtrado[col_uf].isin(uf_sel)]

cidades = sorted(df_filtrado[col_cidade].dropna().unique())

cidade_sel = st.sidebar.multiselect("Cidade", cidades, key="filtro_cidade")

if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado[col_cidade].isin(cidade_sel)]

bairros = sorted(df_filtrado[col_bairro].dropna().unique())

bairro_sel = st.sidebar.multiselect("Bairro", bairros, key="filtro_bairro")

if bairro_sel:
    df_filtrado = df_filtrado[df_filtrado[col_bairro].isin(bairro_sel)]

categorias = sorted(df_filtrado[col_categoria].dropna().unique())

categoria_sel = st.sidebar.multiselect("Categoria", categorias, key="filtro_categoria")

if categoria_sel:
    df_filtrado = df_filtrado[df_filtrado[col_categoria].isin(categoria_sel)]

faixas = sorted(df_filtrado["FAIXA_FATURAMENTO"].dropna().unique())

faixa_sel = st.sidebar.multiselect("Faixa de Faturamento", faixas, key="filtro_faturamento")

if faixa_sel:
    df_filtrado = df_filtrado[df_filtrado["FAIXA_FATURAMENTO"].isin(faixa_sel)]

st.title("Dashboard Inside Sales - PAPAPÁ")

if len(df_filtrado) == 1:

    cliente = df_filtrado.iloc[0]

    telefone = limpar_telefone(cliente[col_telefone])

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

st.subheader("Base de Clientes")

st.dataframe(df_filtrado, use_container_width=True)
