import streamlit as st

st.set_page_config(page_title="Playbook de Vendas - Papapá", layout="wide")

st.title("📖 Playbook de Vendas & Guia de Suporte")
st.markdown("---")

# Seção 1: Guia de Resolução (Troubleshooting)
st.header("🛠️ Guia de Resolução de Problemas")

col1, col2 = st.columns(2)

with col1:
    with st.expander("📌 Papinha Salgada aparecendo no Gap de Mix"):
        st.warning("**Causa:** O sistema confundiu com Papinhas de Fruta.")
        st.info("**Regra Atual:** O Dash agora exige que o produto tenha '120g' e NÃO contenha nomes de frutas no cadastro para ser considerado Salgada.")

    with st.expander("📌 Palitinhos com erro no Gap"):
        st.warning("**Causa:** Cadastro de Cenoura/Beterraba em outras linhas.")
        st.info("**Regra Atual:** Só é validado como Palitinho se a palavra 'PALITINHO' estiver escrita no nome do produto no ERP.")

with col2:
    with st.expander("📌 CNPJ não encontrado"):
        st.error("**Causa:** Formatação ou ausência de vendas recentes.")
        st.write("Verifique se o CNPJ foi digitado apenas com números.")

st.markdown("---")

# Seção 2: Dicas para o Time
st.header("🚀 Dicas para Inside Sales")
st.info("Utilize o Gap de Mix para oferecer produtos das mesmas linhas que o cliente já compra (ex: se compra um sabor de Palitinho, ofereça os outros dois).")

st.success("Dúvidas? Fale com o João (Coord. Inside Sales)")
