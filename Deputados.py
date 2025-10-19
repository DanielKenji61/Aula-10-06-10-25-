import streamlit as st
import pandas as pd
import plotly.express as px

# URL do CSV direto da internet
CSV_URL = "https://www.irdx.com.br/media/uploads/deputados_2022.csv"

@st.cache_data
def load_data(url):
    # Baixa o CSV direto do link e retorna o DataFrame
    return pd.read_csv(url)

def main():
    st.title("📊 Análise dos Deputados Federais - Eleições 2022")

    try:
        df = load_data(CSV_URL)
        st.success("✅ Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return

    st.subheader("👀 Prévia dos dados")
    st.dataframe(df.head())

    # Gráfico 1: Quantidade de deputados por partido
    if "siglaPartido" in df.columns:
        partido_counts = df["siglaPartido"].value_counts().reset_index()
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
        st.warning("Coluna 'siglaPartido' não encontrada no arquivo.")

    # Gráfico 2: Média de gastos por partido
    if "siglaPartido" in df.columns and "gastoTotal" in df.columns:
        media_gastos = df.groupby("siglaPartido")["gastoTotal"].mean().reset_index()

        fig2 = px.bar(
            media_gastos,
            x="siglaPartido",
            y="gastoTotal",
            title="Média de Gastos de Campanha por Partido",
            labels={"siglaPartido": "Partido", "gastoTotal": "Gasto Médio"},
            text=media_gastos["gastoTotal"].round(2)
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Colunas 'siglaPartido' ou 'gastoTotal' não encontradas no arquivo.")

if __name__ == "__main__":
    main()
