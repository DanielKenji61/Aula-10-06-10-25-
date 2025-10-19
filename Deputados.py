import streamlit as st
import pandas as pd
import plotly.express as px

# URL do CSV
CSV_URL = "https://www.irdx.com.br/media/uploads/deputados_2022.csv"

@st.cache_data
def load_data(url):
    return pd.read_csv(url)

def main():
    st.title("📊 Análise dos Deputados - Eleições 2022")

    try:
        df = load_data(CSV_URL)
        st.success("✅ Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return

    st.subheader("👀 Prévia dos dados")
    st.dataframe(df.head())

    # Verificar se a coluna 'siglaPartido' existe
    if 'siglaPartido' in df.columns:
        partido_counts = df['siglaPartido'].value_counts().reset_index()
        partido_counts.columns = ['Partido', 'Quantidade']

        fig = px.bar(partido_counts, x='Partido', y='Quantidade',
                     title="Número de Deputados por Partido",
                     labels={'Partido': 'Partido', 'Quantidade': 'Número de Deputados'},
                     text='Quantidade')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Coluna 'siglaPartido' não encontrada no arquivo.")

if __name__ == "__main__":
    main()
