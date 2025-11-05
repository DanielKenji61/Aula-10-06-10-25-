import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

# Endpoint da API REST v2 da Câmara dos Deputados
URL_API_PROPOSICOES_V2 = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

# Código ÚNICO para Proposta de Emenda à Constituição (PEC)
CODIGO_PEC = 304     

# Códigos de Situação (Usados para o Gráfico de Pizza)
SITUACAO_APROVADA = 300  # Transf. em Norma Jurídica / Aprovada nas 2 Casas
SITUACAO_ARQUIVADA = 239 # Arquivada

# O ano e mês atual
ANO_ATUAL_REAL = date.today().year
MES_ATUAL = date.today().month

# --- 2. FUNÇÕES DE BUSCA (DADOS REAIS DA API) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600) 
def contar_pecs_por_situacao(ano, id_situacao=None):
    """
    Busca o total de PECs com uma situação final específica (Aprovadas, Arquivadas, ou Total Apresentado).
    Esta função é mais eficiente porque não busca todos os meses.
    """
    
    data_inicio = f'{ano}-01-01'
    data_fim = f'{ano}-12-31'
    
    if ano == ANO_ATUAL_REAL:
        data_fim = date.today().strftime('%Y-%m-%d')
    
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
    
    # Lógica de paginação para contar o total
    while True:
        try:
            response = requests.get(URL_API_PROPOSICOES_V2, params={**params, 'pagina': pagina}, timeout=10)
            response.raise_for_status() 
            dados = response.json().get('dados', [])
            total_proposicoes += len(dados)
            
            if len(dados) < params['itens']:
                break
            
            pagina += 1
            time.sleep(0.05) 
            
        except requests.exceptions.RequestException:
            return 0
            
    return total_proposicoes

@st.cache_data(ttl=3600) 
def buscar_pecs_mensais(ano):
    """
    Busca o total de PECs para cada mês do ano. (Para o Gráfico 1)
    """
    dados_mensais = []
    nome_tipo = 'Emenda à Constituição (PEC)'
    
    if ano == ANO_ATUAL_REAL:
        mes_limite = MES_ATUAL 
    else:
        mes_limite = 12

    for mes in range(1, mes_limite + 1):
        
        data_inicio = date(ano, mes, 1)
        
        if mes == MES_ATUAL and ano == ANO_ATUAL_REAL:
             data_fim = date.today()
        elif mes == 12:
            data_fim = date(ano, 12, 31)
        else:
            data_fim = data_inicio + relativedelta(months=1) - relativedelta(days=1)
        
        params = {
            'dataInicio': data_inicio.strftime('%Y-%m-%d'),
            'dataFim': data_fim.strftime('%Y-%m-%d'),
            'codTipo': CODIGO_PEC,
            'ordenarPor': 'id',
            'itens': 100, 
        }
        
        total_no_mes = 0
        pagina = 1
        
        while True:
            try:
                response = requests.get(URL_API_PROPOSICOES_V2, params={**params, 'pagina': pagina}, timeout=10)
                response.raise_for_status() 
                dados = response.json().get('dados', [])
                total_no_mes += len(dados)
                
                if len(dados) < params['itens']:
                    break
                
                pagina += 1
                time.sleep(0.05) 
                
            except requests.exceptions.RequestException:
                break 
                
        dados_mensais.append({
            'Mês': date(2000, mes, 1).strftime('%b/%Y' if ano != 2024 else '%b'), 
            'Ordem_Mes': mes,
            'Total': total_no_mes,
            'Tipo': nome_tipo
        })
            
    return pd.DataFrame(dados_mensais)

# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Análise de PECs - Câmara dos Deputados")

st.title("🏛️ Análise da Produtividade Legislativa (Foco em PECs)")
st.header("Propostas de Emenda à Constituição (2023 vs. 2024)")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use se os dados não se atualizarem ou se o Streamlit falhar.")

st.markdown("---")

# --- SELETOR DE ANO ---
st.subheader("Selecione o Ano para Análise:")
anos_disponiveis = [2024, 2023] 

ano_selecionado = st.radio(
    "Escolha o ano base para visualizar as informações:",
    anos_disponiveis,
    index=0, 
    format_func=lambda x: f"Ano {x}", 
    horizontal=True
)

st.markdown("---")

