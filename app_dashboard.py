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
        return "🔴 INATIVO", "#E74C3C"

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

busca_tel = st.sidebar.text_input("Buscar por Telefone", key="busca_tel")

if busca_tel:
    # Usa a função limpar_telefone e a coluna TEL_LIMPO criadas na Parte 1
    tel_busca_limpo = limpar_telefone(busca_tel)

    df_filtrado = df_filtrado[
        df_filtrado["TEL_LIMPO"].str.contains(tel_busca_limpo, na=False)
    ]

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
    # --- COLUNA DIREITA: CRM ---
    with col_crm:
        st.subheader("📝 Notas e Histórico")
        
        # Seletor de usuário (Pode ser expandido conforme a equipe crescer)
        lista_pessoas = ["João Tadra", "Ana", "Pedro", "João Paulo", "Bernardo", "Thiago"]
        quem_comentou = st.selectbox("Quem está comentando?", lista_pessoas)

        # Controle do estado do campo de texto para permitir o reset após salvar
        if "texto_nota" not in st.session_state:
            st.session_state.texto_nota = ""

        # Função disparada pelo botão (Callback)
        def clicar_salvar():
            # Pega o valor atual do campo pela KEY definida no widget
            texto_digitado = st.session_state.txt_area_crm
            
            if texto_digitado.strip():
                # Data e Hora (Ajustado para Horário de Brasília se necessário)
                agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Formata o texto com o autor
                texto_final = f"[{quem_comentou}] {texto_digitado.strip()}"
                
                # Inicializa a lista de comentários para o cliente se não existir
                if id_cliente not in comentarios:
                    comentarios[id_cliente] = []
                
                # Insere no topo da lista (mais recente primeiro)
                comentarios[id_cliente].insert(0, {"texto": texto_final, "data": agora})
                
                # Salva no arquivo JSON (Função definida na Parte 2)
                salvar_comentarios(comentarios)
                
                # RESET DOS CAMPOS: Limpa a variável de estado e o widget
                st.session_state.texto_nota = ""
                st.session_state.txt_area_crm = "" 
                st.success("Nota salva com sucesso!")
            else:
                st.warning("O campo de nota está vazio.")

        # Widget de entrada de texto
        st.text_area(
            "Novo registro de interação:", 
            placeholder="Ex: Cliente solicitou nova tabela de preços / Previsão de compra para semana que vem...", 
            key="txt_area_crm",
            value=st.session_state.texto_nota,
            height=120
        )
        
        st.button("Salvar Comentário", on_click=clicar_salvar, use_container_width=True)
        st.divider()

        # Listagem do Histórico de Comentários
        if id_cliente in comentarios and isinstance(comentarios[id_cliente], list):
            for idx, item in enumerate(comentarios[id_cliente]):
                with st.container():
                    c1, c2 = st.columns([0.85, 0.15])
                    
                    # Exibe data e o texto da nota
                    c1.caption(f"📅 {item['data']}")
                    c1.write(item['texto'])
                    
                    # Botão para excluir nota específica
                    if c2.button("🗑️", key=f"del_{id_cliente}_{idx}"):
                        comentarios[id_cliente].pop(idx)
                        salvar_comentarios(comentarios)
                        st.rerun()
                        
                    st.markdown("<hr style='margin:10px 0; opacity:0.1'>", unsafe_allow_html=True)
        else:
            st.info("Nenhum histórico registrado para este cliente.")
            
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

                st.markdown("---")
                st.subheader(f"🚚 Detalhamento Logístico: {dados_cadastrais[COL_CIDADE]}")
                
                c_lt1, c_lt2, c_lt3 = st.columns(3)
                with c_lt1:
                    st.metric("Prazo Total", f"{total_dias} dias úteis")
                with c_lt2:
                    st.metric("Estimativa Transporte", f"{transp_estimado} dias", help="Tempo previsto para a mercadoria em trânsito")
                with c_lt3:
                    st.metric("Processamento Interno", f"{proc_interno} dias", help="Tempo de separação e faturamento no CD")
            
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
    # INTELIGÊNCIA DE MERCADO
    # =========================
    st.markdown("---")
    col_opp1, col_opp2 = st.columns(2)

    with col_opp1:
        # PRODUTOS QUE NÃO COMPRA (Gap Analysis)
        produtos_cliente = set(vendas_cliente["DESC PRODUTO"].unique())
        
        # Filtra a base total para pegar apenas produtos reais
        blacklist = ["CONFERIDO", "TESTE", "AJUSTE", "FRETE", "DESCONTO"]
        regex_blacklist = "|".join(blacklist)
        
        todos_produtos = set(
            df_vendas[
                (~df_vendas["DESC PRODUTO"].str.upper().str.contains(regex_blacklist, na=False))
            ]["DESC PRODUTO"].unique()
        )
        
        produtos_nao_compra = sorted(list(todos_produtos - produtos_cliente))
        df_nao_compra = pd.DataFrame({
            "Sugestões de Itens para Ofertar": produtos_nao_compra
        }).head(15)

        st.subheader("🚨 Gap de Mix")
        st.write("Produtos que este cliente ainda não trabalha:")
        st.dataframe(df_nao_compra, use_container_width=True, hide_index=True)

    with col_opp2:
        # CROSS SELL (Linhas Faltantes)
        linhas_cliente = set(
            vendas_cliente["LINHA"]
            .astype(str).str.strip()
            .replace(["", "nan", "None"], pd.NA).dropna().unique()
        )
        
        todas_linhas = set(
            df_vendas["LINHA"]
            .astype(str).str.strip()
            .replace(["", "nan", "None"], pd.NA).dropna().unique()
        )
        
        # Remove a linha "0" ou vazia se existir
        linhas_faltantes = sorted(list(todas_linhas - linhas_cliente - {"0", ""}))
        
        df_cross = pd.DataFrame({
            "Categorias Não Exploradas": linhas_faltantes
        })

        st.subheader("💡 Cross-sell")
        st.write("Linhas completas que podem ser introduzidas:")
        st.dataframe(df_cross, use_container_width=True, hide_index=True)

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

        # 5. PERFORMANCE POR CATEGORIA (Deep Dive)
        st.markdown("---")
        st.markdown("#### 🏆 Destaques por Categoria")
        
        categorias_full = ["Papinhas e Sopinhas", "Snacks", "Macarrões", "Cereais"]
        cat_sel = st.selectbox("Selecione uma categoria para detalhar:", options=categorias_full)
        
        df_cat = vendas_geral[vendas_geral["CAT_CATALOGO"] == cat_sel]
        
        if not df_cat.empty:
            rank = df_cat.groupby("DESC PRODUTO")["VALOR"].sum().sort_values(ascending=False).reset_index()
            
            ce, cd = st.columns(2)
            with ce:
                st.success(f"⭐ **TOP 3: {cat_sel.upper()}**")
                df_top3 = rank.head(3).copy()
                df_top3["VALOR"] = df_top3["VALOR"].apply(lambda x: f"R$ {x:,.2f}")
                st.table(df_top3.rename(columns={"DESC PRODUTO": "Produto", "VALOR": "Total"}))
            with cd:
                st.error(f"⚠️ **OPORTUNIDADE (Menos Vendidos): {cat_sel.upper()}**")
                df_tail3 = rank.tail(3).sort_values("VALOR").copy()
                df_tail3["VALOR"] = df_tail3["VALOR"].apply(lambda x: f"R$ {x:,.2f}")
                st.table(df_tail3.rename(columns={"DESC PRODUTO": "Produto", "VALOR": "Total"}))
        else:
            st.warning(f"Não há registros de venda para a categoria '{cat_sel}' com os filtros aplicados.")

    else:
        st.info("Nenhuma venda encontrada para os clientes selecionados.")
        
