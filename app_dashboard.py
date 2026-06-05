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

import streamlit as st

with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")

    # BOTÃO HUB INSIDE SALES (ABRE EM NOVA ABA)
    st.markdown("""
        <a href="https://playbook-mmnvwibahw4xwru2endcx2.streamlit.app/" target="_blank" style="text-decoration: none;">
            <div style="
                background-color: #ffffff;
                color: #31333F;
                padding: 10px;
                text-align: center;
                border-radius: 8px;
                border: 1px solid #d1d1d1;
                margin-top: 10px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            ">
                🚀 Hub Inside Sales
            </div>
        </a>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
import json
import os

def categorizar_produto_papapa(row):
    # 1. Pega os dados brutos e limpa
    l = str(row.get('LINHA', '')).upper().strip()
    p = str(row.get('DESC PRODUTO', '')).upper().strip()
    
    # --- REGRA 1: YOGUZINHO (PRIORIDADE ABSOLUTA) ---
    if "IOGURTE" in p or "YOGU" in p:
        return "YOGUZINHO"

    # --- REGRA 2: LA CHEF (IDENTIFICAÇÃO POR PALAVRA-CHAVE DO PRODUTO) ---
    # Se no nome do produto tiver Lentilha, Risotinho ou Caseirinho, 
    # vira LA CHEF na hora, não importa o que diz a coluna LINHA.
    palavras_la_chef = ["LENTILHA", "RISOTINHO", "CASEIRINHO", "180G"]
    if any(x in p for x in palavras_la_chef):
        return "LA CHEF"

    # --- REGRA 3: SOPINHAS (APENAS SE NÃO FOR LA CHEF) ---
    if "SOPINHA" in p or "SOPINHA" in l:
        return "SOPINHAS"

    # --- REGRA 4: PAPINHAS SALGADAS (120G) ---
    if "120G" in p or "CARNE" in l or "SALGADA" in l or "FRANGO" in p:
        return "PAPINHAS SALGADAS"
    
    # --- REGRA 5: PAPINHAS DE FRUTAS / OUTROS ---
    if "FRUTA" in l or "ORG" in l: return "PAPINHAS DE FRUTAS"
    if "CERAL" in l or "AVEIA" in l: return "CEREAIS"
    if "DENTI" in l: return "DENTIÇÃO"
    
    return l if l != "" else "OUTROS"

# Nome do arquivo de banco de dados
ARQUIVO_DATABASE = "database_comentarios.json"

# Função para garantir que o arquivo exista e carregar os dados
def carregar_comentarios():
    if os.path.exists(ARQUIVO_DATABASE):
        try:
            with open(ARQUIVO_DATABASE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    else:
        # Se não existe, cria um arquivo JSON vazio {}
        with open(ARQUIVO_DATABASE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}

def salvar_comentarios(dados):
    with open(ARQUIVO_DATABASE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# Inicializa a variável comentários
comentarios = carregar_comentarios()

def limpar_telefone(tel):
    """Remove caracteres não numéricos do telefone."""
    if pd.isna(tel) or tel == "":
        return ""
    # Mantém apenas os números
    return "".join(filter(str.isdigit, str(tel)))

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="Dashboard Inside Sales - PAPAPÁ",
    layout="wide"
)

# ==========================================
# 🔐 PROTEÇÃO DE ACESSO (F5-PROOF + EXPIRAÇÃO DIÁRIA)
# ==========================================
import streamlit as st
from datetime import date

CODIGO_ACESSO = "amamosnossosclientes"
token_hoje = f"access_{date.today().strftime('%Y%m%d')}" # Gera algo como 'access_20260331'

# 1. Tenta ler o token de acesso da URL
query_params = st.query_params
acesso_valido = query_params.get("auth") == token_hoje

# 2. Se o token não existir ou for de um dia passado, pede a senha
if not acesso_valido:
    st.title("🔐 Acesso Restrito - Papapá")
    st.info(f"Validação necessária para o dia: {date.today().strftime('%d/%m/%Y')}")
    
    codigo_digitado = st.text_input(
        "Digite o código de acesso",
        type="password"
    )

    if st.button("Entrar"):
        if codigo_digitado == CODIGO_ACESSO:
            # Salva o token com a data de hoje na URL
            st.query_params["auth"] = token_hoje
            st.rerun()
        else:
            st.error("Código incorreto")

    st.stop()

# Botão opcional na barra lateral para limpar o acesso
if st.sidebar.button("Sair (Limpar Sessão)"):
    st.query_params.clear()
    st.rerun()

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

import pandas as pd
from datetime import datetime, timedelta
from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday


# ==========================================
# CONFIGURAÇÃO E CARREGAMENTO (COM AUTO-REFRESH)
# ==========================================

ARQUIVO_DADOS = "dados_performance.xlsx"


@st.cache_data(ttl=60)
def carregar_dados():
    try:
        df_g = pd.read_excel(ARQUIVO_DADOS, sheet_name="Geral")
        df_v = pd.read_excel(ARQUIVO_DADOS, sheet_name="Vendedores")

        df_g["Data"] = pd.to_datetime(df_g["Data"]).dt.date
        df_v["Data"] = pd.to_datetime(df_v["Data"]).dt.date

        return df_g, df_v

    except Exception as e:
        st.error(f"Erro ao carregar '{ARQUIVO_DADOS}': {e}")
        return None, None


df_geral_hist, df_vendedores_hist = carregar_dados()


# ==========================================
# FUNÇÕES DE FORMATAÇÃO
# ==========================================

def fmt_m(v):
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_br(val):
    try:
        if pd.isna(val) or val == float("inf"):
            return "R$ 0,00"
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def fmt_tm(val):
    try:
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


# ==========================================
# CONFIGURAÇÃO DE FERIADOS
# ==========================================

class FeriadosBrasil(AbstractHolidayCalendar):
    rules = [
        Holiday("Confraternização Universal", month=1, day=1),
        Holiday("Tiradentes", month=4, day=21),
        Holiday("Dia do Trabalho", month=5, day=1),
        Holiday("Independência", month=9, day=7),
        Holiday("Nossa Sra Aparecida", month=10, day=12),
        Holiday("Finados", month=11, day=2),
        Holiday("Proclamação da República", month=11, day=15),
        Holiday("Natal", month=12, day=25),
    ]


# ==========================================
# FILTRO DE DATA
# ==========================================

with st.sidebar:
    st.header("⚙️ Filtro")

    if st.button("📅 Hoje"):
        st.session_state["data_input_key"] = datetime.now().date()

    data_selecionada = st.date_input(
        "Preencha a data de hoje (resultado D -1):",
        value=st.session_state.get("data_input_key", datetime.now().date()),
        format="DD/MM/YYYY",
        key="data_input_key",
    )


# ==========================================
# LÓGICA DE DATAS (D-1 ÚTIL)
# ==========================================

inicio_mes = datetime(data_selecionada.year, data_selecionada.month, 1).date()
fim_mes_civil = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

cal = FeriadosBrasil()
feriados_pandas = cal.holidays(
    start=f"{data_selecionada.year}-01-01",
    end=f"{data_selecionada.year}-12-31",
)
lista_feriados = [d.date() for d in feriados_pandas]

dias_uteis_reais = pd.date_range(inicio_mes, fim_mes_civil, freq="B")
dias_uteis_reais = [d.date() for d in dias_uteis_reais if d.date() not in lista_feriados]

data_limite_faturamento = dias_uteis_reais[-4] if len(dias_uteis_reais) >= 4 else dias_uteis_reais[-1]

dias_uteis_totais_list = [d for d in dias_uteis_reais if d <= data_limite_faturamento]
dias_uteis_comerciais_totais = len(dias_uteis_totais_list)

dias_uteis_anteriores = [d for d in dias_uteis_totais_list if d < data_selecionada]
dias_uteis_passados = len(dias_uteis_anteriores)

data_ref_calculo = dias_uteis_anteriores[-1] if dias_uteis_passados > 0 else inicio_mes

dias_uteis_restantes = len([d for d in dias_uteis_totais_list if d >= data_selecionada])

percentual_esperado = (
    (dias_uteis_passados / dias_uteis_comerciais_totais) * 100
    if dias_uteis_comerciais_totais > 0
    else 100
)


# ==========================================
# BLOCO 1: PERFORMANCE GERAL
# ==========================================

meta_mes = 0.0
faturado_mes = 0.0
digitado_mes = 0.0
valor_devolucoes = 0.0

if df_geral_hist is not None and not df_geral_hist.empty:
    linha = df_geral_hist[df_geral_hist["Data"] == data_selecionada]

    if not linha.empty:
        meta_mes = float(linha.iloc[0]["Meta_Mes"])
        faturado_mes = float(linha.iloc[0]["Faturado_Acumulado"])
        digitado_mes = float(linha.iloc[0]["Digitado_Acumulado"])

        if "Devolucoes" in linha.columns:
            valor_devolucoes = pd.to_numeric(
                linha.iloc[0]["Devolucoes"],
                errors="coerce"
            )
            valor_devolucoes = 0.0 if pd.isna(valor_devolucoes) else abs(float(valor_devolucoes))

total_geral = (faturado_mes + digitado_mes) - valor_devolucoes

percentual_atual = (total_geral / meta_mes) * 100 if meta_mes > 0 else 0
gap_vs_linear = percentual_atual - percentual_esperado
falta_r_cifra = meta_mes - total_geral
ritmo_final = max(falta_r_cifra / dias_uteis_restantes, 0) if dias_uteis_restantes > 0 else 0

st.subheader(f"📊 Resultado - Inside Sales (Ref: {data_ref_calculo.strftime('%d/%m')})")

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

arquivo_dados = Path("dados_performance.xlsx")

ultima_atualizacao = datetime.fromtimestamp(
    arquivo_dados.stat().st_mtime,
    ZoneInfo("America/Sao_Paulo")
)

st.markdown(
    f"🕒 *Última atualização: {ultima_atualizacao.strftime('%d/%m/%Y às %H:%M')}*"
)

st.markdown(
    """
    <style>
    [data-testid="stMetricDelta"] svg { display: none !important; }
    [data-testid="column"]:nth-of-type(7) [data-testid="stMetricDelta"] > div {
        background-color: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# CÁLCULO DO FORECAST
# ==========================================

dias_decorridos = dias_uteis_comerciais_totais - dias_uteis_restantes

if dias_decorridos > 0 and total_geral > 0:
    ritmo_atual_realizado = total_geral / dias_decorridos
    forecast_valor = ritmo_atual_realizado * dias_uteis_comerciais_totais
else:
    forecast_valor = 0

forecast_txt = fmt_br(forecast_valor)

if gap_vs_linear < -2 and falta_r_cifra > 0:
    st.error(
        f"⚠️ **Ritmo Atrasado:** Estamos {abs(gap_vs_linear):.1f}% abaixo do ideal "
        f"para o fechamento de {data_ref_calculo.strftime('%d/%m')}."
    )
elif falta_r_cifra <= 0 and meta_mes > 0:
    st.balloons()
    st.success("🏆 **META BATIDA!**")


col1, col2, col3, col_total, col4, col5, col6 = st.columns(7)

with col1:
    st.metric("🎯 Meta", fmt_m(meta_mes))

with col2:
    st.metric("✅ Faturado", fmt_m(faturado_mes))

with col3:
    st.metric("📝 Digitado", fmt_m(digitado_mes))

with col_total:
    st.metric("💰 Total Geral", fmt_m(total_geral))

with col4:
    st.metric("🚩 Falta (Gap)" if falta_r_cifra > 0 else "🏆 Superavit", fmt_m(abs(falta_r_cifra)))

with col5:
    st.metric("🔥 Atingimento", f"{percentual_atual:.1f}%", delta=f"{gap_vs_linear:.1f}% vs Ideal")

with col6:
    st.metric(
        "📅 Ritmo Diário Necessário",
        f"{fmt_m(ritmo_final)} /dia",
        delta=f"{dias_uteis_restantes} d.ú. rest.",
    )

components.html(
    """
    <script>
    const f = () => {
        const d = window.parent.document.querySelectorAll('[data-testid="stMetricDelta"]');
        if (d.length > 0) {
            const e = d[d.length - 1].querySelector('div');
            if (e) {
                e.style.color = '#29b5e8';
                e.style.setProperty('color', '#29b5e8', 'important');
            }
        }
    };
    f();
    setTimeout(f, 1000);
    </script>
    """,
    height=0,
)

valor_esperado_reais = (percentual_esperado / 100) * meta_mes
valor_formatado_br = fmt_br(valor_esperado_reais)
dev_txt = f"-{fmt_br(valor_devolucoes)}"


# ==========================================
# INDICADORES DE PEDIDOS E TM
# ==========================================

total_ped_fat = 0
total_ped_dig = 0
tm_time_geral = 0.0
dados_v_dia = pd.DataFrame()

if df_vendedores_hist is not None and not df_vendedores_hist.empty:
    dados_v_dia_ciclo = df_vendedores_hist[df_vendedores_hist["Data"] == data_selecionada].copy()

    if not dados_v_dia_ciclo.empty:
        cols_calculo = ["Fat_Ped", "Dig_Ped", "Faturado_Acumulado", "Digitado_Acumulado"]

        for col in cols_calculo:
            if col in dados_v_dia_ciclo.columns:
                dados_v_dia_ciclo[col] = pd.to_numeric(dados_v_dia_ciclo[col], errors="coerce").fillna(0)

        total_ped_fat = int(dados_v_dia_ciclo["Fat_Ped"].sum())
        total_ped_dig = int(dados_v_dia_ciclo["Dig_Ped"].sum())
        total_peds_geral = total_ped_fat + total_ped_dig

        financeiro_total = (
            dados_v_dia_ciclo["Faturado_Acumulado"].sum()
            + dados_v_dia_ciclo["Digitado_Acumulado"].sum()
        )

        tm_time_geral = financeiro_total / total_peds_geral if total_peds_geral > 0 else 0.0


# ==========================================
# ANÁLISE DE CICLO
# ==========================================

st.markdown(
    f"""
> **Análise de ciclo:**
>
> * Valor de devoluções: **{dev_txt}**
> * Referência de dados para meta ideal: **{data_ref_calculo.strftime('%d/%m')}** (último dia útil completo).
> * Prazo final de faturamento: **{data_limite_faturamento.strftime('%d/%m')}**.
> * Dias úteis restantes (contando com a data selecionada): **{dias_uteis_restantes}**.
> * O atingimento ideal para hoje é de **{percentual_esperado:.1f}%** (equivalente a **{valor_formatado_br}**).
> * **Volume do mês:** **{total_ped_fat}** pedidos faturados | **{total_ped_dig}** pedidos digitados | **{total_ped_fat + total_ped_dig}** pedidos no total.
> * **Ticket médio:** **{fmt_tm(tm_time_geral)}**.
> * **Forecast (previsão de fechamento):** :orange[**{forecast_txt}**] (baseado no ritmo atual).
"""
)

st.markdown("---")


# ==========================================
# 📈 PERFORMANCE POR VENDEDOR
# ==========================================

st.subheader(f"👥 Ranking de Performance Individual - {data_selecionada.strftime('%B').capitalize()}")
st.markdown(f"🎯 **Atingimento ideal para hoje:** :blue[{percentual_esperado:.1f}%]")

if df_vendedores_hist is not None:
    # Filtra os dados do dia
    dados_v_dia = df_vendedores_hist[df_vendedores_hist['Data'] == data_selecionada].copy()

    # --- NOVO AVISO DE ATUALIZAÇÃO ---
    # Verifica se a soma do faturamento de todos os vendedores é zero
    faturamento_total_dia = dados_v_dia["Faturado_Acumulado"].sum() if not dados_v_dia.empty else 0

    if faturamento_total_dia == 0:
        st.warning("⚠️ **Aviso:** O dashboard está sendo alimentado com os resultados de ontem. Em breve os números estarão na tela. Se demorar mais que o normal, é só avisar o João Tadra.")

    if not dados_v_dia.empty:
        # --- BLINDAGEM: Garante que colunas críticas sejam números e não tenham vazios (NaN) ---
        cols_numericas = ["Faturado_Acumulado", "Digitado_Acumulado", "Meta", "Fat_Ped", "Dig_Ped"]

        for col in cols_numericas:
            if col in dados_v_dia.columns:
                dados_v_dia[col] = pd.to_numeric(dados_v_dia[col], errors='coerce').fillna(0)

        for idx, v in dados_v_dia.iterrows():
            total = v["Faturado_Acumulado"] + v["Digitado_Acumulado"]
            dados_v_dia.at[idx, "total"] = total

            # Atingimento (evita divisão por zero)
            dados_v_dia.at[idx, "ating"] = (total / v["Meta"]) * 100 if v["Meta"] > 0 else 0.0

            # Valor Ideal e Diferença
            val_id = (percentual_esperado / 100) * v["Meta"]
            dados_v_dia.at[idx, "val_id"] = val_id
            dados_v_dia.at[idx, "diff"] = total - val_id

            # Ticket Médio
            peds = v["Fat_Ped"] + v["Dig_Ped"]
            dados_v_dia.at[idx, "tm"] = total / peds if peds > 0 else 0

            # Ritmo Diário Necessário
            falta_v = max(0, v["Meta"] - total)

            # Se não houver dias restantes, o ritmo é o que falta
            dados_v_dia.at[idx, "ritmo"] = falta_v / dias_uteis_restantes if dias_uteis_restantes > 0 else falta_v

            # Projeção (Forecast) Individual
            dias_passados = dias_uteis_comerciais_totais - dias_uteis_restantes
            dados_v_dia.at[idx, "forecast_ind"] = (total / dias_passados) * dias_uteis_comerciais_totais if dias_passados > 0 else 0

        # Ordenar e formatar para o HTML
        v_lista = dados_v_dia.sort_values(by="ating", ascending=False).to_dict('records')

        # Função fmt_br melhorada para não quebrar com erro
        def fmt_br(val):
            try:
                if pd.isna(val) or val == float('inf'): return "R$ 0,00"
                return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                return "R$ 0,00"

        # --- MONTAGEM DA TABELA HTML ---
        style = """<style>.tab-performance { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; } .tab-performance th { background-color: #f0f2f6; padding: 12px; text-align: center; color: #31333F; border-bottom: 2px solid #ccc; } .tab-performance td { padding: 12px; text-align: center; border-bottom: 1px solid #eee; } .prog-bg { background-color: #ddd; border-radius: 10px; width: 60px; height: 8px; display: inline-block; margin-right: 5px; } .prog-bar { background-color: #29b5e8; height: 8px; border-radius: 10px; } .val-sub { font-size: 11px; color: #757575; display: block; margin-top: 2px; } .col-vendedor { width: 250px !important; text-align: left !important; white-space: nowrap !important; }</style>"""
        html_v = style + """<table class='tab-performance'><thead><tr><th>Pos.</th><th class='col-vendedor'>Vendedor</th><th>Meta</th><th>Faturado</th><th>Digitado</th><th>Total (TM)</th><th>Atingimento</th><th>Ideal Hoje (R$)</th><th>Ritmo Diário Nec.</th></tr></thead><tbody>"""

        for i, v in enumerate(v_lista):
            cor_a = "#2E7D32" if v["ating"] >= percentual_esperado else "#C62828"
            cor_d = "#2E7D32" if v["diff"] >= 0 else "#C62828"
            cor_f = "#2E7D32" if v.get("forecast_ind", 0) >= v["Meta"] else "#C62828"

            fat_ped = int(v.get('Fat_Ped', 0))
            dig_ped = int(v.get('Dig_Ped', 0))

            # Linha corrigida com Forecast em negrito (bold)
            linha = f"<tr><td>{i+1}º</td><td class='col-vendedor'><b>{v['Vendedor']}</b></td><td>{fmt_br(v['Meta'])}</td><td style='color: #2E7D32;'>{fmt_br(v['Faturado_Acumulado'])}<span class='val-sub'>{fat_ped} ped.</span></td><td style='color: #1565C0;'>{fmt_br(v['Digitado_Acumulado'])}<span class='val-sub'>{dig_ped} ped.</span></td><td><b>{fmt_br(v['total'])}</b><span class='val-sub'>TM: {fmt_br(v['tm'])}</span></td><td><div class='prog-bg'><div class='prog-bar' style='width: {min(v['ating'], 100)}%'></div></div> <span style='color: {cor_a}; font-weight: bold;'>{v['ating']:.1f}%</span><span class='val-sub' style='color: {cor_f}; font-weight: bold;'>Forecast: {fmt_br(v.get('forecast_ind', 0))}</span></td><td><b>{fmt_br(v['val_id'])}</b><span class='val-sub' style='color: {cor_d}; font-weight: bold;'>{ 'Acima' if v['diff'] >= 0 else 'Gap'}: {fmt_br(abs(v['diff']))}</span></td><td><span style='color: #E64A19; font-weight: bold;'>{fmt_br(v['ritmo'])}</span><span class='val-sub'>p/ dia</span></td></tr>"
            html_v += linha

        html_v += "</tbody></table>"
        st.markdown(html_v, unsafe_allow_html=True)

        if len(v_lista) > 0 and v_lista[0]["ating"] > 0:
            st.success(f"🚀 **Destaque do Mês:** Atualmente **{v_lista[0]['Vendedor']}** lidera o ranking com **{v_lista[0]['ating']:.1f}%** da meta! 🔥")

    else:
        # MENSAGEM CASO A PLANILHA NÃO ESTEJA ATUALIZADA
        st.info("ℹ️ Os dados de performance para a data selecionada ainda não foram carregados na planilha.")

# ==========================================
# CRONOGRAMA PRO
# ==========================================

st.markdown("---")
st.markdown("## 🗓️ Planejamento Estratégico de Fechamento")

try:
    gap_total = falta_r_cifra
    dias_restantes = dias_uteis_restantes
    qtd_vendedores = 5

    total_peds_mes = (
        dados_v_dia["Fat_Ped"].sum() + dados_v_dia["Dig_Ped"].sum()
        if not dados_v_dia.empty
        else 0
    )

    tm_time = total_geral / total_peds_mes if total_peds_mes > 0 else 2217.21

    c1, c2, c3 = st.columns(3)

    c1.metric("🚩 Gap p/ Meta", fmt_br(gap_total))

    ultimo_dia_str = pd.to_datetime(dias_uteis_totais_list[-1]).strftime("%d/%m") if dias_uteis_totais_list else ""
    c2.metric("⏳ Janela de Faturamento", f"{dias_restantes} d.ú.", delta=f"Até {ultimo_dia_str}")

    esforco_diario = gap_total / dias_restantes if dias_restantes > 0 else 0
    peds_dia_time = esforco_diario / tm_time if tm_time > 0 else 0
    c3.metric("🔥 Esforço Diário (Time)", fmt_br(esforco_diario), delta=f"{int(peds_dia_time)} pedidos/dia")

    datas_janela = [d for d in dias_uteis_totais_list if d >= data_selecionada]
    df_semanas = pd.DataFrame({"Data": pd.to_datetime(datas_janela)})

    if not df_semanas.empty:
        df_semanas["Semana"] = df_semanas["Data"].dt.isocalendar().week

    vendedores_ativos = []

    if not dados_v_dia.empty:
        vendedores_ativos = dados_v_dia[dados_v_dia["Meta"] > 0].to_dict("records")

    total_metas_mes = sum(v["Meta"] for v in vendedores_ativos) if vendedores_ativos else 0
    ultima_semana_do_plano = df_semanas["Semana"].max() if not df_semanas.empty else 0

    for semana, dados_sem in df_semanas.groupby("Semana"):
        ini_dt = dados_sem["Data"].min()
        fim_dt = dados_sem["Data"].max()

        ini = ini_dt.strftime("%d/%m")
        fim = fim_dt.strftime("%d/%m")
        d_uteis = len(dados_sem)

        meta_semana = (gap_total / dias_restantes) * d_uteis if dias_restantes > 0 else 0
        peds_semana = int(meta_semana / tm_time) if tm_time > 0 else 0
        media_p_vendedor = round(peds_semana / qtd_vendedores, 1) if qtd_vendedores > 0 else 0

        if semana == ultima_semana_do_plano:
            acao_titulo = "FECHAMENTO DO MÊS"
            acao_desc = "Garantir pedidos."
            cor_bloco = "orange"
        elif 15 in dados_sem["Data"].dt.day.values:
            acao_titulo = "NATURAL TECH"
            acao_desc = "Trabalhar a base da Natural Tech."
            cor_bloco = "green"
        else:
            acao_titulo = "ERA UMA VEZ"
            acao_desc = "Oferecer nova linha para todos os clientes."
            cor_bloco = "red"

        st.subheader(f"🗓️ Período: {ini} a {fim} ({d_uteis} dias úteis)")

        col_esf, col_prev, col_peds = st.columns([1.5, 1, 1.5])

        with col_esf:
            st.markdown(f"**Ação Estratégica:**\n:{cor_bloco}[**{acao_titulo}**] — *{acao_desc}*")

        with col_prev:
            st.markdown(f"**Valor Previsto:**\n:red[**{fmt_br(meta_semana)}**]")

        with col_peds:
            st.markdown(
                f"**Meta de Pedidos:**\n"
                f"🏆 **{peds_semana}** pedidos total | 🎯 Ind: **{media_p_vendedor} pedidos**"
            )

        if vendedores_ativos:
            with st.expander("📋 Ver Planejamento por Vendedor", expanded=False):
                st.markdown(
                    """
                    <div style="font-family: 'Segoe UI', sans-serif; display: flex; width: 100%; font-weight: bold; font-size: 11px; color: #64748b; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 6px; text-transform: uppercase;">
                        <div style="flex: 2; text-align: left;">Vendedor</div>
                        <div style="flex: 1; text-align: center;">Meta Período</div>
                        <div style="flex: 1; text-align: right;">Qtd Pedidos Esperada</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                for v in vendedores_ativos:
                    peso = (v["Meta"] / total_metas_mes) if total_metas_mes > 0 else (1 / len(vendedores_ativos))
                    meta_ind_semana = meta_semana * peso

                    peds_ind_semana = (
                        max(0, round(meta_ind_semana / v["tm"], 1))
                        if v["tm"] > 0
                        else max(0, round(meta_ind_semana / tm_time, 1))
                    )

                    st.markdown(
                        f"""
                        <div style="font-family: 'Segoe UI', sans-serif; display: flex; width: 100%; font-size: 12px; padding: 4px 0; border-bottom: 1px solid #f1f5f9; align-items: center;">
                            <div style="flex: 2; text-align: left; font-weight: 600; color: #1e293b;">👤 {v['Vendedor']}</div>
                            <div style="flex: 1; text-align: center; font-weight: bold; color: #d32f2f;">{fmt_br(meta_ind_semana)}</div>
                            <div style="flex: 1; text-align: right; font-weight: bold; color: #002D62;">{peds_ind_semana} pedidos</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.markdown("---")

    if dias_restantes > 0 and qtd_vendedores > 0:
        with st.container():
            st.info(
                f"💡 **Insight:** Para atingir o objetivo, cada vendedor precisa faturar em média "
                f"**{fmt_br(gap_total / qtd_vendedores)}** nos próximos {dias_restantes} dias."
            )

except Exception:
    st.warning("Configure os dados de faturamento para visualizar o cronograma.")
        
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
COL_CODIGO = "CÓDIGO"

# Meses para o Sistema de Farol
COL_MES_ATUAL = "FEV/26" 
COL_MES_ANT   = "JAN/26"

# =========================
# CARREGAR BASE CLIENTES
# =========================

@st.cache_data(ttl=60) # O cache "morre" a cada 60 segundos
def carregar_dados():
    df = pd.read_excel(ARQUIVO_BASE, sheet_name="BASE COMPLETA")
    df.columns = df.columns.str.strip() 
    return df

df = carregar_dados()

# =========================
# CARREGAR BASE PRODUTOS (MIX)
# =========================

@st.cache_data(ttl=60) # Adicione o tempo de expiração aqui também!
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
        return "🔴 REATIVAÇÃO", "#E74C3C"

# =========================
# TRATAR FATURAMENTO (RESOLVIDO)
# =========================

# 1. Função para limpar R$, pontos de milhar e converter vírgula em ponto
def limpar_valor_comercial(valor):
    if pd.isna(valor) or valor == "": 
        return 0.0
    if isinstance(valor, (int, float)): 
        return float(valor)
    
    # Remove R$, espaços, pontos de milhar e troca a vírgula decimal por ponto
    texto_limpo = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(texto_limpo)
    except:
        return 0.0

# 2. Aplicamos a limpeza pesada na coluna original
df[COL_T_U_9_M] = df[COL_T_U_9_M].apply(limpar_valor_comercial)

# 3. Definimos os limites (bins) garantindo que o zero seja uma categoria separada
# O primeiro bin começa abaixo de zero para capturar o 0 exato
bins = [-float("inf"), 0.01, 5000, 20000, 50000, 100000, float("inf")]

labels = [
    "Sem Faturamento",
    "Até 5 mil",
    "5 mil – 20 mil",
    "20 mil – 50 mil",
    "50 mil – 100 mil",
    "Acima de 100 mil"
]

# 4. Criamos a coluna de faixas oficial
df["FAIXA_FATURAMENTO"] = pd.cut(df[COL_T_U_9_M], bins=bins, labels=labels, include_lowest=True)

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
# FUNÇÃO GERAR PDF (CORRIGIDA - FATURAMENTO REAL)
# =========================

def gerar_pdf_cliente(cliente, vendas_cliente):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    
    # --- FUNÇÃO INTERNA DE LIMPEZA DE LINHA ---
    def normalizar_nome_linha(linha_bruta):
        l = str(linha_bruta).upper().strip()
        if "CARNE" in l or "SALGADA" in l: return "PAPINHAS SALGADAS"
        if "FRUTA" in l or "ORG" in l: return "PAPINHAS DE FRUTAS"
        if "CERAL" in l or "AVEIA" in l: return "CEREAIS" 
        if "DENTI" in l: return "DENTIÇÃO"
        if "YOGU" in l or "IOGURTE" in l: return "YOGUZINHO"
        return l 

    # Aplicar a normalização no DataFrame de vendas
    if not vendas_cliente.empty:
        vendas_cliente = vendas_cliente.copy()
        vendas_cliente["LINHA"] = vendas_cliente["LINHA"].apply(normalizar_nome_linha)

    # --- CÁLCULO DO FATURAMENTO REAL (Obrigatório estar aqui em cima) ---
    faturamento_real = 0
    if not vendas_cliente.empty:
        faturamento_real = vendas_cliente["VALOR"].sum()

    style_tabela = styles["BodyText"]
    style_tabela.leading = 14
    elementos = []

    titulo = Paragraph("Relatório de Cliente - PAPAPÁ", styles["Title"])
    data_geracao = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"])

    elementos.append(titulo)
    elementos.append(data_geracao)
    elementos.append(Spacer(1,20))

    # Tabela de dados cadastrais (AGORA COM faturamento_real DEFINIDO)
    dados_cliente = [
        ["Razão Social", str(cliente[COL_RAZAO])],
        ["CNPJ", str(cliente[COL_CNPJ])],
        ["Telefone", str(cliente[COL_TELEFONE])],
        ["Email", str(cliente[COL_EMAIL])],
        ["Cidade", f"{cliente[COL_CIDADE]} - {cliente[COL_UF]}"],
        ["Vendedor", str(cliente[COL_VENDEDOR])],
        ["Segmento", str(cliente[COL_SEGMENTO])],
        ["Faturamento Total", f"R$ {faturamento_real:,.2f}"],
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
        # Agrupamento para cálculos gerais
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
            if total_pedidos > 0: ticket_medio = total_valor / total_pedidos

        if "DATA PEDIDO" in vendas_cliente.columns:
            data_max = vendas_cliente["DATA PEDIDO"].max()
            if pd.notna(data_max):
                ultima_compra = pd.to_datetime(data_max).strftime("%d/%m/%Y")

        # TABELA 1: RESUMO COMERCIAL
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
        elementos.append(Spacer(1,20))

        # TABELA 2: RESUMO POR PEDIDO
        elementos.append(Paragraph("Resumo por Pedido (NF)", styles["Heading3"]))
        resumo_nfs = (
            vendas_cliente
            .groupby([vendas_cliente["DATA PEDIDO"].dt.strftime('%d/%m/%Y'), "NUMERO NF"])["VALOR"]
            .sum()
            .reset_index()
        )
        resumo_nfs.columns = ["DATA_PED", "NF_PED", "VALOR_PED"]
        resumo_nfs = resumo_nfs.sort_values("NF_PED", ascending=False)
        
        dados_nfs = [["DATA", "NÚMERO DA NF", "VALOR DO PEDIDO"]]
        for _, row in resumo_nfs.iterrows():
            dados_nfs.append([str(row["DATA_PED"]), str(row["NF_PED"]), f"R$ {row['VALOR_PED']:,.2f}"])

        tabela_nfs = Table(dados_nfs, colWidths=[5.3*cm, 5.3*cm, 5.4*cm])
        tabela_nfs.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elementos.append(tabela_nfs)
        elementos.append(Spacer(1, 25))

        # TOP PRODUTOS
        elementos.append(Paragraph("Top Produtos Comprados", styles["Heading3"]))
        top_produtos = resumo.head(5)
        dados_top = [["Produto", "Linha", "Qtd", "Valor"]]
        for _, row in top_produtos.iterrows():
            dados_top.append([
                Paragraph(str(row["DESC PRODUTO"]), style_tabela),
                Paragraph(str(row["LINHA"]), style_tabela),
                int(row["QTDE"]),
                f"R$ {row['VALOR']:,.2f}"
            ])

        tabela_top = Table(dados_top, colWidths=[8*cm, 3.5*cm, 2*cm, 2.5*cm], repeatRows=1)
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

        # HISTÓRICO DETALHADO
        elementos.append(Paragraph("Histórico Detalhado de Compras", styles["Heading3"]))
        dados_produtos = [["Data", "NF", "Produto", "Linha", "Qtd", "Valor"]]
        for _, row in vendas_cliente.iterrows():
            data_item = pd.to_datetime(row["DATA PEDIDO"]).strftime("%d/%m/%Y") if pd.notna(row["DATA PEDIDO"]) else ""
            dados_produtos.append([
                data_item,
                str(row["NUMERO NF"]) if pd.notna(row["NUMERO NF"]) else "",
                Paragraph(str(row["DESC PRODUTO"]), style_tabela),
                Paragraph(str(row["LINHA"]), style_tabela),
                int(row["QTDE"]) if pd.notna(row["QTDE"]) else 0,
                f"R$ {row['VALOR']:,.2f}"
            ])

        tabela_produtos = Table(dados_produtos, colWidths=[2.5*cm, 2.5*cm, 7*cm, 3.5*cm, 1.5*cm, 2.5*cm], repeatRows=1)
        tabela_produtos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ALIGN", (4, 1), (4, -1), "CENTER"),
            ("ALIGN", (5, 1), (5, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elementos.append(tabela_produtos)
    else:
        elementos.append(Paragraph("Nenhum histórico de compra encontrado.", styles["Normal"]))

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    doc.build(elementos)
    buffer.seek(0)
    return buffer
    
# ==========================================
# SIDEBAR - VERSÃO FINAL (FIX RANKING + SEM DUPLICATAS)
# ==========================================

# --- TRATAMENTO DE DADOS ---
COL_DATA_ULTIMA_COMPRA = "ÚLTIMA COMPRA"
COL_GRUPO = "GRUPO ECONÔMICO"
COL_CODIGO = "CÓDIGO"

if COL_TELEFONE in df.columns:
    df["TEL_LIMPO"] = df[COL_TELEFONE].astype(str).str.replace(r'\D', '', regex=True)
else:
    df["TEL_LIMPO"] = ""

if COL_DATA_ULTIMA_COMPRA in df.columns:
    # Converte para datetime garantindo o formato de data
    df[COL_DATA_ULTIMA_COMPRA] = pd.to_datetime(df[COL_DATA_ULTIMA_COMPRA], errors='coerce')
    
    # Criar mês de referência (Ex: 05/2024)
    df["MES_REF"] = df[COL_DATA_ULTIMA_COMPRA].dt.strftime('%m/%Y')
    
    # --- NOVA LÓGICA DE SEMANA ---
    def categorizar_semana(data):
        if pd.isna(data): return "Sem Registro"
        dia = data.day
        if dia <= 7: return "Semana 1 (01-07)"
        elif dia <= 14: return "Semana 2 (08-14)"
        elif dia <= 21: return "Semana 3 (15-21)"
        else: return "Semana 4 (22+)"
    
    df["SEMANA_REF"] = df[COL_DATA_ULTIMA_COMPRA].apply(categorizar_semana)
else:
    df["MES_REF"] = "Sem Data"
    df["SEMANA_REF"] = "Sem Registro"

st.sidebar.title("Filtros")

# BOTÃO LIMPAR - Reseta as chaves novas e as antigas (para garantir o ranking)
if st.sidebar.button("Limpar todos os filtros"):
    # Adicionado "f_grupo" na lista de chaves para resetar
    chaves = ["b_cnpj", "b_razao", "b_email", "b_tel", "f_mes", "f_vend", "f_uf", "f_cid", "f_bair", "f_seg", "f_fat", "filtro_mes", "f_regiao", "f_semana", "f_grupo"]
    for c in chaves:
        if c in st.session_state:
            st.session_state[c] = [] if isinstance(st.session_state[c], list) else ""
    st.rerun()

df_filtrado = df.copy()

# ==========================================
# 1. BUSCAS POR TEXTO (TOPO)
# ==========================================

# PLACEHOLDERS DINÂMICOS (Garante a ordem visual correta na Sidebar)
placeholder_codigo = st.sidebar.empty()
placeholder_razao = st.sidebar.empty()

# --- NOVO FILTRO: CÓDIGO DO CLIENTE (LISTA SUSPENSA DINÂMICA) ---
if COL_CODIGO in df_filtrado.columns:
    # Cria a lista de códigos únicos baseada nos dados filtrados atuais, ordenando-os
    # Convertemos para string para garantir a exibição limpa no componente
    lista_codigos = sorted(df_filtrado[COL_CODIGO].dropna().astype(str).unique().tolist())
    
    codigo_sel = placeholder_codigo.multiselect(
        "Filtrar Código do Cliente",
        options=lista_codigos,
        key="b_codigo"
    )
    
    # Se houver códigos selecionados, filtra a base usando .isin()
    if codigo_sel:
        df_filtrado = df_filtrado[df_filtrado[COL_CODIGO].astype(str).isin(codigo_sel)]
        
b_cnpj = st.sidebar.text_input("Buscar por CNPJ", key="b_cnpj")
if b_cnpj:
    cnpj_l = "".join(filter(str.isdigit, b_cnpj)) 
    if "CNPJ_LIMPO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["CNPJ_LIMPO"].str.contains(cnpj_l, na=False)]

# RAZÃO SOCIAL DINÂMICA (PLACEHOLDER)
placeholder_razao = st.sidebar.empty()

b_email = st.sidebar.text_input("Buscar por E-mail", key="b_email")
if b_email:
    df_filtrado = df_filtrado[df_filtrado[COL_EMAIL].str.contains(b_email, case=False, na=False)]

b_tel = st.sidebar.text_input("Buscar por Telefone", key="b_tel")
if b_tel:
    t_l = "".join(filter(str.isdigit, b_tel))
    if "TEL_LIMPO" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["TEL_LIMPO"].str.contains(t_l, na=False)]

# ==========================================
# 2. FILTROS DE SEGMENTAÇÃO (COMPLETO + FATURAMENTO REAL)
# ==========================================

# --- PASSO 0: LIMPEZA E CÁLCULO DE FATURAMENTO REAL ---

def limpar_cnpj(cnpj):
    return "".join(filter(str.isdigit, str(cnpj)))

# Garantimos que a base de vendas e a de filtros usem CNPJs apenas numéricos para o cruzamento
df_vendas_limpo = df_vendas.copy()
df_vendas_limpo[COL_CNPJ] = df_vendas_limpo[COL_CNPJ].apply(limpar_cnpj)
df_filtrado[COL_CNPJ + "_LIMPO"] = df_filtrado[COL_CNPJ].apply(limpar_cnpj)

# Soma das vendas reais
faturamento_total_base = df_vendas_limpo.groupby(COL_CNPJ)["VALOR"].sum()
df_filtrado["FAT_REAL"] = df_filtrado[COL_CNPJ + "_LIMPO"].map(faturamento_total_base).fillna(0)

def definir_faixa_real(v):
    if v <= 0: return "Sem Faturamento"
    elif v <= 5000: return "Até R$ 5k"
    elif v <= 20000: return "R$ 5k - 20k"
    elif v <= 50000: return "R$ 20k - 50k"
    else: return "Acima de R$ 50k"

df_filtrado["FAIXA_REAL"] = df_filtrado["FAT_REAL"].apply(definir_faixa_real)

# --- AGORA OS FILTROS DA SIDEBAR (ORDEM COMPLETA) ---

# 1. Filtro de Mês
m_lista = sorted(df_filtrado["MES_REF"].dropna().unique().tolist(), key=lambda x: pd.to_datetime(x, format='%m/%Y'), reverse=True)
mes_sel = st.sidebar.multiselect("Mês da Última Compra", m_lista, key="f_mes")
st.session_state["filtro_mes"] = mes_sel 
if mes_sel:
    df_filtrado = df_filtrado[df_filtrado["MES_REF"].isin(mes_sel)]

# --- NOVO FILTRO: SEMANA DA ÚLTIMA COMPRA ---
# Definimos a ordem lógica para as semanas aparecerem corretamente no menu
ordem_semanas = ["Semana 1 (01-07)", "Semana 2 (08-14)", "Semana 3 (15-21)", "Semana 4 (22+)", "Sem Registro"]

# Filtramos a lista para exibir apenas as semanas que existem nos dados filtrados no momento
s_lista = [s for s in ordem_semanas if s in df_filtrado["SEMANA_REF"].unique()]

semana_sel = st.sidebar.multiselect("Semana da Última Compra", s_lista, key="f_semana")

if semana_sel:
    df_filtrado = df_filtrado[df_filtrado["SEMANA_REF"].isin(semana_sel)]

# 2. Filtro de Vendedor
v_lista = sorted(df_filtrado[COL_VENDEDOR].dropna().unique().tolist())
vendedor_sel = st.sidebar.multiselect("Vendedor", v_lista, key="f_vend")
if vendedor_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_VENDEDOR].isin(vendedor_sel)]

# --- NOVO FILTRO: GRUPO ECONÔMICO ---
if COL_GRUPO in df_filtrado.columns:
    g_lista = sorted(df_filtrado[COL_GRUPO].dropna().unique().tolist())
    grupo_sel = st.sidebar.multiselect("Grupo Econômico", g_lista, key="f_grupo")
    if grupo_sel:
        df_filtrado = df_filtrado[df_filtrado[COL_GRUPO].isin(grupo_sel)]

# --- NOVO FILTRO: REGIÃO (Inserido aqui) ---
mapa_regioes = {
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"]
}

regioes_disponiveis = sorted(list(mapa_regioes.keys()))
regiao_sel = st.sidebar.multiselect("Região", regioes_disponiveis, key="f_regiao")

if regiao_sel:
    # Coleta todos os estados das regiões selecionadas
    estados_selecionados = []
    for r in regiao_sel:
        estados_selecionados.extend(mapa_regioes[r])
    # Filtra o DataFrame para conter apenas esses estados
    df_filtrado = df_filtrado[df_filtrado[COL_UF].isin(estados_selecionados)]

# 3. Filtro de Estado (UF)
# u_lista agora refletirá apenas os estados da região escolhida acima
u_lista = sorted(df_filtrado[COL_UF].dropna().unique().tolist())
uf_sel = st.sidebar.multiselect("Estado (UF)", u_lista, key="f_uf")
if uf_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_UF].isin(uf_sel)]

# 4. Filtro de Cidade
c_lista = sorted(df_filtrado[COL_CIDADE].dropna().unique().tolist())
cidade_sel = st.sidebar.multiselect("Cidade", c_lista, key="f_cid")
if cidade_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_CIDADE].isin(cidade_sel)]

