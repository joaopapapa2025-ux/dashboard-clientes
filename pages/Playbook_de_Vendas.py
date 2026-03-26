import streamlit as st

# Verificação de Segurança (Compartilhada com a Home)
if "acesso_liberado" not in st.session_state or not st.session_state.acesso_liberado:
    st.warning("⚠️ Por favor, acesse primeiro o Dashboard Principal para validar seu login.")
    if st.button("Ir para o Dashboard"):
        st.switch_page("app_dashboard.py")
    st.stop()

# --- ABAIXO DAQUI SEGUE O CONTEÚDO DO PLAYBOOK ---
st.title("📖 Playbook de Vendas")
