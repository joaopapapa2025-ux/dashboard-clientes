import streamlit as st

# Valida se já logou na Home (Compartilha o 'acesso_liberado')
if "acesso_liberado" not in st.session_state or not st.session_state.acesso_liberado:
    st.warning("⚠️ Acesse o Dashboard Principal primeiro para validar seu login.")
    if st.button("Ir para Login"):
        st.switch_page("app_dashboard.py")
    st.stop()

# SIDEBAR DO PLAYBOOK
with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")
    
    if st.button("📊 Voltar ao Dashboard", use_container_width=True):
        st.switch_page("app_dashboard.py")

st.title("📖 Playbook de Vendas")
st.write("Conteúdo do playbook em construção...")