# 5. Filtro de Bairro
b_lista = sorted(df_filtrado[COL_BAIRRO].dropna().unique().tolist())
bairro_sel = st.sidebar.multiselect("Bairro", b_lista, key="f_bair")
if bairro_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_BAIRRO].isin(bairro_sel)]

# 6. Filtro de Segmento
if COL_SEGMENTO in df_filtrado.columns:
    s_lista = sorted(df_filtrado[COL_SEGMENTO].dropna().unique().tolist())
    seg_sel = st.sidebar.multiselect("Segmento", s_lista, key="f_seg")
    if seg_sel:
        df_filtrado = df_filtrado[df_filtrado[COL_SEGMENTO].isin(seg_sel)]

# 7. Filtro de Faixa de Faturamento
ordem_f = ["Sem Faturamento", "Até R$ 5k", "R$ 5k - 20k", "R$ 20k - 50k", "Acima de R$ 50k"]
opcoes_f = [f for f in ordem_f if f in df_filtrado["FAIXA_REAL"].unique()]

fat_sel = st.sidebar.multiselect("Faixa de Faturamento (Real)", options=opcoes_f, key="f_fat_v_final")

if fat_sel:
    df_filtrado = df_filtrado[df_filtrado["FAIXA_REAL"].isin(fat_sel)]

