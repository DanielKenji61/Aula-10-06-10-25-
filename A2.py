import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS (URLs Fixas) ---

ID_PROPOSICAO = "2270800"
ID_VOTACAO = "2270800-175" 

URL_API_BASE = "https://dadosabertos.camara.leg.br/api/v2/"
URL_PROPOSICAO_DETALHE = f"{URL_API_BASE}proposicoes/{ID_PROPOSICAO}"
URL_VOTOS = f"{URL_API_BASE}votacoes/{ID_VOTACAO}/votos"

# EMENTA FIXA: O texto exato fornecido pelo usuário
EMENTA_FIXA = "Altera os arts. 14, 27, 53, 102 e 105 da Constituição Federal, para dispor sobre as prerrogativas parlamentares e dá outras providências."

# --- 2. FUNÇÕES DE BUSCA E PROCESSAMENTO ---

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
        return None

def obter_dados_juridicos():
    """Busca Título e Situação Final da PEC, usando a EMENTA FIXA."""
    dados_proposicao = buscar_dados(URL_PROPOSICAO_DETALHE)
    
    if dados_proposicao:
        titulo = dados_proposicao.get('siglaTipo', 'PEC') + ' ' + str(dados_proposicao.get('numero', '03')) + '/' + str(dados_proposicao.get('ano', '2021'))
        
        ementa_api = dados_proposicao.get('ementa', EMENTA_FIXA)
        
        status_final = dados_proposicao.get('statusProposicao', {}).get('descricaoSituacao', 'Em Tramitação')
        
        if 'promulgada' in status_final.lower() or 'sancionada' in status_final.lower() or 'transformada em norma' in status_final.lower():
            status_juridico = "APROVADA (Lei/Emenda)"
            status_cor = "green"
        elif 'rejeitada' in status_final.lower() or 'arquivamento' in status_final.lower():
            status_juridico = "REJEITADA/ARQUIVADA"
            status_cor = "red"
        else:
            status_juridico = "EM TRAMITAÇÃO"
            status_cor = "orange"
        
        return titulo, ementa_api, status_juridico, status_cor
    
    return "PEC 03/2021", EMENTA_FIXA, "ERRO DE DADOS/API INACESSÍVEL", "red"

def processar_votos_nominais_tabela(dados_votos):
    """Processa o JSON de votos nominais em um DataFrame de votos brutos."""
    if not dados_votos or not dados_votos.get('dados'):
        return pd.DataFrame()

    lista_votos = dados_votos.get('dados', [])
    dados_tabela = []
    
    for voto in lista_votos:
        deputado_info = voto.get('deputado', {})
        
        dados_tabela.append({
            'Nome do Deputado': deputado_info.get('nome', 'N/A'),
            'Partido': deputado_info.get('siglaPartido', 'N/A'),
            'UF': deputado_info.get('siglaUf', 'N/A'),
            'Voto Nominal': voto.get('tipoVoto', 'N/A')
        })
        
    return pd.DataFrame(dados_tabela)

def agrupar_votos_por_partido(df_votos):
    """Cria o DataFrame agrupado por partido para o gráfico de barras."""
    
    df_votos['Sim'] = df_votos['Voto Nominal'].apply(lambda x: 1 if x == 'Sim' else 0)
    df_votos['Não'] = df_votos['Voto Nominal'].apply(lambda x: 1 if x == 'Não' else 0)
    df_votos['Abstenção'] = df_votos['Voto Nominal'].apply(lambda x: 1 if x == 'Abstenção' else 0)
    df_votos['Outro'] = df_votos['Voto Nominal'].apply(lambda x: 1 if x not in ['Sim', 'Não', 'Abstenção'] else 0)

    df_agrupado = df_votos.groupby('Partido')[['Sim', 'Não', 'Abstenção', 'Outro']].sum().reset_index()
    df_agrupado['Total Votos'] = df_agrupado[['Sim', 'Não', 'Abstenção', 'Outro']].sum(axis=1)
    
    return df_agrupado.sort_values(by='Total Votos', ascending=False)


# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Análise PEC 03/2021")

# Carregamento dos dados jurídicos
titulo, ementa, status_juridico, status_cor = obter_dados_juridicos()
dados_votos_raw = buscar_dados(URL_VOTOS)
df_votos_nominais = processar_votos_nominais_tabela(dados_votos_raw)

st.title("⚖️ Monitor de Transparência: PEC 03/2021")
st.header(f"Relatório Jurídico e Votação Nominal Aberta - {titulo}")

st.sidebar.button("Resetar Cache da API", on_click=limpar_cache_api)
st.markdown("---")

# =========================================================
# SEÇÃO 1: STATUS JURÍDICO E EMENTA
# =========================================================

col_titulo, col_status = st.columns([3, 1])

with col_titulo:
    st.subheader(f"Proposta: {titulo}")
    st.markdown("#### Objetivo da PEC (Ementa):")
    st.markdown(f"> **{ementa}**")

with col_status:
    st.markdown("#### Situação Final:")
    st.markdown(
        f"<div style='background-color: {status_cor}; color: white; padding: 10px; border-radius: 5px; text-align: center;'><b>{status_juridico}</b></div>", 
        unsafe_allow_html=True
    )

st.markdown("---")

# =========================================================
# SEÇÃO 2: GRÁFICO DE VOTAÇÃO POR PARTIDO (Título Alterado)
# =========================================================

st.subheader("Total de votos em plenário")
st.caption(f"Análise dos votos na votação {ID_VOTACAO} (Substitutivo em 1º Turno) agrupados por partido.")

if df_votos_nominais.empty:
    st.error("ERRO: Não foi possível carregar a lista de votos nominais. A API da Câmara não retornou dados para /votos.")
else:
    # Agrupa votos para o gráfico de barras
    df_votos_agrupados = agrupar_votos_por_partido(df_votos_nominais.copy())
    
    # CALCULA E EXIBE O TOTAL GERAL DE VOTOS REGISTRADOS
    total_votos_registrados = df_votos_agrupados['Total Votos'].sum()

    st.metric("Total de Votos Registrados na Votação Nominal", f"{total_votos_registrados:,}".replace(",", "."))
    
    st.markdown("---")
    
    # Gráfico de Barras por Partido
    df_votos_plot = df_votos_agrupados.drop(columns=['Total Votos', 'Outro'])
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

st.markdown("---")
st.success("Análise de transparência finalizada.")
