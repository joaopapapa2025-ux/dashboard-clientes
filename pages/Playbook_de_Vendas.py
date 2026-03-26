import streamlit as st

# 1. VALIDAÇÃO POR URL (QUERY PARAMS)
# Se o 'auth=ok' estiver na URL, ele libera o acesso sem depender do session_state
params = st.query_params

if params.get("auth") != "ok" and (not st.session_state.get("acesso_liberado")):
    st.error("🔒 Acesso restrito.")
    if st.button("Voltar para Login"):
        st.switch_page("app_dashboard.py")
    st.stop()

# 2. SE PASSOU, MOSTRA O CONTEÚDO
st.title("📖 Playbook de Vendas - Papapá")

with st.sidebar:
    # Link para voltar sem perder o acesso (mantendo o parâmetro na URL se quiser)
    if st.button("📊 Voltar ao Dashboard", use_container_width=True):
        st.switch_page("app_dashboard.py")
