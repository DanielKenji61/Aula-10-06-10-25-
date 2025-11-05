import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date
import time
from urllib.parse import quote

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_BASE_PROPOSICOES = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
URL_BASE_DEPUTADOS = "https://dadosabertos.camara.leg.br/api/v2/deputados"
# Fixado: Anos solicitados pelo usuário
ANOS_DESEJADOS = [2024, 2023] 

# Códigos de Referência na API (Reais)
CODIGO_PL = 207      
CODIGO_PEC = 304     
SITUACAO_APROVADA = 300  # Transf. em Norma Jurídica / Aprovada nas 2 Casas
SITUACAO_ARQUIVADA = 239 
SITUACAO_TODAS = None    

# --- 2. FUNÇÕES DE BUSCA DA API (DADOS REAIS E ROBUSTOS) ---

# Adicionamos um botão de reset para limpar o cache quando necessário (resolve o problema dos 313 fixos)
def limpar_cache_api():
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600) # Cache de 1 hora
def contar_proposicoes_reais(ano, cod_tipo, id_situacao=None, id_autor=None):
    """
    Faz a chamada real à API da Câmara para contar proposições.
    """
    
    # Usamos o primeiro dia do ano para a data inicial
    data_inicio = f'{ano}-01-01'
    
    # A data final é crucial: se for o ano atual (2025), o filtro deve ir até o mês atual
    data_fim = f'{ano}-12-31'
    if ano == date.today().year:
         data_fim = f'{date.today().year}-{date.today().month:02d}-{date.today().day:02d}'
    
    params = {
        'dataInicio': data_inicio,
        'dataFim': data_fim,
        'codTipo': cod_tipo,
        'ordenarPor': 'id', 
        'itens': 100, 
    }
    
    if id_situacao is not None:
        params['idSituacao'] = id_situacao
        
    if id_autor is not None:
        params['idAutor'] = id_autor
    
    total_proposicoes = 0
    pagina = 1
    
    # Paginação para garantir que todos os dados sejam coletados
    while True:
        try:
            response = requests.get(URL_BASE_PROPOSICOES, params={**params, 'pagina': pagina})
            response.raise_for_status() 
            dados = response.json().get('dados', [])
            total_proposicoes += len(dados)
            
            if len(dados) < params['itens']:
                break
            
            pagina += 1
            time.sleep(0.1) 
            
        except requests.exceptions.RequestException as e:
            # Em caso de erro na API, retorna 0 para evitar quebra do programa
            return 0
            
    return total_proposicoes

@st.cache_data(ttl=3600)
def buscar_id_deputado(nome):
    """Busca o ID do deputado pelo nome."""
    nome_formatado = quote(nome.strip())
    
    params = {
        'nome': nome_formatado,
        'ordem': 'ASC',
        'ordenarPor': 'nome',
        'itens': 10,
    }
    
    try:
        response = requests.get(URL_BASE_DEPUTADOS, params=params)
        response.raise_for_status()
        dados = response.json().get('dados', [])
        
        if dados:
            return dados[0]['id']
        return None
        
    except requests.exceptions.RequestException:
        return None

# --- 3. FUNÇÕES DE PROCESSAMENTO E GRÁFICOS ---

def processar_dados_globais(ano):
    """Busca os totais reais de PLs e PECs na API e calcula as taxas de sucesso."""
    
    # Busca 1: Total Apresentado (usando SITUACAO_TODAS para ter o número máximo)
    total_pl_apres = contar_proposicoes_reais(ano, CODIGO_PL, SITUACAO_TODAS)
    total_pec_apres = contar_proposicoes_reais(ano, CODIGO_PEC, SITUACAO_TODAS)
    
    # Busca 2: Total Aprovado
    total_pl_aprov = contar_proposicoes_reais(ano, CODIGO_PL, SITUACAO_APROVADA)
    total_pec_aprov = contar_proposicoes_reais(ano, CODIGO_PEC, SITUACAO_APROVADA)
    
    # Busca 3: Total Arquivado
    total_pl_arquiv = contar_proposicoes_reais(ano, CODIGO_PL, SITUACAO_ARQUIVADA)
    total_pec_arquiv = contar_proposicoes_reais(ano, CODIGO_PEC, SITUACAO_ARQUIVADA)
    
    # Cria o DataFrame para os gráficos
    data_sucesso = {
        'Tipo': ['PL', 'PEC'],
        'Apresentadas': [total_pl_apres, total_pec_apres],
        'Aprovadas': [total_pl_aprov, total_pec_aprov],
        'Arquivadas': [total_pl_arquiv, total_pec_arquiv],
        'Taxa_Sucesso': [
            (total_pl_aprov / total_pl_apres) * 100 if total_pl_apres > 0 else 0,
            (total_pec_aprov / total_pec_apres) * 100 if total_pec_apres > 0 else 0,
        ]
    }
    
    return pd.DataFrame(data_sucesso)

def criar_grafico_taxa_sucesso(df_dados, ano):
    """Gráfico 1: Taxa de Sucesso (Aprovadas / Apresentadas) por tipo de Proposição."""
    fig = px.bar(
        df_dados,
        x='Tipo',
        y='Taxa_Sucesso',
        color='Tipo',
        title=f'1. Taxa de Sucesso (Aprovação Final) das Proposições ({ano})',
        labels={'Taxa_Sucesso': 'Taxa de Aprovação (%)', 'Tipo': 'Tipo de Proposição'}
    )
    fig.update_yaxes(range=[0, 100])
    return fig