# ==========================================
# 3. RAZÃO SOCIAL (CASCATA ATIVA - SELEÇÃO MÚLTIPLA)
# ==========================================

# Criamos a lista de opções (removendo o "" inicial, pois o multiselect já lida com vazio)
lista_clientes = sorted(df_filtrado[COL_RAZAO].dropna().unique().tolist())

# Trocamos o selectbox pelo multiselect
cliente_sel = placeholder_razao.multiselect(
    "Filtrar Razões Sociais", 
    options=lista_clientes, 
    key="b_razao"
)

# Se houver algo selecionado na lista, filtramos usando .isin()
if cliente_sel:
    df_filtrado = df_filtrado[df_filtrado[COL_RAZAO].isin(cliente_sel)]
    
# =========================
# TÍTULO
# =========================

st.title("Dashboard Inside Sales - PAPAPÁ")

# Você pode alterar a data/hora manualmente aqui sempre que atualizar os números
data_atualizacao = "04/05/2026" 
st.markdown(f"🕒 *Última atualização: {data_atualizacao}*")

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

        # TRATAMENTO DA DATA ÚLTIMA COMPRA
        data_bruta = cliente['ÚLTIMA COMPRA']
        if pd.notnull(data_bruta) and hasattr(data_bruta, 'strftime'):
            data_formatada = data_bruta.strftime('%d/%m/%Y')
        else:
            data_formatada = "Sem registro"

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
                <b>Última Compra:</b> {data_formatada}<br>
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
                st.link_button("💬 WhatsApp", f"https://web.whatsapp.com/send?phone=55{tel_wpp}", use_container_width=True)
        
        with col_btn2:
            # Filtra vendas do cliente na aba MIX
            if not df_vendas.empty:
                v_cli = df_vendas[df_vendas["CNPJ_LIMPO"] == id_cliente]
                pdf_arq = gerar_pdf_cliente(cliente, v_cli)
                st.download_button("📄 Baixar Relatório PDF", data=pdf_arq, 
                                 file_name=f"relatorio_{id_cliente}.pdf", 
                                 mime="application/pdf", use_container_width=True)

