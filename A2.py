import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time
from datetime import date
from calendar import monthrange
import numpy as np # Importado para evitar erro se estiver faltando

# --- 1. CONFIGURAÇÃO E DADOS BASE ---

# O SEU TOKEN DE ACESSO É OBRIGATÓRIO PARA ESTA API
TOKEN_API = "SEU_TOKEN_API_AQUI" 
URL_API_TRANSPARENCIA = "https://api.portaldatransparencia.gov.br/api-de-dados"
ENDPOINT_BOLSA_FAMILIA = "/novo-bolsa-familia-sacado-beneficiario-por-municipio"
URL_BRASIL_API = "https://brasilapi.com.br/api/ibge/municipios/v1/"

MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# Lista de UFs para o Selectbox
UFS_BRASIL = [
    'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS',
    'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC',
    'SE', 'SP', 'TO'
]

# --- 2. FUNÇÕES DE BUSCA DE DADOS (BRASILAPI E TRANSPARÊNCIA) ---

@st.cache_data(ttl=3600)
def buscar_municipios_por_uf(uf):
    """Consulta a BrasilAPI para obter a lista de municípios e seus IBGEs."""
    try:
        url = f"{URL_BRASIL_API}{uf}"
        response = requests.get(url)
        response.raise_for_status()
        dados = response.json()
        
        # Cria um dicionário: {Nome do Município: Código IBGE}
        municipios_dict = {
            mun['nome']: str(mun['codigo_ibge']) 
            for mun in dados 
            if 'codigo_ibge' in mun and mun['codigo_ibge']
        }
        return municipios_dict
    except Exception as e:
        st.error(f"Erro ao buscar lista de municípios da BrasilAPI: {e}")
        return {}

@st.cache_data(ttl=3600)
def buscar_dados_bolsa_familia(codigo_ibge, ano, mes):
    """Consulta a API da Transparência por município, ano e mês (100% Real)."""
    
    if TOKEN_API == "SEU_TOKEN_API_AQUI":
        st.error("ERRO: Por favor, substitua 'SEU_TOKEN_API_AQUI' pelo seu token real.")
        return None
    
    mes_ano = f"{ano}{mes:02d}"
    
    headers = {
        'Accept': 'application/json',
        'chave-api-dados': TOKEN_API 
    }
    
    url_consulta = f"{URL_API_TRANSPARENCIA}{ENDPOINT_BOLSA_FAMILIA}?codigoIbge={codigo_ibge}&mesAno={mes_ano}"
    
    try:
        response = requests.get(url_consulta, headers=headers)
        response.raise_for_status() 
        dados = response.json()
        
        if isinstance(dados, list):
             return dados
        return []

    except requests.exceptions.HTTPError as e:
        # Erro 403: Token incorreto. Erro 404: Dado não encontrado (válido).
        if e.response.status_code == 403:
             st.error("Erro 403: Acesso Negado. Verifique se o seu Token de Acesso está correto.")
        elif e.response.status_code == 404:
            st.warning("Dados não encontrados para esta combinação (Município/Mês/Ano).")
            return [] # Retorna lista vazia em caso de 404
        else:
             st.error(f"Erro na API ({e.response.status_code}): Servidor instável ou sem dados para o período.")
        return None
    except Exception as e:
        st.error(f"Erro na requisição: {e}")
        return None

@st.cache_data(ttl=3600)
def buscar_historico_anual(codigo_ibge, ano):
    """Busca o volume de beneficiários para todos os 12 meses do ano selecionado (100% Real)."""
    
    dados_historico = []
    hoje = date.today()
    limite_mes = 12
    if ano == hoje.year:
        limite_mes = hoje.month 
    
    
    for mes in range(1, limite_mes + 1):
        # A função buscar_dados_bolsa_familia é chamada para cada mês
        dados_mes = buscar_dados_bolsa_familia(codigo_ibge, ano, mes)
        
        total_beneficiarios = len(dados_mes) if dados_mes else 0
        
        dados_historico.append({
            'Mes_Num': mes,
            'Mês': MESES[mes],
            'Beneficiários Sacados': total_beneficiarios
        })
        time.sleep(0.1) # Pausa para respeitar o limite de requisições da API
        
    return pd.DataFrame(dados_historico)


# --- 3. FUNÇÕES DE GERAÇÃO DE GRÁFICOS ---

