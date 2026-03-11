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
# CARREGAR BASE CLIENTES
# =========================

@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO_BASE, sheet_name=0)
    df.columns = df.columns.str.strip().str.upper()
    return df

df = carregar_dados()

# =========================
# CARREGAR BASE PRODUTOS
# =========================

@st.cache_data
def carregar_vendas():
    try:
        vendas = pd.read_excel(ARQUIVO_BASE, sheet_name=1)
        vendas.columns = vendas.columns.str.strip().str.upper()
        
        vendas["CNPJ_LIMPO"] = vendas["CNPJ"].astype(str).str.replace(r"\D", "", regex=True)

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
        ("GRID",(0,0),(-1,-1),0.5,colors.grey)
    ]))

    elementos.append(tabela_cliente)
    elementos.append(Spacer(1,25))

    elementos.append(Paragraph("Histórico de Compras", styles["Heading2"]))

    if not vendas_cliente.empty:

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
            if total_pedidos > 0:
                ticket_medio = total_valor / total_pedidos

        if "DATA PEDIDO" in vendas_cliente.columns:
            data_max = vendas_cliente["DATA PEDIDO"].max()
            if pd.notna(data_max):
                ultima_compra = pd.to_datetime(data_max).strftime("%d/%m/%Y")

        resumo_comercial = [

            ["Total Produtos Comprados", total_skus],
            ["Total Unidades", int(total_qtd)],
            ["Valor Total Comprado", f"R$ {total_valor:,.2f}"],
            ["Ticket Médio", f"R$ {ticket_medio:,.2f}"],
            ["Data da Última Compra", ultima_compra]

        ]

        tabela_resumo = Table(resumo_comercial, colWidths=[8*cm,8*cm])

        tabela_resumo.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.5,colors.grey)
        ]))

        elementos.append(Spacer(1,10))
        elementos.append(tabela_resumo)
        elementos.append(Spacer(1,25))

        # HISTÓRICO POR PEDIDO

        elementos.append(Paragraph("Histórico por Pedido", styles["Heading3"]))

        pedidos = (
            vendas_cliente
            .groupby(["DATA PEDIDO","NUMERO NF"])["VALOR"]
            .sum()
            .reset_index()
            .sort_values("DATA PEDIDO", ascending=False)
        )

        dados_pedidos = [["Data","NF","Valor Pedido"]]

        for _,row in pedidos.iterrows():

            data = ""
            if not pd.isna(row["DATA PEDIDO"]):
                data = pd.to_datetime(row["DATA PEDIDO"]).strftime("%d/%m/%Y")

            nf = str(row["NUMERO NF"])
            valor = f"R$ {row['VALOR']:,.2f}"

            dados_pedidos.append([data,nf,valor])

        tabela_pedidos = Table(
            dados_pedidos,
            colWidths=[4*cm,4*cm,4*cm],
            repeatRows=1
        )

        tabela_pedidos.setStyle(TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.25,colors.grey),
            ("ALIGN",(2,1),(2,-1),"RIGHT")

        ]))

        elementos.append(tabela_pedidos)
        elementos.append(Spacer(1,25))

        # TOP PRODUTOS

        elementos.append(Paragraph("Top Produtos Comprados", styles["Heading3"]))

        top_produtos = resumo.head(5)

        dados_top = [["Produto","Linha","Qtd","Valor"]]

        for _,row in top_produtos.iterrows():

            dados_top.append([

                Paragraph(str(row["DESC PRODUTO"]), style_tabela),
                Paragraph(str(row["LINHA"]), style_tabela),
                int(row["QTDE"]),
                f"R$ {row['VALOR']:,.2f}"

            ])

        tabela_top = Table(
            dados_top,
            colWidths=[8*cm,3.5*cm,2*cm,2.5*cm],
            repeatRows=1
        )

        tabela_top.setStyle(TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.25,colors.grey),

            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),

            ("ALIGN",(2,1),(2,-1),"CENTER"),
            ("ALIGN",(3,1),(3,-1),"RIGHT")

        ]))

        elementos.append(tabela_top)
        elementos.append(Spacer(1,25))

        # HISTÓRICO DETALHADO POR PRODUTO

        elementos.append(Paragraph("Histórico Detalhado de Compras", styles["Heading3"]))

        dados_produtos = [
            ["Data","NF","Produto","Linha","Qtd","Valor"]
        ]

        for _,row in vendas_cliente.iterrows():

            data_pedido = ""
            if not pd.isna(row["DATA PEDIDO"]):
                data_pedido = pd.to_datetime(row["DATA PEDIDO"]).strftime("%d/%m/%Y")

            nf = str(row["NUMERO NF"]) if not pd.isna(row["NUMERO NF"]) else ""

            produto = Paragraph(str(row["DESC PRODUTO"]), style_tabela)
            linha = Paragraph(str(row["LINHA"]), style_tabela)

            qtd = int(row["QTDE"]) if not pd.isna(row["QTDE"]) else ""
            valor = f"R$ {row['VALOR']:,.2f}" if not pd.isna(row["VALOR"]) else ""

            dados_produtos.append([
                data_pedido,
                nf,
                produto,
                linha,
                qtd,
                valor
            ])

        tabela_produtos = Table(
            dados_produtos,
            colWidths=[2.5*cm,2.5*cm,7*cm,3.5*cm,2*cm,2.5*cm],
            repeatRows=1
        )

        tabela_produtos.setStyle(TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.25,colors.grey),

            ("ALIGN",(4,1),(4,-1),"CENTER"),
            ("ALIGN",(5,1),(5,-1),"RIGHT")

        ]))

        elementos.append(tabela_produtos)

    else:

        elementos.append(Paragraph("Nenhum histórico de compra encontrado.", styles["Normal"]))

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

