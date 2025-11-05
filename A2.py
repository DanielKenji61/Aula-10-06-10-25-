import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date
import time
from urllib.parse import quote

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_BASE_PROPOSICOES = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
# Definimos o período de análise conforme solicitado: Jan a Out de 2025
ANO_ALVO = 2025
DATA_INICIO_ALVO = f'{ANO_ALVO}-01-01'
DATA_FIM_ALVO = f'{ANO_ALVO}-10-31' 

# Códigos de Referência na API (Reais)
CODIGO_PL = 207      
SITUACAO_APROVADA = 300  # Transf. em Norma Jurídica / Aprovada nas 2 Casas
SITUACAO_TODAS = None    # Para contar o total apresentado

# Definição dos Trimestres para a Análise Trimestral
TRIMESTRES = {
    '1º Trimestre (Jan-Mar)': {'dataInicio': f'{ANO_ALVO}-01-01', 'dataFim': f'{ANO_ALVO}-03-31'},
    '2º Trimestre (Abr-Jun)': {'dataInicio': f'{ANO_ALVO}-04-01', 'dataFim': f'{ANO_ALVO}-06-30'},
    '3º Trimestre (Jul-Set)': {'dataInicio': f'{ANO_ALVO}-07-01', 'dataFim': f'{ANO_ALVO}-09-30'},
    # Outubro é o 4º período, pois o último mês é parcial
    '4º Período (Out)': {'dataInicio': f'{ANO_ALVO}-10-01', 'dataFim': f'{ANO_ALVO}-10-31'}, 
}

# --- 2. FUNÇÕES DE BUSCA DA API (DADOS REAIS E ROBUSTOS) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600) # Cache de 1 hora
def contar_proposicoes_reais(cod_tipo, id_situacao=None, data_inicio_fixa=None, data_fim_fixa=None):
    """
    Faz a chamada real à API da Câmara para contar proposições dentro de um período fixo.
    """
    
    # Validação do período
    if not data_inicio_fixa or not data_fim_fixa:
        return 0 
    
    params = {
        'dataInicio': data_inicio_fixa,
        'dataFim': data_fim_fixa,
        'codTipo': cod_tipo,
        'ordenarPor': 'id', 
        'itens': 100, 
    }
    
    if id_situacao is not None:
        params['idSituacao'] = id_situacao
        
    total_proposicoes = 0
    pagina = 1
    
    # Paginação para garantir que todos os dados sejam coletados
    while True:
        try:
            response = requests.get(URL_BASE_PROPOSICOES, params={**params, 'pagina': pagina})
            response.raise_for_status() 
            dados = response.json().get('dados', [])
            total_proposicoes += len(dados)
            
            if len(dados) < params['itens']:
                break
            
            pagina += 1
            time.sleep(0.1) 
            
        except requests.exceptions.RequestException as e:
            # Em caso de erro na API, retorna 0 para evitar quebra do programa
            return 0
            
    return total_proposicoes

# --- 3. FUNÇÕES DE PROCESSAMENTO E GRÁFICOS ---

def criar_grafico_volume_trimestral(df_dados):
    """Gráfico A: Volume de PLs Apresentados por Trimestre."""
    
    fig = px.bar(
        df_dados,
        x='Trimestre',
        y='Total',
        color='Total',
        title=f'A. Volume de Projetos de Lei (PLs) Propostos por Período em {ANO_ALVO}',
        labels={'Total': 'PLs Propostos', 'Trimestre': 'Período'},
        color_continuous_scale=px.colors.sequential.Teal
    )
    fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray': list(TRIMESTRES.keys())})
    return fig

