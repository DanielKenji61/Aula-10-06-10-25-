import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
from urllib.parse import quote

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_BASE = "https://dadosabertos.camara.leg.br/api/v2/"
# Para identificar a votação em Plenário (ID do Órgão)
ID_ORGAO_PLENARIO = 180 

# --- 2. FUNÇÕES DE BUSCA DA API (DADOS REAIS E ENCADEDOS) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def buscar_id_proposicao(sigla_tipo, numero, ano):
    """
    Busca o ID interno da proposição pelo número, tipo e ano.
    Ex: PL 1234/2023.
    """
    params = {
        'siglaTipo': sigla_tipo,
        'numero': numero,
        'ano': ano,
        'ordem': 'ASC',
        'ordenarPor': 'id',
        'itens': 1,
    }
    
    url = URL_BASE + "proposicoes"
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        dados = response.json().get('dados', [])
        
        if dados:
            return dados[0]['id']
        return None
        
    except requests.exceptions.RequestException:
        return None

@st.cache_data(ttl=3600)
def buscar_votacoes_proposicao(id_proposicao):
    """
    Busca todas as votações nominais em Plenário para um ID de proposição.
    """
    # Endpoint para buscar votações de uma proposição
    url = f"{URL_BASE}proposicoes/{id_proposicao}/votacoes"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        votacoes = response.json().get('dados', [])
        
        # Filtra a última votação nominal que ocorreu no Plenário
        # (O ideal é buscar a última votação nominal aberta no órgão 180)
        votacoes_plenario = [
            v for v in votacoes 
            if v.get('nomeOrgao') == 'Plenário' and v.get('data') is not None
        ]

        if votacoes_plenario:
            # Retorna o ID da votação mais recente no Plenário
            votacoes_plenario.sort(key=lambda x: x['data'], reverse=True)
            return votacoes_plenario[0]['id']
        
        return None
        
    except requests.exceptions.RequestException:
        return None

@st.cache_data(ttl=3600)
def buscar_votos_nominais(id_votacao):
    """
    Busca a lista completa de votos (Deputado, UF, Partido, Voto) para um ID de votação.
    """
    url = f"{URL_BASE}votacoes/{id_votacao}/votos"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('dados', [])
        
    except requests.exceptions.RequestException:
        return None

# --- 3. FUNÇÕES DE PROCESSAMENTO E GRÁFICOS ---

def processar_votos(dados_votos):
    """Transforma os dados brutos de votos em um DataFrame para visualização."""
    
    # Mapeamento do resultado do voto
    mapeamento_voto = {
        'Sim': 'A Favor',
        'Não': 'Contra',
        'Abstenção': 'Abstenção',
        'Obstrução': 'Obstrução/Ausente',
        'Ausente': 'Obstrução/Ausente',
        # Inclui outros votos que podem aparecer na API, como "Art. 17"
    }

    df = pd.DataFrame(dados_votos)
    
    # Filtra e renomeia colunas
    df_filtrado = df[['deputado_nome', 'deputado_uf', 'deputado_partido', 'voto']]
    df_filtrado.columns = ['Nome do Deputado', 'UF', 'Partido', 'Voto Bruto']
    
    # Normaliza o voto para o gráfico
    df_filtrado['Voto Final'] = df_filtrado['Voto Bruto'].apply(
        lambda x: mapeamento_voto.get(x, 'Outro/Não Votou')
    )
    
    # Exclui votos não relevantes para o gráfico principal (opcional)
    df_plot = df_filtrado[~df_filtrado['Voto Final'].isin(['Outro/Não Votou'])]

    return df_filtrado, df_plot

def criar_grafico_pizza(df_plot):
    """Gráfico de Pizza da Proporção dos Votos."""
    
    # Agrupa por Voto Final
    df_contagem = df_plot['Voto Final'].value_counts().reset_index()
    df_contagem.columns = ['Voto', 'Total']

    fig = px.pie(
        df_contagem,
        values='Total',
        names='Voto',
        title='Proporção dos Votos Nominais em Plenário',
        hole=.5,
        color='Voto',
        color_discrete_map={'A Favor': 'green', 'Contra': 'red', 'Abstenção': 'orange', 'Obstrução/Ausente': 'grey'}
    )
    fig.update_traces(textinfo='label+percent', pull=[0.1 if v == 'A Favor' or v == 'Contra' else 0 for v in df_contagem['Voto']])
    return fig

# --- 4. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Monitor de Votação Nominal")

