import streamlit as st

# O Streamlit Cloud às vezes perde o session_state entre páginas.
# Se isso acontecer, em vez de dar erro, vamos apenas pedir a senha de novo nela.
if "acesso_liberado" not in st.session_state or not st.session_state.acesso_liberado:
    st.warning("Por favor, valide seu acesso na página principal.")
    if st.button("Ir para o Dashboard"):
        st.switch_page("app_dashboard.py")
    st.stop()

# CONTEÚDO DA NOVA PÁGINA
st.title("📖 Playbook de Vendas")
st.subheader("🎯 Metas e Premiações - Março/2026")

st.table({
    "Atingimento": ["< 90%", "90% a 99%", "100% a 109%", ">= 110%"],
    "Bônus": ["R$ 0,00", "R$ 500,00", "R$ 1.200,00", "R$ 2.000,00 + Aceleração"]
})
