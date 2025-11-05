import streamlit as st
import pandas as pd
import requests
import time
from urllib.parse import quote

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_BASE_API = "https://dadosabertos.camara.leg.br/api/v2/"
URL_DEPUTADOS = URL_BASE_API + "deputados"

# --- 2. FUNÇÕES DE BUSCA DA API (DADOS REAIS E ENCADEDOS) ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def buscar_id_e_dados_basicos(nome):
    """
    Busca o ID, Partido e UF do deputado pelo nome.
    Retorna o ID, nome e sigla do Partido.
    """
    nome_formatado = quote(nome.strip()) 
    
    params = {
        'nome': nome_formatado,
        'ordem': 'ASC',
        'ordenarPor': 'nome',
        'itens': 1, # Buscamos apenas o primeiro resultado
    }
    
    try:
        response = requests.get(URL_DEPUTADOS, params=params, timeout=5)
        response.raise_for_status()
        dados = response.json().get('dados', [])
        
        if dados:
            deputado = dados[0]
            return {
                'id': deputado['id'],
                'nome': deputado['nome'],
                'partido': deputado['siglaPartido'],
                'uf': deputado['siglaUf'],
                'urlFoto': deputado['urlFoto']
            }
        return None
        
    except requests.exceptions.RequestException:
        return None

@st.cache_data(ttl=3600)
def buscar_lista_detalhada(deputado_id, endpoint):
    """
    Função genérica para buscar listas detalhadas (Frentes ou Órgãos/Comissões).
    """
    url = f"{URL_DEPUTADOS}/{deputado_id}/{endpoint}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        dados = response.json().get('dados', [])
        
        # Extrai os nomes das frentes ou órgãos
        if endpoint == 'frentes':
             return [d['titulo'] for d in dados]
        elif endpoint == 'orgaos':
             # Filtra apenas Comissões Permanentes (tipo ORG_PERM)
             return [d['sigla'] for d in dados if d['tipoOrgao'] == 'Comissão Permanente']
        return []

    except requests.exceptions.RequestException:
        return []

# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Monitor Parlamentar")

st.title("🔎 Monitor de Perfil Parlamentar")
st.header("Comissões e Frentes (Dados Reais da Câmara)")

# --- BOTÃO DE LIMPEZA DE CACHE ---
with st.sidebar:
    st.markdown("### 🛠️ Ferramentas")
    st.button("Resetar Dados (Limpar Cache da API)", on_click=limpar_cache_api)
    st.caption("Use se a busca falhar repetidamente.")

st.markdown("---")

# --- BLOCO PRINCIPAL DE PESQUISA ---

st.subheader("Busca por Nome do Parlamentar")
st.caption("Digite o nome completo ou parte do nome para buscar a ficha de filiação e atuação.")

col_input, col_btn = st.columns([3, 1])

with col_input:
    nome_deputado = st.text_input("Nome do Deputado:", placeholder="Ex: Célio Studart, Maria do Rosário, etc.")

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True) 
    botao_buscar = st.button("Buscar Ficha", type="primary")

st.markdown("---")

if botao_buscar and nome_deputado:
    
    with st.spinner(f"Buscando informações de {nome_deputado}..."):
        
        # 1. BUSCA ID e DADOS BÁSICOS
        dados_basicos = buscar_id_e_dados_basicos(nome_deputado)
        
        if dados_basicos is None:
            st.error(f"Deputado(a) '{nome_deputado}' não encontrado(a) ou houve falha na API da Câmara. Tente o nome completo.")
            st.stop()
            
        deputado_id = dados_basicos['id']

        # 2. BUSCA FRENTES
        frentes = buscar_lista_detalhada(deputado_id, 'frentes')
        
        # 3. BUSCA COMISSÕES (Órgãos)
        comissoes = buscar_lista_detalhada(deputado_id, 'orgaos')

        # --- EXIBIÇÃO DE RESULTADOS ---
        
        col_foto, col_info = st.columns([1, 3])
        
        with col_foto:
            if dados_basicos.get('urlFoto'):
                 st.image(dados_basicos['urlFoto'], width=150)
            st.markdown(f"**ID da Câmara:** {deputado_id}")
            
        with col_info:
            st.subheader(dados_basicos['nome'])
            st.markdown(f"**Partido:** **{dados_basicos['partido']}** | **UF:** {dados_basicos['uf']}")
        
        st.markdown("---")

        col_frentes, col_comissoes = st.columns(2)

        with col_frentes:
            st.metric("Total de Frentes Parlamentares", len(frentes))
            st.subheader("1. Frentes Parlamentares")
            if frentes:
                 # Interatividade: Tabela com as Frentes
                 df_frentes = pd.DataFrame(frentes, columns=['Nome da Frente Parlamentar'])
                 st.dataframe(df_frentes, use_container_width=True, hide_index=True)
            else:
                st.info("Não foi registrada participação em Frentes Parlamentares.")

        with col_comissoes:
            st.metric("Total de Comissões Permanentes", len(comissoes))
            st.subheader("2. Comissões (Órgãos)")
            if comissoes:
                 # Interatividade: Tabela com as Comissões
                 df_comissoes = pd.DataFrame(comissoes, columns=['Sigla da Comissão'])
                 st.dataframe(df_comissoes, use_container_width=True, hide_index=True)
            else:
                st.info("Não foi registrada participação em Comissões Permanentes.")

st.markdown("---")
st.success("O aplicativo de monitoramento parlamentar está pronto! Use a barra de pesquisa para testar.")
