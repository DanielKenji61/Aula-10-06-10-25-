# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

def load_data(file):
    try:
        df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o CSV: {e}")
        return None

def main():
    st.title("📊 Visualização de Dados dos Deputados 2022")

    uploaded_file = st.file_uploader("Faça upload do arquivo CSV dos deputados", type="csv")

    if uploaded_file is not None:
        df = load_data(uploaded_file)

        if df is not None:
            st.subheader("Prévia dos Dados")
            st.dataframe(df.head())

            st.markdown("---")

            st.subheader("Colunas disponíveis")
            st.write(df.columns.tolist())

            if "siglaPartido" in df.columns:
                st.subheader("Número de Deputados por Partido")
                fig1 = px.histogram(df, x="siglaPartido", title="Deputados por Partido", labels={"siglaPartido": "Partido"})
                st.plotly_chart(fig1, use_container_width=True)

            if "siglaUf" in df.columns:
                st.subheader("Número de Deputados por Estado (UF)")
                fig2 = px.histogram(df, x="siglaUf", title="Deputados por Estado", labels={"siglaUf": "Estado"})
                st.plotly_chart(fig2, use_container_width=True)

            if "gastos" in df.columns and "siglaPartido" in df.columns:
                st.subheader("Média de Gastos por Partido")
                gastos_partido = df.groupby("siglaPartido")["gastos"].mean().reset_index()
                fig3 = px.bar(gastos_partido, x="siglaPartido", y="gastos",
                              labels={"gastos": "Gasto Médio", "siglaPartido": "Partido"},
                              title="Gasto Médio por Partido")
                st.plotly_chart(fig3, use_container_width=True)

            if "gastos" in df.columns and "siglaPartido" in df.columns:
                st.subheader("Distribuição dos Gastos por Partido")
                fig4 = px.box(df, x="siglaPartido", y="gastos",
                             title="Boxplot de Gastos por Partido",
                             labels={"gastos": "Gastos", "siglaPartido": "Partido"})
                st.plotly_chart(fig4, use_container_width=True)

        else:
            st.error("Erro ao processar o arquivo CSV. Verifique o formato.")
    else:
        st.info("Faça upload de um arquivo CSV para visualizar os dados.")

if __name__ == "__main__":
    main()
