import streamlit as st

# ISSO AQUI É A TRAVA SILENCIOSA
if "acesso_liberado" not in st.session_state or not st.session_state.acesso_liberado:
    st.warning("⚠️ Acesse o Dashboard Principal primeiro para validar seu login.")
    if st.button("Ir para Login"):
        st.switch_page("app_dashboard.py")
    st.stop()

# SIDEBAR PARA CONSEGUIR VOLTAR
with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")
    
    if st.button("📊 Voltar ao Dashboard", use_container_width=True):
        st.switch_page("app_dashboard.py")

# CONTEÚDO DO PLAYBOOK
st.title("📖 Playbook de Vendas - Papapá")
st.info("Aqui você vai colocar as regras de comissão e processos do time.")
