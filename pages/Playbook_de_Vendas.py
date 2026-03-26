import streamlit as st

# Configuração obrigatória da página
st.set_page_config(page_title="Playbook de Vendas - Papapá", layout="wide")

# Sidebar para conseguir voltar
with st.sidebar:
    try:
        st.image("Papapa-azul.png", width=180)
    except:
        st.subheader("💙 Papapá")
    st.markdown("---")
    if st.button("⬅️ Voltar ao Dashboard", use_container_width=True):
        st.switch_page("app_dashboard.py")

st.title("📖 Playbook de Vendas - Inside Sales")
st.write("Bem-vindo ao guia oficial da operação Papapá.")

# Exemplo de conteúdo para testar
st.info("As regras de comissionamento de Março/2026 serão listadas aqui.")
