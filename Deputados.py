import streamlit as st
import pandas as pd

CSV_URL = "https://www.irdx.com.br/media/uploads/deputados_2022.csv"

@st.cache_data
def load_data(url):
    return pd.read_csv(url)

def main():
    st.title("Colunas do arquivo CSV")

    try:
        df = load_data(CSV_URL)
        st.success("Dados carregados!")
    except Exception as e:
        st.error(f"Erro: {e}")
        return

    st.write("Colunas do arquivo:")
    st.write(df.columns.tolist())

if __name__ == "__main__":
    main()
