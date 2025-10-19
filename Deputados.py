import streamlit as st
import pandas as pd
import plotly.express as px

CSV_URL = "https://www.irdx.com.br/media/uploads/deputados_2022.csv"

@st.cache_data
def load_data(url):
    return pd.read_csv(url)

def main():
    st.title("Análise dos Deputados - Eleições 2022")

    try:
        df = load_data(CSV_URL)
        st.success("Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    st.subheader("Prévia dos dados")
    st.dataframe(df.head())

    # Gráfico 1: Quantidade de deputados por partido
    if "partido" in df.columns:
        partido_counts = df["partido"].value_counts().reset_index()
        partido_counts.columns = ["Partido", "Quantidade"]

        fig1 = px.bar(
            partido_counts,
            x="Partido",
            y="Quantidade",
            title="Número de Deputados por Partido",
            text="Quantidade"
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("Coluna 'partido' não encontrada no arquivo.")

    # Gráfico 2: Quantidade de deputados por sexo
    if "sexo" in df.columns:
        sexo_counts = df["sexo"].value_counts().reset_index()
        sexo_counts.columns = ["Sexo", "Quantidade"]

        # Ajustar legenda para ficar mais legível, se quiser
        sexo_counts["Sexo"] = sexo_counts["Sexo"].replace({
            "M": "Masculino",
            "F": "Feminino"
        })

        fig2 = px.bar(
            sexo_counts,
            x="Sexo",
            y="Quantidade",
            title="Número de Deputados por Sexo",
            text="Quantidade"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Coluna 'sexo' não encontrada no arquivo.")

if __name__ == "__main__":
    main()