def criar_grafico_historico(df_historico):
    """Gráfico de Série Histórica de Beneficiários Sacados ao longo do ano."""
    
    fig = px.line(
        df_historico,
        x='Mês',
        y='Beneficiários Sacados',
        markers=True,
        title='Histórico Mensal de Beneficiários Sacados (Série Temporal)',
        labels={'Beneficiários Sacados': 'Total de Beneficiários'}
    )
    fig.update_xaxes(categoryorder='array', categoryarray=list(MESES.values()))
    return fig

# --- 4. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Monitor Bolsa Família (Dados Reais)")

st.title("💸 Monitor de Transparência: Saque do Novo Bolsa Família")
st.header("Análise por Município - Dados Reais CGU")

# --- SIDEBAR DE FILTROS ---
with st.sidebar:
    st.markdown("### 🛠️ Configurações")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=lambda: st.cache_data.clear() or st.rerun())
    st.caption("Clique se os dados não se atualizarem.")
    st.markdown("---")

    st.subheader("Filtros de Consulta")

    # 1. INPUT: Seleção de Estado (UF)
    uf_selecionada = st.selectbox("Estado (UF):", UFS_BRASIL, index=18) # RJ como padrão

    # 2. BUSCA DE MUNICÍPIOS (Chama a BrasilAPI)
    municipios_disponiveis = buscar_municipios_por_uf(uf_selecionada)
    
    # 3. INPUT: Seleção de Município
    municipio_selecionado_nome = st.selectbox(
        "Município:", 
        list(municipios_disponiveis.keys())
    )
    
    # 4. BUSCA DO IBGE (Automática)
    codigo_ibge_selecionado = municipios_disponiveis.get(municipio_selecionado_nome)
    
    # 5. INPUT: Seleção de Ano
    ano_selecionado = st.selectbox("Ano:", [2024, 2023])

    # 6. INPUT: Seleção de Mês
    mes_selecionado_nome = st.selectbox("Mês de Foco:", list(MESES.values()))
    mes_selecionado_num = {v: k for k, v in MESES.items()}[mes_selecionado_nome]


# --- BLOCO PRINCIPAL ---

if not codigo_ibge_selecionado:
    st.warning("Selecione um município e certifique-se de que o Token da API está configurado.")
else:
    st.markdown(f"**Analisando Dados Reais:** {municipio_selecionado_nome} ({uf_selecionada}) | IBGE: {codigo_ibge_selecionado}")
    st.markdown("---")
    
    # --- BUSCA DO MÊS SELECIONADO (MÉTRICA CHAVE) ---
    with st.spinner(f"1/2 - Buscando dado de {mes_selecionado_nome}/{ano_selecionado} na API..."):
        
        # A primeira busca foca apenas no mês selecionado
        dados_municipio_raw = buscar_dados_bolsa_familia(codigo_ibge_selecionado, ano_selecionado, mes_selecionado_num)
        
        if dados_municipio_raw is None:
            # Erro já reportado na função (Token ou API)
            st.stop() 

        total_beneficiarios_mes = len(dados_municipio_raw)
        
        # --- GRÁFICO A: MÉTRICA CHAVE ---
        st.subheader("1. Volume de Beneficiários Sacados (Mês Foco)")
        
        if total_beneficiarios_mes > 0:
            st.metric(
                label=f"Total de Beneficiários que Sacaram em {mes_selecionado_nome}/{ano_selecionado}",
                value=f"{total_beneficiarios_mes:,}".replace(",", ".")
            )
        else:
             st.info(f"Sem dados de saque encontrados para {municipio_selecionado_nome} em {mes_selecionado_nome}/{ano_selecionado}.")
        
        st.markdown("---")
        
        # --- GRÁFICO B: SÉRIE HISTÓRICA (COMPARAÇÃO REAL) ---
        st.subheader(f"2. Série Histórica Anual de Beneficiários ({ano_selecionado})")
        st.caption("Análise de variação mensal (Dados 100% Reais).")

        # BUSCA HISTÓRICA (Dados reais para o Gráfico B)
        with st.spinner(f"2/2 - Buscando série histórica de 12 meses..."):
            df_historico = buscar_historico_anual(codigo_ibge_selecionado, ano_selecionado)

        if not df_historico.empty and df_historico['Beneficiários Sacados'].sum() > 0:
            fig_b = criar_grafico_historico(df_historico)
            st.plotly_chart(fig_b, use_container_width=True)
        else:
            st.info("Não foi possível carregar o histórico de 12 meses para o município. O IBGE está correto?")