# ... (Final do seu código de CRM aqui) ...
        
    # --- SAINDO DAS COLUNAS (Largura Total) ---
        
    # 2. GRÁFICO EM PÁGINA INTEIRA (Full Width)
    if not df_vendas.empty:
        id_cliente_str = str(id_cliente).strip()
        vendas_hist = df_vendas[df_vendas["CNPJ_LIMPO"] == id_cliente_str].copy()

        if not vendas_hist.empty:
            st.markdown("---")
            st.subheader("📈 Histórico Mensal de Compras")
            
            vendas_hist['DATA PEDIDO'] = pd.to_datetime(vendas_hist['DATA PEDIDO'], errors='coerce')
            vendas_hist = vendas_hist.dropna(subset=['DATA PEDIDO'])
            vendas_hist['MES_ANO'] = vendas_hist['DATA PEDIDO'].dt.strftime('%Y-%m')
            
            hist_mensal = vendas_hist.groupby('MES_ANO')['VALOR'].sum().reset_index()
            hist_mensal = hist_mensal.sort_values("MES_ANO")

            fig_hist_cli = px.bar(
                hist_mensal,
                x="MES_ANO",
                y="VALOR",
                text_auto='.2s',
                title="Evolução de Pedidos (R$)",
                color_discrete_sequence=["#E74C3C"]
            )
            
            # Força o gráfico a usar toda a largura disponível
            st.plotly_chart(fig_hist_cli, use_container_width=True)

    # --- COLUNA DIREITA: CRM ---
