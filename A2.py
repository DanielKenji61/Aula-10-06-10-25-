import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import datetime

# --- 1. CONFIGURAÇÃO E CARREGAMENTO DE DADOS SIMULADOS ---

# Metadados do Projeto
NOME_TRIBUNAL = "TJ do Rio de Janeiro (TJRJ)"
ENDPOINT_SIMULADO = "https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search"

# Função que SIMULA a busca na API do CNJ
@st.cache_data
def carregar_dados_simulados():
    """
    Cria um DataFrame que simula o resultado de uma busca massiva na API do CNJ 
    para processos de MPU (Lei Maria da Penha) no TJRJ, incluindo 2023, 2024 e 2025.
    """
    st.info("Simulando busca de metadados processuais na API do DataJud do CNJ...")
    
    # 1. Definindo dados base para 2023, 2024 e 2025
    data_range = pd.to_datetime(pd.date_range(start='2023-01-01', end='2025-12-31', freq='D'))
    # Aumentando o número de registros para simular uma base maior
    num_registros = 20000 
    
    # Gera datas aleatórias de ajuizamento
    datas_ajuizamento = np.random.choice(data_range, num_registros)
    
    # Datas de Decisão (Simulação de tempo de resposta)
    # 70% das decisões em até 48h (Rápida), 30% mais demoradas
    delta_horas = np.where(
        np.random.rand(num_registros) < 0.7, 
        np.random.randint(1, 48, num_registros),
        np.random.randint(48, 200, num_registros) 
    )
    datas_decisao = datas_ajuizamento + pd.to_timedelta(delta_horas, unit='H')

    # Tipos de MPU e Desfechos
    tipos_mpu = ['Afastamento do Lar', 'Restrição de Contato', 'Suspensão de Posse de Arma', 'Outras']
    desfechos = ['Proferida (Concedida)', 'Não Proferida (Indeferida)', 'Extinta']
    
    # Cria o DataFrame simulado
    df = pd.DataFrame({
        'data_ajuizamento': datas_ajuizamento,
        'data_decisao_mpu': datas_decisao,
        'tipo_mpu_expedida': np.random.choice(tipos_mpu, num_registros, p=[0.55, 0.30, 0.10, 0.05]),
        'desfecho': np.random.choice(desfechos, num_registros, p=[0.85, 0.10, 0.05]),
        'ano': pd.to_datetime(datas_ajuizamento).year,
        'mes': pd.to_datetime(datas_ajuizamento).month,
    })
    
    # Filtra apenas MPU 'pedidas' e 'proferidas'
    df['status'] = np.where(df['desfecho'] == 'Proferida (Concedida)', 'MPU Proferida', 'MPU Pedida')
    df['tempo_tramitacao_horas'] = (df['data_decisao_mpu'] - df['data_ajuizamento']).dt.total_seconds() / 3600
    
    return df

# --- 2. FUNÇÕES DE GERAÇÃO DE GRÁFICOS ---

def criar_grafico_1_comparacao_anual(df_geral):
    """Gráfico 1: Compara MPU Pedidas vs. Proferidas ao longo de TODOS os anos (Visão Macro)."""
    
    # Agrupa por ano e conta
    df_agrupado = df_geral.groupby(['ano', 'status']).size().reset_index(name='Total')
    
    # Cria o Gráfico de Linhas Interativo (Plotly Express)
    fig = px.line(
        df_agrupado,
        x='ano',
        y='Total',
        color='status',
        title='MPU Solicitadas e Proferidas (Comparação Anual)',
        markers=True
    )
    fig.update_xaxes(dtick=1, tickformat="%Y")
    fig.update_layout(yaxis_title="Volume de MPUs", xaxis_title="Ano")
    return fig