# =========================
# GRÁFICO SEGMENTO
# =========================

st.markdown("---")
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
    
# =========================
# GRÁFICO FATURAMENTO (CORRIGIDO)
# =========================

    st.markdown("---")
    col_graf_cad1, col_graf_cad2 = st.columns(2)

    with col_graf_cad1:
    # Este bloco deve estar identado com 4 espaços
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
    # O erro estava aqui. Todo este bloco precisa de identação:
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
    
# =========================
# MAPA DE CALOR (BRASIL)
# =========================

st.subheader("🗺️ Presença Geográfica")

resumo_estado = df_filtrado[COL_UF].value_counts().reset_index()
resumo_estado.columns = ["UF", "Quantidade"]

# Link do GeoJSON para estados brasileiros
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
        scope="south america", # Foca na América do Sul para melhor visualização
        labels={"Quantidade": "Nº de Clientes"}
    )

    # Ajusta o zoom para focar apenas no Brasil
    fig_mapa.update_geos(fitbounds="locations", visible=False)
    fig_mapa.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    st.plotly_chart(fig_mapa, use_container_width=True)
except:
    st.warning("⚠️ Não foi possível carregar o mapa. Verifique a conexão com a internet.")
    # Fallback para gráfico de barras se o mapa falhar
    st.bar_chart(resumo_estado.set_index("UF"))

st.divider()

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

































































