def criar_grafico_funil_sucesso(total_propostos, total_aprovados):
    """Gráfico B: Funil de Sucesso (Aprovados vs. Outras Situações)."""
    
    total_outras_situacoes = total_propostos - total_aprovados
    
    df_funil = pd.DataFrame({
        'Situação': ['Aprovados (Sucesso)', 'Outras Situações (Tramitando/Arquivado)'],
        'Total': [total_aprovados, total_outras_situacoes]
    })
    
    fig = px.pie(
        df_funil,
        values='Total',
        names='Situação',
        title=f'B. Taxa de Conversão de PLs (Propostos vs. Aprovados) em {ANO_ALVO}',
        hole=.5, # Gráfico Donut
        color_discrete_sequence=['green', 'darkred']
    )
    fig.update_traces(textinfo='percent+label', pull=[0.1, 0])
    return fig

# --- 4. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Termômetro Legislativo 2025")

st.title("🌡️ Termômetro de Produtividade Legislativa")
st.header(f"Análise de Projetos de Lei (PLs) - {ANO_ALVO}")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use se os dados não se atualizarem.")

st.markdown("---")

# --- BLOCO 1: ANÁLISE TRIMESTRAL (GRÁFICO A) ---

st.subheader("1. Volume de Propostas Apresentadas (Análise Trimestral)")
st.caption("Acompanhamento da Produtividade em PLs ao longo de 2025 (Dados Reais da API da Câmara).")

with st.spinner("Buscando dados trimestrais na API..."):
    dados_trimestrais = []
    
    for nome_trimestre, datas in TRIMESTRES.items():
        total = contar_proposicoes_reais(
            CODIGO_PL, 
            SITUACAO_TODAS, 
            data_inicio_fixa=datas['dataInicio'], 
            data_fim_fixa=datas['dataFim']
        )
        dados_trimestrais.append({'Trimestre': nome_trimestre, 'Total': total})

    df_trimestral = pd.DataFrame(dados_trimestrais)

# Gráfico A: Volume Trimestral
if df_trimestral['Total'].sum() > 0:
    fig_a = criar_grafico_volume_trimestral(df_trimestral)
    st.plotly_chart(fig_a, use_container_width=True)
else:
    st.error("Não foi possível carregar dados da API para o período de 2025. Tente limpar o cache.")

st.markdown("---")

# --- BLOCO 2: TAXA DE CONVERSÃO TOTAL (GRÁFICO B) ---

st.subheader("2. Taxa de Sucesso: Propostos vs. Aprovados (Jan a Out/2025)")

with st.spinner("Calculando taxa de conversão total..."):
    
    # 1. Total de PLs Propostos (Jan-Out)
    total_pl_proposto = contar_proposicoes_reais(
        CODIGO_PL, 
        SITUACAO_TODAS, 
        data_inicio_fixa=DATA_INICIO_ALVO, 
        data_fim_fixa=DATA_FIM_ALVO
    )

    # 2. Total de PLs Aprovados (Jan-Out)
    total_pl_aprovado = contar_proposicoes_reais(
        CODIGO_PL, 
        SITUACAO_APROVADA, 
        data_inicio_fixa=DATA_INICIO_ALVO, 
        data_fim_fixa=DATA_FIM_ALVO
    )
    
    taxa_sucesso = (total_pl_aprovado / total_pl_proposto) * 100 if total_pl_proposto > 0 else 0

    col_prop, col_aprov, col_taxa = st.columns(3)

    col_prop.metric("PLs Propostos (Jan-Out)", f"{total_pl_proposto:,}".replace(",", "."))
    col_aprov.metric("PLs Aprovados (Jan-Out)", f"{total_pl_aprovado:,}".replace(",", "."))
    col_taxa.metric("Taxa de Aprovação", f"{taxa_sucesso:.2f}%")

    # Gráfico B: Funil de Sucesso
    if total_pl_proposto > 0:
        fig_b = criar_grafico_funil_sucesso(total_pl_proposto, total_pl_aprovado)
        st.plotly_chart(fig_b, use_container_width=True)
    else:
        st.info("Dados insuficientes para calcular a Taxa de Sucesso.")

st.markdown("---")
st.success("Análise de Jurimetria concluída com dados reais da API da Câmara dos Deputados.")
