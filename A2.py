import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time
from urllib.parse import urlparse

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS (URLs Fixas) ---

ID_PROPOSICAO = "2387114"
ID_VOTACAO = "2387114-177" 
ID_PL_ATIVO = 37905
LEGISLATURA_ALVO = 57

URL_API_BASE = "https://dadosabertos.camara.leg.br/api/v2/"
URL_VOTOS = f"{URL_API_BASE}votacoes/{ID_VOTACAO}/votos"
URL_MEMBROS_PL_57 = f"{URL_API_BASE}partidos/{ID_PL_ATIVO}/membros?idLegislatura={LEGISLATURA_ALVO}"
URL_PROPOSICAO_DETALHE = f"{URL_API_BASE}proposicoes/{ID_PROPOSICAO}"

# Variável de Controle (Para você inserir a Ementa)
EMENTA_CUSTOMIZADA = "" # Deixe em branco; você pode inserir aqui o resumo.
STATUS_APROVADO = "Aprovado" # Usado como referência para o status da votação

# --- 2. FUNÇÕES DE BUSCA E PROCESSAMENTO ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def buscar_dados(url):
    """Função robusta para buscar dados da API e retornar JSON."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

@st.cache_data(ttl=3600)
def obter_dados_juridicos_e_votos():
    """Busca o status da votação e os votos nominais."""
    
    # 1. Busca STATUS DA VOTAÇÃO (para saber se foi Aprovada)
    dados_votacao = buscar_dados(f"{URL_API_BASE}votacoes/{ID_VOTACAO}")
    status_aprovacao = "N/A"
    if dados_votacao:
        # Tenta extrair a aprovação da votação
        status_aprovacao = dados_votacao.get('aprovacao', 'Não Registrado')
        
    # 2. Busca VOTOS NOMINAIS
    dados_votos_raw = buscar_dados(URL_VOTOS)
    
    # 3. Processa a lista de votos nominais
    if not dados_votos_raw or not dados_votos_raw.get('dados'):
        df_votos = pd.DataFrame()
    else:
        lista_votos = dados_votos_raw.get('dados', [])
        
        dados_tabela = []
        for voto in lista_votos:
            deputado_info = voto.get('deputado', {})
            dados_tabela.append({
                'Nome do Deputado': deputado_info.get('nome', 'N/A'),
                'Partido': deputado_info.get('siglaPartido', 'N/A'),
                'ID Deputado': deputado_info.get('id', 0), # Usado para comparação
                'Voto Nominal': voto.get('tipoVoto', 'N/A')
            })
        df_votos = pd.DataFrame(dados_tabela)
        
    return df_votos, status_aprovacao

@st.cache_data(ttl=3600)
def buscar_membros_pl_ids(url_membros):
    """Busca os IDs de todos os membros do PL na 57ª Legislatura."""
    dados = buscar_dados(url_membros)
    if dados and dados.get('dados'):
        # Retorna um set de IDs para busca rápida
        return {membro.get('id') for membro in dados['dados'] if membro.get('id')}
    return set()

# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Monitor PLP 177/2023")

st.title("⚖️ Análise de Votação: PLP 177/2023")
st.header("Fidelidade Partidária do Partido Liberal (PL)")

# --- EXECUÇÃO PRINCIPAL DE BUSCA ---
df_votos_nominais, status_aprovacao = obter_dados_juridicos_e_votos()
membros_pl_ids = buscar_membros_pl_ids(URL_MEMBROS_PL_57)
st.sidebar.button("Resetar Cache da API", on_click=limpar_cache_api)
st.markdown("---")

# =========================================================
# SEÇÃO 1: STATUS JURÍDICO E EMENTA (Input Manual)
# =========================================================

col_proposta, col_status_box = st.columns([3, 1])

with col_proposta:
    st.subheader("PLP 177/2023")
    st.markdown("#### Ementa:")
    
    # Input para você colar o resumo da Ementa
    ementa_resumo = st.text_area(
        "Resumo da Ementa (Edite para adicionar o texto):",
        value=EMENTA_CUSTOMIZADA or "Aguardando Ementa Jurídica..." ,
        height=100
    )

with col_status_box:
    st.markdown("#### Votação em Plenário:")
    
    # Define a cor do status
    if status_aprovacao == STATUS_APROVADO:
        status_display = "APROVADO"
        status_cor = "green"
    elif status_aprovacao == "Rejeitado":
        status_display = "REJEITADO"
        status_cor = "red"
    else:
        status_display = "NÃO REGISTRADO / EM ANDAMENTO"
        status_cor = "orange"
        
    st.markdown(
        f"<div style='background-color: {status_cor}; color: white; padding: 10px; border-radius: 5px; text-align: center;'><b>{status_display}</b></div>", 
        unsafe_allow_html=True
    )
    
st.markdown("---")

# =========================================================
# SEÇÃO 2: GRÁFICOS E ANÁLISE DE FIDELIDADE (Dados Reais)
# =========================================================

if df_votos_nominais.empty:
    st.error("ERRO: Não foi possível carregar os votos nominais. O ID da votação pode estar incorreto ou a API falhou.")
else:
    # 1. PRÉ-PROCESSAMENTO: Agrupamento de Votos
    df_votos_agrupados = df_votos_nominais.copy()
    
    df_votos_agrupados['Sim'] = df_votos_agrupados['Voto Nominal'].apply(lambda x: 1 if x == 'Sim' else 0)
    df_votos_agrupados['Não'] = df_votos_agrupados['Voto Nominal'].apply(lambda x: 1 if x == 'Não' else 0)
    df_votos_agrupados['Abstenção'] = df_votos_agrupados['Voto Nominal'].apply(lambda x: 1 if x == 'Abstenção' else 0)

    # 2. ANÁLISE PL: Identifica e conta os votos do PL
    
    # Deputados do PL que votaram (Filtra pelo ID e pelo Partido na lista de votos)
    df_pl_votos = df_votos_agrupados[
        (df_votos_agrupados['Partido'] == 'PL') & 
        (df_votos_agrupados['ID Deputado'].isin(membros_pl_ids))
    ]
    
    # Contagem final
    total_pl_votos = df_pl_votos.shape[0]
    pl_sim = df_pl_votos['Sim'].sum()
    pl_nao = df_pl_votos['Não'].sum()
    
    # Contagem Global
    contagem_global = df_votos_agrupados.groupby('Voto Nominal').size()
    total_votos_registrados = contagem_global.sum()
    
    # --- KPIs e Totais ---
    st.subheader("Total de votos em plenário")

    col_geral_total, col_pl_total, col_pl_sim, col_pl_nao = st.columns(4)

    with col_geral_total:
        st.metric("Total de Votos Registrados", f"{total_votos_registrados:,}".replace(",", "."))
    
    with col_pl_total:
        st.metric("Total de Votos da Bancada PL", total_pl_votos)
        
    with col_pl_sim:
        st.metric("Votos PL: A Favor (Sim)", pl_sim)
        
    with col_pl_nao:
        st.metric("Votos PL: Contra (Não)", pl_nao)

    st.markdown("---")
    
    # 3. GRÁFICO: Votação Global (Pizza/Donut)
    st.subheader("1. Distribuição Global dos Votos em Plenário")

    df_pizza = contagem_global.reset_index(name='Total')
    
    fig_pizza = px.pie(
        df_pizza,
        values='Total',
        names='Voto Nominal',
        title='Proporção Total de Votos Registrados (Sim, Não, Abstenção)',
        hole=.5,
        color_discrete_map={'Sim': 'green', 'Não': 'red', 'Abstenção': 'gold', 'Obstrução': 'darkred', 'Ausente': 'grey'}
    )
    st.plotly_chart(fig_pizza, use_container_width=True)

    st.markdown("---")

    # 4. GRÁFICO: Fidelidade PL (Barras)
    st.subheader("2. Fidelidade Partidária da Bancada PL (A Favor vs. Contra)")

    df_fidelidade = pd.DataFrame({
        'Posição': ['A Favor', 'Contra', 'Abstenção/Outro'],
        'Total': [pl_sim, pl_nao, total_pl_votos - pl_sim - pl_nao]
    })
    
    fig_fidelidade = px.bar(
        df_fidelidade,
        x='Posição',
        y='Total',
        color='Posição',
        title='Votos do Partido Liberal (PL) na Votação Nominal',
        color_discrete_map={'A Favor': 'green', 'Contra': 'red', 'Abstenção/Outro': 'gold'}
    )
    st.plotly_chart(fig_fidelidade, use_container_width=True)

st.markdown("---")
st.success("Análise de transparência concluída e pronta para uso.")
