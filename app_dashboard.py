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

if col_cnpj in df.columns:
    df["CNPJ_LIMPO"] = df[col_cnpj].apply(limpar_cnpj)
else:
    df["CNPJ_LIMPO"] = ""

# =========================
# LIMPAR TELEFONE
# =========================

def limpar_telefone(tel):
    if pd.isna(tel):
        return ""
    return re.sub(r"\D", "", str(tel))

if col_telefone in df.columns:
    df["TEL_LIMPO"] = df[col_telefone].apply(limpar_telefone)
else:
    df["TEL_LIMPO"] = ""

# =========================
# FATURAMENTO
# =========================

if col_faturamento in df.columns:

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

if busca_nome and col_razao in df.columns:

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

if busca_email and col_email in df.columns:

    df_filtrado = df_filtrado[
        df_filtrado[col_email].astype(str).str.contains(busca_email, case=False, na=False)
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

if col_vendedor in df.columns:

    vendedores = sorted(df[col_vendedor].dropna().unique())

    vendedor_sel = st.sidebar.multiselect("Vendedor", vendedores)

    if vendedor_sel:
        df_filtrado = df_filtrado[df_filtrado[col_vendedor].isin(vendedor_sel)]

if col_uf in df.columns:

    ufs = sorted(df_filtrado[col_uf].dropna().unique())

    uf_sel = st.sidebar.multiselect("Estado (UF)", ufs)

    if uf_sel:
        df_filtrado = df_filtrado[df_filtrado[col_uf].isin(uf_sel)]

if col_cidade in df.columns:

    cidades = sorted(df_filtrado[col_cidade].dropna().unique())

    cidade_sel = st.sidebar.multiselect("Cidade", cidades)

    if cidade_sel:
        df_filtrado = df_filtrado[df_filtrado[col_cidade].isin(cidade_sel)]

if col_bairro in df.columns:

    bairros = sorted(df_filtrado[col_bairro].dropna().unique())

    bairro_sel = st.sidebar.multiselect("Bairro", bairros)

    if bairro_sel:
        df_filtrado = df_filtrado[df_filtrado[col_bairro].isin(bairro_sel)]

if col_categoria in df.columns:

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

    telefone = cliente[col_telefone] if col_telefone in df.columns else ""
    email = cliente[col_email] if col_email in df.columns else ""

    st.markdown(
        f"""
        <div style="padding:20px;border-radius:10px;background-color:#f6f6f6">

        <h3 style="color:#FF4B4B">{cliente[col_razao]}</h3>

        <b>Vendedor:</b> <span style="color:#1f77b4">{cliente[col_vendedor]}</span><br><br>

        <b>CNPJ:</b> {cliente[col_cnpj]}<br>
        <b>Telefone:</b> {telefone}<br>
        <b>E-mail:</b> {email}<br>
        <b>Cidade:</b> {cliente[col_cidade]} - {cliente[col_uf]}<br>

        </div>
        """,
        unsafe_allow_html=True
    )

    tel_limpo = limpar_telefone(telefone)

    if tel_limpo:

        link_whatsapp = f"https://wa.me/55{tel_limpo}"

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
k2.metric("Estados Ativos", df_filtrado[col_uf].nunique() if col_uf in df.columns else 0)
k3.metric("Categorias", df_filtrado[col_categoria].nunique() if col_categoria in df.columns else 0)
k4.metric("Vendedores", df_filtrado[col_vendedor].nunique() if col_vendedor in df.columns else 0)

st.divider()

# =========================
# MAPA
# =========================

if col_uf in df.columns:

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
# DOWNLOAD EXCEL
# =========================

def gerar_excel(df):

    buffer = BytesIO()

    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer, index=False)

    return buffer.getvalue()

st.subheader("Base de Clientes")

excel = gerar_excel(df_filtrado)

st.download_button(
    label="⬇️ Baixar base em Excel",
    data=excel,
    file_name="base_clientes_filtrada.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.dataframe(df_filtrado, width="stretch")