def criar_grafico_desempenho_deputado(df_deputado, nome, ano):
    """Gráfico 3: Desempenho individual do Deputado."""
    fig = px.bar(
        df_deputado,
        x='Situação',
        y='Total',
        color='Situação',
        title=f'Desempenho Legislativo de {nome} ({ano})',
        labels={'Total': 'Total de Projetos (PLs e PECs)', 'Situação': 'Situação do Projeto'}
    )
    return fig

# --- 4. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Analisador de Jurimetria")

st.title("⚖️ Jurimetria: Análise da Produção Legislativa")
st.header("Dados Reais da API da Câmara dos Deputados")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use se os dados globais parecerem incorretos ou não se atualizarem.")

st.markdown("---")

# --- SELETOR DE ANO ---
st.subheader("Período de Análise:")

# Usamos a lista fixa de anos desejada
anos_disponiveis = ANOS_DESEJADOS

ano_selecionado = st.radio(
    "Escolha o ano base para todos os gráficos:",
    anos_disponiveis,
    index=anos_disponiveis.index(2024), 
    horizontal=True
)

st.markdown("---")

# --- BLOCO 1: ANÁLISE GERAL (PL vs PEC) ---

st.subheader(f"📊 Análise Global: Produtividade por Tipo ({ano_selecionado})")

# A chamada agora é mais robusta 
df_analise_global = processar_dados_globais(ano_selecionado)

total_apresentado = df_analise_global['Apresentadas'].sum()
total_aprovado = df_analise_global['Aprovadas'].sum()

if total_apresentado == 0:
    st.error(f"Não foi possível carregar o total de proposições para o ano de {ano_selecionado}. Tente o ano de 2023 ou clique em 'Resetar Dados'.")
else:
    # --- KPIs ---
    taxa_global = (total_aprovado / total_apresentado) * 100 if total_apresentado > 0 else 0
    
    col1, col2, col3 = st.columns(3)

    col1.metric("Total de Proposições Apresentadas", f"{total_apresentado:,}".replace(",", "."))
    col2.metric("Aprovadas (Transformadas em Norma)", f"{total_aprovado:,}".replace(",", "."))
    col3.metric("Taxa de Sucesso Global", f"{taxa_global:.2f}%")
    
    # Gráfico 1: Taxa de Sucesso
    fig1 = criar_grafico_taxa_sucesso(df_analise_global, ano_selecionado)
    st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# --- BLOCO 2: ANÁLISE INDIVIDUAL POR DEPUTADO ---

st.subheader(f"👤 Análise Individual: Desempenho do Parlamentar ({ano_selecionado})")
st.caption("Pesquise o nome completo ou parte do nome de um Deputado para ver sua produtividade no ano selecionado.")

nome_deputado = st.text_input("Nome do Deputado:", placeholder="Ex: Nikolas Ferreira, Gleisi Hoffmann, etc.")
botao_buscar = st.button("Buscar Desempenho")

if botao_buscar and nome_deputado:
    
    with st.spinner(f"Buscando ID e projetos de {nome_deputado}..."):
        
        # 1. BUSCA ID
        id_deputado = buscar_id_deputado(nome_deputado)
        
        if id_deputado is None:
            st.error(f"Deputado(a) '{nome_deputado}' não encontrado(a) na base de dados da Câmara.")
        else:
            # 2. BUSCA TOTAL APRESENTADO (PL + PEC)
            total_apresentado = (
                contar_proposicoes_reais(ano_selecionado, CODIGO_PL, SITUACAO_TODAS, id_deputado) +
                contar_proposicoes_reais(ano_selecionado, CODIGO_PEC, SITUACAO_TODAS, id_deputado)
            )

            # 3. BUSCA TOTAL APROVADO (PL + PEC)
            total_aprovado = (
                contar_proposicoes_reais(ano_selecionado, CODIGO_PL, SITUACAO_APROVADA, id_deputado) +
                contar_proposicoes_reais(ano_selecionado, CODIGO_PEC, SITUACAO_APROVADA, id_deputado)
            )
            
            # 4. CÁLCULO
            taxa_aprovacao = (total_aprovado / total_apresentado) * 100 if total_apresentado > 0 else 0
            
            # 5. EXIBIÇÃO
            st.success(f"Desempenho de **{nome_deputado}** (ID: {id_deputado}) em {ano_selecionado} obtido com sucesso:")
            
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Projetos Apresentados", f"{total_apresentado:,}".replace(",", "."))
            col_b.metric("Projetos Aprovados", f"{total_aprovado:,}".replace(",", "."))
            col_c.metric("Taxa de Aprovação Individual", f"{taxa_aprovacao:.2f}%")

            # 6. GRÁFICO INDIVIDUAL
            df_deputado_plot = pd.DataFrame({
                'Situação': ['Projetos Apresentados', 'Projetos Aprovados'],
                'Total': [total_apresentado, total_aprovado]
            })
            
            if total_apresentado > 0:
                fig3 = criar_grafico_desempenho_deputado(df_deputado_plot, nome_deputado, ano_selecionado)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("O deputado não apresentou projetos (PL ou PEC) no ano selecionado que foram contabilizados pela API.")
