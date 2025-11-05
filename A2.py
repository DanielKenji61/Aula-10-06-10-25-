import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import date

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_BASE_PROPOSICOES = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

# Período de análise solicitado: Jan a Out de 2025
ANO_ALVO = 2025
DATA_INICIO_ALVO = f'{ANO_ALVO}-01-01'
DATA_FIM_ALVO = f'{ANO_ALVO}-10-31' 

# Códigos de Referência na API (Reais)
CODIGO_PL = 207      
SITUACAO_APROVADA = 300  # Transf. em Norma Jurídica / Aprovada nas 2 Casas
SITUACAO_TODAS = None    # Para contar o total apresentado

# --- 2. FUNÇÕES DE BUSCA DA API (MÁXIMA EFICIÊNCIA) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600) # Cache de 1 hora
def contar_proposicoes_reais(cod_tipo, id_situacao=None):
    """
    Faz a chamada real à API da Câmara para contar proposições no período Jan-Out/2025.
    Otimizada para fazer o mínimo de requisições.
    """
    
    params = {
        'dataInicio': DATA_INICIO_ALVO,
        'dataFim': DATA_FIM_ALVO,
        'codTipo': cod_tipo,
        'ordenarPor': 'id', 
        'itens': 100, # Max de itens por página
    }
    
    if id_situacao is not None:
        params['idSituacao'] = id_situacao
        
    total_proposicoes = 0
    pagina = 1
    
    # Tentativa de obter o total em até 3 páginas para evitar timeout
    for pagina in range(1, 4): 
        try:
            response = requests.get(URL_BASE_PROPOSICOES, params={**params, 'pagina': pagina})
            response.raise_for_status() 
            dados = response.json().get('dados', [])
            total_proposicoes += len(dados)
            
            if len(dados) < params['itens']:
                break
            
            time.sleep(0.1) 
            
        except requests.exceptions.RequestException as e:
            # Se falhar na primeira tentativa, encerramos a busca e avisamos.
            st.error(f"Falha na conexão com a API da Câmara. Erro: {e}")
            return 0
            
    return total_proposicoes

# --- 3. FUNÇÕES DE GERAÇÃO DE GRÁFICOS ---

def criar_grafico_funil_sucesso(total_propostos, total_aprovados):
    """Gráfico Funil/Pizza: Taxa de Sucesso (Aprovados vs. Outras Situações)."""
    
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

st.title("🔥 Jurimetria de Alto Risco: Desempenho Legislativo")
st.header(f"Projetos de Lei (PLs) - Dados Reais da Câmara ({DATA_INICIO_ALVO} a {DATA_FIM_ALVO})")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use se os dados globais não se atualizarem.")

st.markdown("---")

# --- BLOCO PRINCIPAL: TAXA DE CONVERSÃO TOTAL ---

st.subheader("Taxa de Conversão Total: Propostos vs. Aprovados (Jan a Out/2025)")

with st.spinner("Buscando dados reais na API da Câmara..."):
    
    # 1. Total de PLs Propostos (Jan-Out)
    total_pl_proposto = contar_proposicoes_reais(
        CODIGO_PL, 
        SITUACAO_TODAS
    )

    # 2. Total de PLs Aprovados (Jan-Out)
    total_pl_aprovado = contar_proposicoes_reais(
        CODIGO_PL, 
        SITUACAO_APROVADA
    )
    
# Processamento e Exibição
if total_pl_proposto == 0 and total_pl_aprovado == 0:
    st.error("ERRO CRÍTICO: Não foi possível obter dados reais da API da Câmara. O servidor está inoperante ou limitando o acesso. Favor tentar novamente em alguns minutos ou usar uma alternativa.")
else:
    taxa_sucesso = (total_pl_aprovado / total_pl_proposto) * 100 if total_pl_proposto > 0 else 0

    # --- KPIs ---
    col_prop, col_aprov, col_taxa = st.columns(3)

    col_prop.metric("PLs Propostos (Total)", f"{total_pl_proposto:,}".replace(",", "."))
    col_aprov.metric("PLs Aprovados (Final)", f"{total_pl_aprovado:,}".replace(",", "."))
    col_taxa.metric("Taxa de Conversão", f"{taxa_sucesso:.2f}%")

    st.markdown("---")
    
    # Gráfico B: Funil de Sucesso
    if total_pl_proposto > 0:
        fig_b = criar_grafico_funil_sucesso(total_pl_proposto, total_pl_aprovado)
        st.plotly_chart(fig_b, use_container_width=True)
    
st.markdown("---")
st.success("Análise finalizada. Se o número for 0, o servidor da Câmara não respondeu.")
