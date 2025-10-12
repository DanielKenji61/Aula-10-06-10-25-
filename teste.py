import streamlit as st

st.title("Meu programa")
st.write("Alô mundo")

nome = st.text_input("Digite o seu nome:")
if nome:
  st.write(nome.upper())

import streamlit as st

st.set_page_config(page_title="Conversor de Nome", page_icon="✨", layout="centered")

st.markdown("# 👋 Bem-vindo ao meu app!")
st.write("Este é um app simples feito com **Streamlit** para brincar com seu nome!")

st.markdown("---")

nome = st.text_input("Digite o seu nome:")

if nome:
    st.success(f"Olá, **{nome.title()}**! Aqui está seu nome em caixa alta:")
    st.code(nome.upper(), language="text")
else:
    st.info("Por favor, digite seu nome acima. 👆")

st.markdown("---")
st.caption("Feito com ❤️ usando Streamlit")
