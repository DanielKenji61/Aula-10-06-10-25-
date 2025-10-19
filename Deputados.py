import streamlit as st
import pandas as pd
import plotly.express as px

CSV_URL = "https://www.irdx.com.br/media/uploads/deputados_2022.csv"

@st.cache_data
def load_data(url):
    return pd.read_csv(url)

def main():
    st.title(" Análise Completa dos Deputados 2022")

    try:
        df = load_data(CSV_URL)
        st.success("Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    st.subheader("Colunas disponíveis no CSV:")
    st.write(df.columns.tolist())

    st.subheader("Prévia dos dados")
    st.dataframe(df.head())

    coluna_partido = "siglaPartido"
    coluna_sexo = "sexo"

    
    if coluna_partido in df.columns:
        st.subheader("Deputados por Partido")
        contagem_partidos = df[coluna_partido].value_counts().reset_index()
        contagem_partidos.columns = ["Partido", "Quantidade"]

        fig_partidos = px.bar(
            contagem_partidos,
            x="Partido",
            y="Quantidade",
            title="Quantidade de Deputados por Partido",
            text="Quantidade",
        )
        st.plotly_chart(fig_partidos, use_container_width=True)
    else:
        st.warning(f"Coluna '{coluna_partido}' não encontrada.")

    if coluna_sexo in df.columns:
        st.subheader("Deputados por Sexo")

        df["Sexo_Legivel"] = df[coluna_sexo].map({
            "MASCULINO": "Homens",
            "FEMININO": "Mulheres"
        }).fillna("Outro/Indefinido")

        contagem_sexo = df["Sexo_Legivel"].value_counts().reset_index()
        contagem_sexo.columns = ["Sexo", "Quantidade"]

        fig_sexo = px.bar(
            contagem_sexo,
            x="Sexo",
            y="Quantidade",
            color="Sexo",
            title="Quantidade de Deputados por Sexo",
            text="Quantidade",
        )
        st.plotly_chart(fig_sexo, use_container_width=True)
    else:
        st.warning(f"Coluna '{coluna_sexo}' não encontrada.")

if __name__ == "__main__":
    main()
