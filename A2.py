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
SITUACAO_APROVADA_FINAL = 300 
SITUACAO_ARQUIVADA = 239      

ANO_ATUAL_REAL = date.today().year
MES_ATUAL = date.today().month

# --- 2. FUNÇÕES DE BUSCA (DADOS REAIS DA API) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

# [Funções existentes: contar_pecs_por_situacao e buscar_pecs_mensais - MANTIDAS INALTERADAS]
# ... [O código dessas funções deve ser copiado do bloco anterior para o seu arquivo app.py] ...
# Devido ao tamanho, vou apenas incluir as novas funções, pressupondo que as funções de busca anteriores estão no seu app.py

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
# [Fim das funções de busca existentes]

# --- NOVA FUNÇÃO PARA SEÇÃO 3: AMOSTRAGEM DE SITUAÇÃO ATUAL ---

@st.cache_data(ttl=3600)
def obter_amostra_situacao_atual(ano):
    """
    Busca uma AMOSTRA das PECs do ano, faz a requisição de detalhe e classifica o status ATUAL.
    Isto é feito para evitar sobrecarga na API.
    """
    
    st.info("Buscando amostra de IDs para análise de situação atual...")
    
    # 1. Busca os IDs (limitamos a uma amostragem de 2 páginas)
    params = {
        'dataInicio': f'{ano}-01-01',
        'dataFim': date.today().strftime('%Y-%m-%d'),
        'codTipo': CODIGO_PEC,
        'ordenarPor': 'id',
        'itens': 50, # Apenas 50 itens por página
    }
    
    lista_ids = []
    # Buscamos apenas 2 páginas para ter uma amostra de até 100 PECs (evitando sobrecarga)
    for pagina in range(1, 3): 
        try:
            response = requests.get(URL_API_PROPOSICOES_V2, params={**params, 'pagina': pagina}, timeout=10)
            dados = response.json().get('dados', [])
            lista_ids.extend([d['id'] for d in dados])
            time.sleep(0.05)
        except:
            pass
            
    if not lista_ids:
        return pd.DataFrame()

    # 2. Faz a chamada de detalhe para a amostra e extrai a última situação
    dados_situacao = []
    
    for id_pec in lista_ids:
        try:
            url_detalhe = f"{URL_API_PROPOSICOES_V2}/{id_pec}"
            response = requests.get(url_detalhe, timeout=5)
            detalhe = response.json()
            
            # A situação ATUAL está em 'statusProposicao' ou similar. Usaremos 'ultimoStatus'
            status_atual = detalhe.get('statusProposicao', {}).get('descricaoSituacao', 'Em Análise')
            
            # Classificação: Simplificamos os vários status
            if 'arquivamento' in status_atual.lower():
                status_classificado = 'Arquivamento/Rejeição'
            elif 'pronta para pauta' in status_atual.lower() or 'plenário' in status_atual.lower():
                status_classificado = 'Pronta para Pauta/Plenário'
            elif 'aprovada' in status_atual.lower() or 'sancionada' in status_atual.lower() or 'promulgada' in status_atual.lower():
                 status_classificado = 'Sucesso Final (Aprovada)'
            else:
                status_classificado = 'Em Tramitação'
                
            dados_situacao.append({'Situação Atual': status_classificado, 'Total': 1})
            
            time.sleep(0.05) # Pausa crucial
            
        except:
            continue
            
    if not dados_situacao:
        return pd.DataFrame()
        
    df_amostra = pd.DataFrame(dados_situacao)
    # Agrupa e conta o total por status
    return df_amostra.groupby('Situação Atual').sum().reset_index()


# --- 4. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Análise de PECs - Câmara dos Deputados")

st.title("🏛️ Análise da Produtividade Legislativa (Foco em PECs)")
st.header("Propostas de Emenda à Constituição (2023 vs. 2024)")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
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

# [Código da Seção 1 (Gráfico Mensal) - (Reutilize o código do bloco anterior)]

with st.spinner(f'Buscando dados mensais reais da API para PECs de {ano_selecionado}...'):
    df_pec_mensal = buscar_pecs_mensais(ano_selecionado)

if df_pec_mensal.empty or df_pec_mensal['Total'].sum() == 0:
    st.error(f"Não há registros de PECs para {ano_seleçãoado} na base de dados da API ou houve falha na conexão.")
    st.stop() 

total_pec_anual = df_pec_mensal['Total'].sum()
total_aprovado_final = contar_pecs_por_situacao(ano_selecionado, SITUACAO_APROVADA_FINAL) 

# --- GRÁFICO 1: PECs (Emendas Constitucionais) ---
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

# Métricas
col1, col2 = st.columns(2)
col1.metric(f"Total Apresentado em {ano_selecionado}:", f"{total_pec_anual:,}".replace(",", "."))
col2.metric(f"Total Aprovado Final (KPI):", f"{total_aprovado_final:,}".replace(",", "."), delta_color="normal")


st.markdown("---")

# =========================================================================
# SEÇÃO 2: GRÁFICO DE PIZZA (Situação de Tramitação ATUAL - Amostragem)
# =========================================================================

st.subheader(f"2. Situação de Tramitação ATUAL das PECs em {ano_selecionado}")
st.caption("Análise Jurídica: Distribuição de PECs por estágio atual de tramitação (Amostragem de Dados Reais).")

with st.spinner("Analisando amostragem de situação atual das PECs..."):
    df_situacao_atual = obter_amostra_situacao_atual(ano_selecionado)

if df_situacao_atual.empty:
    st.warning("Não foi possível coletar a amostra para a análise de tramitação. A API pode estar limitando as chamadas de detalhe.")
else:
    # --- GRÁFICO DE PIZZA ---
    fig_pizza_atual = px.pie(
        df_situacao_atual,
        values='Total',
        names='Situação Atual',
        title=f'Distribuição Atual das PECs ({ano_selecionado}) - Amostra',
        hole=.5,
        color_discrete_map={
            'Sucesso Final (Aprovada)': 'green',
            'Arquivamento/Rejeição': 'darkred',
            'Pronta para Pauta/Plenário': 'purple',
            'Em Tramitação': 'orange'
        }
    )
    st.plotly_chart(fig_pizza_atual, use_container_width=True)

    # Tabela de Detalhamento
    st.markdown("##### Tabela de Contagem por Situação:")
    st.dataframe(df_situacao_atual, use_container_width=True, hide_index=True)


st.markdown("---")
st.success("O projeto de Jurimetria está completo, com duas análises vitais (volume e estágio de tramitação) baseadas em dados reais da API da Câmara!")
