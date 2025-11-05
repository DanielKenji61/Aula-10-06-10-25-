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
CODIGO_PEC = 304     # Proposta de Emenda à Constituição (PEC)

# O ano e mês atual (para limitar a busca do ano corrente)
ANO_ATUAL_REAL = date.today().year
MES_ATUAL = date.today().month

# --- 2. FUNÇÕES DE BUSCA (DADOS REAIS E MENSAIS) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

# --- FUNÇÕES PARA SEÇÃO 1 (Gráfico Mensal) ---

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

# --- NOVAS FUNÇÕES PARA SEÇÃO 2 (Gráfico de Pizza Partidário) ---

@st.cache_data(ttl=3600)
def buscar_ids_pecs_para_analise(ano):
    """
    Busca TODOS os IDs de PECs para o ano, em uma única lista paginada.
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
    
    lista_ids = []
    pagina = 1
    
    while True:
        try:
            response = requests.get(URL_API_PROPOSICOES_V2, params={**params, 'pagina': pagina}, timeout=10)
            response.raise_for_status() 
            dados = response.json().get('dados', [])
            
            if not dados:
                break
                
            lista_ids.extend([d['id'] for d in dados])
            
            if len(dados) < params['itens']:
                break
            
            pagina += 1
            time.sleep(0.05)
            
        except requests.exceptions.RequestException:
            break
            
    return lista_ids

@st.cache_data(ttl=3600)
def processar_autoria_por_partido(lista_ids):
    """
    Faz a chamada individual para cada PEC (ID) e extrai o partido do primeiro autor.
    """
    dados_autoria = []
    
    for id_pec in lista_ids:
        try:
            # Endpoint de detalhe da proposição
            url_detalhe = f"{URL_API_PROPOSICOES_V2}/{id_pec}"
            response = requests.get(url_detalhe, timeout=5)
            response.raise_for_status()
            detalhe = response.json()
            
            # Tenta encontrar o autor principal (deputado)
            autores = detalhe.get('autores', [])
            
            if autores:
                # O primeiro autor é geralmente o principal proponente
                autor_principal = autores[0]
                
                # Extrai a sigla do partido, se for um deputado (tipo 1002 - Deputado)
                if autor_principal.get('tipoAutor') == 'Deputado':
                     sigla_partido = autor_principal.get('siglaPartido')
                     
                     if sigla_partido:
                          dados_autoria.append({'Partido': sigla_partido, 'Total': 1})
            
            time.sleep(0.05) # Pausa crucial entre chamadas individuais
            
        except requests.exceptions.RequestException:
            continue
            
    if not dados_autoria:
        return pd.DataFrame()
        
    df_autoria = pd.DataFrame(dados_autoria)
    # Agrupa e conta o total por partido
    return df_autoria.groupby('Partido').sum().reset_index()


# --- 4. INTERFACE STREAMLIT PRINCIPAL ---

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

# st.radio para seleção de ano (horizontal, como solicitado)
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

# BUSCA E PROCESSAMENTO DE DADOS PARA GRÁFICO MENSAL
with st.spinner(f'Buscando dados mensais reais da API para PECs de {ano_selecionado}...'):
    df_pec_mensal = buscar_pecs_mensais(ano_selecionado)


# --- EXIBIÇÃO DE GRÁFICOS E DADOS DA SEÇÃO 1 ---

st.subheader(f"1. Volume Mensal de Emendas à Constituição (PECs) em {ano_selecionado}")
st.caption("Gráfico de Barras: Número de PECs apresentadas por mês.")

if df_pec_mensal.empty or df_pec_mensal['Total'].sum() == 0:
    st.info(f"Não há registros de Propostas de Emenda à Constituição (PECs) para {ano_selecionado} na base de dados da API.")
else:
    df_pec_mensal = df_pec_mensal.sort_values(by='Ordem_Mes')
    total_pec_anual = df_pec_mensal['Total'].sum()
    
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

    # Métrica
    st.metric(f"Total Acumulado de PECs em {ano_selecionado}:", f"{total_pec_anual:,}".replace(",", "."))

st.markdown("---")

# =========================================================================
# SEÇÃO 2: GRÁFICO DE PIZZA POR PARTIDO (Autoria)
# =========================================================================

st.subheader(f"2. Distribuição da Autoria das PECs por Partido em {ano_selecionado}")
st.caption("Análise Jurimétrica: O gráfico demonstra quais siglas partidárias propuseram mais Propostas de Emenda à Constituição.")

if df_pec_mensal.empty or df_pec_mensal['Total'].sum() == 0:
    st.info("Não é possível realizar a análise partidária sem as proposições da Seção 1.")
else:
    # 1. BUSCA DE TODOS OS IDs PARA O ANO
    lista_ids = buscar_ids_pecs_para_analise(ano_selecionado)
    
    # 2. PROCESSAMENTO DE AUTORIA (CHAMADAS INDIVIDUAIS)
    with st.spinner(f"Processando a autoria de {len(lista_ids)} PECs. Isso pode levar alguns segundos devido às chamadas individuais à API..."):
        df_autoria_partido = processar_autoria_por_partido(lista_ids)

    # 3. EXIBIÇÃO
    if df_autoria_partido.empty:
        st.warning("Não foi possível extrair dados de autoria (partido) para as PECs encontradas.")
    else:
        # Gráfico de Pizza
        fig_pizza_partido = px.pie(
            df_autoria_partido,
            values='Total',
            names='Partido',
            title='Propostas de PECs por Partido (Autoria Principal)',
            hole=.5,
            color_discrete_sequence=px.colors.qualitative.Alphabet
        )
        fig_pizza_partido.update_traces(textinfo='percent+label', pull=[0.1 if p == df_autoria_partido['Partido'].iloc[0] else 0 for p in df_autoria_partido['Partido']])
        st.plotly_chart(fig_pizza_partido, use_container_width=True)

        # Tabela de Detalhamento
        st.markdown("##### Tabela de Contagem por Sigla:")
        st.dataframe(df_autoria_partido.sort_values(by='Total', ascending=False), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### Próximos Passos:")
st.markdown("Com a autoria concluída, podemos focar na **situação atual das PECs** (ex: Taxa de sucesso ou arquivamento).")