st.title("👁️‍🗨️ Monitor de Votação Nominal (Dados Reais)")
st.header("Fiscalização de Parlamentares via API da Câmara")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use se a busca falhar repetidamente ou os dados não se atualizarem.")
    st.markdown("---")

# --- BLOCO PRINCIPAL DE PESQUISA ---

st.subheader("Pesquisa de Proposição Legislativa")
st.caption("Digite o número exato do Projeto de Lei (PL ou PEC) para buscar a última votação nominal em Plenário.")

col_input, col_btn = st.columns([3, 1])

with col_input:
    proposicao_input = st.text_input("Número da Proposição (Ex: PL 1234/2023)", 
                                    placeholder="PL 1234/2023 ou PEC 01/2023")

with col_btn:
    # Adiciona um espaço para alinhar o botão
    st.markdown("<br>", unsafe_allow_html=True) 
    botao_buscar = st.button("Buscar Votação", type="primary")

if botao_buscar and proposicao_input:
    
    # 1. PARSE DA ENTRADA
    try:
        # Tenta dividir a entrada: [PL, 1234, 2023]
        partes = proposicao_input.upper().replace("/", " ").split()
        sigla_tipo = partes[0].replace('PEC', 'PEC').replace('PL', 'PL').replace('PLP', 'PLP')
        numero = int(partes[1])
        ano = int(partes[2])
    except:
        st.error("Formato incorreto. Use o formato: [SIGLA NÚMERO/ANO], Ex: PL 1234/2023.")
        st.stop()

    with st.spinner(f"Buscando a votação nominal para {sigla_tipo} {numero}/{ano} na API..."):
        
        # 2. BUSCA ID DA PROPOSIÇÃO
        id_proposicao = buscar_id_proposicao(sigla_tipo, numero, ano)
        
        if id_proposicao is None:
            st.error(f"Proposição '{sigla_tipo} {numero}/{ano}' não encontrada na base de dados da Câmara.")
            st.stop()
        
        # 3. BUSCA ID DA VOTAÇÃO EM PLENÁRIO
        id_votacao = buscar_votacoes_proposicao(id_proposicao)

        if id_votacao is None:
            st.error(f"Nenhuma votação nominal recente em Plenário foi encontrada para esta proposição (ID: {id_proposicao}).")
            st.stop()

        # 4. BUSCA VOTOS NOMINAIS (DADOS FINAIS)
        dados_votos = buscar_votos_nominais(id_votacao)

        if dados_votos is None or not dados_votos:
            st.error("Falha ao buscar a lista de votos ou votação não foi nominal/aberta.")
            st.stop()
            
        # 5. PROCESSAMENTO E GERAÇÃO DE GRÁFICOS
        df_tabela, df_plot = processar_votos(dados_votos)
        
        st.success("Votação nominal encontrada e processada com sucesso!")
        
        # --- OUTPUT KPI e GRÁFICO ---
        
        # Totalização de Votos
        votos_contados = df_plot['Voto Final'].value_counts()
        total_votantes = votos_contados.sum()
        votos_sim = votos_contados.get('A Favor', 0)
        votos_nao = votos_contados.get('Contra', 0)
        
        st.subheader(f"Resultado em Plenário (Votação {id_votacao})")
        
        col_s, col_n, col_abs, col_total = st.columns(4)
        col_s.metric("Votos 'Sim'", votos_sim, delta=f"+{round((votos_sim/total_votantes)*100, 1)}%" if total_votantes else None, delta_color="normal")
        col_n.metric("Votos 'Não'", votos_nao, delta=f"-{round((votos_nao/total_votantes)*100, 1)}%" if total_votantes else None, delta_color="inverse")
        col_abs.metric("Abstenções/Ausentes", votos_contados.get('Abstenção', 0) + votos_contados.get('Obstrução/Ausente', 0), delta_color="off")
        col_total.metric("Total de Votos Registrados", total_votantes)
        
        st.markdown("---")

        # Gráfico de Pizza
        st.subheader("1. Proporção dos Votos Registrados")
        fig_pizza = criar_grafico_pizza(df_plot)
        st.plotly_chart(fig_pizza, use_container_width=True)

        # Tabela Interativa
        st.subheader("2. Detalhamento Nominal da Votação")
        st.caption("Use os cabeçalhos das colunas para ordenar a lista (por Partido ou UF) e filtre o voto nominal.")
        st.dataframe(
            df_tabela[['Nome do Deputado', 'Partido', 'UF', 'Voto Final']].sort_values(by='Voto Final', ascending=False),
            use_container_width=True,
            hide_index=True
        )
