import streamlit as st

st.title("Meu programa")
st.write("Alô mundo")

nome = st.text_input("Digite o seu nome:")
if nome:
  st.write(nome.upper())

import streamlit as st

st.title("Meu programa")
st.write("Alô mundo")

nome = st.text_input("Digite o seu nome:")

cor = st.selectbox("Escolha a cor do texto:", ["blue", "red", "green", "purple", "orange"])

if nome:
    st.markdown(f'<p style="color:{cor}; font-size:24px;">{nome.upper()}</p>', unsafe_allow_html=True)
