import streamlit as st
import pandas as pd
import plotly.express as px

CSV_URL = "https://www.irdx.com.br/media/uploads/deputados_2022.csv"

@st.cache_data 
def load_data(url):
    df = pd.read_csv(url)
    return df

def main():
    st.title(" Visualização de Dados dos Deputados 2022")

    try:
        df = load_data(CSV_URL)
        st.success("Dados carregados com sucesso a partir da URL.")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return

    st.subheader("Prévia dos Dados")
    st.dataframe(df.head())

    st.markdown("---")

    st.subheader("Colunas disponíveis")
    st.write(df.columns.tolist())

    if "siglaPartido" in df.columns:
        st.subheader("Deputados por Partido")
        fig1 = px.histogram(df, x="siglaPartido", title="Deputados por Partido")
        st.plotly_chart(fig1, use_container_width=True)

    if "siglaUf" in df.columns:
        st.subheader("Deputados por Estado (UF)")
        fig2 = px.histogram(df, x="siglaUf", title="Deputados por Estado")
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
