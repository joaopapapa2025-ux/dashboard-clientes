import streamlit as st

st.set_page_config(page_title="Playbook de Vendas - Papapá", layout="wide")

st.title("📖 Playbook de Vendas & Guia de Suporte")
st.markdown("---")

# Seção 1: Guia de Resolução (O que a gente penou hoje!)
st.header("🛠️ Guia de Resolução de Problemas (Troubleshooting)")

col1, col2 = st.columns(2)

with col1:
    with st.expander("📌 Papinha Salgada aparecendo no Gap de Mix errado"):
        st.warning("**Causa:** O cliente comprou Papinhas de Fruta (100g) e o sistema confundiu com a linha Salgada.")
        st.info("**Solução:** O código atual já filtra por '120g' e exclui palavras como 'Maçã' ou 'Banana'. Se o erro persistir, verifique se o nome do produto no ERP contém o peso correto.")

    with st.expander("📌 Palitinhos não aparecem no Cross-sell"):
        st.warning("**Causa:** Algum produto de outra linha (ex: Papinha de Cenoura) está usando a palavra 'Palitinho' indevidamente.")
        st.info("**Solução:** A regra de ouro no Dash é: Só é Palitinho se a palavra 'PALITINHO' estiver explícita no nome do produto.")

with col2:
    with st.expander("📌 CNPJ não retorna dados"):
        st.error("**Causa:** Formatação do CNPJ ou delay na base Vekta.")
        st.write("1. Verifique se há pontos ou traços (o dash prefere apenas números).")
        st.write("2. Confirme se o cliente teve vendas nos últimos 12 meses.")

st.markdown("---")

# Seção 2: Estratégia Comercial
st.header("🚀 Estratégias de Vendas")

tab1, tab2 = st.tabs(["💡 Argumentos de Cross-sell", "📈 Melhoria de Mix"])

with tab1:
    st.subheader("Como converter cliente de Fruta para Salgada?")
    st.write("""
    1. **Foco na Proteína:** Explique que a linha de 120g é a introdução ideal para o almoço/jantar.
    2. **Praticidade:** Reforce que são orgânicas e prontas para consumo, ideal para saídas.
    """)

with tab2:
    st.subheader("Aumentando o Ticket Médio com La Chef")
    st.write("Se o cliente já compra Papinhas Salgadas, o próximo passo natural é o **La Chef (180g)**, que possui pedaços maiores para o desenvolvimento da mastigação.")

st.success("Dúvidas sobre o Dashboard? Fale com o João (Coordenador Inside Sales).")
