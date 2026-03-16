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
# COMENTÁRIOS POR CLIENTE
# =========================

ARQUIVO_COMENTARIOS = "comentarios_clientes.json"

def carregar_comentarios():

    try:
        with open(ARQUIVO_COMENTARIOS, "r") as f:
            return json.load(f)
    except:
        return {}

def salvar_comentarios(comentarios):

    with open(ARQUIVO_COMENTARIOS, "w") as f:
        json.dump(comentarios, f, indent=4)

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
# CARD CLIENTE + CRM (COMENTÁRIOS)
# =========================

# =========================
# CARD CLIENTE + CRM (COMENTÁRIOS)
# =========================

vendas_cliente = pd.DataFrame()

if len(df_filtrado) == 1:
    cliente = df_filtrado.iloc[0]
    id_cliente = cliente["CNPJ_LIMPO"]

    st.markdown("### 🏢 Cliente encontrado")
    
    # Criamos duas colunas para o topo: Info à esquerda e CRM à direita
    col_info, col_crm = st.columns([1, 1])

    with col_info:
        # --- LÓGICA DE BUSCA DO LEAD TIME AJUSTADA ---
        prazo_html = ""
        try:
            # Lendo a aba de lead time (índice 1)
            # skiprows=2 pula as linhas vazias do topo
            df_lt = pd.read_excel("Tabela lead time operacao e comercial.xlsx", sheet_name=1, skiprows=2)
            
            # Ajustando colunas conforme seu arquivo real:
            # Coluna 1 = Cidade, Coluna 2 = UF, Coluna 3 = Lead Time Total
            df_lt = df_lt.iloc[:, [1, 2, 3]]
            df_lt.columns = ['Cidade', 'UF', 'Total']
            
            def normalizar(txt):
                import unicodedata
                if pd.isna(txt): return ""
                return "".join(c for c in unicodedata.normalize('NFD', str(txt).upper().strip())
                               if unicodedata.category(c) != 'Mn')

            cidade_cliente = normalizar(cliente[col_cidade])
            uf_cliente = normalizar(cliente[col_uf])
            
            df_lt['Cidade_Norm'] = df_lt['Cidade'].apply(normalizar)
            df_lt['UF_Norm'] = df_lt['UF'].apply(normalizar)
            
            busca = df_lt[(df_lt['Cidade_Norm'] == cidade_cliente) & 
                          (df_lt['UF_Norm'] == uf_cliente)]
            
            if not busca.empty:
                v_prazo = busca['Total'].values[0]
                # Agora aceita o valor 0 (comum para Curitiba)
                if pd.notna(v_prazo):
                    prazo_html = f"<br><b style='color:#E67E22;'>🚚 Prazo de Entrega: {int(v_prazo)} dias úteis</b>"
                else:
                    prazo_html = "<br><i style='color:gray;'>📍 Prazo não preenchido no Excel</i>"
            else:
                prazo_html = f"<br><i style='color:gray; font-size:11px;'>📍 Logística não mapeada ({cidade_cliente})</i>"
        except Exception as e:
            prazo_html = ""

        # --- QUADRO INFORMATIVO ---
        st.markdown(
            f"""
            <div style="padding:20px; border-radius:10px; background-color:#f6f6f6; border: 1px solid #ddd">
                <h3 style="color:#FF4B4B; margin-top:0;">{cliente[col_razao]}</h3>
                <b>Vendedor:</b> <span style="color:#1f77b4">{cliente[col_vendedor]}</span><br><br>
                <b>CNPJ:</b> {cliente[col_cnpj]}<br>
                <b>Telefone:</b> {cliente[col_telefone]}<br>
                <b>E-mail:</b> {cliente[col_email]}<br>
                <b>Cidade:</b> {cliente[col_cidade]} - {cliente[col_uf]}
                {prazo_html}
            </div>
            """, unsafe_allow_html=True
        )

        # Botões de ação
        telefone_btn = limpar_telefone(cliente[col_telefone])
        if telefone_btn:
            st.link_button("💬 Chamar no WhatsApp", f"https://wa.me/55{telefone_btn}")
        
        if not df_vendas.empty:
            v_cli = df_vendas[df_vendas["CNPJ_LIMPO"] == id_cliente]
            pdf_arq = gerar_pdf_cliente(cliente, v_cli)
            st.download_button("📄 Baixar PDF do Cliente", data=pdf_arq, 
                             file_name=f"relatorio_{cliente[col_razao]}.pdf", mime="application/pdf")

    with col_crm:
        st.subheader("📝 Notas e Histórico")
        
        # Campo para novo comentário
        novo_txt = st.text_area("Novo registro:", placeholder="O que foi conversado?", key="txt_area_crm")
        
        if st.button("Salvar Comentário"):
            if novo_txt.strip():
                # Ajusta para o horário de Brasília (UTC-3)
                agora = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M")
                
                novo_registro = {"texto": novo_txt, "data": agora}
                
                # Garantia de que a chave existe e é uma lista
                if id_cliente not in comentarios or not isinstance(comentarios[id_cliente], list):
                    comentarios[id_cliente] = []
                
                comentarios[id_cliente].insert(0, novo_registro) # Mais recente primeiro
                salvar_comentarios(comentarios)
                st.success("Salvo com sucesso!")
                st.rerun()
            else:
                st.warning("O campo de comentário está vazio.")

            st.divider()

        # Listagem de comentários com botão de excluir
        if id_cliente in comentarios and isinstance(comentarios[id_cliente], list):
            for idx, item in enumerate(comentarios[id_cliente]):
                with st.container():
                    if isinstance(item, dict) and 'data' in item:
                        c1, c2 = st.columns([0.85, 0.15])
                        c1.caption(f"📅 {item['data']}")
                        c1.write(item['texto'])
                        
                        if c2.button("🗑️", key=f"del_{id_cliente}_{idx}"):
                            comentarios[id_cliente].pop(idx)
                            salvar_comentarios(comentarios)
                            st.rerun()
                        st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        else:
            st.info("Nenhum histórico registrado para este cliente.")

