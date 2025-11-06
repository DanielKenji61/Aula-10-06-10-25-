import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time


ID_PROPOSICAO = "2270800"
ID_VOTACAO = "2270800-175" 

URL_API_BASE = "https://dadosabertos.camara.leg.br/api/v2/"
URL_PROPOSICAO_DETALHE = f"{URL_API_BASE}proposicoes/{ID_PROPOSICAO}"
URL_ORIENTACOES = f"{URL_API_BASE}votacoes/{ID_VOTACAO}/orientacoes"
URL_VOTOS = f"{URL_API_BASE}votacoes/{ID_VOTACAO}/votos"


def limpar_cache_api():
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def buscar_dados(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Falha ao acessar API: {url}. Erro: {e}")
        return None

@st.cache_data(ttl=3600)
def obter_titulo():
    """Busca apenas o título curto da PEC para o cabeçalho."""
    dados = buscar_dados(URL_PROPOSICAO_DETALHE)
    if dados:
        return dados.get('siglaTipo', 'PEC') + ' ' + str(dados.get('numero', '03')) + '/' + str(dados.get('ano', '2021'))
    return "PEC 03/2021"

def processar_orientacoes(dados_orientacoes):
    """Processa o JSON de orientações para um DataFrame de visualização."""
    if not dados_orientacoes or not dados_orientacoes.get('dados'):
        # Retorna DataFrame vazio se não houver dados, indicando 'Não Orientou'
        return pd.DataFrame()
        
    dados_processados = []
    
    for item in dados_orientacoes['dados']:
        orientacao = item.get('orientacao')
        sigla_partido = item.get('siglaPartido', 'Sem Partido')
        
        dados_processados.append({
            'Partido': sigla_partido,
            'Orientação': orientacao
        })
        
    return pd.DataFrame(dados_processados)

def processar_votos_nominais(dados_votos):
    """Processa o JSON de votos nominais em um DataFrame agrupado por Partido."""
    if not dados_votos or not dados_votos.get('dados'):
        return pd.DataFrame()

    df = pd.DataFrame(dados_votos['dados'])
    
    df['Partido'] = df['deputado'].apply(lambda x: x['siglaPartido'])
    df['Voto'] = df['tipoVoto']
    
    df['Sim'] = df['Voto'].apply(lambda x: 1 if x == 'Sim' else 0)
    df['Não'] = df['Voto'].apply(lambda x: 1 if x == 'Não' else 0)
    df['Abstenção'] = df['Voto'].apply(lambda x: 1 if x == 'Abstenção' else 0)
    df['Outro'] = df['Voto'].apply(lambda x: 1 if x not in ['Sim', 'Não', 'Abstenção'] else 0)

    df_agrupado = df.groupby('Partido')[['Sim', 'Não', 'Abstenção', 'Outro']].sum().reset_index()
    df_agrupado['Total Votos'] = df_agrupado[['Sim', 'Não', 'Abstenção', 'Outro']].sum(axis=1)
    
    return df_agrupado.sort_values(by='Total Votos', ascending=False)


st.set_page_config(layout="wide", page_title="Análise PEC 03/2021")

titulo = obter_titulo()
st.title("⚖️ Monitor de Transparência: PEC 03/2021 (Blindagem)")
st.header(f"Análise Política e Jurimétrica de Votação Nominal - {titulo}")

dados_orientacoes_raw = buscar_dados(URL_ORIENTACOES)
dados_votos_raw = buscar_dados(URL_VOTOS)

st.sidebar.button("Resetar Cache da API", on_click=limpar_cache_api)
st.markdown("---")


st.subheader("1. Orientação das Lideranças Partidárias")
st.caption("A posição oficial que os líderes determinaram à bancada para a votação do Substitutivo em 1º Turno.")

df_orientacoes = processar_orientacoes(dados_orientacoes_raw)

if df_orientacoes.empty:
    st.info("A API não retornou orientações partidárias. Isso significa que a maioria das lideranças optou por 'Liberar a Bancada' ou 'Não Orientar' ativamente nesta votação específica.")
else:
    cores_orientacao = {
        'Sim': 'green', 'Não': 'red', 'Obstrução': 'darkred', 
        'Liberado': 'blue', 'Abstenção': 'gold', 'Não Orientou': 'gray'
    }
    
    fig_orientacao = px.bar(
        df_orientacoes,
        x='Partido',
        y=[1] * len(df_orientacoes),
        color='Orientação',
        title='Orientação das Lideranças Partidárias (Substitutivo 1º Turno)',
        labels={'y': 'Presença', 'Partido': 'Partido'},
        color_discrete_map=cores_orientacao
    )
    fig_orientacao.update_traces(marker_line_width=1.5, marker_line_color='black')
    fig_orientacao.update_layout(yaxis_visible=False, yaxis_showticklabels=False)
    
    st.plotly_chart(fig_orientacao, use_container_width=True)

st.markdown("---")

st.subheader("2. Resultado da Votação Nominal por Partido")

df_votos_partido = processar_votos_nominais(dados_votos_raw)

if df_votos_partido.empty:
    st.error("Não foi possível carregar os votos nominais detalhados.")
else:
    # 1. Gráfico de Votos (Empilhadas)
    df_votos_plot = df_votos_partido.drop(columns=['Total Votos', 'Outro'])
    df_plot_melt = df_votos_plot.melt(id_vars='Partido', var_name='Tipo de Voto', value_name='Total')

    fig_votos = px.bar(
        df_plot_melt,
        x='Partido',
        y='Total',
        color='Tipo de Voto',
        title='Votos Registrados na PEC 03/2021 por Partido',
        barmode='stack',
        color_discrete_map={'Sim': 'green', 'Não': 'red', 'Abstenção': 'gold'}
    )
    fig_votos.update_layout(xaxis_title="Partido", yaxis_title="Número Total de Votos")
    st.plotly_chart(fig_votos, use_container_width=True)

    # 2. Tabela Detalhada
    st.markdown("##### Detalhamento da Votação Nominal (Contagem de Votos):")
    st.dataframe(
        df_votos_partido.sort_values(by='Total Votos', ascending=False),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")
st.success("Análise de transparência finalizada. Os dados de orientação e votação estão completos.")
