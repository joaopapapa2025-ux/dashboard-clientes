import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request
import re

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="Dashboard Inside Sales - PAPAPÁ",
    layout="wide"
)

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

df_filtrado = df.copy()

# =========================
# BUSCA CNPJ
# =========================

busca_cnpj = st.sidebar.text_input("Buscar por CNPJ")

if busca_cnpj:

    cnpj_limpo = limpar_cnpj(busca_cnpj)

    df_filtrado = df_filtrado[
        df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_limpo, na=False)
    ]

# =========================
# BUSCA RAZÃO SOCIAL
# =========================

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

# =========================
# BUSCA EMAIL
# =========================

busca_email = st.sidebar.text_input("Buscar por E-mail")

if busca_email:
    df_filtrado = df_filtrado[
        df_filtrado[col_email].str.contains(busca_email, case=False, na=False)
    ]

# =========================
# BUSCA TELEFONE
# =========================

busca_tel = st.sidebar.text_input("Buscar por Telefone")

if busca_tel:

    tel_limpo = limpar_telefone(busca_tel)

    df_filtrado = df_filtrado[
        df_filtrado["TEL_LIMPO"].str.contains(tel_limpo, na=False)
    ]

# =========================
# FILTROS
# =========================

vendedores = sorted(df[col_vendedor].dropna().unique())

vendedor_sel = st.sidebar.multiselect("Vendedor", vendedores)

if vendedor_sel:
    df_filtrado = df_filtrado[df_filtrado[col_vendedor].isin(vendedor_sel)]

ufs = sorted(df_filtrado[col_uf].dropna().unique())

uf_sel = st.sidebar.multiselect("Estado (UF)", ufs)

if uf_sel:
    df_filtrado = df_filtrado[df_filtrado[col_uf].isin(uf_sel)]

cidades = sorted(df_filtrado[col_cidade].dropna().unique())

cidade_sel = st.sidebar.multiselect("Cidade", cidades)

if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado[col_cidade].isin(cidade_sel)]

bairros = sorted(df_filtrado[col_bairro].dropna().unique())

bairro_sel = st.sidebar.multiselect("Bairro", bairros)

if bairro_sel:
    df_filtrado = df_filtrado[df_filtrado[col_bairro].isin(bairro_sel)]

categorias = sorted(df_filtrado[col_categoria].dropna().unique())

categoria_sel = st.sidebar.multiselect("Categoria", categorias)

if categoria_sel:
    df_filtrado = df_filtrado[df_filtrado[col_categoria].isin(categoria_sel)]

# =========================
# TÍTULO
# =========================

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

    st.divider()

# =========================
# KPIs
# =========================

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Clientes", len(df_filtrado))
k2.metric("Estados Ativos", df_filtrado[col_uf].nunique())
k3.metric("Categorias", df_filtrado[col_categoria].nunique())
k4.metric("Vendedores", df_filtrado[col_vendedor].nunique())

st.divider()

# =========================
# GRÁFICO SEGMENTO
# =========================

resumo_categoria = df_filtrado[col_categoria].value_counts().reset_index()

resumo_categoria.columns = ["Categoria", "Quantidade"]

fig_cat = px.bar(
    resumo_categoria,
    x="Categoria",
    y="Quantidade",
    title="Distribuição por Categoria"
)

st.plotly_chart(fig_cat, width="stretch")

# =========================
# GRÁFICO FATURAMENTO
# =========================

resumo_faixa = df_filtrado["FAIXA_FATURAMENTO"].value_counts().reset_index()

resumo_faixa.columns = ["Faixa", "Quantidade"]

fig_faixa = px.bar(
    resumo_faixa,
    x="Faixa",
    y="Quantidade",
    title="Distribuição por Faixa de Faturamento"
)

st.plotly_chart(fig_faixa, width="stretch")

# =========================
# MAPA
# =========================

resumo_estado = df_filtrado[col_uf].value_counts().reset_index()

resumo_estado.columns = ["UF", "Quantidade"]

url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

with urllib.request.urlopen(url) as response:
    geojson_br = json.load(response)

fig_mapa = px.choropleth(
    resumo_estado,
    geojson=geojson_br,
    locations="UF",
    featureidkey="properties.sigla",
    color="Quantidade",
    color_continuous_scale="Reds",
    title="Distribuição de Clientes por Estado"
)

fig_mapa.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig_mapa, width="stretch")

st.divider()

# =========================
# TABELA
# =========================

st.subheader("Base de Clientes")

st.dataframe(df_filtrado, width="stretch")