# ==========================================
# CÁLCULO E EXIBIÇÃO DE LEAD TIME POR CLIENTE
# ==========================================

# 1. Carregamento da base de Lead Time
@st.cache_data
def carregar_lead_time():
    try:
        # Tenta ler como Excel (ajuste o nome se necessário)
        caminho = "Tabela lead time operacao e comercial.xlsx"
        # Lendo a aba específica (pelo nome ou índice)
        # Se for a segunda aba, usamos sheet_name=1
        df_lt = pd.read_excel(caminho, sheet_name=1, skiprows=2)
        
        # Ajuste de colunas baseado no seu arquivo
        df_lt = df_lt.iloc[:, [1, 2, 3, 4]] 
        df_lt.columns = ['Cidade', 'UF', 'Lead_Time_Total', 'Lead_Time_Transp']
        return df_lt.dropna(subset=['Cidade', 'UF'])
    except Exception as e:
        st.error(f"Erro ao carregar Excel de Lead Time: {e}")
        return pd.DataFrame()

df_lead_time = carregar_lead_time()

# 2. Exibição (Mesma lógica anterior)
if 'id_cliente' in locals() and id_cliente:
    try:
        dados_cadastrais = df_filtrado[df_filtrado["CNPJ_LIMPO"] == id_cliente].iloc[0]
        cidade_alvo = str(dados_cadastrais[col_cidade]).upper().strip()
        uf_alvo = str(dados_cadastrais[col_uf]).upper().strip()

        if not df_lead_time.empty:
            busca = df_lead_time[
                (df_lead_time['Cidade'].astype(str).str.upper().str.strip() == cidade_alvo) & 
                (df_lead_time['UF'].astype(str).str.upper().str.strip() == uf_alvo)
            ]

            if not busca.empty:
                lt_total = busca['Lead_Time_Total'].values[0]
                lt_transp = busca['Lead_Time_Transp'].values[0]
                
                st.markdown("---")
                st.subheader(f"🚚 Logística e Entrega: {cidade_alvo} - {uf_alvo}")
                
                c_lt1, c_lt2, c_lt3 = st.columns(3)
                with c_lt1:
                    st.metric("Lead Time Total", f"{int(lt_total)} dias úteis")
                with c_lt2:
                    st.metric("Lead Time Transp.", f"{int(lt_transp)} dias úteis")
                with c_lt3:
                    proc = int(lt_total) - int(lt_transp)
                    st.metric("Processamento Interno", f"{max(0, proc)} dias")
            else:
                st.info(f"ℹ️ Lead Time não mapeado para {cidade_alvo}/{uf_alvo}.")
    except Exception as e:
        pass

    # =========================
    # ANÁLISE DE COMPRAS (DENTRO DO IF DO CLIENTE ÚNICO)
    # =========================

    if not vendas_cliente.empty:
        st.divider()
        st.subheader("📊 Análise de Compras do Cliente")

        # Conversão de data para garantir funcionamento dos gráficos
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

        # PRODUTOS QUE NÃO COMPRA
        produtos_cliente = set(vendas_cliente["DESC PRODUTO"].unique())
        todos_produtos = set(
            df_vendas[
                (~df_vendas["DESC PRODUTO"].str.upper().str.contains("CONFERIDO", na=False)) &
                (~df_vendas["DESC PRODUTO"].str.upper().str.contains("TESTE", na=False)) &
                (~df_vendas["DESC PRODUTO"].str.upper().str.contains("AJUSTE", na=False))
            ]["DESC PRODUTO"].unique()
        )
        produtos_nao_compra = list(todos_produtos - produtos_cliente)
        df_nao_compra = pd.DataFrame({
            "Produtos que o cliente ainda não compra": produtos_nao_compra
        }).head(20)

        st.subheader("🚨 Produtos que o cliente ainda não compra")
        st.dataframe(df_nao_compra, use_container_width=True)

        # CROSS SELL
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
        st.dataframe(df_cross, use_container_width=True, hide_index=True)

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
# ANÁLISE DE MIX COMPLETA (COLORIDA + SEM ERRO DE NEGATIVO)
# =========================

