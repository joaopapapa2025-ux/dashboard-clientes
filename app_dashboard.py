import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request
import re
import unicodedata
import os
from io import BytesIO
from datetime import datetime, timedelta

# Bibliotecas para PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

# ==========================================
# 1. CONFIGURAÇÕES E MAPEAMENTO DE COLUNAS
# ==========================================

st.set_page_config(
    page_title="Dashboard Inside Sales - PAPAPÁ",
    layout="wide"
)

# Nomes dos Arquivos
ARQUIVO_BASE = "Base Dashboard Inside Sales.xlsx"
ARQUIVO_LEAD_TIME = "Tabela lead time operacao e comercial.xlsx"
ARQUIVO_COMENTARIOS = "comentarios_clientes.json"

# MAPEAMENTO GLOBAL (Isso resolve os erros de NameError)
# Definimos em MAIÚSCULO para o código interno e minúsculo para compatibilidade
COL_RAZAO = col_razao = "RAZÃO SOCIAL"
COL_CNPJ = col_cnpj = "CNPJ"
COL_UF = col_uf = "UF"
COL_CIDADE = col_cidade = "CIDADE"
COL_BAIRRO = col_bairro = "BAIRRO"
COL_TELEFONE = col_telefone = "TELEFONE"
COL_EMAIL = col_email = "E-MAIL"
COL_VENDEDOR = col_vendedor = "VENDEDOR"
COL_SEGMENTO = col_segmento = "SEGMENTO"
COL_TIER = col_tier = "TIER"
COL_ESTRAT = col_estrat = "ESTRATÉGIA"
COL_ULT_COMPRA = col_ult_compra = "ÚLTIMA COMPRA"
COL_FAT_9M = col_fat_9m = "TOTAL ÚLTIMO 9 MESES"
COL_GRUPO = col_grupo = "GRUPO ECONÔMICO"

# Colunas de Meses para o Farol (Ajuste conforme os nomes na sua planilha)
COL_MES_ATUAL = "FEV/26"
COL_MES_ANT = "JAN/26"

# ==========================================
# 2. PROTEÇÃO DE ACESSO
# ==========================================

CODIGO_ACESSO = "amamosnossosclientes"

if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False

if not st.session_state.acesso_liberado:
    st.title("🔒 Acesso Restrito - Papapá")
    codigo_digitado = st.text_input("Digite o código de acesso", type="password")
    if st.button("Entrar"):
        if codigo_digitado == CODIGO_ACESSO:
            st.session_state.acesso_liberado = True
            st.rerun()
        else:
            st.error("Código incorreto")
    st.stop()

# ==========================================
# 3. FUNÇÕES DE SUPORTE E CARREGAMENTO
# ==========================================

def limpar_cnpj(val):
    return re.sub(r'\D', '', str(val)) if pd.notna(val) else ""

def normalizar_texto(txt):
    if not txt: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(txt).upper().strip()) 
                   if unicodedata.category(c) != 'Mn')