# ==========================================
# BLOCO CRM - SÓ APARECE COM 1 CLIENTE
# ==========================================

if len(df_filtrado) == 1:
    with col_crm:
        st.subheader("📝 Notas e Histórico")
        
        # 1. Seletor de usuário (Iniciando em branco)
        lista_pessoas = ["João Tadra", "Ana", "Pedro", "João Paulo", "Bernardo", "Thiago"]
        
        quem_comentou = st.selectbox(
            "Quem está comentando?", 
            lista_pessoas,
            index=None,
            placeholder="Selecione seu nome...",
            key="nome_usuario_crm"
        )

        # 2. Função que processa o salvamento
        def clicar_salvar():
            global comentarios
            
            # Pega os dados dos campos via session_state
            texto_digitado = st.session_state.get("txt_area_crm", "")
            autor = st.session_state.get("nome_usuario_crm")
            
            if texto_digitado.strip() and autor:
                # Data e Hora (Brasília)
                from datetime import datetime, timedelta
                agora = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M")
                texto_final = f"[{autor}] {texto_digitado.strip()}"
                
                # Garante que a chave do cliente existe (id_cliente deve estar definido antes)
                id_cliente_str = str(id_cliente)
                if id_cliente_str not in comentarios:
                    comentarios[id_cliente_str] = []
                
                # Adiciona o novo comentário no topo da lista
                comentarios[id_cliente_str].insert(0, {"texto": texto_final, "data": agora})
                
                # SALVAMENTO FÍSICO (Certifique-se que essa função existe no seu código)
                salvar_comentarios(comentarios)
                
                # Limpa o campo de texto
                st.session_state["txt_area_crm"] = ""
                st.toast("✅ Nota salva com sucesso!")
            else:
                if not autor:
                    st.warning("⚠️ Por favor, selecione quem está registrando a nota.")
                else:
                    st.warning("⚠️ O campo de texto está vazio.")

        # 3. Interface de entrada
        st.text_area(
            "Novo registro:", 
            placeholder="Descreva a conversa...", 
            key="txt_area_crm",
            height=120
        )
        
        # 4. Botão de Salvar
        st.button("Salvar Comentário", on_click=clicar_salvar, use_container_width=True)
        
        st.divider()

        # 5. Listagem do Histórico
        id_cliente_str = str(id_cliente)
        if id_cliente_str in comentarios and len(comentarios[id_cliente_str]) > 0:
            for idx, item in enumerate(comentarios[id_cliente_str]):
                with st.container():
                    col_txt, col_del = st.columns([0.85, 0.15])
                    
                    with col_txt:
                        st.caption(f"📅 {item['data']}")
                        st.write(item['texto'])
                    
                    with col_del:
                        if st.button("🗑️", key=f"btn_del_{id_cliente_str}_{idx}"):
                            comentarios[id_cliente_str].pop(idx)
                            salvar_comentarios(comentarios)
                            st.rerun()
                    
                    st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        else:
            st.info("Sem histórico para este cliente.")
else:
    # Mensagem amigável quando os filtros estão abertos (mais de 1 cliente)
    st.info("💡 Selecione um cliente específico nos filtros ao lado para visualizar mais detalhes sobre o cliente.")

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
            
            else:
                # Caso não encontre na aba 'base', o card anterior (Parte 6) já mostra o erro simplificado
                pass
    except Exception as e:
        # Silencioso para não poluir o Dashboard se o ID não estiver pronto
        pass

# ==========================================
# FUNÇÕES E CATÁLOGOS - NOVAS LINHAS
# ==========================================

import unicodedata

def limpar_texto(t):
    return "".join(
        c for c in unicodedata.normalize("NFD", str(t))
        if unicodedata.category(c) != "Mn"
    ).upper().strip()


CATALOGO_NOVAS_LINHAS = {
    "ERA UMA VEZ": {
        "Salgadinho Integral Orgânico Queijo 40g": ["SALGADINHO", "QUEIJO", "ERA UMA VEZ"],
        "Salgadinho Integral Orgânico Cebola & Salsa 40g": ["SALGADINHO", "CEBOLA", "SALSA", "ERA UMA VEZ"],
        "Salgadinho Integral Orgânico Churrasco 40g": ["SALGADINHO", "CHURRASCO", "ERA UMA VEZ"],
        "Biscoito Recheado Frutas Amarelas 30g": ["BISCOITO", "RECHEADO", "FRUTAS", "AMARELAS"],
        "Biscoito Recheado Morango 30g": ["BISCOITO", "RECHEADO", "MORANGO"],
        "Bebida de Laranja 200ml": ["BEBIDA", "LARANJA", "ERA UMA VEZ"],
        "Bebida de Uva 200ml": ["BEBIDA", "UVA", "ERA UMA VEZ"],
        "Bebida de Morango 200ml": ["BEBIDA", "MORANGO", "ERA UMA VEZ"],
        "Bebida de Maçã 200ml": ["BEBIDA", "MACA", "ERA UMA VEZ"],
        "Bebida Láctea UHT Chocolate 200ml": ["BEBIDA", "LACTEA", "CHOCOLATE"],
    },
    "PUERICULTURA": {
        "Kit De Talheres Infantil - Azul": ["KIT", "TALHERES", "AZUL"],
        "Kit De Talheres Infantil - Verde": ["KIT", "TALHERES", "VERDE"],
        "Kit De Talheres Infantil - Rosa": ["KIT", "TALHERES", "ROSA"],
        "Babador Infantil Com Bolso - Azul": ["BABADOR", "BOLSO", "AZUL"],
        "Babador Infantil Com Bolso - Verde": ["BABADOR", "BOLSO", "VERDE"],
        "Babador Infantil Com Bolso - Rosa": ["BABADOR", "BOLSO", "ROSA"],
        "Bowl Infantil Com Ventosa - Azul": ["BOWL", "VENTOSA", "AZUL"],
        "Bowl Infantil Com Ventosa - Verde": ["BOWL", "VENTOSA", "VERDE"],
        "Bowl Infantil Com Ventosa - Rosa": ["BOWL", "VENTOSA", "ROSA"],
        "Pratinho Infantil Com Ventosa - Azul": ["PRATINHO", "VENTOSA", "AZUL"],
        "Pratinho Infantil Com Ventosa - Verde": ["PRATINHO", "VENTOSA", "VERDE"],
        "Pratinho Infantil Com Ventosa - Rosa": ["PRATINHO", "VENTOSA", "ROSA"],
    }
}


def classificar_nova_linha(desc_produto, linha_original=""):
    nome = limpar_texto(desc_produto)
    linha = limpar_texto(linha_original)

    if "PUERICULTURA" in linha:
        return "PUERICULTURA"

    termos_puericultura = ["TALHERES", "BABADOR", "BOWL", "PRATINHO", "VENTOSA"]
    if any(t in nome for t in termos_puericultura):
        return "PUERICULTURA"

    termos_era_uma_vez = [
        "ERA UMA VEZ",
        "SALGADINHO INTEGRAL ORGANICO",
        "BISCOITO RECHEADO",
        "BEBIDA LACTEA UHT CHOCOLATE",
    ]
    if any(t in nome for t in termos_era_uma_vez):
        return "ERA UMA VEZ"

    return None


def preparar_novas_linhas(df):
    if df is None or df.empty:
        return pd.DataFrame()

    base = df.copy()

    if "DATA PEDIDO" in base.columns:
        base["DATA PEDIDO"] = pd.to_datetime(base["DATA PEDIDO"], errors="coerce")

    for col in ["VALOR", "QTDE", "QTD"]:
        if col in base.columns:
            base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0)

    if "LINHA" not in base.columns:
        base["LINHA"] = ""

    base["NOVA_LINHA"] = base.apply(
        lambda r: classificar_nova_linha(r.get("DESC PRODUTO", ""), r.get("LINHA", "")),
        axis=1
    )

    return base[base["NOVA_LINHA"].notna()].copy()


def produto_ja_comprado(vendas_nomes, keywords):
    keys = [limpar_texto(k) for k in keywords]
    return any(all(k in nome for k in keys) for nome in vendas_nomes)


def moeda_br(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ==========================================
# ANÁLISE DE COMPRAS (DENTRO DO IF DO CLIENTE ÚNICO)
# ==========================================

if not vendas_cliente.empty:
    st.divider()
    st.subheader("📊 Análise de Performance e Mix")

    vendas_cliente["DATA PEDIDO"] = pd.to_datetime(vendas_cliente["DATA PEDIDO"], errors="coerce")

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
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
        fig_mix.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_mix, use_container_width=True)

    with col_graf2:
        top_produtos = (
            vendas_cliente
            .groupby("DESC PRODUTO")["VALOR"]
            .sum()
            .reset_index()
            .sort_values("VALOR", ascending=True)
            .tail(10)
        )
        fig_top = px.bar(
            top_produtos,
            x="VALOR",
            y="DESC PRODUTO",
            orientation="h",
            title="Top 10 Produtos (Valor Total)",
            labels={"VALOR": "Total Gasto (R$)", "DESC PRODUTO": "Produto"},
            color="VALOR",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_top, use_container_width=True)

    evolucao = (
        vendas_cliente
        .set_index("DATA PEDIDO")
        .resample("MS")["VALOR"]
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

    # ==========================================
    # 🚀 RADAR DE NOVAS LINHAS - CLIENTE
    # ==========================================

    vendas_novas_cliente = preparar_novas_linhas(vendas_cliente)

    st.markdown("#### 🚀 Radar de Novas Linhas no Cliente")

    if not vendas_novas_cliente.empty:
        qtd_col = "QTDE" if "QTDE" in vendas_novas_cliente.columns else "QTD"

        total_novas = vendas_novas_cliente["VALOR"].sum()
        qtd_novas = vendas_novas_cliente[qtd_col].sum() if qtd_col in vendas_novas_cliente.columns else 0
        linhas_compradas = vendas_novas_cliente["NOVA_LINHA"].nunique()
        skus_comprados = vendas_novas_cliente["DESC PRODUTO"].nunique()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Faturamento Novas Linhas", moeda_br(total_novas))
        k2.metric("Volume", f"{int(qtd_novas):,}".replace(",", "."))
        k3.metric("Linhas Compradas", f"{linhas_compradas}/2")
        k4.metric("SKUs Comprados", skus_comprados)

        c_nova_1, c_nova_2 = st.columns(2)

        with c_nova_1:
            evol_novas_cliente = (
                vendas_novas_cliente
                .groupby([pd.Grouper(key="DATA PEDIDO", freq="D"), "NOVA_LINHA"])["VALOR"]
                .sum()
                .reset_index()
            )
            fig_evol_novas_cliente = px.line(
                evol_novas_cliente,
                x="DATA PEDIDO",
                y="VALOR",
                color="NOVA_LINHA",
                markers=True,
                title="Evolução das Novas Linhas no Cliente",
                labels={"VALOR": "Valor (R$)", "DATA PEDIDO": "Data", "NOVA_LINHA": "Nova Linha"},
                color_discrete_map={"ERA UMA VEZ": "#FF7A00", "PUERICULTURA": "#7C3AED"}
            )
            fig_evol_novas_cliente.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_evol_novas_cliente, use_container_width=True)

        with c_nova_2:
            top_novas_cliente = (
                vendas_novas_cliente
                .groupby(["NOVA_LINHA", "DESC PRODUTO"])["VALOR"]
                .sum()
                .reset_index()
                .sort_values("VALOR", ascending=True)
                .tail(10)
            )
            fig_top_novas_cliente = px.bar(
                top_novas_cliente,
                x="VALOR",
                y="DESC PRODUTO",
                color="NOVA_LINHA",
                orientation="h",
                title="Top SKUs das Novas Linhas",
                labels={"VALOR": "Valor (R$)", "DESC PRODUTO": "Produto"},
                color_discrete_map={"ERA UMA VEZ": "#FF7A00", "PUERICULTURA": "#7C3AED"}
            )
            fig_top_novas_cliente.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_top_novas_cliente, use_container_width=True)

    else:
        st.info("Este cliente ainda não comprou Era Uma Vez nem Puericultura.")


