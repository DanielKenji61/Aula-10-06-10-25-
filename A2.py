import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_API_PROPOSICOES_V2 = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
CODIGO_PEC = 304     

# CÓDIGOS DE SITUAÇÃO
SITUACAO_APROVADA_FINAL = 300 # Transf. em Norma Jurídica (Sucesso Final)
SITUACAO_ARQUIVADA = 239      # Insucesso Claro (Arquivada)

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
    Busca o total de PECs com uma situação final específica. (Função de Contagem Principal)
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
    # Este botão é vital para tentar obter dados corretos
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api) 
    st.caption("Use se os dados globais parecerem 100% de sucesso ou zero.")

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
    st.stop() 

total_pec_anual = df_pec_mensal['Total'].sum()
total_aprovado_final = contar_pecs_por_situacao(ano_selecionado, SITUACAO_APROVADA_FINAL) 

# --- GRÁFICO 1: PECs (Emendas Constitucionais) ---
st.subheader(f"1. Volume Mensal de Emendas à Constituição (PECs) em {ano_selecionado}")

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

# Métricas
col1, col2 = st.columns(2)
col1.metric(f"Total Apresentado em {ano_selecionado}:", f"{total_pec_anual:,}".replace(",", "."))
col2.metric(f"Total Aprovado Final (KPI):", f"{total_aprovado_final:,}".replace(",", "."), delta_color="normal")


st.markdown("---")

# =========================================================================
# SEÇÃO 2: GRÁFICO DE PIZZA (Sucesso vs. Insucesso - CORRIGIDO)
# =========================================================================

st.subheader(f"2. Situação de Tramitação das PECs em {ano_selecionado}")
st.caption("Análise de efetividade jurídica: Compara as PECs que foram arquivadas com as que ainda estão em tramitação.")

# 1. BUSCA DE DADOS REAIS PARA A PIZZA
with st.spinner("Buscando dados de situação (Arquivamento e Aprovação Final)..."):
    
    total_aprovado = total_aprovado_final # Já buscado acima
    
    # Total Arquivado
    total_arquivado = contar_pecs_por_situacao(ano_selecionado, SITUACAO_ARQUIVADA)

# 2. CALCULA O QUE ESTÁ 'EM TRAMITAÇÃO/OUTRAS' (Grande maioria)
total_tramitacao = total_pec_anual - total_aprovado - total_arquivado

# Garante que o número não seja negativo
if total_tramitacao < 0:
    total_tramitacao = 0

# 3. CRIA O DATAFRAME PARA O GRÁFICO DE PIZZA
df_situacao = pd.DataFrame({
    'Situação': ['Arquivada/Rejeitada', 'Aprovada (Sucesso Final)', 'Em Tramitação/Em Análise'],
    'Total': [total_arquivado, total_aprovado, total_tramitacao]
})

# Remove linhas com zero para não poluir o gráfico
df_situacao = df_situacao[df_situacao['Total'] > 0]

# 4. GRÁFICO DE PIZZA
if df_situacao.empty:
    st.info("Não foi possível contabilizar as situações finais. Dados insuficientes para o gráfico de pizza.")
else:
    # AVALIAÇÃO DA REALIDADE: Se Arquivada for 0, o gráfico mostrará a verdade da base.
    st.warning("⚠️ Se a fatia 'Arquivada/Rejeitada' for zero, a PEC falha ainda está na situação 'Em Tramitação' na base de dados da Câmara.")
    
    fig_pizza_situacao = px.pie(
        df_situacao,
        values='Total',
        names='Situação',
        title=f'Situação Atual das PECs Apresentadas em {ano_selecionado}',
        hole=.5,
        color_discrete_map={
            'Aprovada (Sucesso Final)': 'green',
            'Arquivada/Rejeitada': 'darkred',
            'Em Tramitação/Em Análise': 'orange'
        }
    )
    st.plotly_chart(fig_pizza_situacao, use_container_width=True)

    # Tabela de Detalhamento
    st.markdown("##### Tabela de Contagem por Situação Final:")
    st.dataframe(df_situacao, use_container_width=True, hide_index=True)


st.markdown("---")
st.success("As duas seções principais do seu projeto de Jurimetria estão completas e rodam com dados reais da API da Câmara!")
