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
# FUNÇÕES
# =========================

def limpar_cnpj(cnpj):
    if pd.isna(cnpj):
        return ""
    return re.sub(r"\D", "", str(cnpj))


# =========================
# CARREGAR BASE
# =========================

@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO_BASE)
    df.columns = df.columns.str.strip().str.upper()

    df["CNPJ_LIMPO"] = df["CNPJ"].apply(limpar_cnpj)
    df["RAZAO_BUSCA"] = df["RAZÃO SOCIAL"].str.lower()

    return df


df = carregar_dados()

# =========================
# DEFINIR COLUNAS
# =========================

col_categoria = "CATEGORIA_FINAL"
col_uf = "UF"
col_cidade = "CIDADE"
col_bairro = "BAIRRO"
col_vendedor = "VENDEDOR"
col_faturamento = "FATURAMENTO ÚLTIMOS 6 MESES"

# =========================
# TRATAR FATURAMENTO
# =========================

df[col_faturamento] = (
    df[col_faturamento]
    .astype(str)
    .str.replace("R$", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

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
# SIDEBAR FILTROS
# =========================

st.sidebar.title("Filtros")

df_filtrado = df.copy()

# -------------------------
# BUSCA CNPJ
# -------------------------

busca_cnpj = st.sidebar.text_input("Buscar por CNPJ")

if busca_cnpj:

    busca_limpa = limpar_cnpj(busca_cnpj)

    df_filtrado = df_filtrado[
        df_filtrado["CNPJ_LIMPO"].str.contains(busca_limpa)
    ]

# -------------------------
# BUSCA RAZAO SOCIAL
# -------------------------

busca_razao = st.sidebar.text_input("Buscar Razão Social")

cliente_escolhido = None

if busca_razao:

    busca = busca_razao.lower()

    sugestoes = df[
        df["RAZAO_BUSCA"].str.contains(busca)
    ]

    lista_clientes = sugestoes["RAZÃO SOCIAL"].unique()[:50]

    if len(lista_clientes) > 0:

        cliente_escolhido = st.sidebar.selectbox(
            "Selecione o cliente",
            lista_clientes
        )

        df_filtrado = df_filtrado[
            df_filtrado["RAZÃO SOCIAL"] == cliente_escolhido
        ]

# -------------------------
# FILTRO VENDEDOR
# -------------------------

vendedores = sorted(df_filtrado[col_vendedor].dropna().unique())

vendedor_sel = st.sidebar.multiselect(
    "Vendedor",
    vendedores
)

if vendedor_sel:
    df_filtrado = df_filtrado[
        df_filtrado[col_vendedor].isin(vendedor_sel)
    ]

# -------------------------
# FILTRO UF
# -------------------------

ufs = sorted(df_filtrado[col_uf].dropna().unique())

uf_sel = st.sidebar.multiselect(
    "Estado (UF)",
    ufs
)

if uf_sel:
    df_filtrado = df_filtrado[
        df_filtrado[col_uf].isin(uf_sel)
    ]

# -------------------------
# FILTRO CIDADE
# -------------------------

cidades = sorted(df_filtrado[col_cidade].dropna().unique())

cidade_sel = st.sidebar.multiselect(
    "Cidade",
    cidades
)

if cidade_sel:
    df_filtrado = df_filtrado[
        df_filtrado[col_cidade].isin(cidade_sel)
    ]

# -------------------------
# FILTRO BAIRRO
# -------------------------

bairros = sorted(df_filtrado[col_bairro].dropna().unique())

bairro_sel = st.sidebar.multiselect(
    "Bairro",
    bairros
)

if bairro_sel:
    df_filtrado = df_filtrado[
        df_filtrado[col_bairro].isin(bairro_sel)
    ]

# -------------------------
# FILTRO SEGMENTO
# -------------------------

categorias = sorted(df_filtrado[col_categoria].dropna().unique())

categoria_sel = st.sidebar.multiselect(
    "Segmento Final",
    categorias
)

if categoria_sel:
    df_filtrado = df_filtrado[
        df_filtrado[col_categoria].isin(categoria_sel)
    ]

# -------------------------
# FILTRO FAIXA FATURAMENTO
# -------------------------

faixas = sorted(df_filtrado["FAIXA_FATURAMENTO"].dropna().unique())

faixa_sel = st.sidebar.multiselect(
    "Faixa de Faturamento (6 meses)",
    faixas
)

if faixa_sel:
    df_filtrado = df_filtrado[
        df_filtrado["FAIXA_FATURAMENTO"].isin(faixa_sel)
    ]

# =========================
# TÍTULO
# =========================

st.title("Dashboard Inside Sales - PAPAPÁ")

# =========================
# MOSTRAR VENDEDOR
# =========================

if len(df_filtrado) == 1:

    vendedor_cliente = df_filtrado[col_vendedor].iloc[0]
    cliente_nome = df_filtrado["RAZÃO SOCIAL"].iloc[0]

    st.success(f"Cliente: {cliente_nome}")
    st.info(f"Vendedor responsável: {vendedor_cliente}")

# =========================
# KPIs
# =========================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Clientes", len(df_filtrado))

col2.metric("Estados Ativos", df_filtrado[col_uf].nunique())

col3.metric("Segmentos Ativos", df_filtrado[col_categoria].nunique())

col4.metric("Vendedores Ativos", df_filtrado[col_vendedor].nunique())

st.divider()

# =========================
# GRÁFICO SEGMENTO
# =========================

resumo_categoria = df_filtrado[col_categoria].value_counts().reset_index()

resumo_categoria.columns = ["Segmento", "Quantidade"]

fig_cat = px.bar(
    resumo_categoria,
    x="Segmento",
    y="Quantidade",
    title="Distribuição por Segmento Final"
)

st.plotly_chart(fig_cat, use_container_width=True)

# =========================
# GRÁFICO FAIXA
# =========================

resumo_faixa = df_filtrado["FAIXA_FATURAMENTO"].value_counts().reset_index()

resumo_faixa.columns = ["Faixa", "Quantidade"]

fig_faixa = px.bar(
    resumo_faixa,
    x="Faixa",
    y="Quantidade",
    title="Distribuição por Faixa de Faturamento"
)

st.plotly_chart(fig_faixa, use_container_width=True)

# =========================
# MAPA DO BRASIL
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

fig_mapa.update_geos(
    fitbounds="locations",
    visible=False
)

st.plotly_chart(fig_mapa, use_container_width=True)

st.divider()

# =========================
# TABELA FINAL
# =========================

st.subheader("Base de Clientes Filtrada")

st.dataframe(
    df_filtrado,
    use_container_width=True
)
