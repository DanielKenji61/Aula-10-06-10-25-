import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS (URLs Fixas) ---

ID_PROPOSICAO = "2270800"
ID_VOTACAO = "2270800-175" 

URL_API_BASE = "https://dadosabertos.camara.leg.br/api/v2/"
URL_PROPOSICAO_DETALHE = f"{URL_API_BASE}proposicoes/{ID_PROPOSICAO}"
URL_VOTOS = f"{URL_API_BASE}votacoes/{ID_VOTACAO}/votos"

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
        st.error(f"Falha ao acessar API: {url}. Erro: {e}")
        return None

@st.cache_data(ttl=3600)
def obter_dados_juridicos():
    """Busca Título, Ementa e Situação Final da PEC."""
    dados = buscar_dados(URL_PROPOSICAO_DETALHE)
    if dados:
        titulo = dados.get('siglaTipo', 'PEC') + ' ' + str(dados.get('numero', '03')) + '/' + str(dados.get('ano', '2021'))
        ementa = dados.get('ementa', 'Ementa não disponível.')
        
        # A situação final pode ser encontrada na descrição (ex: "Aprovada e enviada ao Senado")
        status_final = dados.get('statusProposicao', {}).get('descricaoSituacao', 'Em Tramitação')
        
        # Classificação do Status Jurídico (simplificada)
        if 'promulgada' in status_final.lower() or 'sancionada' in status_final.lower() or 'transformada em norma' in status_final.lower():
            status_juridico = "APROVADA (Lei/Emenda)"
            status_cor = "green"
        elif 'rejeitada' in status_final.lower() or 'arquivamento' in status_final.lower():
            status_juridico = "REJEITADA/ARQUIVADA"
            status_cor = "red"
        else:
            status_juridico = "EM TRAMITAÇÃO"
            status_cor = "orange"
        
        return titulo, ementa, status_juridico, status_cor
    return "PEC 03/2021", "Ementa não disponível.", "ERRO DE DADOS", "red"

def processar_votos_nominais_tabela(dados_votos):
    """Processa o JSON de votos nominais em um DataFrame para TABELA NOMINAL."""
    if not dados_votos or not dados_votos.get('dados'):
        return pd.DataFrame()

    df = pd.DataFrame(dados_votos['dados'])
    
    # Extrair campos chave diretamente
    df['Nome do Deputado'] = df['deputado'].apply(lambda x: x['nome'])
    df['Partido'] = df['deputado'].apply(lambda x: x['siglaPartido'])
    df['UF'] = df['deputado'].apply(lambda x: x['siglaUf'])
    df['Voto Nominal'] = df['tipoVoto']
    
    # Colunas para o relatório final
    return df[['Nome do Deputado', 'Partido', 'UF', 'Voto Nominal']]

# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Análise PEC 03/2021")

# Carregamento dos dados jurídicos
titulo, ementa, status_juridico, status_cor = obter_dados_juridicos()
dados_votos_raw = buscar_dados(URL_VOTOS)
df_votos_nominais = processar_votos_nominais_tabela(dados_votos_raw)

st.title("⚖️ Monitor de Transparência: PEC 03/2021")
st.header("Relatório Jurídico e Votação Nominal Aberta")

st.sidebar.button("Resetar Cache da API", on_click=limpar_cache_api)
st.markdown("---")

# =========================================================
# SEÇÃO 1: STATUS JURÍDICO (KPI Principal)
# =========================================================

col_titulo, col_status = st.columns([3, 1])

with col_titulo:
    st.subheader(f"Proposta: {titulo}")
    st.markdown(f"> **Ementa:** {ementa}")
    st.caption("Ementa buscada via API da Câmara dos Deputados.")

with col_status:
    st.markdown("#### Situação Final:")
    st.markdown(
        f"<div style='background-color: {status_cor}; color: white; padding: 10px; border-radius: 5px; text-align: center;'><b>{status_juridico}</b></div>", 
        unsafe_allow_html=True
    )

st.markdown("---")

# =========================================================
# SEÇÃO 2: RELATÓRIO NOMINAL DE VOTAÇÃO
# =========================================================

st.subheader("Votação Nominal Aberta (Registro de Cada Parlamentar)")
st.caption(f"Esta tabela mostra o voto individual de cada deputado na votação {ID_VOTACAO} (Substitutivo em 1º Turno).")

if df_votos_nominais.empty:
    st.error("Não foi possível carregar a lista de votos nominais. A API pode estar limitando o acesso aos dados brutos.")
else:
    # 1. Gráfico de Pizza (Síntese)
    contagem_votos = df_votos_nominais['Voto Nominal'].value_counts().reset_index()
    contagem_votos.columns = ['Voto', 'Total']

    fig_pizza = px.pie(
        contagem_votos,
        values='Total',
        names='Voto',
        title='Proporção Global de Votos Registrados',
        hole=.5,
        color_discrete_map={'Sim': 'green', 'Não': 'red', 'Abstenção': 'gold', 'Obstrução': 'darkred', 'Ausente': 'grey'}
    )
    st.plotly_chart(fig_pizza, use_container_width=True)

    # 2. Tabela Nominal Interativa
    st.markdown("##### Lista Nominal (Voto por Parlamentar):")
    st.dataframe(
        df_votos_nominais,
        use_container_width=True,
        hide_index=True,
        # Permite ao usuário filtrar e ordenar por Partido ou Voto Nominal
    )

st.markdown("---")
st.success("Análise de transparência concluída.")
