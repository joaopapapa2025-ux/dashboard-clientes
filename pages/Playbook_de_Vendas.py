import streamlit as st

# 1. VERIFICAÇÃO DE ACESSO (O SEGREDO ESTÁ AQUI)
if "acesso_liberado" not in st.session_state or not st.session_state.acesso_liberado:
    st.error("⚠️ Sessão expirada ou acesso não validado.")
    st.info("Por favor, digite a senha na tela principal para liberar o acesso.")
    
    # Em vez de switch_page automático, usamos um botão manual 
    # para evitar o "loop" infinito de vai e volta
    if st.button("Ir para tela de senha"):
        st.switch_page("app_dashboard.py")
    st.stop()

# 2. SE PASSOU PELA TRAVA, DESENHA A SIDEBAR
with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")
    
    if st.button("📊 Voltar ao Dashboard", use_container_width=True):
        st.switch_page("app_dashboard.py")

# 3. CONTEÚDO DO PLAYBOOK
st.title("📖 Playbook de Vendas - Papapá")