# ==========================================
# 🚀 INTELIGÊNCIA DE MERCADO - GAP E CROSS-SELL
# ==========================================

if 1 <= len(df_filtrado) <= 300:
    cnpjs_no_filtro = df_filtrado["CNPJ_LIMPO"].unique()
    vendas_analise = df_vendas[df_vendas["CNPJ_LIMPO"].isin(cnpjs_no_filtro)].copy()

    if not vendas_analise.empty:
        vendas_nomes = [limpar_texto(n) for n in vendas_analise["DESC PRODUTO"].unique()]

        ja_compra_salgada = any(
            ("120G" in n or "SALGADA" in n)
            and not any(x in n for x in ["FRUTA", "DOCE", "MACA", "BANANA", "MANGA", "PERA", "AMEIXA", "MIRTILO"])
            for n in vendas_nomes
        )
        ja_compra_palitinho = any("PALIT" in n for n in vendas_nomes)
        ja_compra_fruta = any(("100G" in n or "FRUTA" in n) and "PAPINHA" in n for n in vendas_nomes)

        catalogo_dna = {
            "LA CHEF": ["LENTILHA", "RISOTINHO", "CASEIRINHO", "CHEF"],
            "SOPINHAS": ["SOPINHA", "240G"],
            "YOGUZINHO": ["IOGURTE", "YOGU"],
            "PAPINHAS SALGADAS": ["120G", "SALGADA"],
            "PAPINHAS DE FRUTAS": ["100G", "FRUTA"],
            "BISCOTTI": ["BISCOTTI"],
            "PALITINHOS": ["PALIT"],
            "DENTIÇÃO": ["DENTICAO", "DENTIÇÃO"],
            "MACARRÃO": ["ELBOW", "FUSILLI", "MACARRAO"],
            "CEREAIS": ["CEREAL", "AVEIA"],
            "ERA UMA VEZ": ["ERA UMA VEZ", "SALGADINHO", "BISCOITO RECHEADO", "BEBIDA"],
            "PUERICULTURA": ["PUERICULTURA", "TALHERES", "BABADOR", "BOWL", "PRATINHO", "VENTOSA"]
        }

        catalogo_papapa = {
            "LA CHEF": {
                "Lentilha Carne Legumes 180g": ["LENTILHA"],
                "Risotinho Arroz Quinoa Frango 180g": ["RISOTINHO"],
                "Caseirinho Arroz Feijão Carne Leg. 180g": ["CASEIRINHO"]
            },
            "SOPINHAS": {
                "Sopinha Frango Arroz Legumes 240g": ["SOPINHA", "FRANGO"],
                "Sopinha Carne Macarrao Legumes 240g": ["SOPINHA", "MACARRAO"],
                "Sopinha Carne Mandioquinha Leg 240g": ["SOPINHA", "MANDIOQ"],
                "Sopinha Feijão Carne Leg 240g": ["SOPINHA", "FEIJAO"]
            },
            "YOGUZINHO": {
                "Iogurte Frutas Amarelas e Banana 100g": ["IOGURTE", "AMARELAS"],
                "Iogurte Frutas Vermelhas e Banana 100g": ["IOGURTE", "VERMELHAS"]
            },
            "PAPINHAS SALGADAS": {
                "Papinha Carne Arroz Legumes 120g": ["CARNE", "120G"],
                "Papinha Frango Grão Vegetais 120g": ["FRANGO", "120G"]
            },
            "PAPINHAS DE FRUTAS": {
                "Papinha Org Maçã Ameixa 100g": ["MACA", "AMEIXA"],
                "Papinha Org Banana Mirtilo Quinoa 100g": ["BANANA", "MIRTILO"],
                "Papinha Org Manga 100g": ["MANGA"],
                "Papinha Org Pera Espinafre Abobrinha 100g": ["PERA", "ESPINA"],
                "Papinha Org Maçã B. Doce Cenoura 100g": ["DOCE", "CENOURA"],
                "Papinha Org Morango Maçã 100g": ["MORANGO", "MACA"]
            },
            "BISCOTTI": {
                "Biscotti Laranja e Cenoura 60g": ["BISCOTTI", "LARANJ"],
                "Biscotti Maçã e Canela 60g": ["BISCOTTI", "MAC", "CANEL"],
                "Biscotti Banana e Cacau 60g": ["BISCOTTI", "CACAU"],
                "Biscotti Goiaba 60g": ["BISCOTTI", "GOIAB"],
                "Biscotti Maracujá e Camomila 60g": ["BISCOTTI", "MARACUJ"]
            },
            "PALITINHOS": {
                "Palitinho Org. Beterraba 20g": ["BETERRABA"],
                "Palitinho Org. Cenoura 20g": ["CENOURA"],
                "Palitinho Org. Tomate/Manjericão 20g": ["TOMATE"]
            },
            "DENTIÇÃO": {
                "Biscoito de Dentição Maçã e Abóbora": ["DENTICAO", "ABOBORA"],
                "Biscoito de Dentição Vegetais": ["DENTICAO", "VEGETAIS"]
            },
            "MACARRÃO": {
                "Macarrão Inf. Elbow Quinoa 200g": ["ELBOW"],
                "Macarrão Inf. Fusilli Vegetais 200g": ["FUSILLI"]
            },
            "CEREAIS": {
                "Cereal Multicereais 170g": ["CEREAL", "MULTI"],
                "Cereal Aveia Morango e Beterraba 170g": ["AVEIA", "MORANGO"],
                "Cereal Aveia Banana e Ameixa 170g": ["AVEIA", "BANANA"]
            },
            "ERA UMA VEZ": CATALOGO_NOVAS_LINHAS["ERA UMA VEZ"],
            "PUERICULTURA": CATALOGO_NOVAS_LINHAS["PUERICULTURA"]
        }

        gap_mix = []
        cross_sell = []

        for linha, skus_dict in catalogo_papapa.items():
            if linha == "PAPINHAS SALGADAS":
                trabalha_a_linha = ja_compra_salgada
            elif linha == "PALITINHOS":
                trabalha_a_linha = ja_compra_palitinho
            elif linha == "PAPINHAS DE FRUTAS":
                trabalha_a_linha = ja_compra_fruta
            else:
                ids_dna = catalogo_dna.get(linha, [])
                trabalha_a_linha = any(any(id_dna in n for id_dna in ids_dna) for n in vendas_nomes)

            for nome_exibicao, keywords in skus_dict.items():
                ja_tem_sku = produto_ja_comprado(vendas_nomes, keywords)

                if not ja_tem_sku:
                    item = {"Linha": linha, "Produto": nome_exibicao}
                    if trabalha_a_linha:
                        gap_mix.append(item)
                    else:
                        cross_sell.append(item)

        st.subheader("📦 Sugestões de Expansão")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### 🚨 Gap de Mix")
            if gap_mix:
                st.dataframe(pd.DataFrame(gap_mix), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Mix completo nas categorias atuais!")

        with c2:
            st.markdown("#### 📦 Cross-sell")
            if cross_sell:
                st.dataframe(pd.DataFrame(cross_sell), use_container_width=True, hide_index=True)
            else:
                st.info("💡 Já compra todas as linhas!")

elif len(df_filtrado) > 300:
    st.info("💡 Filtre um cliente ou uma rede específica para ver as sugestões de Gap e Cross-sell.")


# ==========================================
# 📦 ANÁLISE GERAL DE MIX E PRODUTOS
# ==========================================

st.subheader("📦 Análise Geral de Mix e Produtos")

if not df_vendas.empty:
    cnpjs_visiveis = df_filtrado["CNPJ_LIMPO"].unique()
    vendas_geral = df_vendas[df_vendas["CNPJ_LIMPO"].isin(cnpjs_visiveis)].copy()

    vendas_geral["DATA PEDIDO"] = pd.to_datetime(vendas_geral["DATA PEDIDO"], errors="coerce")
    vendas_geral["MES_ANO"] = vendas_geral["DATA PEDIDO"].dt.strftime("%m/%Y")

    meses_df_mix = (
        vendas_geral[["MES_ANO", "DATA PEDIDO"]]
        .dropna()
        .assign(MES_DATA=lambda x: x["DATA PEDIDO"].dt.to_period("M").dt.to_timestamp())
        .drop_duplicates("MES_ANO")
        .sort_values("MES_DATA", ascending=False)
    )

    meses_disponiveis_mix = ["Todos os meses"] + meses_df_mix["MES_ANO"].tolist()

    mes_selecionado_mix = st.selectbox(
        "Filtrar mês:",
        options=meses_disponiveis_mix,
        key="filtro_mes_mix_geral"
    )

    if mes_selecionado_mix != "Todos os meses":
        vendas_geral = vendas_geral[vendas_geral["MES_ANO"] == mes_selecionado_mix]

    blacklist_geral = ["CONFERIDO", "AJUSTE", "TESTE", "FRETE"]
    regex_geral = "|".join(blacklist_geral)
    vendas_geral = vendas_geral[~vendas_geral["DESC PRODUTO"].str.upper().str.contains(regex_geral, na=False)]

    if not vendas_geral.empty:
        def mapear_catalogo_detalhado(nome, linha_original=""):
            nova_linha = classificar_nova_linha(nome, linha_original)
            if nova_linha:
                return nova_linha

            nome = limpar_texto(nome)

            termos_macarrao = ["ELBOW", "FUSILLI", "MACARRAO", "MASSA", "LETRE"]
            if any(key in nome for key in termos_macarrao):
                return "MACARRÃO"

            catalogo = {
                "LA CHEF": ["LENTILHA", "RISOTINHO", "CASEIRINHO"],
                "SOPINHAS": ["SOPINHA"],
                "YOGUZINHO": ["IOGURTE", "YOGUZINHO", "YOGU"],
                "PAPINHAS SALGADAS": ["CARNE", "ARROZ", "120G", "GRAO"],
                "PAPINHAS DE FRUTAS": ["MACA", "AMEIXA", "BANANA", "MIRTILO", "MANGA", "PERA", "ESPINA", "DOCE", "CENOURA", "MORANGO"],
                "BISCOTTI": ["LARANJ", "MAC", "CANEL", "CACAU", "GOIAB", "MARACUJ", "BISCOTTI"],
                "PALITINHOS": ["PALIT"],
                "DENTIÇÃO": ["DENTICAO", "DENTIÇÃO"],
                "CEREAIS": ["CEREAL", "AVEIA"]
            }

            for linha, keywords in catalogo.items():
                if any(key in nome for key in keywords):
                    return linha

            return "OUTROS"

        def mapear_sabor(nome):
            nome = limpar_texto(nome)

            if any(x in nome for x in ["PUERICULTURA", "TALHERES", "BABADOR", "BOWL", "PRATINHO", "VENTOSA"]):
                return "Puericultura"

            doces = ["FRUTA", "BANANA", "MACA", "MAMAO", "AMEIXA", "DOCE", "CACAU", "LARANJA", "MORANGO", "MANGA", "PERA", "IOGURTE", "YOGUZINHO", "UVA", "CHOCOLATE"]
            return "Doce" if any(x in nome for x in doces) else "Salgado"

        def mapear_idade(nome):
            nome = limpar_texto(nome)

            if any(x in nome for x in ["PUERICULTURA", "TALHERES", "BABADOR", "BOWL", "PRATINHO", "VENTOSA"]):
                return "Infantil"

            if "12" in nome or "CEREAL" in nome or "PALIT" in nome:
                return "12 meses+"

            if any(x in nome for x in ["MACARRAO", "MASSA", "LETRE", "ELBOW", "FUSILLI"]):
                return "8 meses+"

            return "6 meses+"

        vendas_geral["CAT_CATALOGO"] = vendas_geral.apply(
            lambda r: mapear_catalogo_detalhado(r.get("DESC PRODUTO", ""), r.get("LINHA", "")),
            axis=1
        )
        vendas_geral["SABOR"] = vendas_geral["DESC PRODUTO"].apply(mapear_sabor)
        vendas_geral["IDADE"] = vendas_geral["DESC PRODUTO"].apply(mapear_idade)

        c1, c2 = st.columns(2)

        with c1:
            mix_cat = vendas_geral.groupby("CAT_CATALOGO")["VALOR"].sum().reset_index()
            fig_mix_cat = px.pie(
                mix_cat,
                names="CAT_CATALOGO",
                values="VALOR",
                title="Mix por Linha de Produto",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_mix_cat.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_mix_cat, use_container_width=True)

        with c2:
            mix_sabor = vendas_geral.groupby("SABOR")["VALOR"].sum().reset_index()
            fig_sabor = px.pie(
                mix_sabor,
                names="SABOR",
                values="VALOR",
                title="Divisão Doce vs Salgado vs Puericultura",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_sabor.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_sabor, use_container_width=True)

        c3, c4 = st.columns(2)

        with c3:
            ordem_idade = ["6 meses+", "8 meses+", "12 meses+", "Infantil"]
            vendas_geral["IDADE"] = pd.Categorical(vendas_geral["IDADE"], categories=ordem_idade, ordered=True)
            mix_idade = vendas_geral.groupby("IDADE", observed=True)["VALOR"].sum().reset_index()

            fig_idade = px.bar(
                mix_idade,
                x="IDADE",
                y="VALOR",
                color="IDADE",
                title="Vendas por Faixa/Perfil",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_idade.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_idade, use_container_width=True)

        with c4:
            top_10_geral = (
                vendas_geral
                .groupby("DESC PRODUTO")["VALOR"]
                .sum()
                .reset_index()
                .sort_values("VALOR", ascending=True)
                .tail(10)
            )
            fig_top_geral = px.bar(
                top_10_geral,
                x="VALOR",
                y="DESC PRODUTO",
                orientation="h",
                title="Top 10 Produtos Mais Vendidos",
                color="VALOR",
                color_continuous_scale="Reds"
            )
            fig_top_geral.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_top_geral, use_container_width=True)

