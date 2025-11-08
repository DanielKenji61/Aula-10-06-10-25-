import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time

# --- 1. CONFIGURAÇÃO E DADOS FIXOS (57ª LEGISLATURA) ---

URL_API_BASE = "https://dadosabertos.camara.leg.br/api/v2/"
LEGISLATURA_ALVO = 57

# DEFINIÇÃO DOS DOIS PROJETOS A SEREM COMPARADOS
PROJETOS = {
    "PLP 177/2023 (Fixação de Deputados)": {
        "ID_PROPOSICAO": "2387114",
        "ID_VOTACAO": "2387114-177",
        "TIPO_VOTACAO": "Substitutivo (Mérito)"
    },
    "PL 29/2023 (Telecomunicações)": {
        "ID_PROPOSICAO": "2372562",
        "ID_VOTACAO": "2372562-111", # ID da votação do Texto-Base
        "TIPO_VOTACAO": "Texto-Base"
    }
}

# --- 2. FUNÇÕES DE BUSCA E PROCESSAMENTO DA API ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.experimental_rerun()

@st.cache_data(ttl=3600)
def buscar_dados(url):
    """Função robusta para buscar dados da API e retornar JSON."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # st.error(f"Falha na conexão com a API: {url}")
        return None

def processar_votos_nominais(id_votacao):
    """
    Busca a lista de votos nominais e processa o DataFrame agrupado por partido.
    Retorna o DataFrame nominal (para contagem) e o DataFrame agrupado.
    """
    url_votos = f"{URL_API_BASE}votacoes/{id_votacao}/votos"
    dados_votos_raw = buscar_dados(url_votos)

    if not dados_votos_raw or not dados_votos_raw.get('dados'):
        return pd.DataFrame(), pd.DataFrame()

    lista_votos = dados_votos_raw.get('dados', [])
    
    # DataFrame Nominal Bruto (Necessário para o agrupamento)
    df_votos = pd.DataFrame([
        {
            'Nome do Deputado': voto.get('deputado', {}).get('nome', 'N/A'),
            'Partido': voto.get('deputado', {}).get('siglaPartido', 'N/A'),
            'ID Deputado': voto.get('deputado', {}).get('id', 0),
            'Voto Nominal': voto.get('tipoVoto', 'N/A')
        } for voto in lista_votos
    ])

    # DataFrame Agrupado (Para o Gráfico de Barras)
    df_agrupado = df_votos.groupby('Partido')['Voto Nominal'].value_counts().unstack(fill_value=0)
    
    # Garantir que as colunas essenciais existam
    for col in ['Sim', 'Não', 'Abstenção', 'Obstrução', 'Ausente']:
        if col not in df_agrupado.columns:
            df_agrupado[col] = 0
            
    df_agrupado['Total Votos'] = df_agrupado[['Sim', 'Não', 'Abstenção', 'Obstrução', 'Ausente']].sum(axis=1)
    df_agrupado = df_agrupado.reset_index().sort_values(by='Total Votos', ascending=False)
    
    return df_votos, df_agrupado


# --- 3. FUNÇÕES DE ANÁLISE E GRÁFICOS ---

def analisar_desempenho_partido(df_agrupado, sigla_partido='PL'):
    """Extrai os votos Sim e Não para o partido alvo (PL) dos dados agrupados."""
    
    try:
        # Acessa a linha do partido alvo (PL)
        dados_pl = df_agrupado[df_agrupado['Partido'] == sigla_partido].iloc[0]
        
        votos_sim = dados_pl.get('Sim', 0)
        votos_nao = dados_pl.get('Não', 0)
        total_participantes = dados_pl.get('Total Votos', 0)
        
        # Determina a posição majoritária
        if votos_sim > votos_nao:
            posicao = "A Favor (Sim)"
        elif votos_nao > votos_sim:
            posicao = "Contra (Não)"
        else:
            posicao = "Neutro/Dividido"
            
        return total_participantes, votos_sim, votos_nao, posicao
        
    except IndexError:
        # O partido PL pode não ter votado ou não ter deputados na votação
        return 0, 0, 0, "Sem Voto Registrado"


# --- 4. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Monitor de Votação PLP/PL")

st.title("⚖️ Jurimetria Parlamentar: Comparativo de Votações")
st.header("Análise de Voto por Partido na 57ª Legislatura")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Configurações")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use para forçar a busca de novos dados da Câmara.")
    st.markdown("---")

# --- SELETOR PRINCIPAL ---
st.subheader("Selecione o Projeto para Análise Detalhada:")
projeto_selecionado_nome = st.selectbox(
    "Projeto (PLP ou PL):", 
    list(PROJETOS.keys()),
    index=0 # Padrão PLP 177/2023
)

# Define os IDs da votação e da proposição
PROJETO_SELECIONADO = PROJETOS[projeto_selecionado_nome]
ID_VOTACAO_SELECIONADA = PROJETO_SELECIONADO['ID_VOTACAO']
TIPO_VOTACAO_SELECIONADA = PROJETO_SELECIONADO['TIPO_VOTACAO']

st.markdown("---")

# --- EXECUÇÃO E CARREGAMENTO DE DADOS ---
with st.spinner(f"Buscando votos nominais para {projeto_selecionado_nome} ({ID_VOTACAO_SELECIONADA})..."):
    df_votos_nominais, df_votos_agrupados = processar_votos_nominais(ID_VOTACAO_SELECIONADA)

if df_votos_agrupados.empty:
    st.error("Falha Crítica: Não foi possível carregar os dados de votação da API. O ID pode estar incorreto ou o recurso está temporariamente bloqueado.")
    st.stop()


# --- ANÁLISE DO PL E KPIS ---
total_votos_registrados = df_votos_agrupados['Total Votos'].sum()
total_participantes_pl, pl_sim, pl_nao, posicao_pl = analisar_desempenho_partido(df_votos_agrupados, sigla_partido='PL')

st.subheader(f"Resultado da Votação: {TIPO_VOTACAO_SELECIONADA}")

col_geral_total, col_votos_pl, col_pl_sim, col_pl_nao = st.columns(4)

with col_geral_total:
    st.metric("Total de Votos Registrados", f"{total_votos_registrados:,}".replace(",", "."))

# Exibir os votos do PL
with col_votos_pl:
    st.metric("Participação do Partido PL", f"{total_participantes_pl} Votos")
with col_pl_sim:
    st.metric("PL: Votos Sim (A Favor)", pl_sim)
with col_pl_nao:
    st.metric("PL: Votos Não (Contra)", pl_nao)

st.markdown("---")

# --- GRÁFICO DE BARRAS (VOTAÇÃO POR PARTIDO) ---

st.subheader("1. Distribuição de Votos por Partido")
st.caption("Gráfico interativo que mostra o posicionamento das bancadas (Sim/Não/Abstenção).")

# Filtra colunas de voto para o gráfico
df_plot = df_votos_agrupados.set_index('Partido')[['Sim', 'Não', 'Abstenção', 'Obstrução', 'Ausente']].reset_index()

df_plot_melt = df_plot.melt(
    id_vars='Partido', 
    var_name='Tipo de Voto', 
    value_vars=['Sim', 'Não', 'Abstenção'],
    value_name='Total'
)

fig_votos = px.bar(
    df_plot_melt,
    x='Partido',
    y='Total',
    color='Tipo de Voto',
    title=f'Votos Nominais na Proposição ({TIPO_VOTACAO_SELECIONADA})',
    barmode='stack',
    color_discrete_map={'Sim': 'green', 'Não': 'red', 'Abstenção': 'gold'}
)
fig_votos.update_layout(xaxis_title="Partido", yaxis_title="Número Total de Votos")
st.plotly_chart(fig_votos, use_container_width=True)

st.markdown("---")

# Tabela de Detalhamento
st.subheader("2. Tabela de Detalhamento Nominal (PL)")
st.caption("Lista de como os deputados do Partido Liberal votaram.")

df_pl_nominal = df_votos_nominais[df_votos_nominais['Partido'] == 'PL'].drop(columns=['ID Deputado'])

st.dataframe(
    df_pl_nominal.sort_values(by='Voto Nominal', ascending=False),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.success("Análise de jurimetria concluída com sucesso! ✅")
