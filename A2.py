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

# O ano atual é 2025 (e o código já lida com a limitação de dados para o ano atual, se fosse necessário)
ANO_ATUAL_REAL = date.today().year
MES_ATUAL = date.today().month

# --- 2. FUNÇÕES DE BUSCA (DADOS REAIS E MENSAIS) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600) # Cache de 1 hora para evitar chamadas repetidas à API
def buscar_proposicoes_mensais_por_tipo(ano, cod_tipo, nome_tipo):
    """
    Busca o total de proposições de um tipo específico (PL ou PEC) para cada mês do ano.
    A função lida com paginação e limita a busca até o mês atual em 2025.
    """
    dados_mensais = []
    
    # Define o limite final da busca
    if ano == ANO_ATUAL_REAL:
        # Se for o ano atual (2025), limitamos a busca até o mês de Outubro (10), 
        # que é o último mês completo antes de Novembro.
        mes_limite = 10 
    else:
        mes_limite = 12

    # Itera sobre os meses de Janeiro (1) até o mês limite
    for mes in range(1, mes_limite + 1):
        
        # Define as datas de início e fim do mês
        data_inicio = date(ano, mes, 1)
        
        # Calcula o último dia do mês
        if mes == 12:
            data_fim = date(ano, 12, 31)
        else:
            data_fim = data_inicio + relativedelta(months=1) - relativedelta(days=1)
        
        params = {
            'dataInicio': data_inicio.strftime('%Y-%m-%d'),
            'dataFim': data_fim.strftime('%Y-%m-%d'),
            'codTipo': cod_tipo,
            'ordenarPor': 'id',
            'itens': 100, # Número de itens por página
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
                
                # Se a página não estiver completa, é a última página
                if len(dados) < params['itens']:
                    break
                
                pagina += 1
                time.sleep(0.05) 
                
            except requests.exceptions.RequestException:
                # Retorna dados parciais em caso de falha na API
                break 
                
        # Adiciona o resultado
        dados_mensais.append({
            'Mês': date(2000, mes, 1).strftime('%b/%Y' if ano != 2024 else '%b'), # Exibe o nome do mês
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
# CORRIGIDO: Lista explícita de 2024 e 2023
anos_disponiveis = [2024, 2023] 

# st.radio para seleção de ano (horizontal, como solicitado)
ano_selecionado = st.radio(
    "Escolha o ano base para visualizar as informações:",
    anos_disponiveis,
    index=0, # 2024 é o padrão
    format_func=lambda x: f"Ano {x}", 
    horizontal=True
)

st.markdown("---")

# --- BUSCA E PROCESSAMENTO DE DADOS ---

with st.spinner(f'Buscando dados reais da API da Câmara para {ano_selecionado}...'):
    # Busca dados de PL
    df_pl = buscar_proposicoes_mensais_por_tipo(ano_selecionado, CODIGO_PL, 'Projeto de Lei (PL)')
    
    # Busca dados de PEC
    df_pec = buscar_proposicoes_mensais_por_tipo(ano_selecionado, CODIGO_PEC, 'Emenda à Constituição (PEC)')

# Combina os DataFrames
df_combinado = pd.concat([df_pl, df_pec]).reset_index(drop=True)


if df_combinado.empty or df_combinado['Total'].sum() == 0:
    st.error(f"Não foi possível carregar dados da API para o ano de {ano_selecionado}.")
else:
    # Garante que a ordem dos meses está correta para o gráfico
    df_combinado = df_combinado.sort_values(by='Ordem_Mes')

    # --- GRÁFICO 1: VOLUME MENSAL (PL vs PEC) ---
    st.subheader(f"1. Volume Mensal de Proposições Apresentadas em {ano_selecionado}")
    st.caption("Gráfico de Barras Agrupadas: Comparação entre a produção de Leis Ordinárias (PL) e Emendas Constitucionais (PEC).")

    fig_mensal = px.bar(
        df_combinado,
        x='Mês',
        y='Total',
        color='Tipo',
        barmode='group', # Agrupa as barras lado a lado
        title=f'Proposições (PL e PEC) Apresentadas Mês a Mês em {ano_selecionado}',
        labels={'Total': 'Número de Proposições', 'Mês': 'Mês de Apresentação'},
        color_discrete_map={
            'Projeto de Lei (PL)': 'blue',
            'Emenda à Constituição (PEC)': 'red'
        }
    )
    
    # Ajusta o layout para melhor visualização
    fig_mensal.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': df_combinado['Mês'].unique()})
    
    st.plotly_chart(fig_mensal, use_container_width=True)

    # --- MÉTRICAS CHAVE (KPIs) ---
    total_pl_anual = df_pl['Total'].sum()
    total_pec_anual = df_pec['Total'].sum()

    st.markdown("#### Totais Acumulados no Ano:")
    col1, col2, col3 = st.columns(3)
    col1.metric("PLs Apresentadas", f"{total_pl_anual:,}".replace(",", "."))
    col2.metric("PECs Apresentadas", f"{total_pec_anual:,}".replace(",", "."))
    col3.metric("Total Geral", f"{total_pl_anual + total_pec_anual:,}".replace(",", "."))

    st.markdown("---")

    st.markdown("### Próximos Passos:")
    st.markdown("O primeiro bloco está pronto! Podemos adicionar a próxima análise (Ex: Distribuição por Autores, Partidos ou Sucesso) logo abaixo deste ponto.")
