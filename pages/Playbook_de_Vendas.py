import streamlit as st

st.set_page_config(page_title="Playbook - Papapá", layout="wide")

st.title("📖 Playbook de Vendas")
st.write("O conteúdo do playbook aparecerá aqui em breve.")

if st.button("⬅️ Voltar para o Dashboard"):
    st.switch_page("app_dashboard.py")
