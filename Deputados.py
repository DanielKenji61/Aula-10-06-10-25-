# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import plotly.express as px

def load_data(path):
    df = pd.read_csv(path)
    return df

def main():
    st.title("Visualizações de Deputados 2022")

    uploaded_file = st.file_uploader("Carregue o arquivo CSV", type="csv")
    if uploaded_file is None:
        st.info("Por favor, carregue um arquivo CSV.")
        return

    df = load_data(uploaded_file)

    st.dataframe(df.head(10))

    if "siglaPartido" in df.columns:
        partido_counts = df["siglaPartido"].value_counts().reset_index()
        partido_counts.columns = ["partido", "contagem"]
        fig1 = px.bar(partido_counts, x="partido", y="contagem",
                      title="Número de Deputados por Partido",
                      labels={"contagem":"Quantidade", "partido":"Partido"})
        st.plotly_chart(fig1, use_container_width=True)

    if "siglaUf" in df.columns:
        uf_counts = df["sigalaUf"] = df["siglaUf"].value_counts().reset_index()  # cuidado: erro de digitação
        # correção:
        uf_counts = df["siglaUf"].value_counts().reset_index()
        uf_counts.columns = ["uf", "contagem"]
        fig2 = px.bar(uf_counts, x="uf", y="contagem",
                      title="Número de Deputados por Estado (UF)",
                      labels={"contagem":"Quantidade", "uf":"UF"})
        st.plotly_chart(fig2, use_container_width=True)

    num_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    st.write("Colunas numéricas detectadas:", num_cols)

    if "gastos" in df.columns and "siglaPartido" in df.columns:
        gastos_partido = df.groupby("siglaPartido")["gastos"].mean().reset_index()
        fig3 = px.bar(gastos_partido, x="siglaPartido", y="gastos",
                      title="Média de Gastos por Partido",
                      labels={"gastos":"Gasto Médio", "siglaPartido":"Partido"})
        st.plotly_chart(fig3, use_container_width=True)

    if "gastos" in df.columns and "siglaPartido" in df.columns:
        fig4 = px.box(df, x="siglaPartido", y="gastos",
                      title="Distribuição de Gastos por Partido",
                      labels={"gastos":"Gastos", "siglaPartido":"Partido"})
        st.plotly_chart(fig4, use_container_width=True)


if __name__ == "__main__":
    main()
