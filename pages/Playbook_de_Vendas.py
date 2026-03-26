import streamlit as st

# 1. Configuração da Página
st.set_page_config(page_title="Playbook de Vendas - Papapá", layout="wide")

# 2. Sidebar (Logo e Voltar)
with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")
    st.markdown("---")
    st.page_link("app_dashboard.py", label="⬅️ Voltar ao Dashboard", icon="🏠")

# 3. Cabeçalho do Playbook
st.title("📖 Playbook de Vendas - Inside Sales")
st.info("Consulte aqui as regras de negócio, metas e processos da operação.")

# 4. Conteúdo em Abas (Fica muito mais organizado)
tab1, tab2, tab3 = st.tabs(["🎯 Metas e Comissionamento", "⚙️ Processo RD CRM", "📞 Pitch de Vendas"])

with tab1:
    st.header("Estrutura de Metas - Março/2026")
    st.write("Abaixo estão os gatilhos de aceleração baseados no faturamento:")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Piso (90%)", "R$ 785.256")
    col2.metric("Meta (100%)", "R$ 872.507")
    col3.metric("Acelerador (110%)", "R$ 959.758")
    
    st.markdown("""
    **Regras de Comissionamento:**
    * **Até 90%:** Comissão base sobre o faturado.
    * **90% a 100%:** Bônus fixo por atingimento de faixa.
    * **Acima de 110%:** Campanha de aceleração (Double Commission).
    """)

with tab2:
    st.header("Fluxo no RD CRM")
    st.markdown("""
    1.  **Lead Qualificado:** Entrada via Inbound/Outbound.
    2.  **Negociação:** Proposta enviada e follow-up ativo.
    3.  **Reativação:** Clientes da base sem compra há +30 dias.
    4.  **Fechamento:** Registro do faturamento para o Dashboard.
    """)

with tab3:
    st.header("Scripts e Abordagem")
    with st.expander("Ver Script de Reativação"):
        st.write("Olá [Nome], aqui é o [Seu Nome] da Papapá! Vi que faz um tempo que não repomos seu estoque...")