def criar_grafico_2_tempo_segmentado(df_filtrado):
    """Gráfico 2: Segmenta o tempo médio de expedição em faixas de horas do ANO SELECIONADO."""
    
    # 1. Cria as faixas de tempo
    bins = [0, 24, 48, 72, np.inf]
    labels = ['0-24h (Meta Jurisdicional)', '24-48h', '48-72h', '>72h (Morosidade)']
    df_filtrado['faixa_tempo'] = pd.cut(df_filtrado['tempo_tramitacao_horas'], bins=bins, labels=labels, right=False)
    
    # 2. Conta o número de casos em cada faixa
    df_faixas = df_filtrado['faixa_tempo'].value_counts().reset_index()
    df_faixas.columns = ['Faixa de Tempo', 'Total de Casos']
    
    # Ordena as faixas
    df_faixas['Faixa de Tempo'] = pd.Categorical(df_faixas['Faixa de Tempo'], categories=labels, ordered=True)
    df_faixas = df_faixas.sort_values('Faixa de Tempo')
    
    # Calcula a média de tempo para exibir no detalhe
    media_horas = df_filtrado['tempo_tramitacao_horas'].mean()
    
    # 3. Cria o Gráfico de Barras Interativo
    fig = px.bar(
        df_faixas,
        x='Faixa de Tempo',
        y='Total de Casos',
        color='Faixa de Tempo',
        title=f'Distribuição do Tempo de Expedição da Decisão (da MPU)',
        color_discrete_sequence=['green', 'gold', 'orange', 'red']
    )
    fig.update_layout(xaxis_title="Tempo de Tramitação (Ajuizamento até Decisão)")
    
    # Adiciona anotação para simular o detalhe da média do Tribunal
    fig.add_annotation(
        text=f"Média Geral de Expedição: **{media_horas:.1f} horas**",
        xref="paper", yref="paper", x=0.5, y=1.05, showarrow=False, font=dict(size=14, color="black")
    )
    
    return fig

def criar_grafico_3_tipos_mpu(df_filtrado):
    """Gráfico 3: Mostra a proporção de cada tipo de MPU expedida no ANO SELECIONADO."""
    
    # Filtra apenas MPU proferidas/concedidas
    df_proferidas = df_filtrado[df_filtrado['desfecho'] == 'Proferida (Concedida)']
    
    # Agrupa por tipo e calcula a porcentagem
    df_tipos = df_proferidas['tipo_mpu_expedida'].value_counts().reset_index()
    df_tipos.columns = ['Tipo de MPU', 'Total']
    df_tipos['Porcentagem'] = (df_tipos['Total'] / df_tipos['Total'].sum()) * 100
    
    # Cria o Gráfico de Pizza (Donut) Interativo
    fig = px.pie(
        df_tipos,
        values='Total',
        names='Tipo de MPU',
        title='Proporção dos Tipos de MPU Expedidas (Concedidas)',
        hole=.4 # Transforma em gráfico Donut
    )
    fig.update_traces(textinfo='label+percent', textfont_size=15)
    return fig

def criar_grafico_4_mensal(df_filtrado, ano):
    """Gráfico 4: Mostra MPU Pedidas vs. Proferidas ao longo dos meses do ANO SELECIONADO."""
    
    # O dataframe já está filtrado, mas garante que a visualização seja do ano
    df_mensal = df_filtrado[df_filtrado['ano'] == ano]
    
    # Agrupa por mês e status (pedida/proferida)
    df_agrupado = df_mensal.groupby(['mes', 'status']).size().reset_index(name='Total')
    
    # Mapeia números de meses para nomes (melhor visualização)
    meses_map = {i: datetime.date(2000, i, 1).strftime('%B') for i in range(1, 13)}
    df_agrupado['mes_nome'] = df_agrupado['mes'].map(meses_map)
    
    # Cria o Gráfico de Linhas Interativo (Plotly Express)
    fig = px.line(
        df_agrupado,
        x='mes_nome',
        y='Total',
        color='status',
        title=f'Evolução Mensal de MPUs - Pedidos e Resultados ({ano})',
        markers=True
    )
    fig.update_layout(yaxis_title="Volume de MPUs", xaxis_title="Mês", xaxis={'categoryorder':'array', 'categoryarray': [meses_map[i] for i in range(1, 13)]})
    return fig

