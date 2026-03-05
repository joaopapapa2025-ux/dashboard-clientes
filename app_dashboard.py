import streamlit as st
import pandas as pd
import plotly.express as px
import re
import json
import urllib.request

st.set_page_config(layout="wide")

st.title("Dashboard Inside Sales - PAPAPÁ")

# =========================
# UPLOAD DA BASE
# =========================

arquivo = st.file_uploader("Envie sua base de clientes", type=["xlsx", "csv"])

if arquivo:

    if arquivo.name.endswith(".csv"):
        df = pd.read_csv(arquivo)
    else:
        df = pd.read_excel(arquivo)

    # =========================
    # DETECTAR COLUNAS
    # =========================

    col_categoria = None
    col_faturamento = None
    col_uf = None
    col_telefone = None

    for col in df.columns:

        nome = col.lower()

        if "categoria" in nome:
            col_categoria = col

        if "faturamento" in nome:
            col_faturamento = col

        if nome == "uf":
            col_uf = col

        if "telefone" in nome or "celular" in nome or "phone" in nome:
            col_telefone = col

    # =========================
    # LIMPAR TELEFONE
    # =========================

    def limpar_telefone(telefone):

        telefone = str(telefone)

        telefone = re.sub(r"\D", "", telefone)

        if len(telefone) == 11:
            return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"

        if len(telefone) == 10:
            return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"

        return telefone

    if col_telefone:
        df["TEL_LIMPO"] = df[col_telefone].apply(limpar_telefone)

    # =========================
    # CRIAR FAIXA FATURAMENTO
    # =========================

    if col_faturamento:

        df["FAIXA_FATURAMENTO"] = pd.cut(
            df[col_faturamento],
            bins=[0, 5000, 20000, 50000, 100000, 999999999],
            labels=[
                "Até 5 mil",
                "5 mil – 20 mil",
                "20 mil – 50 mil",
                "50 mil – 100 mil",
                "Acima de 100 mil",
            ],
        )

    df_filtrado = df.copy()

    # =========================
    # KPIs
    # =========================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Clientes", len(df_filtrado))

    with c2:
        if col_uf:
            st.metric("Estados", df_filtrado[col_uf].nunique())

    with c3:
        if col_categoria:
            st.metric("Categorias", df_filtrado[col_categoria].nunique())

    with c4:
        if "VENDEDOR" in df_filtrado.columns:
            st.metric("Vendedores", df_filtrado["VENDEDOR"].nunique())

    st.divider()

    # =========================
    # GRÁFICO CATEGORIA
    # =========================

    if col_categoria:

        categoria_count = (
            df_filtrado[col_categoria]
            .value_counts()
            .reset_index()
        )

        categoria_count.columns = ["Categoria", "Quantidade"]

        fig_categoria = px.bar(
            categoria_count,
            x="Categoria",
            y="Quantidade",
            title="Distribuição por Categoria",
        )

        st.plotly_chart(fig_categoria, use_container_width=True)

    # =========================
    # GRÁFICO FATURAMENTO
    # =========================

    if "FAIXA_FATURAMENTO" in df_filtrado.columns:

        fat_count = (
            df_filtrado["FAIXA_FATURAMENTO"]
            .value_counts()
            .sort_index()
            .reset_index()
        )

        fat_count.columns = ["Faixa", "Quantidade"]

        fig_fat = px.bar(
            fat_count,
            x="Faixa",
            y="Quantidade",
            title="Distribuição por Faixa de Faturamento",
        )

        st.plotly_chart(fig_fat, use_container_width=True)

    # =========================
    # MAPA BRASIL
    # =========================

    @st.cache_data
    def carregar_geojson():
        url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        with urllib.request.urlopen(url) as response:
            return json.load(response)

    geojson = carregar_geojson()

    if col_uf:

        mapa = (
            df_filtrado[col_uf]
            .value_counts()
            .reset_index()
        )

        mapa.columns = ["UF", "Quantidade"]

        fig_mapa = px.choropleth(
            mapa,
            geojson=geojson,
            locations="UF",
            featureidkey="properties.sigla",
            color="Quantidade",
            scope="south america",
            title="Distribuição de Clientes por Estado",
        )

        fig_mapa.update_geos(fitbounds="locations", visible=False)

        st.plotly_chart(fig_mapa, use_container_width=True)

    st.divider()

    # =========================
    # DOWNLOAD BASE
    # =========================

    csv = df_filtrado.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Baixar base filtrada",
        data=csv,
        file_name="clientes_filtrados.csv",
        mime="text/csv",
    )

    # =========================
    # TABELA
    # =========================

    st.subheader("Base de Clientes")

    st.dataframe(
        df_filtrado,
        use_container_width=True,
        height=400
    )
