import streamlit as st
import pandas as pd
import plotly.express as px

CSV_URL = "https://www.irdx.com.br/media/uploads/deputados_2022.csv"

@st.cache_data  
def load_data(url):
    df = pd.read_csv(url)
    return df

def main():
    st.title(" Análise dos Deputados Federais Eleitos em 2022")

    try:
        df = load_data(CSV_URL)
        st.success("Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return

    st.subheader(" Prévia dos dados")
    st.dataframe(df.head())

    if "siglaPartido" in df.columns:
        st.subheader(" Número de Deputados por Partido")
        partido_counts = df["siglaPartido"].value_counts().reset_index()
        partido_counts.columns = ["Partido", "Quantidade"]
        fig1 = px.bar(partido_counts, x="Partido", y="Quantidade",
                      title="Deputados por Partido", text="Quantidade")
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("Coluna 'siglaPartido' não encontrada no CSV.")

    if "sexo" in df.columns:
        st.subheader(" Distribuição por Sexo")
        sexo_counts = df["sexo"].value_counts().reset_index()
        sexo_counts.columns = ["Sexo", "Quantidade"]
        fig2 = px.bar(sexo_counts, x="Sexo", y="Quantidade",
                      title="Deputados por Sexo", text="Quantidade",
                      color="Sexo")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Coluna 'sexo' não encontrada no CSV.")

if __name__ == "__main__":
    main()
