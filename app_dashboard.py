import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request
import re
from io import BytesIO

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

ARQUIVO_BASE = "base_clientes_segmentada_EXECUTIVO.xlsx"

# =========================
# CARREGAR BASE
# =========================

@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO_BASE)
    df.columns = df.columns.str.strip().str.upper()
    return df

df = carregar_dados()

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
# GARANTIR COLUNAS
# =========================

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
# SIDEBAR
# =========================

st.sidebar.title("Filtros")

# BOTÃO LIMPAR FILTROS
if st.sidebar.button("Limpar filtros"):
    for key in [
        "busca_cnpj",
        "busca_nome",
        "busca_email",
        "busca_tel",
        "filtro_vendedor",
        "filtro_uf",
        "filtro_cidade",
        "filtro_bairro",
        "filtro_categoria",
        "filtro_faixa"
    ]:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

df_filtrado = df.copy()

# =========================
# BUSCA CNPJ
# =========================

busca_cnpj = st.sidebar.text_input("Buscar por CNPJ", key="busca_cnpj")

if busca_cnpj:

    cnpj_limpo = limpar_cnpj(busca_cnpj)

    df_filtrado = df_filtrado[
        df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_limpo, na=False)
    ]

# =========================
# BUSCA RAZÃO SOCIAL
# =========================

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

# =========================
# BUSCA EMAIL
# =========================

busca_email = st.sidebar.text_input("Buscar por E-mail", key="busca_email")

if busca_email:
    df_filtrado = df_filtrado[
        df_filtrado[col_email].str.contains(busca_email, case=False, na=False)
    ]

# =========================
# BUSCA TELEFONE
# =========================

busca_tel = st.sidebar.text_input("Buscar por Telefone", key="busca_tel")

if busca_tel:

    tel_limpo = limpar_telefone(busca_tel)

    df_filtrado = df_filtrado[
        df_filtrado["TEL_LIMPO"].str.contains(tel_limpo, na=False)
    ]

# =========================
# FILTROS
# =========================

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

# =========================
# FILTRO FAIXA FATURAMENTO
# =========================

faixas = sorted(df_filtrado["FAIXA_FATURAMENTO"].dropna().unique())

faixa_sel = st.sidebar.multiselect("Faixa de Faturamento", faixas, key="filtro_faixa")

if faixa_sel:
    df_filtrado = df_filtrado[df_filtrado["FAIXA_FATURAMENTO"].isin(faixa_sel)]

# =========================
# RESTANTE DO DASH
# =========================

st.title("Dashboard Inside Sales - PAPAPÁ")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Clientes", len(df_filtrado))
k2.metric("Estados Ativos", df_filtrado[col_uf].nunique())
k3.metric("Categorias", df_filtrado[col_categoria].nunique())
k4.metric("Vendedores", df_filtrado[col_vendedor].nunique())

st.divider()

st.subheader("Base de Clientes")

st.dataframe(df_filtrado, use_container_width=True)