@st.cache_data
def carregar_dados():
    try:
        # Base Completa
        df = pd.read_excel(ARQUIVO_BASE, sheet_name="BASE COMPLETA")
        df.columns = df.columns.str.strip()
        
        # Mix de Vendas
        df_mix = pd.read_excel(ARQUIVO_BASE, sheet_name="MIX")
        df_mix.columns = df_mix.columns.str.strip()
        
        # Lead Time
        try:
            df_lt = pd.read_excel(ARQUIVO_LEAD_TIME)
            df_lt.columns = df_lt.columns.str.strip()
        except:
            df_lt = pd.DataFrame()
            
        return df, df_mix, df_lt
    except Exception as e:
        st.error(f"Erro ao carregar arquivos Excel: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_raw, df_mix, df_lt = carregar_dados()

# Processamento de IDs
if not df_raw.empty:
    df = df_raw.copy()
    df['CNPJ_LIMPO'] = df[COL_CNPJ].apply(limpar_cnpj)
    df_mix['CNPJ_LIMPO'] = df_mix['CNPJ'].astype(str).apply(limpar_cnpj)
else:
    st.error("A base de dados está vazia ou não foi encontrada.")
    st.stop()

# CRM JSON
def carregar_crm():
    if os.path.exists(ARQUIVO_COMENTARIOS):
        with open(ARQUIVO_COMENTARIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_crm(dados):
    with open(ARQUIVO_COMENTARIOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# ==========================================
# 4. LÓGICA DO SISTEMA DE FAROL
# ==========================================

def calcular_farol(row):
    # Pega os valores dos últimos dois meses da planilha
    f_atual = pd.to_numeric(row.get(COL_MES_ATUAL, 0), errors='coerce')
    f_ant = pd.to_numeric(row.get(COL_MES_ANT, 0), errors='coerce')
    
    if f_atual > 0:
        return "🟢 ATIVO", "#27AE60"
    elif f_ant > 0:
        return "🟡 ALERTA", "#F1C40F"
    else:
        return "🔴 INATIVO", "#E74C3C"

# ==========================================
# 5. SIDEBAR E FILTROS
# ==========================================

st.sidebar.title("Filtros de Busca")
busca = st.sidebar.text_input("🔍 Razão Social ou CNPJ")
filtro_vendedor = st.sidebar.multiselect("Vendedor", sorted(df[COL_VENDEDOR].dropna().unique()))
filtro_segmento = st.sidebar.multiselect("Segmento", sorted(df[COL_SEGMENTO].dropna().unique()))
filtro_uf = st.sidebar.multiselect("Estado (UF)", sorted(df[COL_UF].dropna().unique()))

# Aplicação dos Filtros
df_filtrado = df.copy()
if busca:
    df_filtrado = df_filtrado[df_filtrado[COL_RAZAO].str.contains(busca, case=False, na=False) | 
                              df_filtrado['CNPJ_LIMPO'].str.contains(limpar_cnpj(busca))]
if filtro_vendedor:
    df_filtrado = df_filtrado[df_filtrado[COL_VENDEDOR].isin(filtro_vendedor)]
if filtro_segmento:
    df_filtrado = df_filtrado[df_filtrado[COL_SEGMENTO].isin(filtro_segmento)]
if filtro_uf:
    df_filtrado = df_filtrado[df_filtrado[COL_UF].isin(filtro_uf)]

# ==========================================
# 6. INTERFACE PRINCIPAL
# ==========================================

st.title("🚀 Dashboard Inside Sales - Papapá")

if len(df_filtrado) == 1:
    cliente = df_filtrado.iloc[0]
    id_cnpj = cliente['CNPJ_LIMPO']
    status_txt, status_cor = calcular_farol(cliente)
    
    # CARD VISUAL DO CLIENTE (Com Farol)
    st.markdown(f"""
        <div style="padding:25px; border-radius:15px; background-color:#fdfdfd; border-left: 12px solid {status_cor}; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1 style="margin:0; color:#333;">{cliente[COL_RAZAO]}</h1>
                <span style="background-color:{status_cor}; color:white; padding:8px 25px; border-radius:30px; font-weight:bold; font-size:20px;">
                    {status_txt}
                </span>
            </div>
            <p style="font-size:18px; color:#666; margin-top:10px;">
                <b>CNPJ:</b> {cliente[COL_CNPJ]} | <b>Grupo:</b> {cliente[COL_GRUPO]}
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.write("") # Espaçamento

    col_info, col_crm = st.columns([1, 1])

    with col_info:
        st.subheader("📋 Informações Estratégicas")
        st.write(f"**Vendedor:** {cliente[COL_VENDEDOR]}")
        st.write(f"**Segmento:** {cliente[COL_SEGMENTO]}")
        st.write(f"**Tier:** {cliente[COL_TIER]}")
        st.write(f"**Estratégia:** {cliente[COL_ESTRAT]}")
        st.write(f"**Local:** {cliente[COL_CIDADE]} - {cliente[COL_UF]} ({cliente[COL_BAIRRO]})")
        st.write(f"**Última Compra:** {cliente[COL_ULT_COMPRA]}")
        st.write(f"**Faturamento Acumulado (9M):** R$ {cliente[COL_FAT_9M]:,.2f}")
        
        # Botão WhatsApp
        tel = limpar_cnpj(cliente[COL_TELEFONE])
        if tel:
            st.link_button(f"💬 Abrir WhatsApp ({cliente[COL_TELEFONE]})", f"https://wa.me/55{tel}", use_container_width=True)

        # Cálculo Lead Time
        if not df_lt.empty:
            cid_n = normalizar_texto(cliente[COL_CIDADE])
            uf_n = normalizar_texto(cliente[COL_UF])
            match_lt = df_lt[(df_lt.iloc[:,0].apply(normalizar_texto) == cid_n) & 
                           (df_lt.iloc[:,1].apply(normalizar_texto) == uf_n)]
            if not match_lt.empty:
                prazo = match_lt.iloc[0, 2]
                st.info(f"🚚 **Lead Time de Entrega:** {prazo} dias úteis")

    with col_crm:
        st.subheader("📝 Histórico CRM")
        crm = carregar_crm()
        
        # Adição de Notas
        operador = st.selectbox("Quem está atendendo?", ["Bernardo", "João Paulo", "João Tadra", "Ana", "Pedro"])
        nova_nota = st.text_area("Descreva a interação:", height=100)
        
        if st.button("Salvar Nota no CRM", use_container_width=True):
            if nova_nota:
                data_agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                if id_cnpj not in crm: crm[id_cnpj] = []
                crm[id_cnpj].insert(0, {"data": data_agora, "autor": operador, "texto": nova_nota})
                salvar_crm(crm)
                st.success("Nota salva com sucesso!")
                st.rerun()

        # Exibição de Notas Antigas
        if id_cnpj in crm:
            for item in crm[id_cnpj][:5]:
                with st.expander(f"📌 {item['data']} - {item['autor']}"):
                    st.write(item['texto'])

    # --- ANÁLISE DE MIX ---
    st.divider()
    st.subheader("📊 Mix de Produtos do Cliente")
    mix_c = df_mix[df_mix['CNPJ_LIMPO'] == id_cnpj]
    
    if not mix_c.empty:
        c1, c2 = st.columns(2)
        # Gráfico por Linha
        fig_mix = px.pie(mix_c, values='VALOR', names='LINHA', hole=0.4, title="Participação por Linha")
        c1.plotly_chart(fig_mix, use_container_width=True)
        
        # Histórico de Pedidos
        mix_c['DATA PEDIDO'] = pd.to_datetime(mix_c['DATA PEDIDO'])
        evolucao = mix_c.groupby(mix_c['DATA PEDIDO'].dt.to_period('M'))['VALOR'].sum().reset_index()
        evolucao['DATA PEDIDO'] = evolucao['DATA PEDIDO'].astype(str)
        fig_evol = px.bar(evolucao, x='DATA PEDIDO', y='VALOR', title="Evolução de Compras Mensal", color_discrete_sequence=['#E63946'])
        c2.plotly_chart(fig_evol, use_container_width=True)
    else:
        st.warning("Nenhum dado de Mix encontrado para este CNPJ.")

elif len(df_filtrado) > 1:
    # VISÃO GERAL DA LISTA
    st.write(f"### Clientes Encontrados: {len(df_filtrado)}")
    
    # KPIs Rápidos
    k1, k2, k3 = st.columns(3)
    k1.metric("Faturamento Filtrado", f"R$ {df_filtrado[COL_FAT_9M].sum():,.2f}")
    k2.metric("Média por Cliente", f"R$ {df_filtrado[COL_FAT_9M].mean():,.2f}")
    k3.metric("Vendedores na Lista", df_filtrado[COL_VENDEDOR].nunique())

    # Tabela com as novas colunas
    st.dataframe(
        df_filtrado[[COL_RAZAO, COL_VENDEDOR, COL_SEGMENTO, COL_TIER, COL_UF, COL_FAT_9M]], 
        use_container_width=True,
        hide_index=True
    )

    # MAPA BRASIL
    try:
        st.divider()
        st.subheader("🗺️ Distribuição Geográfica")
        resumo_uf = df_filtrado.groupby(COL_UF).size().reset_index(name='Quantidade')
        
        url_geo = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        with urllib.request.urlopen(url_geo) as response:
            geojson_br = json.load(response)

        fig_mapa = px.choropleth(
            resumo_uf,
            geojson=geojson_br,
            locations=COL_UF,
            featureidkey="properties.sigla",
            color="Quantidade",
            color_continuous_scale="Reds",
            title="Clientes por Estado"
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_mapa, use_container_width=True)
    except:
        st.info("Mapa indisponível no momento.")

else:
    st.info("Use os filtros ao lado para encontrar um cliente.")

# ==========================================
# 7. EXPORTAÇÃO (EXCEL)
# ==========================================

st.sidebar.divider()
def gerar_excel(df_export):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Base Filtrada')
    return output.getvalue()

if st.sidebar.button("📥 Baixar Lista Filtrada (Excel)"):
    excel_data = gerar_excel(df_filtrado)
    st.sidebar.download_button("Clique para Confirmar Download", excel_data, "clientes_papapa.xlsx")
