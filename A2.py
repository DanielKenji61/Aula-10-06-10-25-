import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import datetime


NOME_TRIBUNAL = "TJ do Rio de Janeiro (TJRJ)"
ENDPOINT_SIMULADO = "https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search"

@st.cache_data
def carregar_dados_simulados():
    """
    Cria um DataFrame que simula o resultado de uma busca massiva na API do CNJ 
    para processos de MPU (Lei Maria da Penha) no TJRJ, incluindo 2023, 2024 e 2025.
    """

    data_range = pd.to_datetime(pd.date_range(start='2023-01-01', end='2025-12-31', freq='D'))
    num_registros = 20000 
    
    datas_ajuizamento = np.random.choice(data_range, num_registros)

    delta_horas = np.where(
        np.random.rand(num_registros) < 0.7, 
        np.random.randint(1, 48, num_registros),
        np.random.randint(48, 200, num_registros) 
    )
    datas_decisao = datas_ajuizamento + pd.to_timedelta(delta_horas, unit='H')

    tipos_mpu = ['Afastamento do Lar', 'Restrição de Contato', 'Suspensão de Posse de Arma', 'Outras']
    desfechos = ['Proferida (Concedida)', 'Não Proferida (Indeferida)', 'Extinta']
    desfechos_finais = ['Condenação', 'Absolvição', 'Arquivamento/Extinção']

    df = pd.DataFrame({
        'data_ajuizamento': datas_ajuizamento,
        'data_decisao_mpu': datas_decisao,
        'tipo_mpu_expedida': np.random.choice(tipos_mpu, num_registros, p=[0.55, 0.30, 0.10, 0.05]),
        'desfecho': np.random.choice(desfechos, num_registros, p=[0.85, 0.10, 0.05]),
        'desfecho_final': np.random.choice(desfechos_finais, num_registros, p=[0.45, 0.10, 0.45]),
        'ano': pd.to_datetime(datas_ajuizamento).year,
        'mes': pd.to_datetime(datas_ajuizamento).month,
    })
    
    df['status'] = np.where(df['desfecho'] == 'Proferida (Concedida)', 'MPU Proferida', 'MPU Pedida')
    df['tempo_tramitacao_horas'] = (df['data_decisao_mpu'] - df['data_ajuizamento']).dt.total_seconds() / 3600
    
    return df


def criar_grafico_2_tempo_segmentado(df_filtrado):
    """Gráfico 2: Segmenta o tempo médio de expedição em faixas de horas do ANO SELECIONADO."""
    bins = [0, 24, 48, 72, np.inf]
    labels = ['0-24h (Meta Jurisdicional)', '24-48h', '48-72h', '>72h (Morosidade)']
    df_filtrado['faixa_tempo'] = pd.cut(df_filtrado['tempo_tramitacao_horas'], bins=bins, labels=labels, right=False)
    df_faixas = df_filtrado['faixa_tempo'].value_counts().reset_index()
    df_faixas.columns = ['Faixa de Tempo', 'Total de Casos']
    df_faixas['Faixa de Tempo'] = pd.Categorical(df_faixas['Faixa de Tempo'], categories=labels, ordered=True)
    df_faixas = df_faixas.sort_values('Faixa de Tempo')
    media_horas = df_filtrado['tempo_tramitacao_horas'].mean()
    
    fig = px.bar(df_faixas, x='Faixa de Tempo', y='Total de Casos', color='Faixa de Tempo',
                 title=f'Distribuição do Tempo de Expedição da Decisão (da MPU)',
                 color_discrete_sequence=['green', 'gold', 'orange', 'red'])
    fig.update_layout(xaxis_title="Tempo de Tramitação (Ajuizamento até Decisão)")
    fig.add_annotation(
        text=f"Média Geral de Expedição: **{media_horas:.1f} horas**",
        xref="paper", yref="paper", x=0.5, y=1.05, showarrow=False, font=dict(size=14, color="black")
    )
    return fig

def criar_grafico_3_tipos_mpu(df_filtrado):
    """Gráfico 3: Mostra a proporção de cada tipo de MPU expedida no ANO SELECIONADO."""
    df_proferidas = df_filtrado[df_filtrado['desfecho'] == 'Proferida (Concedida)']
    df_tipos = df_proferidas['tipo_mpu_expedida'].value_counts().reset_index()
    df_tipos.columns = ['Tipo de MPU', 'Total']
    
    fig = px.pie(df_tipos, values='Total', names='Tipo de MPU',
                 title='Proporção dos Tipos de MPU Expedidas (Concedidas)', hole=.4)
    fig.update_traces(textinfo='label+percent', textfont_size=15)
    return fig

