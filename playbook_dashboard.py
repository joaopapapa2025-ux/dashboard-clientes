import streamlit as st

st.set_page_config(
    page_title="Playbook de Vendas",
    layout="wide"
)

st.title("📘 Playbook de Vendas")

st.subheader("🎯 Metas e Premiações - Março/2026")

st.table({
    "Atingimento": ["< 90%", "90% a 99%", "100% a 109%", ">= 110%"],
    "Bônus": ["R$ 0,00", "R$ 500,00", "R$ 1.200,00", "R$ 2.000,00 + Aceleração"]
})
