import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_API_PROPOSICOES_V2 = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
CODIGO_PEC = 304     # Código para Proposta de Emenda à Constituição
SITUACAO_APROVADA_FINAL = 300 

ANO_ATUAL_REAL = date.today().year
MES_ATUAL = date.today().month

# --- 2. FUNÇÕES DE BUSCA (REAPROVEITAMENTO E NOVAS) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600) 
def contar_pecs_por_situacao(ano, id_situacao=None, buscar_ids=False):
    """
    Busca o total de PECs com ou sem filtro de situação.
    Se 'buscar_ids' for True, retorna a lista de IDs para amostragem.
    """
    data_inicio = f'{ano}-01-01'
    data_fim = date.today().strftime('%Y-%m-%d') if ano == ANO_ATUAL_REAL else f'{ano}-12-31'
    
    params = {
        'dataInicio': data_inicio,
        'dataFim': data_fim,
        'codTipo': CODIGO_PEC,
        'ordenarPor': 'id',
        'itens': 100, 
    }
    
    if id_situacao is not None:
        params['idSituacao'] = id_situacao
        
    total_proposicoes = 0
    pagina = 1
    lista_ids = []
    
    while True:
        try:
            # Limita a busca a 2 páginas se for apenas para IDs de amostragem
            if buscar_ids and pagina > 2:
                 break
            
            response = requests.get(URL_API_PROPOSICOES_V2, params={**params, 'pagina': pagina}, timeout=10)
            response.raise_for_status() 
            dados = response.json().get('dados', [])
            
            if buscar_ids:
                lista_ids.extend([d['id'] for d in dados])
            
            total_proposicoes += len(dados)
            
            if len(dados) < params['itens'] or (buscar_ids and pagina >= 2):
                break
            
            pagina += 1
            time.sleep(0.05) 
            
        except requests.exceptions.RequestException:
            return lista_ids if buscar_ids else 0
            
    return lista_ids if buscar_ids else total_proposicoes

@st.cache_data(ttl=3600)
def analise_longitudinal(anos_a_analisar):
    """
    (NOVA ANÁLISE ROBUSTA) Contagem total de PECs por ano (Tendência).
    """
    dados_longitudinais = []
    for ano in anos_a_analisar:
        # Reutiliza a função de contagem principal
        total = contar_pecs_por_situacao(ano) 
        dados_longitudinais.append({'Ano': str(ano), 'Total de PECs': total})
    return pd.DataFrame(dados_longitudinais)

@st.cache_data(ttl=3600)
def analise_orgao_amostral(ano):
    """
    (NOVA ANÁLISE ROBUSTA) Busca uma AMOSTRA de PECs e classifica a tramitação 
    pela sigla do Órgão/Comissão (Bottleneck).
    """
    st.info("Buscando amostra de 200 PECs para análise de Órgão/Comissão...")
    
    # Busca IDs (limita a 2 páginas na função de contagem)
    lista_ids = contar_pecs_por_situacao(ano, buscar_ids=True)
            
    if not lista_ids:
        return pd.DataFrame()

    dados_orgao = []
    
    # Processa apenas os primeiros 200 IDs para evitar Timeout
    for id_pec in lista_ids[:200]: 
        try:
            url_detalhe = f"{URL_API_PROPOSICOES_V2}/{id_pec}"
            response = requests.get(url_detalhe, timeout=5)
            detalhe = response.json()
            
            # Extrai o ÓRGÃO/COMISSÃO que está com a PEC (onde ela está parada)
            sigla_orgao = detalhe.get('statusProposicao', {}).get('siglaOrgao', 'Sem Órgão Designado')
            
            dados_orgao.append({'Órgão Responsável': sigla_orgao, 'Total': 1})
            
            time.sleep(0.05) 
            
        except:
            continue
            
    if not dados_orgao:
        return pd.DataFrame()
        
    df_amostra = pd.DataFrame(dados_orgao)
    # Agrupa e conta o total por Órgão
    return df_amostra.groupby('Órgão Responsável').sum().reset_index()


# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Análise de PECs - Câmara dos Deputados")