else:
    st.warning("Base de vendas não encontrada. Verifique o arquivo de dados.")


# ==========================================
# 🚀 RADAR GERAL DE NOVAS LINHAS
# ==========================================

st.markdown("---")
st.subheader("🚀 Radar de Desenvolvimento das Novas Linhas")

if not df_vendas.empty:
    cnpjs_visiveis = df_filtrado["CNPJ_LIMPO"].unique()
    base_clientes_visiveis = df_filtrado["CNPJ_LIMPO"].nunique()

    vendas_radar = df_vendas[df_vendas["CNPJ_LIMPO"].isin(cnpjs_visiveis)].copy()
    vendas_radar["DATA PEDIDO"] = pd.to_datetime(vendas_radar["DATA PEDIDO"], errors="coerce")
    vendas_radar["MES_ANO"] = vendas_radar["DATA PEDIDO"].dt.strftime("%m/%Y")

    meses_df = (
        vendas_radar[["MES_ANO", "DATA PEDIDO"]]
        .dropna()
        .assign(MES_DATA=lambda x: x["DATA PEDIDO"].dt.to_period("M").dt.to_timestamp())
        .drop_duplicates("MES_ANO")
        .sort_values("MES_DATA", ascending=False)
    )

    meses_disponiveis = ["Todos os meses"] + meses_df["MES_ANO"].tolist()

    mes_selecionado = st.selectbox(
        "Filtrar mês:",
        options=meses_disponiveis,
        key="filtro_mes_novas_linhas"
    )

    if mes_selecionado != "Todos os meses":
        vendas_radar = vendas_radar[vendas_radar["MES_ANO"] == mes_selecionado]

    vendas_novas = preparar_novas_linhas(vendas_radar)

    if not vendas_novas.empty:
        qtd_col = "QTDE" if "QTDE" in vendas_novas.columns else "QTD"

        clientes_novas = vendas_novas["CNPJ_LIMPO"].nunique()
        penetracao = (clientes_novas / base_clientes_visiveis) * 100 if base_clientes_visiveis > 0 else 0
        total_novas = vendas_novas["VALOR"].sum()
        qtd_novas = vendas_novas[qtd_col].sum() if qtd_col in vendas_novas.columns else 0
        ticket_cliente = total_novas / clientes_novas if clientes_novas > 0 else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Faturamento", moeda_br(total_novas))
        m2.metric("Volume", f"{int(qtd_novas):,}".replace(",", "."))
        m3.metric("Clientes Compradores", clientes_novas)
        m4.metric("Penetração", f"{penetracao:.1f}%")
        m5.metric("Ticket/Cliente", moeda_br(ticket_cliente))

        st.markdown("##### Visão Executiva de Tração")

        c1, c2 = st.columns(2)

        with c1:
            evol_novas = (
                vendas_novas
                .groupby([pd.Grouper(key="DATA PEDIDO", freq="D"), "NOVA_LINHA"])["VALOR"]
                .sum()
                .reset_index()
            )
            fig_evol_novas = px.area(
                evol_novas,
                x="DATA PEDIDO",
                y="VALOR",
                color="NOVA_LINHA",
                title="Evolução Diária das Novas Linhas",
                labels={"VALOR": "Valor (R$)", "DATA PEDIDO": "Data", "NOVA_LINHA": "Nova Linha"},
                color_discrete_map={"ERA UMA VEZ": "#FF7A00", "PUERICULTURA": "#7C3AED"},
                line_shape="spline"
            )
            fig_evol_novas.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_evol_novas, use_container_width=True)

        with c2:
            resumo_linha = (
                vendas_novas
                .groupby("NOVA_LINHA")
                .agg(
                    Valor=("VALOR", "sum"),
                    Clientes=("CNPJ_LIMPO", "nunique"),
                    SKUs=("DESC PRODUTO", "nunique")
                )
                .reset_index()
            )
            fig_resumo_linha = px.bar(
                resumo_linha,
                x="NOVA_LINHA",
                y="Valor",
                color="NOVA_LINHA",
                text="Clientes",
                title="Tração por Nova Linha",
                labels={"Valor": "Valor (R$)", "NOVA_LINHA": "Nova Linha"},
                color_discrete_map={"ERA UMA VEZ": "#FF7A00", "PUERICULTURA": "#7C3AED"}
            )
            fig_resumo_linha.update_traces(texttemplate="%{text} clientes", textposition="outside")
            fig_resumo_linha.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_resumo_linha, use_container_width=True)

        c3, c4 = st.columns(2)

        with c3:
            top_skus_novas = (
                vendas_novas
                .groupby(["NOVA_LINHA", "DESC PRODUTO"])
                .agg(Valor=("VALOR", "sum"), Volume=(qtd_col, "sum") if qtd_col in vendas_novas.columns else ("VALOR", "count"))
                .reset_index()
                .sort_values("Valor", ascending=True)
                .tail(12)
            )
            fig_top_skus_novas = px.bar(
                top_skus_novas,
                x="Valor",
                y="DESC PRODUTO",
                color="NOVA_LINHA",
                orientation="h",
                title="Top SKUs das Novas Linhas",
                labels={"Valor": "Valor (R$)", "DESC PRODUTO": "Produto"},
                color_discrete_map={"ERA UMA VEZ": "#FF7A00", "PUERICULTURA": "#7C3AED"}
            )
            fig_top_skus_novas.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_top_skus_novas, use_container_width=True)

        with c4:
            clientes_por_linha = (
                vendas_novas
                .groupby(["CNPJ_LIMPO", "NOVA_LINHA"])["VALOR"]
                .sum()
                .reset_index()
            )
            matriz_clientes = (
                clientes_por_linha
                .pivot_table(index="CNPJ_LIMPO", columns="NOVA_LINHA", values="VALOR", aggfunc="sum", fill_value=0)
                .reset_index()
            )

            if "ERA UMA VEZ" not in matriz_clientes.columns:
                matriz_clientes["ERA UMA VEZ"] = 0
            if "PUERICULTURA" not in matriz_clientes.columns:
                matriz_clientes["PUERICULTURA"] = 0

            compradores_ambas = len(matriz_clientes[(matriz_clientes["ERA UMA VEZ"] > 0) & (matriz_clientes["PUERICULTURA"] > 0)])
            compradores_era = len(matriz_clientes[(matriz_clientes["ERA UMA VEZ"] > 0) & (matriz_clientes["PUERICULTURA"] == 0)])
            compradores_pueri = len(matriz_clientes[(matriz_clientes["PUERICULTURA"] > 0) & (matriz_clientes["ERA UMA VEZ"] == 0)])
            sem_novas = max(base_clientes_visiveis - clientes_novas, 0)

            aderencia = pd.DataFrame({
                "Status": ["Comprou as duas", "Só Era Uma Vez", "Só Puericultura", "Ainda não comprou"],
                "Clientes": [compradores_ambas, compradores_era, compradores_pueri, sem_novas]
            })

            fig_aderencia = px.pie(
                aderencia,
                names="Status",
                values="Clientes",
                title="Aderência das Novas Linhas na Base Filtrada",
                hole=0.45,
                color_discrete_sequence=["#16A34A", "#FF7A00", "#7C3AED", "#CBD5E1"]
            )
            fig_aderencia.update_traces(textposition="inside", textinfo="percent+label")
            fig_aderencia.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_aderencia, use_container_width=True)

        st.markdown("##### Clientes com Maior Tração nas Novas Linhas")

        cols_cliente = ["CNPJ_LIMPO"]
        for possivel_col in ["RAZÃO SOCIAL", "RAZAO SOCIAL", "CLIENTE", "GRUPO ECONÔMICO", "VENDEDOR", "UF", "CIDADE"]:
            if possivel_col in df_filtrado.columns:
                cols_cliente.append(possivel_col)

        cadastro_clientes = df_filtrado[cols_cliente].drop_duplicates("CNPJ_LIMPO")

        ranking_clientes_novas = (
            vendas_novas
            .groupby(["CNPJ_LIMPO", "NOVA_LINHA"])
            .agg(Valor=("VALOR", "sum"), SKUs=("DESC PRODUTO", "nunique"))
            .reset_index()
        )

        ranking_clientes_pivot = (
            ranking_clientes_novas
            .pivot_table(index="CNPJ_LIMPO", columns="NOVA_LINHA", values="Valor", aggfunc="sum", fill_value=0)
            .reset_index()
        )

        if "ERA UMA VEZ" not in ranking_clientes_pivot.columns:
            ranking_clientes_pivot["ERA UMA VEZ"] = 0
        if "PUERICULTURA" not in ranking_clientes_pivot.columns:
            ranking_clientes_pivot["PUERICULTURA"] = 0

        ranking_clientes_pivot["TOTAL NOVAS LINHAS"] = ranking_clientes_pivot["ERA UMA VEZ"] + ranking_clientes_pivot["PUERICULTURA"]

        ranking_clientes_pivot = ranking_clientes_pivot.merge(cadastro_clientes, on="CNPJ_LIMPO", how="left")
        ranking_clientes_pivot = ranking_clientes_pivot.sort_values("TOTAL NOVAS LINHAS", ascending=False).head(15)

        st.download_button(
            label="📥 Baixar Base Clientes Novas Linhas",
            data=ranking_clientes_pivot.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name="clientes_maior_tracao_novas_linhas.csv",
            mime="text/csv",
            use_container_width=True
        )

        for col in ["ERA UMA VEZ", "PUERICULTURA", "TOTAL NOVAS LINHAS"]:
            ranking_clientes_pivot[col] = ranking_clientes_pivot[col].apply(moeda_br)

        st.dataframe(ranking_clientes_pivot, use_container_width=True, hide_index=True)

    else:
        st.info("Ainda não há vendas de Era Uma Vez ou Puericultura na base filtrada.")

else:
    st.warning("Base de vendas não encontrada. Verifique o arquivo de dados.")


# ==========================================
# 🏆 PERFORMANCE POR LINHA (VISÃO DETALHADA - MULTI CLIENTE)
# ==========================================

