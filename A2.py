#Configuração inicial do programa - importar bibliotecas necessárias
import requests
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go

#Apresentação
st.title("Câmara Aberta")
st.header("Uma plataforma dedicada ao acesso a informações da Câmara dos Deputados")
st.subheader("Aqui você pode buscar informações sobre Projetos de Lei, Propostas de Emenda Constitucional, ou deputados.")

#Menu 1 - Opção de Busca
st.header("O que você está procurando?")
opcoes = ["a) Projetos de Lei", "b) Propostas de Emenda Constitucional", "c) Deputados", "d) Sair"]
busca = st.radio("Selecione a opção da sua busca:", opcoes)
if busca == "a) Projetos de Lei":
  st.subheader("Você escolheu a opção de buscar projetos de lei.")
if busca == "b) Propostas de Emenda Constitucional":
  st.subheader("Você escolheu a opção de buscar propostas de emenda constitucional.")
if busca == "c) Deputados":
  st.subheader("Você escolheu a opção de buscar informações de deputados.")
if busca == "d) Sair":
  st.subheader("Você escolheu a opção de sair da pesquisa.")
  st.subheader("Obrigado por usar o programa. Até a próxima!")

#Resultado do Menu a) PL
if busca == "a) Projetos de Lei":
    numero_pl = st.text_input("Digite o número do projeto de lei:")
    ano_pl = st.text_input("Digite o ano do projeto de lei:")
    url_busca_pl = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&numero={numero_pl}&ano={ano_pl}"
    response_pl = requests.get(url_busca_pl)
    if response_pl.status_code == 200:
        dados_pl = response_pl.json()
        if dados_pl['dados']:
            for proposicao in dados_pl['dados']:
                id_proposicao = proposicao['id']
                st.subheader(f"Projeto encontrado!")
                url_detalhes = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_proposicao}"
                response_detalhes = requests.get(url_detalhes)
                if response_detalhes.status_code == 200:
                    detalhes = response_detalhes.json()['dados']
                    st.subheader("Detalhes do Projeto")
                    st.write(f"Situação atual: {detalhes['statusProposicao']['descricaoSituacao']}")
                    st.write(f"Ementa completa: {detalhes['ementa']}")
                    st.write("Obrigado por usar o programa. Até a próxima!")
        else:
          st.warning(f"Projeto com o número {numero_pl} do ano {ano_pl} não encontrado.")
    else:
        st.warning(f"Erro na requisição")

#Resultado Menu b) PEC
if busca == "b) Propostas de Emenda Constitucional":
    numero_pec = st.text_input("Digite o número da proposta de emenda constitucional:")
    ano_pec = st.text_input("Digite o ano da proposta de emenda constitucional:")
    url_busca_pec = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PEC&numero={numero_pec}&ano={ano_pec}"
    response_pec = requests.get(url_busca_pec)
    if response_pec.status_code == 200:
        dados_pec = response_pec.json()
        if dados_pec['dados']:
            for proposicao in dados_pec['dados']:
                  id_proposicao = proposicao['id']
                  st.subheader(f"PEC encontrada!")
                  url_detalhes = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_proposicao}"
                  response_detalhes = requests.get(url_detalhes)
                  if response_detalhes.status_code == 200:
                      detalhes = response_detalhes.json()['dados']
                      st.subheader("Detalhes da PEC")
                      st.write(f"Situação atual: {detalhes['statusProposicao']['descricaoSituacao']}")
                      st.write(f"Ementa completa: {detalhes['ementa']}")
                      st.write("Obrigado por usar o programa. Até a próxima!")
        else:
          st.warning(f"PEC {numero_pec}/{ano_pec} não encontrada.")
    else:
        st.warning(f"Erro na requisição")

#Resultado do Menu c) Deputados
if busca == "c) Deputados":
    nome_deputado = st.text_input("Digite o nome do deputado(a):")
    url_deputados = f"https://dadosabertos.camara.leg.br/api/v2/deputados?nome={nome_deputado}"
    response = requests.get(url_deputados)
#Informações Gerais do Deputado(a)
    if response.status_code == 200:
        dados_deputado = response.json()['dados']
        if dados_deputado:
            deputado_id = dados_deputado[0]['id']
            deputado_nome = dados_deputado[0]['nome']
            deputado_partido = dados_deputado[0]['siglaPartido']
            deputado_uf = dados_deputado[0]['siglaUf']
            df_deputado = pd.DataFrame(dados_deputado)
            st.subheader(f"Deputado(a) encontrado(a).")
            st.write(f"Nome: {deputado_nome}")
            st.write(f"Partido: {deputado_partido}")
            st.write(f"UF: {deputado_uf}")
#Frentes do Deputado(a)
            url_frentes = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/frentes"
            response_frentes = requests.get(url_frentes)
            if response_frentes.status_code == 200:
              dados_frentes = response_frentes.json()
              df_frentes = pd.DataFrame(dados_frentes['dados'])
              st.subheader("Frentes parlamentares do deputado(a)")
              st.dataframe(df_frentes['titulo'],
                          column_config={'titulo': 'Frente Parlamentar'})
#Órgãos do Deputado(a)
            url_orgaos = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/orgaos"
            response_orgaos = requests.get(url_orgaos)
            if response_orgaos.status_code == 200:
              dados_orgaos = response_orgaos.json()
              df_orgaos = pd.DataFrame(dados_orgaos['dados'])
              st.subheader("Órgãos que o deputado(a) integra")
              st.dataframe(df_orgaos[['siglaOrgao', 'nomePublicacao', 'titulo']],
                           column_config={'siglaOrgao': 'Sigla do Órgão',
                                          'nomePublicacao': 'Nome do Orgao',
                                          'titulo': 'Status do Deputado'})
#Despesas do Deputado(a)
            url_despesas = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado_id}/despesas"
            response_despesas = requests.get(url_despesas)
            if response_despesas.status_code == 200:
              dados_despesas = response_despesas.json()
              df_despesas = pd.DataFrame(dados_despesas['dados'])
              if not df_despesas.empty:
                st.subheader("Despesas do Deputado(a)")
                fig_despesas = px.bar(df_despesas,
                                      x='mes',
                                      y='valorDocumento',
                                      color='tipoDespesa',
                                      title=f'Despesas de {nome_deputado}',
                                      labels={'tipoDespesa': 'Tipo de Despesa',
                                              'valorDocumento': 'Valor da Despesa',
                                              'mes': 'Mês'})
                st.plotly_chart(fig_despesas, use_container_width=True)
            else:
              st.warning(f"Nenhuma despesa encontrada para {nome_deputado} no período.")         
              st.write("Obrigado por usar o programa. Até a próxima!")
    else:
        st.warning(f"Erro na requisição.")
        st.write(f"Nenhum deputado(a) encontrado com o nome '{nome_deputado}'.")