# --- 3. INTERFACE STREAMLIT ---

# Carrega os dados uma única vez
df_dados = carregar_dados_simulados()

st.set_page_config(layout="wide")

st.title("🛡️ Analisador Jurimétrico de Medidas Protetivas (MPU)")
st.subheader(f"Foco: Efetividade da Lei Maria da Penha no {NOME_TRIBUNAL}")

# Explicação da Simulação (Crucial para o trabalho)
st.markdown(f"""
> **Nota de Metodologia:** Devido às restrições de acesso à chave da API Pública do DataJud (CNJ), este aplicativo simula a resposta do endpoint do {NOME_TRIBUNAL} (**{ENDPOINT_SIMULADO}**) utilizando um *dataset* interno, preservando a lógica de filtragem e a análise jurimétrica interativa.
""")

st.markdown("---")

# Barra Lateral (Filtros Interativos)
with st.sidebar:
    st.header("⚙️ Configuração da Análise")
    
    # Seleção de Ano (Filtro 1)
    anos_disponiveis = sorted(df_dados['ano'].unique(), reverse=True)
    # Garante que o usuário escolha entre os anos disponíveis na simulação
    ano_selecionado = st.selectbox(
        "Selecione o Ano para Análise Detalhada:",
        anos_disponiveis,
        index=0 # Seleciona o ano mais recente como padrão
    )
    
    st.success(f"Analisando o período de **{ano_selecionado}**.")

# 1. Filtra o DataFrame Geral pelo Ano Selecionado
df_ano_selecionado = df_dados[df_dados['ano'] == ano_selecionado]

st.header(f"Resultados da Jurimetria (Ano {ano_selecionado} em destaque)")

# --- MÉTRICAS CHAVE (KPIs) ---
total_pedidas = len(df_ano_selecionado)
total_proferidas = len(df_ano_selecionado[df_ano_selecionado['desfecho'] == 'Proferida (Concedida)'])
taxa_atendimento = (total_proferidas / total_pedidas) * 100 if total_pedidas > 0 else 0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total de MPUs Solicitadas", value=f"{total_pedidas:,}".replace(",", "."))

with col2:
    st.metric(label="MPUs Concedidas (Proferidas)", value=f"{total_proferidas:,}".replace(",", "."))

with col3:
    st.metric(label="Taxa de Atendimento (%)", value=f"{taxa_atendimento:.2f}%")

st.markdown("---")

# --- GRÁFICOS ---

# Gráfico 1: Comparação Anual (Usa TODOS os dados)
st.subheader("Gráfico 1: Comparação Anual de Pedidos e Proferimentos de MPU")
fig1 = criar_grafico_1_comparacao_anual(df_dados)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# Gráfico 2: Tempo de Expedição (Usa APENAS os dados do ano selecionado)
st.subheader(f"Gráfico 2: Distribuição do Tempo de Expedição (Horas) no ano de {ano_selecionado}")
fig2 = criar_grafico_2_tempo_segmentado(df_ano_selecionado) 
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Gráfico 4: Mensal (Usa APENAS os dados do ano selecionado)
st.subheader(f"Gráfico 4: Evolução Mensal de Pedidos e Proferimentos (Ano {ano_selecionado})")
fig4 = criar_grafico_4_mensal(df_dados, ano_selecionado)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# Gráfico 3: Proporção dos Tipos (Usa APENAS os dados do ano selecionado)
st.subheader(f"Gráfico 3: Proporção dos Tipos de Medidas Protetivas Concedidas no ano de {ano_selecionado}")
fig3 = criar_grafico_3_tipos_mpu(df_ano_selecionado)
st.plotly_chart(fig3, use_container_width=True)
