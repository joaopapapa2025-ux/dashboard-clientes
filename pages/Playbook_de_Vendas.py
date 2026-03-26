import streamlit as st

# REMOVEMOS A TRAVA DAQUI PARA ACABAR COM O LOOP
# O acesso já foi validado na página principal (app_dashboard.py)

with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")
    
    # Link manual para voltar ao Dash
    st.page_link("app_dashboard.py", label="📊 Voltar ao Dashboard", icon="📊")

st.title("📖 Playbook de Vendas - Papapá")
st.success("Operação validada. Bem-vindo, João!")

# --- AQUI VAMOS COLOCAR AS REGRAS DE MARÇO ---
