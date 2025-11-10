import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time
from urllib.parse import urlparse

# --- 1. CONFIGURAÇÃO E DADOS BASE ---

# Base URL para a API da Câmara
URL_BASE_API = "https://dadosabertos.camara.leg.br/api/v2/"

# DADOS COMPLETOS DE TODOS OS 11 LÍDERES
LIDERES = {
    "Sóstenes Cavalcante (PL)": {
        "id": "178947",
        "partido": "PL",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/178947",
            "Despesas": f"{URL_BASE_API}deputados/178947/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/178947/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/178947/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/178947/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Talíria Petrone (PSOL)": {
        "id": "204464",
        "partido": "PSOL",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/204464",
            "Despesas": f"{URL_BASE_API}deputados/204464/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/204464/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/204464/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/204464/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Lindbergh Farias (PT)": {
        "id": "74858",
        "partido": "PT",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/74858",
            "Despesas": f"{URL_BASE_API}deputados/74858/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/74858/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/74858/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/74858/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Marcel Van Hattem (NOVO)": {
        "id": "156190",
        "partido": "NOVO",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/156190",
            "Despesas": f"{URL_BASE_API}deputados/156190/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/156190/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/156190/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/156190/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Antonio Brito (PSD)": {
        "id": "160553",
        "partido": "PSD",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/160553",
            "Despesas": f"{URL_BASE_API}deputados/160553/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/160553/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/160553/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/160553/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Pedro Lucas Fernandes (UNIÃO)": {
        "id": "122974",
        "partido": "UNIÃO",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/122974",
            "Despesas": f"{URL_BASE_API}deputados/122974/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/122974/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/122974/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/122974/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Dr. Luizinho (PP)": {
        "id": "204450",
        "partido": "PP",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/204450",
            "Despesas": f"{URL_BASE_API}deputados/204450/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/204450/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/204450/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/204450/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Gilberto Abramo (REPUBLICANOS)": {
        "id": "204491",
        "partido": "REPUBLICANOS",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/204491",
            "Despesas": f"{URL_BASE_API}deputados/204491/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/204491/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/204491/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/204491/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Isnaldo Bulhões Jr. (MDB)": {
        "id": "204436",
        "partido": "MDB",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/204436",
            "Despesas": f"{URL_BASE_API}deputados/204436/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/204436/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/204436/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/204436/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Pedro Campos (PSB)": {
        "id": "220667",
        "partido": "PSB",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/220667",
            "Despesas": f"{URL_BASE_API}deputados/220667/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/220667/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/220667/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/220667/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Mário Heringer (PDT)": {
        "id": "74158",
        "partido": "PDT",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/74158",
            "Despesas": f"{URL_BASE_API}deputados/74158/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/74158/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/74158/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/74158/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Neto Carletto (AVANTE)": {
        "id": "220703",
        "partido": "AVANTE",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/220703",
            "Despesas": f"{URL_BASE_API}deputados/220703/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/220703/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/220703/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/220703/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Áureo Ribeiro (SOLIDARIEDADE)": {
        "id": "160512",
        "partido": "SOLIDARIEDADE",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/160512",
            "Despesas": f"{URL_BASE_API}deputados/160512/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/160512/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/160512/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/160512/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Adolfo Viana (PSDB)": {
        "id": "204560",
        "partido": "PSDB",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/204560",
            "Despesas": f"{URL_BASE_API}deputados/204560/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/204560/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/204560/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/204560/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    },
    "Rodrigo Gambale (PODE)": {
        "id": "220641",
        "partido": "PODE",
        "urls": {
            "Gerais": f"{URL_BASE_API}deputados/220641",
            "Despesas": f"{URL_BASE_API}deputados/220641/despesas?ordem=ASC&ordenarPor=ano",
            "Frentes": f"{URL_BASE_API}deputados/220641/frentes",
            "Profissoes": f"{URL_BASE_API}deputados/220641/profissoes",
            "Eventos": f"{URL_BASE_API}deputados/220641/eventos?dataInicio=2025-01-01&dataFim=2025-11-08&ordem=ASC&ordenarPor=dataHoraInicio"
        }
    }
}


# --- 2. FUNÇÕES DE BUSCA E PROCESSAMENTO DA API ---

@st.cache_data(ttl=3600)
def buscar_dados(url):
    """Busca dados da API e trata a resposta JSON."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get('dados', [])
    except requests.exceptions.RequestException:
        return []

def limpar_cache_api():
    """Limpa o cache do Streamlit."""
    st.cache_data.clear()
    st.experimental_rerun()

def processar_despesas(dados):
    """Soma o valor líquido das despesas e retorna o total."""
    if not dados:
        return 0.0
    df = pd.DataFrame(dados)
    # A API usa 'valorLiquido' para o valor da despesa
    total = df['valorLiquido'].sum()
    return total

def agregar_todos_os_dados():
    """Busca e agrega Despesas, Eventos e Gênero para todos os líderes."""
    
    dados_agregados = []
    
    for nome, dados in LIDERES.items():
        urls = dados['urls']
        
        # 1. Busca Despesas e Eventos
        total_despesas = processar_despesas(buscar_dados(urls['Despesas']))
        total_eventos = len(buscar_dados(urls['Eventos']))
        
        # 2. Busca Gênero e Nome Completo (do endpoint Geral)
        dados_gerais = buscar_dados(urls['Gerais'])
        
        # A API tem o gênero na propriedade 'sexo' dentro do objeto principal
        genero = 'Não Informado'
        nome_parlamentar = nome.split('(')[0].strip()
        
        if dados_gerais and isinstance(dados_gerais, dict):
            genero = dados_gerais.get('sexo', 'Não Informado')
            # Usa o nomeCivil para o ranking se o nome for complexo (ex: 'Dr. Luizinho')
            nome_parlamentar = dados_gerais.get('nomeCivil', nome_parlamentar)
            
        dados_agregados.append({
            'Líder': nome,
            'Nome Curto': nome_parlamentar,
            'Gênero': 'Mulher' if genero == 'F' else 'Homem',
            'Despesas_Total': total_despesas,
            'Eventos_Total': total_eventos
        })
        
    return pd.DataFrame(dados_agregados)


def exibir_ficha_parlamentar(nome_completo, dados_deputado):
    """Busca e exibe todas as informações do deputado em expansores."""
    
    urls = dados_deputado['urls']
    
    # 1. Dados Gerais (Nome, Partido, UF)
    dados_gerais = buscar_dados(urls['Gerais'])
    if dados_gerais and isinstance(dados_gerais, dict):
        nome_parlamentar = dados_gerais.get('nomeCivil', nome_completo.split('(')[0].strip())
        partido = dados_gerais.get('ultimoStatus', {}).get('siglaPartido', 'N/A')
        uf = dados_gerais.get('ultimoStatus', {}).get('siglaUf', 'N/A')
        url_foto = dados_gerais.get('ultimoStatus', {}).get('urlFoto', '')
    else:
        nome_parlamentar = nome_completo.split('(')[0].strip()
        partido, uf, url_foto = 'N/A', 'N/A', ''
    
    
    # 2. Busca de Métricas (Simples)
    total_despesas = processar_despesas(buscar_dados(urls['Despesas']))
    total_eventos = len(buscar_dados(urls['Eventos']))
    
    # --- Apresentação da Ficha ---
    
    st.subheader(f"Ficha Parlamentar: {nome_parlamentar}")
    
    col_kpi_info, col_kpi_dados = st.columns([1, 4])
    
    with col_kpi_info:
        if url_foto:
            st.image(url_foto, width=120)
        st.markdown(f"**Sigla:** {partido}")
        st.markdown(f"**UF:** {uf}")

    with col_kpi_dados:
        st.markdown("#### **Indicadores de Transparência e Atuação**")
        col_m1, col_m2 = st.columns(2)
        
        # CORREÇÃO: Métrica de Despesas
        col_m1.metric("Despesas Totais (últimos 6 meses)", f"R$ {total_despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        col_m2.metric("Eventos Públicos em 2025", f"{total_eventos} Eventos")

    st.markdown("---")
    
    # 3. Informações Detalhadas em Expansores (Tabelas)
    
    # Frentes Parlamentares
    with st.expander("🌐 Frentes Parlamentares e Grupos de Interesse"):
        dados_frentes = buscar_dados(urls['Frentes'])
        if dados_frentes:
            df_frentes = pd.DataFrame(dados_frentes)
            st.dataframe(df_frentes[['titulo', 'idLegislatura']], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma Frente Parlamentar encontrada.")

    # Profissões
    with st.expander("📚 Profissões Declaradas"):
        dados_profissoes = buscar_dados(urls['Profissoes'])
        if dados_profissoes:
             df_profissoes = pd.DataFrame(dados_profissoes)
             st.dataframe(df_profissoes[['titulo', 'codTipoProfissao']], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma profissão declarada encontrada.")


# --- 3. INTERFACE STREAMLIT PRINCIPAL ---

st.set_page_config(layout="wide", page_title="Monitor de Lideranças Parlamentares")

st.title("🏛️ Análise de Transparência das Lideranças da Câmara")
# CORREÇÃO: Removida a parte "e Presidência" do cabeçalho
st.header("Líderes Partidários (57ª Legislatura)")

# --- BOTÃO DE LIMPEZA DE CACHE ---
st.sidebar.button("Resetar Cache da API", on_click=limpar_cache_api)

st.markdown("---")

# =========================================================================
# SEÇÃO 1: GRÁFICOS DE COMPARAÇÃO (Jurimetria)
# =========================================================================

st.subheader("1. Análise Comparativa de Atividade e Transparência")

# Execução da Agregação
with st.spinner("Buscando e agregando dados de todos os líderes..."):
    df_comparativo = agregar_todos_os_dados()

if not df_comparativo.empty and df_comparativo['Líder'].nunique() > 1:

    # GRÁFICO A: Ranking de Despesas
    st.markdown("##### 1.1. Ranking de Despesas Parlamentares (Cota/Gabinete)")
    df_despesas_rank = df_comparativo.sort_values(by='Despesas_Total', ascending=False)
    
    fig_despesas = px.bar(
        df_despesas_rank,
        x='Nome Curto',
        y='Despesas_Total',
        color='Despesas_Total',
        title='Líderes: Quem Gastou Mais (Valor não mostrado)',
        labels={'Despesas_Total': 'Valor (R$)', 'Nome Curto': 'Líder'},
        color_continuous_scale=px.colors.sequential.Reds
    )
    fig_despesas.update_traces(hovertemplate='Líder: %{x}<br>Despesa Total: R$ %{y:,.2f}<extra></extra>')
    fig_despesas.update_yaxes(showticklabels=False) # Não mostrar valor exato no eixo
    st.plotly_chart(fig_despesas, use_container_width=True)


    # GRÁFICO B: Ranking de Eventos
    st.markdown("##### 1.2. Ranking de Participação em Eventos Públicos (2025)")
    df_eventos_rank = df_comparativo.sort_values(by='Eventos_Total', ascending=False)
    
    fig_eventos = px.bar(
        df_eventos_rank,
        x='Nome Curto',
        y='Eventos_Total',
        color='Eventos_Total',
        title='Líderes: Quem Mais Participou de Eventos em 2025',
        labels={'Eventos_Total': 'Quantidade', 'Nome Curto': 'Líder'},
        color_continuous_scale=px.colors.sequential.Blues
    )
    fig_eventos.update_yaxes(showticklabels=False) # Não mostrar valor exato no eixo
    st.plotly_chart(fig_eventos, use_container_width=True)

    # GRÁFICO C: Distribuição de Gênero
    st.markdown("##### 1.3. Distribuição de Gênero na Liderança")
    df_genero_count = df_comparativo['Gênero'].value_counts().reset_index()
    df_genero_count.columns = ['Gênero', 'Total']
    
    fig_genero = px.pie(
        df_genero_count,
        values='Total',
        names='Gênero',
        title='Proporção de Gênero entre os Líderes Partidários',
        hole=.5,
        color_discrete_map={'Mulher': 'purple', 'Homem': 'darkblue'}
    )
    st.plotly_chart(fig_genero, use_container_width=True)
    

st.markdown("---")


# =========================================================================
# SEÇÃO 2: FICHA INDIVIDUAL (Interatividade)
# =========================================================================
st.subheader("2. Ficha Individual de Transparência")
st.caption("Detalhes sobre despesas, profissões e grupos de interesse de cada líder.")


# Cria os botões radio com os nomes dos líderes
parlamentar_selecionado = st.radio(
    "Líder:",
    list(LIDERES.keys()),
    index=0, 
    horizontal=True
)

st.markdown("---")

# --- EXIBIÇÃO DA FICHA ---

if parlamentar_selecionado:
    dados_do_lider = LIDERES[parlamentar_selecionado]
    exibir_ficha_parlamentar(parlamentar_selecionado, dados_do_lider)