if len(df_filtrado) >= 1:
    cnpjs_selecionados = df_filtrado[COL_CNPJ].unique()
    vendas_clientes_selecionados = df_vendas[df_vendas[COL_CNPJ].isin(cnpjs_selecionados)].copy()

    if not vendas_clientes_selecionados.empty:
        st.markdown("---")
        st.markdown("#### 🏆 Performance Consolidada por Linha de Produto")

        termos_la_chef = ["LENTILHA", "RISOTINHO", "CASEIRINHO", "CHEF"]

        regras_linhas = {
            "ERA UMA VEZ": ["ERA UMA VEZ", "SALGADINHO INTEGRAL ORGANICO", "BISCOITO RECHEADO", "BEBIDA LACTEA UHT CHOCOLATE"],
            "PUERICULTURA": ["PUERICULTURA", "TALHERES", "BABADOR", "BOWL", "PRATINHO", "VENTOSA"],
            "LA CHEF": termos_la_chef,
            "SOPINHAS": ["SOPINHA"],
            "YOGUZINHO": ["IOGURTE", "YOGU"],
            "PAPINHAS SALGADAS": ["CARNE ARROZ LEGUMES 120G", "FRANGO GRAO VEGETAIS 120G"],
            "PAPINHAS DE FRUTAS": ["PAPAPA ORGANICA"],
            "BISCOTTI": ["BISCOTTI"],
            "PALITINHOS": ["TOMATE/MANJERICAO 20G", "BETERRABA 20G", "CENOURA 20G"],
            "DENTIÇÃO": ["DENTICAO", "DENTIÇÃO"],
            "MACARRÃO": ["ELBOW", "FUSILLI"],
            "CEREAIS": ["CEREAL", "AVEIA"]
        }

        linha_selecionada = st.selectbox(
            "Selecione uma linha para análise consolidada:",
            options=list(regras_linhas.keys())
        )

        termos = regras_linhas[linha_selecionada]
        filtro_termos = "|".join(termos)

        nomes_normalizados = vendas_clientes_selecionados["DESC PRODUTO"].apply(limpar_texto)

        df_detalhe_linha = vendas_clientes_selecionados[
            nomes_normalizados.str.contains(filtro_termos, na=False)
        ].copy()

        if linha_selecionada == "SOPINHAS":
            filtro_trava = "|".join(termos_la_chef)
            df_detalhe_linha = df_detalhe_linha[
                ~df_detalhe_linha["DESC PRODUTO"].apply(limpar_texto).str.contains(filtro_trava, na=False)
            ]

        if not df_detalhe_linha.empty:
            col_valor = "VALOR TOTAL" if "VALOR TOTAL" in df_detalhe_linha.columns else "VALOR"
            col_qtd = "QTD" if "QTD" in df_detalhe_linha.columns else "QTDE"

            performance_sku = (
                df_detalhe_linha
                .groupby("DESC PRODUTO")[col_valor]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )

            c_top, c_vol = st.columns(2)

            with c_top:
                st.success(f"⭐ **Top SKUs do Grupo: {linha_selecionada}**")
                df_top_sku = performance_sku.head(5).copy()
                df_top_sku[col_valor] = df_top_sku[col_valor].apply(moeda_br)
                st.table(df_top_sku.rename(columns={"DESC PRODUTO": "Produto", col_valor: "Total Gasto"}))

            with c_vol:
                total_linha = df_detalhe_linha[col_valor].sum()
                qtd_total = df_detalhe_linha[col_qtd].sum() if col_qtd in df_detalhe_linha.columns else 0
                clientes_linha = df_detalhe_linha[COL_CNPJ].nunique() if COL_CNPJ in df_detalhe_linha.columns else 0

                st.metric(label="Investimento Total (Grupo)", value=moeda_br(total_linha))
                st.metric(label="Volume Total (Unidades)", value=int(qtd_total))
                st.metric(label="Clientes Compradores", value=clientes_linha)

                fig_bar_linha = px.bar(
                    performance_sku.head(5),
                    x=col_valor,
                    y="DESC PRODUTO",
                    orientation="h",
                    title=f"Ranking de Vendas: {linha_selecionada}",
                    labels={col_valor: "Valor Acumulado (R$)", "DESC PRODUTO": "Produto"},
                    color_discrete_sequence=["#00CC96"]
                )
                fig_bar_linha.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_bar_linha, use_container_width=True)

        else:
            st.warning(f"Os clientes selecionados não possuem compras na linha '{linha_selecionada}'.")
        
# ==========================================
# 📊 DISTRIBUIÇÃO CADASTRAL (CORREÇÃO COLUNA FATURAMENTO)
# ==========================================

if len(df_filtrado) > 1:
    st.markdown("---")
    st.subheader("📊 Distribuição Cadastral")
    
    col1, col2 = st.columns(2)

    with col1:
        resumo_seg = df_filtrado[COL_SEGMENTO].value_counts().reset_index()
        resumo_seg.columns = ["Segmento", "Quantidade"]
        
        fig_seg = px.bar(
            resumo_seg, x="Quantidade", y="Segmento", orientation="h",
            title="Distribuição por Segmento",
            color="Quantidade", color_continuous_scale="Reds"
        )
        fig_seg.update_layout(margin=dict(l=150, r=20, t=50, b=20), height=450, showlegend=False)
        st.plotly_chart(fig_seg, use_container_width=True)

    with col2:
        # 1. Identificamos a coluna correta que você mencionou
        col_faturamento_real = "TOTAL ÚLTIMOS 9 MESES"
        
        if col_faturamento_real in df_filtrado.columns:
            # 2. Criamos as faixas de faturamento (ajuste os valores se precisar)
            def categorizar_faturamento(valor):
                try:
                    v = float(valor)
                    if v <= 5000: return "Até R$ 5k"
                    elif v <= 20000: return "R$ 5k - 20k"
                    elif v <= 50000: return "R$ 20k - 50k"
                    else: return "Acima de R$ 50k"
                except:
                    return "Não Identificado"

            # Criamos uma coluna temporária para o gráfico
            temp_df = df_filtrado.copy()
            temp_df["FAIXA_TEMP"] = temp_df[col_faturamento_real].apply(categorizar_faturamento)
            
            resumo_fat = temp_df["FAIXA_TEMP"].value_counts().reset_index()
            resumo_fat.columns = ["Faixa", "Quantidade"]

            fig_fat = px.pie(
                resumo_fat, names="Faixa", values="Quantidade",
                title="Distribuição por Faturamento (9 Meses)",
                hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r
            )
            fig_fat.update_layout(
                margin=dict(l=20, r=20, t=50, b=20),
                height=450,
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_fat, use_container_width=True)
        else:
            st.error(f"⚠️ Coluna '{col_faturamento_real}' não encontrada na planilha.")
    
    st.divider()

    # ==========================================
    # 🗺️ PRESENÇA GEOGRÁFICA
    # ==========================================
    st.subheader("🗺️ Presença Geográfica")

    resumo_estado = df_filtrado[COL_UF].value_counts().reset_index()
    resumo_estado.columns = ["UF", "Quantidade"]

    url_geojson = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

    try:
        import urllib.request, json
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
            scope="south america",
            labels={"Quantidade": "Nº de Clientes"}
        )

        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

        st.plotly_chart(fig_mapa, use_container_width=True)
    except:
        st.warning("⚠️ Não foi possível carregar o mapa. Verificando conexão...")
        st.bar_chart(resumo_estado.set_index("UF"))

    st.divider()

# ==========================================
# 🏆 RESULTADO FINANCEIRO E RANKING (VISUAL PREMIUM)
# ==========================================

st.markdown("### 💰 Resultado Financeiro e Ranking")

if not df_filtrado.empty:
    meses_selecionados = st.session_state.get("filtro_mes", [])

    if not meses_selecionados:
        st.info("💡 Selecione um ou mais meses no filtro lateral para visualizar o faturamento e o ranking.")
    else:
        # 1. Tradutor de Meses (Filtro -> Planilha)
        tradutor_meses = {
            "01": "JAN", "02": "FEV", "03": "MAR", "04": "ABR",
            "05": "MAI", "06": "JUN", "07": "JUL", "08": "AGO",
            "09": "SET", "10": "OUT", "11": "NOV", "12": "DEZ"
        }

        colunas_reais = []
        for m in meses_selecionados:
            try:
                mes_num, ano_num = m.split("/")
                nome_coluna = f"{tradutor_meses[mes_num]}/{ano_num[2:]}"
                if nome_coluna in df_filtrado.columns:
                    colunas_reais.append(nome_coluna)
            except: continue

        if not colunas_reais:
            st.warning("⚠️ Nenhuma coluna de faturamento encontrada para este período.")
        else:
            # 2. Cálculos
            df_calc = df_filtrado.copy()
            for col in colunas_reais:
                df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)

            df_calc["TOTAL_VENDAS"] = df_calc[colunas_reais].sum(axis=1)
            total_periodo = df_calc["TOTAL_VENDAS"].sum()
            qtd_clientes = df_filtrado[COL_RAZAO].nunique()
            
            ranking = df_calc.groupby(COL_VENDEDOR)["TOTAL_VENDAS"].sum().sort_values(ascending=False).reset_index()

            # 3. ESTILIZAÇÃO DOS CARDS (KPIs)
            st.markdown("---")
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7bcf;">
                        <p style="color: #555; margin-bottom: 5px; font-size: 14px; font-weight: bold;">FATURAMENTO TOTAL ({', '.join(colunas_reais)})</p>
                        <h2 style="color: #1f77b4; margin: 0;">R$ {total_periodo:,.2f}</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
                        <p style="color: #555; margin-bottom: 5px; font-size: 14px; font-weight: bold;">CLIENTES ATENDIDOS</p>
                        <h2 style="color: #ff4b4b; margin: 0;">{qtd_clientes}</h2>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 4. RANKING ESTILIZADO EM TABELA LIMPA
            st.markdown("#### 🥇 Ranking de Performance")
            
            # Criando uma visualização de ranking mais elegante
            for i, row in ranking.iterrows():
                valor = f"R$ {row['TOTAL_VENDAS']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                # Cores e ícones por posição
                cor_fundo = "#fffdf0" if i == 0 else "#f8f9fa"
                emoji = "🏆" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
                
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; 
                                background-color: {cor_fundo}; padding: 10px 15px; border-radius: 8px; 
                                margin-bottom: 5px; border: 1px solid #eee;">
                        <span style="font-weight: bold; color: #333;">{i+1}º {emoji} {row[COL_VENDEDOR]}</span>
                        <span style="font-family: monospace; font-weight: bold; color: #2e7bcf;">{valor}</span>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================
# 📂 EXPORTAÇÃO E LISTAGEM (MANTIDOS)
# ==========================================
st.markdown("---")
if not df_filtrado.empty:
    def gerar_excel(df_exp):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            cols_excluir = ["MES_REF", "CONTATO", "TEL_LIMPO", "CNPJ_LIMPO", "TOTAL_VENDAS"]
            df_exp.drop(columns=[c for c in cols_excluir if c in df_exp.columns]).to_excel(writer, index=False)
        return buffer.getvalue()

    st.download_button(label="📥 Baixar Base Completa", data=gerar_excel(df_filtrado), 
                       file_name="vendas_papapa.xlsx", use_container_width=True)

st.subheader("📋 Listagem Detalhada")

# WhatsApp e Tabela (Sua lógica que já funciona)
def criar_link_whatsapp(tel):
    if not tel or pd.isna(tel): return None
    num = "".join(filter(str.isdigit, str(tel)))
    if len(num) > 0 and not num.startswith("55"): num = "55" + num
    return f"https://web.whatsapp.com/send?phone={num}"

df_filtrado["CONTATO"] = df_filtrado["TELEFONE"].apply(criar_link_whatsapp)
cols = list(df_filtrado.columns)
if "TELEFONE" in cols and "CONTATO" in cols:
    idx = cols.index("TELEFONE")
    cols.insert(idx + 1, cols.pop(cols.index("CONTATO")))
    df_filtrado = df_filtrado[cols]

# Configurações de exibição
colunas_meses = [c for c in df_filtrado.columns if "/" in c and len(c) == 6]
config_moeda = {c: st.column_config.NumberColumn(c, format="R$ %.2f") for c in colunas_meses}

st.dataframe(
    df_filtrado,
    column_config={
        "CONTATO": st.column_config.LinkColumn("WhatsApp", display_text="💬 Chamar"),
        "ÚLTIMA COMPRA": st.column_config.DateColumn("Última Compra", format="DD/MM/YYYY"),
        **config_moeda,
        **{c: None for c in ["CNPJ_LIMPO", "TEL_LIMPO", "MES_REF", "TOTAL_VENDAS"] if c in df_filtrado.columns}
    },
    use_container_width=True, hide_index=True
)

st.markdown("<div style='text-align: center; color: #888; font-size: 12px; margin-top: 50px;'>Dashboard Inside Sales Papapá © 2026 - v1.2</div>", unsafe_allow_html=True)






























































































