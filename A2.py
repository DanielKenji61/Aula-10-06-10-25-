import streamlit as st
import pandas as pd
import requests
import time

# --- 1. CONFIGURAÇÃO E VARIÁVEIS GLOBAIS ---

URL_BASE_API = "https://dadosabertos.camara.leg.br/api/v2/"
URL_PROPOSICOES = URL_BASE_API + "proposicoes"

# --- 2. FUNÇÕES DE BUSCA DA API ---

def limpar_cache_api():
    """Limpa o cache do Streamlit e reinicia a execução."""
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def buscar_proposicao_e_votos(tipo_proposicao, numero, ano):
    """
    1. Busca a PEC específica pelo seu número/ano.
    2. Busca as votações associadas a ela.
    3. Extrai os votos nominais da votação principal no Plenário.
    """
    
    # 1. BUSCAR ID DA PROPOSIÇÃO
    params_busca = {
        'tipo': tipo_proposicao,
        'numero': numero,
        'ano': ano,
        'ordenarPor': 'id',
        'itens': 1
    }
    
    try:
        response_busca = requests.get(URL_PROPOSICOES, params=params_busca, timeout=10)
        response_busca.raise_for_status()
        dados_busca = response_busca.json().get('dados', [])
        
        if not dados_busca:
            return None, "Proposição não encontrada na Câmara dos Deputados."
        
        proposicao_id = dados_busca[0]['id']
        nome_completo = dados_busca[0]['uri']

    except requests.exceptions.RequestException:
        return None, "Falha ao buscar o ID da Proposição na API."

    # 2. BUSCAR VOTACÕES
    url_votacoes = f"{URL_PROPOSICOES}/{proposicao_id}/votacoes"
    try:
        response_votacoes = requests.get(url_votacoes, timeout=10)
        response_votacoes.raise_for_status()
        votacoes = response_votacoes.json().get('dados', [])
    except requests.exceptions.RequestException:
        return None, "Falha ao buscar votações da PEC na API."
    
    # 3. FILTRAR E ENCONTRAR A VOTAÇÃO PRINCIPAL
    # A votação de admissibilidade da PEC 03/2021 é a mais referenciada (Sim: 304, Não: 154)
    # Procuramos por votações de "Parecer" em "Plenário"
    id_votacao_principal = None
    titulo_votacao = ""
    
    for v in votacoes:
        # Tenta encontrar a votação de admissibilidade ou similar
        if "Admissibilidade" in v.get('resumo', '') and v.get('tipo', '') == 'Admissibilidade de Proposta de Emenda à Constituição':
            id_votacao_principal = v['id']
            titulo_votacao = v['resumo']
            break
        # Se não encontrar a mais específica, pega a última votação nominal de Plenário
        if v.get('aprovacao') == "Aprovado" and v.get('siglaOrgao') == 'PLEN' and 'voto nominal' in v.get('resumo', ''):
             id_votacao_principal = v['id']
             titulo_votacao = v['resumo']
             
    if not id_votacao_principal:
         return nome_completo, "Nenhuma votação nominal relevante no Plenário foi encontrada para esta PEC."

    # 4. BUSCAR VOTOS NOMINAIS DETALHADOS
    url_votos = f"{URL_BASE_API}votacoes/{id_votacao_principal}/votos"
    votos_por_partido = {}
    
    try:
        response_votos = requests.get(url_votos, timeout=10)
        response_votos.raise_for_status()
        votos_detalhados = response_votos.json().get('dados', [])
        
        # Agrupar votos por partido
        for voto in votos_detalhados:
            partido = voto['deputado']['siglaPartido']
            tipo_voto = voto['tipoVoto']
            
            if partido not in votos_por_partido:
                votos_por_partido[partido] = {'Sim': 0, 'Não': 0, 'Abstenção': 0, 'Outro': 0}
            
            if tipo_voto == 'Sim':
                votos_por_partido[partido]['Sim'] += 1
            elif tipo_voto == 'Não':
                votos_por_partido[partido]['Não'] += 1
            elif tipo_voto == 'Abstenção':
                votos_por_partido[partido]['Abstenção'] += 1
            else:
                 # Inclui Obstrução, Presidente, e outros
                votos_por_partido[partido]['Outro'] += 1
                
        # Converte o resultado em DataFrame para exibição
        df_resultado = pd.DataFrame.from_dict(votos_por_partido, orient='index')
        df_resultado.index.name = 'Partido'
        df_resultado = df_resultado.reset_index()

        return df_resultado, titulo_votacao
        
    except requests.exceptions.RequestException:
        return nome_completo, "Falha ao buscar os votos nominais detalhados."


# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Votação PEC 03/2021")

st.title("🗳️ Análise de Votação Nominal por Partido")
st.header("PEC 03/2021 (Prerrogativas Parlamentares)")

# --- BUSCA DA PEC ESPECÍFICA ---
TIPO_BUSCA = "PEC"
NUMERO_BUSCA = 3
ANO_BUSCA = 2021

st.markdown(f"**Proposição Alvo:** **{TIPO_BUSCA} {NUMERO_BUSCA}/{ANO_BUSCA}**")
st.markdown("---")

# --- EXECUÇÃO E EXIBIÇÃO ---

with st.spinner(f"Buscando e processando os votos nominais da {TIPO_BUSCA} {NUMERO_BUSCA}/{ANO_BUSCA} na API da Câmara..."):
    df_votos, status_ou_titulo = buscar_proposicao_e_votos(TIPO_BUSCA, NUMERO_BUSCA, ANO_BUSCA)

if isinstance(df_votos, pd.DataFrame):
    st.subheader(f"Resultado da Votação: {status_ou_titulo}")
    
    # 1. GRÁFICO DE BARRAS: VISÃO GERAL POR PARTIDO
    
    # Derrete (melt) o DataFrame para Plotly
    df_plot = df_votos.melt(id_vars='Partido', var_name='Tipo de Voto', value_name='Total de Votos')
    
    # Define as cores para os votos
    cores_votos = {'Sim': 'green', 'Não': 'red', 'Abstenção': 'gold', 'Outro': 'gray'}
    
    fig_barras = px.bar(
        df_plot,
        x='Partido',
        y='Total de Votos',
        color='Tipo de Voto',
        title='Distribuição de Votos por Partido na PEC 03/2021',
        color_discrete_map=cores_votos,
        category_orders={"Tipo de Voto": ["Sim", "Não", "Abstenção", "Outro"]}
    )
    
    fig_barras.update_layout(xaxis_title="Partido", yaxis_title="Número de Votos")
    st.plotly_chart(fig_barras, use_container_width=True)

    # 2. TABELA DETALHADA
    st.markdown("### Detalhamento da Votação Nominal por Partido")
    
    # Calcula o total de votos e a coluna de totalização
    df_votos['Total'] = df_votos[['Sim', 'Não', 'Abstenção', 'Outro']].sum(axis=1)
    
    # Remove a coluna 'Outro' para simplificar a visualização
    df_votos_final = df_votos.drop(columns=['Outro'])
    
    st.dataframe(
        df_votos_final.sort_values(by='Total', ascending=False),
        use_container_width=True,
        hide_index=True
    )

elif status_ou_titulo:
    st.error(f"Não foi possível completar a análise para a PEC 03/2021: {status_ou_titulo}")
    
st.markdown("---")
st.caption("Dados extraídos diretamente da API Dados Abertos da Câmara dos Deputados.")