# =========================================================================
# SEÇÃO 1: GRÁFICO MENSAL (Volume de Propostas)
# =========================================================================

with st.spinner(f'Buscando dados mensais reais da API para PECs de {ano_selecionado}...'):
    df_pec_mensal = buscar_pecs_mensais(ano_selecionado)

if df_pec_mensal.empty or df_pec_mensal['Total'].sum() == 0:
    st.error(f"Não há registros de PECs para {ano_selecionado} na base de dados da API ou houve falha na conexão.")
    st.stop() # Interrompe a execução se não houver dados

total_pec_anual = df_pec_mensal['Total'].sum()

st.subheader(f"1. Volume Mensal de Emendas à Constituição (PECs) em {ano_selecionado}")
st.caption("Gráfico de Barras: Número de Propostas de Emenda à Constituição (PECs) apresentadas por mês.")

df_pec_mensal = df_pec_mensal.sort_values(by='Ordem_Mes')

fig_pec_mensal = px.bar(
    df_pec_mensal,
    x='Mês',
    y='Total',
    color_discrete_sequence=['red'], 
    title=f'PECs Apresentadas Mês a Mês em {ano_selecionado}',
    labels={'Total': 'Número de PECs', 'Mês': 'Mês de Apresentação'},
)
fig_pec_mensal.update_layout(
    xaxis={'categoryorder': 'array', 'categoryarray': df_pec_mensal['Mês'].unique()},
    yaxis={'title': 'Número de PECs'}
)
st.plotly_chart(fig_pec_mensal, use_container_width=True)

st.metric(f"Total Acumulado de PECs em {ano_selecionado}:", f"{total_pec_anual:,}".replace(",", "."))

st.markdown("---")

# =========================================================================
# SEÇÃO 2: GRÁFICO DE PIZZA (Sucesso vs. Insucesso)
# =========================================================================

st.subheader(f"2. Taxa de Sucesso: PECs Aprovadas vs. Não Aprovadas em {ano_selecionado}")
st.caption("Análise de efetividade jurídica: Aprovadas (Transf. em Norma) ou Arquivadas/Outras Situações.")

# 1. BUSCA DE DADOS REAIS PARA A PIZZA
with st.spinner("Buscando dados de aprovação e arquivamento..."):
    # Total Aprovado (Sucesso)
    total_aprovado = contar_pecs_por_situacao(ano_selecionado, SITUACAO_APROVADA)
    
    # Total Arquivado
    total_arquivado = contar_pecs_por_situacao(ano_selecionado, SITUACAO_ARQUIVADA)

# 2. CALCULA O QUE ESTÁ 'EM ABERTO/TRAMITAÇÃO'
# PECs em Tramitação/Outras Situações = Total Apresentado - Aprovadas - Arquivadas
total_em_aberto = total_pec_anual - total_aprovado - total_arquivado

# Garante que não há número negativo
if total_em_aberto < 0:
    total_em_aberto = 0

# 3. CRIA O DATAFRAME PARA O GRÁFICO DE PIZZA
df_situacao = pd.DataFrame({
    'Situação': ['Aprovada (Sucesso)', 'Arquivada/Rejeitada', 'Em Tramitação/Outras'],
    'Total': [total_aprovado, total_arquivado, total_em_aberto]
})

# Remove linhas com zero para não poluir o gráfico
df_situacao = df_situacao[df_situacao['Total'] > 0]

# 4. GRÁFICO DE PIZZA
if df_situacao.empty:
    st.info("Não foi possível contabilizar as situações finais. Dados insuficientes para o gráfico de pizza.")
else:
    fig_pizza_situacao = px.pie(
        df_situacao,
        values='Total',
        names='Situação',
        title=f'Situação Final das PECs Apresentadas em {ano_selecionado}',
        hole=.5,
        color_discrete_map={
            'Aprovada (Sucesso)': 'green',
            'Arquivada/Rejeitada': 'darkred',
            'Em Tramitação/Outras': 'gray'
        }
    )
    st.plotly_chart(fig_pizza_situacao, use_container_width=True)

    # Tabela de Detalhamento
    st.markdown("##### Tabela de Contagem por Situação Final:")
    st.dataframe(df_situacao, use_container_width=True, hide_index=True)


st.markdown("---")
st.success("As duas seções principais do seu projeto de Jurimetria estão completas e rodam com dados reais da API da Câmara!")
