import streamlit as st

st.title("Meu programa")
st.write("Alô mundo")

nome = st.text_input("Digite o seu nome:")

cor = st.selectbox("Escolha a cor do texto:", ["blue", "red", "green", "purple", "orange"])

if nome:
    # Nome em maiúsculas com a cor escolhida
    st.markdown(
        f'<p style="color:{cor}; font-size:24px;">{nome.upper()}</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<p style="color:{cor}; font-size:20px;">Alô mundo, meu nome é {nome}</p>',
        unsafe_allow_html=True
    )