st.divider()
st.subheader("📦 Análise Geral de Mix e Produtos")

if not df_vendas.empty:
    # 1. Filtro Inicial e Trava de Segurança
    cnpjs_visiveis = df_filtrado["CNPJ_LIMPO"].unique()
    vendas_geral = df_vendas[df_vendas["CNPJ_LIMPO"].isin(cnpjs_visiveis)].copy()
    
    # Remove itens de conferência/ajuste
    vendas_geral = vendas_geral[~vendas_geral["DESC PRODUTO"].str.contains("CONFERIDO", case=False, na=False)]

    if not vendas_geral.empty:
        # 2. MAPEAMENTO (Categorias do Catálogo, Sabor e Idade)
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

        # 3. LINHA 1 DE GRÁFICOS (Categorias e Sabores)
        c1, c2 = st.columns(2)
        with c1:
            mix_cat = vendas_geral.groupby("CAT_CATALOGO")["VALOR"].sum().reset_index()
            st.plotly_chart(px.pie(mix_cat, names="CAT_CATALOGO", values="VALOR", title="Mix por Categoria (Catálogo)", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        with c2:
            mix_sabor = vendas_geral.groupby("SABOR")["VALOR"].sum().reset_index()
            st.plotly_chart(px.pie(mix_sabor, names="SABOR", values="VALOR", title="Divisão Doce vs Salgado", color_discrete_map={"Doce":"#FFB6C1","Salgado":"#90EE90"}), use_container_width=True)

        # 4. LINHA 2 DE GRÁFICOS (Idade Colorida e Top 10)
        c3, c4 = st.columns(2)
        with c3:
            mix_idade = vendas_geral.groupby("IDADE")["VALOR"].sum().reset_index()
            fig_idade = px.bar(mix_idade, x="IDADE", y="VALOR", color="IDADE", title="Vendas por Idade Recomendada", color_discrete_sequence=px.colors.qualitative.Bold)
            fig_idade.update_layout(showlegend=False)
            st.plotly_chart(fig_idade, use_container_width=True)
        with c4:
            top_10 = vendas_geral.groupby("DESC PRODUTO")["VALOR"].sum().reset_index().sort_values("VALOR", ascending=False).head(10)
            st.plotly_chart(px.bar(top_10, x="VALOR", y="DESC PRODUTO", orientation="h", title="Top 10 Produtos (Geral)"), use_container_width=True)

        # 5. PERFORMANCE POR CATEGORIA (BLINDAGEM TOTAL COM TABELAS)
        st.markdown("---")
        st.markdown("#### 🏆 Destaques por Categoria")
        
        # Lista com todas as categorias do catálogo
        categorias_full = ["Papinhas e Sopinhas", "Snacks", "Macarrões", "Cereais"]
        cat_sel = st.selectbox("Selecione a Categoria:", options=categorias_full)
        
        df_cat = vendas_geral[vendas_geral["CAT_CATALOGO"] == cat_sel]
        
        if not df_cat.empty:
            rank = df_cat.groupby("DESC PRODUTO")["VALOR"].sum().sort_values(ascending=False).reset_index()
            rank["VALOR"] = rank["VALOR"].apply(lambda x: f"R$ {x:,.2f}")

            ce, cd = st.columns(2)
            with ce:
                st.success(f"⭐ **MAIS VENDIDOS: {cat_sel.upper()}**")
                st.table(rank.head(3).rename(columns={"DESC PRODUTO": "Produto", "VALOR": "Faturamento"}))
            with cd:
                st.error(f"⚠️ **MENOS VENDIDOS: {cat_sel.upper()}**")
                st.table(rank.tail(3).sort_values("VALOR").rename(columns={"DESC PRODUTO": "Produto", "VALOR": "Faturamento"}))
        else:
            st.warning(f"Sem vendas registradas para {cat_sel} nesta seleção.")

    else:
        st.info("Nenhuma venda encontrada nos filtros atuais.")
        
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

































































