def criar_grafico_4_mensal(df_filtrado, ano):
    """
    Gráfico 4: Mostra MPU Pedidas vs. Proferidas ao longo dos meses do ANO SELECIONADO.
    APLICA LÓGICA DE ZERAMENTO PARA NOV/DEZ DE 2025.
    """
    df_mensal = df_filtrado[df_filtrado['ano'] == ano]

    df_agrupado = df_mensal.groupby(['mes', 'status']).size().reset_index(name='Total')

    if ano == 2025:
        mes_limite = 10 

        filtro_futuro = df_agrupado['mes'] > mes_limite

        df_agrupado.loc[filtro_futuro, 'Total'] = 0

    meses_map = {i: datetime.date(2000, i, 1).strftime('%B') for i in range(1, 13)}
    df_agrupado['mes_nome'] = df_agrupado['mes'].map(meses_map)
    
    fig = px.line(df_agrupado, x='mes_nome', y='Total', color='status',
                  title=f'Evolução Mensal de MPUs - Pedidos e Resultados ({ano})', markers=True)
    fig.update_layout(yaxis_title="Volume de MPUs", xaxis_title="Mês", xaxis={'categoryorder':'array', 'categoryarray': [meses_map[i] for i in range(1, 13)]})
    return fig

def criar_grafico_funil_desfecho(df_filtrado):
    """Gráfico 5: Cria um Funnel Chart que analisa a taxa de "conversão" do processo."""
    
    total_pedidos = len(df_filtrado)
    total_concedidas = len(df_filtrado[df_filtrado['desfecho'] == 'Proferida (Concedida)'])
    df_concedidas = df_filtrado[df_filtrado['desfecho'] == 'Proferida (Concedida)']
    contagem_desfechos = df_concedidas['desfecho_final'].value_counts()
    
    desfechos_finais = {
        '1. Pedido Inicial (MPU)': total_pedidos,
        '2. MPU Concedida': total_concedidas,
        '3. Desfecho: Condenação': contagem_desfechos.get('Condenação', 0),
        '4. Desfecho: Absolvição/Arquivamento': contagem_desfechos.get('Absolvição', 0) + contagem_desfechos.get('Arquivamento/Extinção', 0)
    }
    
    df_funil = pd.DataFrame(list(desfechos_finais.items()), columns=['Etapa', 'Volume'])
    
    fig = px.funnel(
        df_funil, 
        x='Volume', 
        y='Etapa',
        title='Funil de Conversão: Do Pedido de Proteção ao Desfecho Principal'
    )
    fig.update_layout(yaxis_title="Etapas do Processo", xaxis_title="Volume de Casos")
    return fig



df_dados = carregar_dados_simulados()

st.set_page_config(layout="wide")

st.title("🛡️ Analisador Jurimétrico de Medidas Protetivas")
st.header(f"Tribunal de Justiça do Rio de Janeiro ({NOME_TRIBUNAL})")

st.markdown("---")
-
st.subheader("Selecione o Ano para Análise Detalhada:")

anos_disponiveis = sorted(df_dados['ano'].unique(), reverse=True)

ano_selecionado = st.radio(
    "Escolha o período para focar a análise:",
    anos_disponiveis,
    index=0, 
    horizontal=True
)

df_ano_selecionado = df_dados[df_dados['ano'] == ano_selecionado]

st.markdown("---")

st.subheader(f"Relatório Detalhado de Efetividade da Lei Maria da Penha (Ano {ano_selecionado})")


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

st.subheader(f"1. Evolução Mensal de Pedidos e Resultados ({ano_selecionado})")
st.caption("Nota: Os meses de Novembro e Dezembro de 2025 estão zerados, pois os dados ainda não estão disponíveis.")
fig4 = criar_grafico_4_mensal(df_dados, ano_selecionado)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

st.subheader(f"2. Distribuição do Tempo de Expedição em Horas ({ano_selecionado})")
fig2 = criar_grafico_2_tempo_segmentado(df_ano_selecionado) 
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.subheader(f"3. Proporção dos Tipos de Medidas Protetivas Concedidas ({ano_selecionado})")
fig3 = criar_grafico_3_tipos_mpu(df_ano_selecionado)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

st.subheader(f"4. Funil de Efetividade e Desfecho Final ({ano_selecionado})")
st.caption("Taxa de Conversão: Do Pedido de Proteção à Sentença na Ação Principal (Simulação)")
fig_funil = criar_grafico_funil_desfecho(df_ano_selecionado)
st.plotly_chart(fig_funil, use_container_width=True)

st.markdown("##### Detalhamento Amostral dos Dados de Processos (Tabela Interativa):")
st.caption("Use esta tabela para filtrar e ordenar dados brutos, simulando o acesso aos metadados processuais.")

df_tabela = df_ano_selecionado[['data_ajuizamento', 'data_decisao_mpu', 'tipo_mpu_expedida', 'tempo_tramitacao_horas', 'desfecho_final']].copy()
df_tabela.columns = ['Data Ajuizamento', 'Data Decisão MPU', 'Tipo MPU', 'Tempo (h)', 'Desfecho Final']

st.dataframe(
    df_tabela,
    use_container_width=True,
    height=300 
)