faixas = sorted(df_filtrado["FAIXA_FATURAMENTO"].dropna().unique())

faixa_sel = st.sidebar.multiselect("Faixa de Faturamento", faixas, key="filtro_faturamento")

if faixa_sel:
    df_filtrado = df_filtrado[df_filtrado["FAIXA_FATURAMENTO"].isin(faixa_sel)]

# =========================
# TÍTULO
# =========================

st.title("Dashboard Inside Sales - PAPAPÁ")

# =========================
# CARD CLIENTE
# =========================

vendas_cliente = pd.DataFrame()

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

    if not df_vendas.empty:

        vendas_cliente = df_vendas[
            df_vendas["CNPJ_LIMPO"] == cliente["CNPJ_LIMPO"]
        ]

    # GERAR PDF
    pdf = gerar_pdf_cliente(cliente, vendas_cliente)

    st.download_button(
        label="📄 Baixar PDF do Cliente",
        data=pdf,
        file_name=f"relatorio_{cliente[col_razao]}.pdf",
        mime="application/pdf"
    )

    # =========================
    # ANÁLISE DE COMPRAS
    # =========================

    if not vendas_cliente.empty:

        st.divider()
        st.subheader("📊 Análise de Compras do Cliente")

        vendas_cliente["DATA PEDIDO"] = pd.to_datetime(vendas_cliente["DATA PEDIDO"])

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
            title="Mix de Compras por Linha"
        )

        st.plotly_chart(fig_mix, use_container_width=True)

        # TOP PRODUTOS

        top_produtos = (
            vendas_cliente
            .groupby("DESC PRODUTO")["VALOR"]
            .sum()
            .reset_index()
            .sort_values("VALOR", ascending=False)
            .head(10)
        )

        fig_top = px.bar(
            top_produtos,
            x="VALOR",
            y="DESC PRODUTO",
            orientation="h",
            title="Top Produtos Comprados"
        )

        st.plotly_chart(fig_top, use_container_width=True)

        # EVOLUÇÃO DE COMPRAS

        evolucao = (
            vendas_cliente
            .groupby("DATA PEDIDO")["VALOR"]
            .sum()
            .reset_index()
        )

        fig_evolucao = px.line(
            evolucao,
            x="DATA PEDIDO",
            y="VALOR",
            title="Evolução de Compras"
        )

        st.plotly_chart(fig_evolucao, use_container_width=True)

# =========================
# PRODUTOS QUE O CLIENTE NÃO COMPRA
# =========================

if "vendas_cliente" in locals() and not vendas_cliente.empty:

    produtos_cliente = set(
        vendas_cliente["DESC PRODUTO"]
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
    )

    produtos_base = (
        df_vendas["DESC PRODUTO"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # remover produtos inválidos
    produtos_base = produtos_base[
        (~produtos_base.str.contains("CONFERIR", na=False)) &
        (~produtos_base.str.contains("TESTE", na=False)) &
        (~produtos_base.str.contains("AJUSTE", na=False))
    ]

    todos_produtos = set(produtos_base.unique())

    produtos_nao_compra = sorted(list(todos_produtos - produtos_cliente))

    df_nao_compra = pd.DataFrame({
        "Produtos que o cliente ainda não compra": produtos_nao_compra
    })

    st.subheader("🚨 Produtos que o cliente ainda não compra")

    st.dataframe(
        df_nao_compra.head(20),
        use_container_width=True,
        hide_index=True
    )

# =========================
# CROSS SELL
# =========================

if "vendas_cliente" in locals() and not vendas_cliente.empty:

    linhas_cliente = set(
        vendas_cliente["LINHA"]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "None"], pd.NA)
        .dropna()
        .unique()
    )

    todas_linhas = set(
        df_vendas["LINHA"]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "None"], pd.NA)
        .dropna()
        .unique()
    )

    linhas_faltantes = sorted(list(todas_linhas - linhas_cliente))

    df_cross = pd.DataFrame({
        "Linhas que o cliente ainda não compra (oportunidade)": linhas_faltantes
    })

    st.subheader("💡 Oportunidades de Cross-sell")

    st.dataframe(
        df_cross,
        use_container_width=True,
        hide_index=True
    )

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

st.plotly_chart(fig_cat, use_container_width=True)

# =========================
# GRÁFICO FATURAMENTO
# =========================

resumo_faturamento = df_filtrado["FAIXA_FATURAMENTO"].value_counts().reset_index()
resumo_faturamento.columns = ["Faixa", "Quantidade"]

fig_fat = px.bar(
    resumo_faturamento,
    x="Faixa",
    y="Quantidade",
    title="Distribuição por Faixa de Faturamento"
)

st.plotly_chart(fig_fat, use_container_width=True)

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

st.plotly_chart(fig_mapa, use_container_width=True)

st.divider()

# =========================
# GERAR EXCEL
# =========================

def gerar_excel(df):

    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Clientes")

    return buffer.getvalue()

excel = gerar_excel(df_filtrado)

st.download_button(
    label="📥 Baixar base filtrada em Excel",
    data=excel,
    file_name="clientes_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# TABELA
# =========================

st.subheader("Base de Clientes")

st.dataframe(df_filtrado, use_container_width=True)




















































