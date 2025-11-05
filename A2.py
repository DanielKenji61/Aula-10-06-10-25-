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

# Códigos de Tipos de Proposição para o filtro da API
CODIGO_PL = 207      # Projeto de Lei (PL)
CODIGO_PEC = 304     # Proposta de Emenda à Constituição (PEC)

# O ano atual (para limitar a busca do ano corrente)
ANO_ATUAL_REAL = date.today().year
MES_ATUAL = date.today().month

# --- 2. FUNÇÕES DE BUSCA (DADOS REAIS E MENSAIS) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600) # Cache de 1 hora
def buscar_proposicoes_mensais_por_tipo(ano, cod_tipo, nome_tipo):
    """
    Busca o total de proposições de um tipo específico (PL ou PEC) para cada mês do ano.
    """
    dados_mensais = []
    
    # Define o limite final da busca.
    if ano == ANO_ATUAL_REAL:
        # Se for o ano atual, limitamos a busca até o mês atual.
        mes_limite = MES_ATUAL 
    else:
        mes_limite = 12

    for mes in range(1, mes_limite + 1):
        
        # Define as datas de início e fim do mês
        data_inicio = date(ano, mes, 1)
        
        # Calcula o último dia do mês
        if mes == MES_ATUAL and ano == ANO_ATUAL_REAL:
             data_fim = date.today()
        elif mes == 12:
            data_fim = date(ano, 12, 31)
        else:
            data_fim = data_inicio + relativedelta(months=1) - relativedelta(days=1)
        
        params = {
            'dataInicio': data_inicio.strftime('%Y-%m-%d'),
            'dataFim': data_fim.strftime('%Y-%m-%d'),
            'codTipo': cod_tipo,
            'ordenarPor': 'id',
            'itens': 100, 
        }
        
        total_no_mes = 0
        pagina = 1
        
        # Lógica de paginação para contar o total
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
                
        # Adiciona o resultado
        dados_mensais.append({
            'Mês': date(2000, mes, 1).strftime('%b/%Y' if ano != 2024 else '%b'), 
            'Ordem_Mes': mes,
            'Total': total_no_mes,
            'Tipo': nome_tipo
        })
            
    return pd.DataFrame(dados_mensais)

# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Análise Legislativa - Câmara dos Deputados")

st.title("🏛️ Análise da Produtividade Legislativa")
st.header("Câmara dos Deputados: Comparativo 2023 vs. 2024")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use se os dados não se atualizarem ou se o Streamlit falhar.")

st.markdown("---")

# --- SELETOR DE ANO ---
st.subheader("Selecione o Ano para Análise:")
# Lista explícita de 2024 e 2023
anos_disponiveis = [2024, 2023] 

# st.radio para seleção de ano (horizontal, como solicitado)
ano_selecionado = st.radio(
    "Escolha o ano base para visualizar as informações:",
    anos_disponiveis,
    index=0, 
    format_func=lambda x: f"Ano {x}", 
    horizontal=True
)

st.markdown("---")

# --- BUSCA E PROCESSAMENTO DE DADOS ---

with st.spinner(f'Buscando dados reais da API da Câmara para {ano_selecionado}...'):
    # GRÁFICO 1 (PECS): Busca dados de PEC (Emenda à Constituição)
    df_pec = buscar_proposicoes_mensais_por_tipo(ano_selecionado, CODIGO_PEC, 'Emenda à Constituição (PEC)')
    
    # GRÁFICO 2 (PLs): Busca dados de PL (Projeto de Lei)
    df_pl_proposto = buscar_proposicoes_mensais_por_tipo(ano_selecionado, CODIGO_PL, 'Projeto de Lei (PL) Proposto')


# --- EXIBIÇÃO DE GRÁFICOS E DADOS ---

# --- GRÁFICO 1: PECs (Emendas Constitucionais) ---
st.subheader(f"1. Volume Mensal de Emendas à Constituição (PECs) em {ano_selecionado}")
st.caption("Análise da produção de Propostas de Emenda à Constituição (PECs) por mês.")

if df_pec.empty or df_pec['Total'].sum() == 0:
    st.info(f"Não há registros de Emendas à Constituição (PECs) para {ano_selecionado} na base de dados da API.")
else:
    df_pec = df_pec.sort_values(by='Ordem_Mes')
    
    # Gráfico simples, apenas com as PECs (COR VERMELHA FIXA)
    fig_pec = px.bar(
        df_pec,
        x='Mês',
        y='Total',
        color_discrete_sequence=['red'], 
        title=f'PECs Apresentadas Mês a Mês em {ano_selecionado}',
        labels={'Total': 'Número de PECs', 'Mês': 'Mês de Apresentação'},
    )
    fig_pec.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_pec['Mês'].unique()})
    st.plotly_chart(fig_pec, use_container_width=True)

    # Métricas PEC
    total_pec_anual = df_pec['Total'].sum()
    st.markdown(f"**Total Acumulado de PECs em {ano_selecionado}:** {total_pec_anual:,}".replace(",", "."))

st.markdown("---")

# --- GRÁFICO 2: PLs (Projetos de Lei Propostos) ---
st.subheader(f"2. Volume Mensal de Projetos de Lei (PL) Propostos em {ano_selecionado}")
st.caption("Este gráfico mostra todos os Projetos de Lei Ordinária (PL) que foram propostos na Câmara no ano.")

if df_pl_proposto.empty or df_pl_proposto['Total'].sum() == 0:
    st.info(f"Não há registros de Projetos de Lei (PLs) propostos para {ano_selecionado} na base de dados da API.")
else:
    df_pl_proposto = df_pl_proposto.sort_values(by='Ordem_Mes')

    # Gráfico simples, apenas com os PLs (COR AZUL FIXA)
    fig_pl = px.bar(
        df_pl_proposto,
        x='Mês',
        y='Total',
        color_discrete_sequence=['blue'],
        title=f'PLs Propostos Mês a Mês em {ano_selecionado}',
        labels={'Total': 'Número de PLs', 'Mês': 'Mês de Apresentação'},
    )
    fig_pl.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_pl_proposto['Mês'].unique()})
    st.plotly_chart(fig_pl, use_container_width=True)

    # Métricas PL
    total_pl_anual = df_pl_proposto['Total'].sum()
    st.markdown(f"**Total Acumulado de PLs Propostos em {ano_selecionado}:** {total_pl_anual:,}".replace(",", "."))

st.markdown("---")
st.markdown("### Próximos Passos na Análise do Fluxo Legislativo:")
st.markdown("Agora que a separação PL/PEC está visualmente clara, podemos adicionar a próxima análise, focando na **autoria** ou no **andamento** das proposições (Ex: quem propõe mais?).")