st.title("🏛️ Análise Jurimétrica da Produtividade Legislativa")
st.header("Propostas de Emenda à Constituição (PECs)")

# --- SIDEBAR E CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api) 
    st.caption("Use se os dados parecerem desatualizados ou incompletos.")

st.markdown("---")

# --- SELETOR DE ANO ---
st.subheader("Selecione o Ano para Análise Específica:")
anos_disponiveis = [2024, 2023] 

ano_selecionado = st.radio(
    "Escolha o ano base:",
    anos_disponiveis,
    index=0, 
    format_func=lambda x: f"Ano {x}", 
    horizontal=True
)

st.markdown("---")

# =========================================================================
# SEÇÃO 1: GRÁFICO LONGITUDINAL (NOVA IDEIA)
# =========================================================================
st.subheader("1. Tendência Histórica: Volume de PECs Protocoladas (2019-2024)")
st.caption("Esta análise robusta mostra a evolução do trabalho legislativo ao longo do tempo, sem depender de 'situações finais'.")

with st.spinner("Buscando dados longitudinais (2019 até hoje)..."):
    anos_historicos = list(range(2019, ANO_ATUAL_REAL + 1))
    df_longitudinal = analise_longitudinal(anos_historicos)

if df_longitudinal.empty or df_longitudinal['Total de PECs'].sum() == 0:
    st.error("Falha ao buscar dados históricos. A API pode estar indisponível.")
else:
    fig_longitudinal = px.line(
        df_longitudinal,
        x='Ano',
        y='Total de PECs',
        title='Volume de Propostas de Emenda à Constituição (PECs) - Últimos 6 Anos',
        markers=True,
        line_shape='linear',
        color_discrete_sequence=['darkblue']
    )
    fig_longitudinal.update_layout(yaxis={'title': 'Total de PECs Protocoladas'})
    st.plotly_chart(fig_longitudinal, use_container_width=True)


st.markdown("---")

# =========================================================================
# SEÇÃO 2: GRÁFICO DE PIZZA (ANÁLISE DE BOTTLENECK - NOVA IDEIA)
# =========================================================================

st.subheader(f"2. Análise de Bottleneck: Onde as PECs estão Paradas? ({ano_selecionado})")
st.caption("Mostra em qual Órgão ou Comissão a PEC está aguardando, revelando os principais gargalos da tramitação. (Amostragem de dados)")

with st.spinner(f"Analisando em tempo real os Órgãos responsáveis por uma amostra de PECs de {ano_selecionado}..."):
    df_orgao_atual = analise_orgao_amostral(ano_selecionado)

if df_orgao_atual.empty:
    st.warning("Não foi possível coletar a amostra para a análise de bottleneck. A API de detalhe está limitando as chamadas.")
else:
    # Filtra os órgãos com maior representatividade (acima de 2% para clareza)
    total_amostra = df_orgao_atual['Total'].sum()
    df_orgao_filtrado = df_orgao_atual[df_orgao_atual['Total'] / total_amostra > 0.02]
    
    # Agrupa o restante em "Outros"
    total_outros = total_amostra - df_orgao_filtrado['Total'].sum()
    if total_outros > 0:
        df_outros = pd.DataFrame([{'Órgão Responsável': 'Outros Órgãos/Comissões (Menos de 2%)', 'Total': total_outros}])
        df_orgao_filtrado = pd.concat([df_orgao_filtrado, df_outros], ignore_index=True)
    
    fig_pizza_orgao = px.pie(
        df_orgao_filtrado,
        values='Total',
        names='Órgão Responsável',
        title=f'Distribuição de PECs pelo Órgão/Comissão Responsável ({ano_selecionado})',
        hole=.5,
    )
    st.plotly_chart(fig_pizza_orgao, use_container_width=True)

    # Tabela de Detalhamento
    st.markdown("##### Detalhamento do Órgão Responsável (Bottleneck):")
    st.dataframe(df_orgao_filtrado.sort_values(by='Total', ascending=False), use_container_width=True, hide_index=True)

st.markdown("---")
st.success("Estes gráficos são robustos e fornecem insights reais sobre a dinâmica legislativa da Câmara!")
