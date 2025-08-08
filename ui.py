# ui.py (VERSÃO 2.0)

import streamlit as st
import pandas as pd
from datetime import datetime

# Importa as novas funções de análise que criamos
from data_analysis import analisar_pontuacao_doutor, calcular_dias_restantes

def exibir_painel_kpis(df_completo, col_map):
    """Exibe o painel superior com KPIs e filtros de data."""
    st.header("Painel de Metas da Carteira")

    # Colunas para os filtros
    col1, col2 = st.columns(2)
    
    # Filtro de data
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)
    
    with col1:
        data_inicio = st.date_input("Data de Início", value=inicio_mes)
    with col2:
        data_fim = st.date_input("Data de Fim", value=hoje)

    # Garante que as datas estão no formato correto para comparação
    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)
    
    # Filtra o DataFrame com base no intervalo de datas
    # Usaremos a coluna de fim do onboarding para a meta
    onb_end_col = col_map.get('onb end (farming_at_cx)', None)
    if onb_end_col:
        df_filtrado = df_completo[pd.to_datetime(df_completo[onb_end_col], errors='coerce').between(data_inicio, data_fim)]
    else:
        df_filtrado = df_completo # Se não houver coluna de data, usa o df completo

    total_clientes = len(df_filtrado)
    if total_clientes == 0:
        st.warning("Nenhum cliente encontrado no período selecionado para calcular as metas.")
        return

    grade_col = col_map['onb grade']
    
    # Cálculos de KPI
    nota_a = df_filtrado[df_filtrado[grade_col] == 'A'].shape[0]
    nota_b = df_filtrado[df_filtrado[grade_col] == 'B'].shape[0]
    nota_c = df_filtrado[df_filtrado[grade_col] == 'C'].shape[0]
    nota_d = df_filtrado[df_filtrado[grade_col] == 'D'].shape[0]
    
    perc_a = (nota_a / total_clientes) * 100
    perc_a_b = ((nota_a + nota_b) / total_clientes) * 100
    perc_c = (nota_c / total_clientes) * 100
    perc_d = (nota_d / total_clientes) * 100

    # Exibição dos KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label="Carteira em A", value=f"{perc_a:.1f}%")
    kpi2.metric(label="Carteira em A+B", value=f"{perc_a_b:.1f}%")
    kpi3.metric(label="Carteira em C", value=f"{perc_c:.1f}%")
    kpi4.metric(label="Carteira em D", value=f"{perc_d:.1f}%")
    st.markdown("---")


def exibir_detalhes_doutor(doutor_selecionado, df_completo, col_map):
    """Exibe a análise detalhada para um único doutor."""
    
    # Pega a linha inteira de dados do doutor selecionado
    doutor_series = df_completo[df_completo[col_map['doctor_name']] == doutor_selecionado].iloc[0]

    st.subheader(f"Análise Detalhada: {doutor_selecionado}")

    # --- Informações Gerais ---
    col1, col2, col3 = st.columns(3)
    
    # Dias Restantes
    onb_start_col = col_map.get('onb start (onboarding_at_cx)')
    dias_restantes = calcular_dias_restantes(doutor_series[onb_start_col])
    col1.metric("Dias Restantes no Onboarding", value=dias_restantes)
    
    # Link do HubSpot
    hubspot_col = col_map.get('sf or hs link')
    if hubspot_col and pd.notna(doutor_series[hubspot_col]):
        col2.markdown(f"**HubSpot Link**\n\n[Acessar Perfil]({doutor_series[hubspot_col]})")
    else:
        col2.info("Link do HubSpot não disponível.")
    
    # Plano
    package_col = col_map.get('package')
    plano_atual = doutor_series.get(package_col, "Não definido")
    if pd.isna(plano_atual) or plano_atual == "Não definido":
        plano_atual = col3.selectbox("Selecione o Plano:", options=["STARTER", "PLUS", "VIP"], key=f"plano_{doutor_selecionado}")
    col3.metric("Plano", value=plano_atual)
    
    st.markdown("---")

    # --- Análise de Pontuação ---
    st.subheader("Análise de Pontuação")
    analise_pontos = analisar_pontuacao_doutor(doutor_series, col_map)
    
    st.progress(analise_pontos['pontos_atuais'] / analise_pontos['pontos_maximos'])
    st.write(f"**Pontuação Atual:** {analise_pontos['pontos_atuais']} / {analise_pontos['pontos_maximos']}")

    with st.expander("Ver detalhes e ações recomendadas"):
        st.write("**O que falta para atingir a pontuação máxima:**")
        if analise_pontos['acoes_faltantes']:
            for acao in analise_pontos['acoes_faltantes']:
                st.warning(f"- {acao}")
        else:
            st.success("Parabéns! Pontuação máxima atingida em todos os itens analisados!")

    st.markdown("---")
    
    # --- Análise de Respostas da Reunião ---
    st.subheader("Anotações da Reunião")
    st.text_area(
        "Cole aqui o texto da primeira reunião (ONBOARDING 1 - REALIZADO COM SUCESSO)",
        height=250,
        key=f"respostas_{doutor_selecionado}"
    )


def exibir_dashboard(user_profile, df_completo, categorias_dfs):
    """Função principal que monta a interface do dashboard."""

    col_map = {col.strip().lower(): col for col in df_completo.columns}

    # 1. Exibir Painel de KPIs no topo
    exibir_painel_kpis(df_completo, col_map)

    # 2. Criar as abas com a nova estrutura
    tab_analise, tab_farming, tab_waiting, tab_backtosales, tab_outros = st.tabs([
        f"🔍 Análise Individual ({len(categorias_dfs.get('atuar', [])) + len(categorias_dfs.get('avancar', []))})",
        f"🌱 Farming ({len(categorias_dfs.get('farming', []))})",
        f"⏳ Waiting ({len(categorias_dfs.get('waiting', []))})",
        f"🔙 Back to Sales ({len(categorias_dfs.get('back_to_sales', []))})",
        f"❓ Outros ({len(categorias_dfs.get('outros', []))})"
    ])

    with tab_analise:
        st.header("Análise Individual de Doutores")
        
        df_para_analise = pd.concat([categorias_dfs.get('atuar', pd.DataFrame()), categorias_dfs.get('avancar', pd.DataFrame())])
        
        if not df_para_analise.empty:
            lista_doutores = df_para_analise[col_map['doctor_name']].tolist()
            
            doutor_selecionado = st.selectbox(
                "Selecione um doutor para analisar em detalhes:",
                options=[""] + sorted(lista_doutores),
                format_func=lambda x: "Selecione..." if x == "" else x
            )

            if doutor_selecionado:
                exibir_detalhes_doutor(doutor_selecionado, df_completo, col_map)
        else:
            st.info("Nenhum doutor na categoria de 'Atuar' ou 'Avançar' para análise.")

    with tab_farming:
        st.header("Clientes em Estágio de Farming")
        st.dataframe(categorias_dfs.get('farming', pd.DataFrame()))

    with tab_waiting:
        st.header("Clientes em Espera (Waiting)")
        st.dataframe(categorias_dfs.get('waiting', pd.DataFrame()))

    with tab_backtosales:
        st.header("Clientes Retornados para Vendas")
        st.dataframe(categorias_dfs.get('back_to_sales', pd.DataFrame()))
        
    with tab_outros:
        st.header("Clientes sem Categoria Definida")
        st.dataframe(categorias_dfs.get('outros', pd.DataFrame()))
