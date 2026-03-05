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
    page_title="Dashboard Estratégico de Clientes",
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
col_categoria = "CATEGORIA_FINAL"
col_uf = "UF"
col_cidade = "CIDADE"
col_bairro = "BAIRRO"
col_vendedor = "VENDEDOR"
col_faturamento = "FATURAMENTO ÚLTIMOS 6 MESES"
col_cnpj = "CNPJ"

for col in [col_categoria, col_uf, col_cidade, col_bairro, col_vendedor, col_faturamento, col_cnpj]:
    if col not in df.columns:
        st.error(f"Coluna '{col}' não encontrada na base.")
        st.stop()

# =========================
# FUNÇÃO LIMPAR CNPJ
# =========================
def limpar_cnpj(valor):
    return re.sub(r"\D", "", str(valor))

df["CNPJ_LIMPO"] = df[col_cnpj].apply(limpar_cnpj)

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
# SIDEBAR FILTROS
# =========================
st.sidebar.title("Filtros")

df_filtrado = df.copy()

# 🔎 Busca por CNPJ (ignora pontuação)
cnpj_busca = st.sidebar.text_input("Buscar por CNPJ")

if cnpj_busca:
    cnpj_busca_limpo = limpar_cnpj(cnpj_busca)
    df_filtrado = df_filtrado[
        df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_busca_limpo, na=False)
    ]

# Vendedor
vendedores = sorted(df[col_vendedor].dropna().unique())
vendedor_sel = st.sidebar.multiselect("Vendedor", vendedores)
if vendedor_sel:
    df_filtrado = df_filtrado[df_filtrado[col_vendedor].isin(vendedor_sel)]

# UF
ufs = sorted(df[col_uf].dropna().unique())
uf_sel = st.sidebar.multiselect("Estado (UF)", ufs)
if uf_sel:
    df_filtrado = df_filtrado[df_filtrado[col_uf].isin(uf_sel)]

# Cidade
cidades = sorted(df[col_cidade].dropna().unique())
cidade_sel = st.sidebar.multiselect("Cidade", cidades)
if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado[col_cidade].isin(cidade_sel)]

# Bairro
bairros = sorted(df[col_bairro].dropna().unique())
bairro_sel = st.sidebar.multiselect("Bairro", bairros)
if bairro_sel:
    df_filtrado = df_filtrado[df_filtrado[col_bairro].isin(bairro_sel)]

# Segmento
categorias = sorted(df[col_categoria].dropna().unique())
categoria_sel = st.sidebar.multiselect("Segmento Final", categorias)
if categoria_sel:
    df_filtrado = df_filtrado[df_filtrado[col_categoria].isin(categoria_sel)]

# Faixa faturamento
faixas = sorted(df["FAIXA_FATURAMENTO"].dropna().unique())
faixa_sel = st.sidebar.multiselect("Faixa de Faturamento (6 meses)", faixas)
if faixa_sel:
    df_filtrado = df_filtrado[df_filtrado["FAIXA_FATURAMENTO"].isin(faixa_sel)]

# =========================
# TÍTULO
# =========================
st.title("Dashboard Estratégico de Clientes")
st.markdown("Mini sistema analítico estilo Power BI")

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
# GRÁFICO POR SEGMENTO
# =========================
resumo_categoria = df_filtrado[col_categoria].value_counts().reset_index()
resumo_categoria.columns = ["Segmento", "Quantidade"]

fig_cat = px.bar(
    resumo_categoria,
    x="Segmento",
    y="Quantidade",
    title="Distribuição por Segmento Final"
)

st.plotly_chart(fig_cat, width="stretch")

# =========================
# GRÁFICO POR FAIXA
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

fig_mapa.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig_mapa, width="stretch")

st.divider()

# =========================
# TABELA FINAL
# =========================
st.subheader("Base de Clientes Filtrada")
st.dataframe(df_filtrado, width="stretch")
