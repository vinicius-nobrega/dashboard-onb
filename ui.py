# ui.py (VERSÃO FINAL AJUSTADA)

import streamlit as st
import pandas as pd
from datetime import datetime

from data_analysis import analisar_pontuacao_doutor, calcular_dias_restantes

def exibir_painel_metas(df_completo, col_map):
    """Exibe o painel superior com KPIs e metas, sem as barras de progresso."""
    st.header("Metas da Carteira")

    metas = {'A': 60, 'A+B': 77, 'Bookable Hours': 50}
    
    col1, col2 = st.columns(2)
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)
    data_inicio = col1.date_input("Data de Início do Filtro", value=inicio_mes)
    data_fim = col2.date_input("Data de Fim do Filtro", value=hoje)

    onb_end_col = col_map.get('onb end (farming_at_cx)')
    df_filtrado = df_completo[pd.to_datetime(df_completo[onb_end_col], errors='coerce').dt.date.between(data_inicio, data_fim)] if onb_end_col else df_completo

    if df_filtrado.empty:
        st.warning("Nenhum cliente com data de finalização no período selecionado.")
        return

    total = len(df_filtrado)
    grade_col = col_map['onb grade']
    nota_a = df_filtrado[df_filtrado[grade_col] == 'A'].shape[0]
    nota_b = df_filtrado[df_filtrado[grade_col] == 'B'].shape[0]
    perc_a = (nota_a / total) * 100
    perc_a_b = ((nota_a + nota_b) / total) * 100
    
    bookable_hours_col = col_map.get('bookable hours')
    # --- CORREÇÃO NO CÁLCULO ---
    if bookable_hours_col:
        clientes_com_meta = df_filtrado[df_filtrado[bookable_hours_col] >= metas['Bookable Hours']].shape[0]
        perc_bookable_hours = (clientes_com_meta / total) * 100
    else:
        perc_bookable_hours = 0

    # Exibição dos KPIs em colunas
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label=f"% Carteira em A (Meta: {metas['A']}%)", value=f"{perc_a:.1f}%")
    kpi2.metric(label=f"% Carteira em A+B (Meta: {metas['A+B']}%)", value=f"{perc_a_b:.1f}%")
    kpi3.metric(label=f"% Carteira com Horas OK (Meta: {metas['Bookable Hours']}%)", value=f"{perc_bookable_hours:.1f}%")
    
    st.markdown("---")

def exibir_detalhes_doutor(doutor_selecionado, df_completo, col_map):
    """Exibe a análise detalhada para um único doutor."""
    doutor_series = df_completo[df_completo[col_map['doctor_name']] == doutor_selecionado].iloc[0]

    st.subheader(f"Painel de Ação: {doutor_selecionado}")
    
    # --- Informações Gerais ---
    col1, col2, col3 = st.columns(3)
    
    # --- CORREÇÃO NO CÁLCULO DE DIAS ---
    tech_onb_end_col = col_map.get('technical onb end')
    dias_restantes = calcular_dias_restantes(doutor_series[tech_onb_end_col]) if tech_onb_end_col else "Coluna não encontrada"
    col1.metric("Dias Restantes no Onboarding", value=dias_restantes)
    
    col2.metric("Curva Atual (ONB Grade)", value=doutor_series[col_map['onb grade']])
    
    hubspot_link = doutor_series.get(col_map.get('sf or hs link'))
    if hubspot_link and pd.notna(hubspot_link):
        col3.markdown(f"**[Acessar HubSpot]({hubspot_link})**")

    st.markdown("---")

    # --- Análise de Pontuação ---
    st.subheader("Diagnóstico de Pontuação")
    analise_pontos = analisar_pontuacao_doutor(doutor_series, col_map)
    
    st.progress(analise_pontos['total_atual'] / analise_pontos['total_maximo'])
    st.write(f"**Pontuação Atual:** {analise_pontos['total_atual']} / {analise_pontos['total_maximo']}")

    for categoria, valores in analise_pontos['categorias'].items():
        if valores['atual'] < valores['max']:
            st.warning(f"**{categoria}:** Faltam **{valores['max'] - valores['atual']}** pontos.")
    
    with st.expander("Ver plano de ação detalhado com pontuações"):
        if analise_pontos['acoes_faltantes']:
            for acao, pontos in analise_pontos['acoes_faltantes']:
                st.write(f"- {acao} `+{pontos} pts`")
        else:
            st.success("Parabéns! Nenhuma ação de pontuação pendente encontrada!")

def exibir_card_cliente(cliente_series, col_map):
    """Exibe um 'card' com informações resumidas de um cliente."""
    tech_onb_end_col = col_map.get('technical onb end')
    dias_restantes = calcular_dias_restantes(cliente_series.get(tech_onb_end_col)) if tech_onb_end_col else "N/A"
    
    with st.expander(f"{cliente_series[col_map['doctor_name']]} - Curva: {cliente_series[col_map['onb grade']]}"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Pontos", value=cliente_series.get(col_map.get('onb points'), 'N/A'))
        col2.metric("Plano", value=cliente_series.get(col_map.get('package'), 'N/A'))
        col3.metric("Dias Restantes", value=dias_restantes)

def exibir_dashboard(user_profile, df_completo, categorias_dfs):
    """Função principal que monta a interface do dashboard."""
    col_map = {col.strip().lower(): col for col in df_completo.columns}
    
    exibir_painel_metas(df_completo.copy(), col_map)

    tab_analise, tab_farming, tab_waiting, tab_backtosales, tab_outros = st.tabs([
        "🔍 Análise Individual", "🌱 Farming", "⏳ Waiting", "🔙 Back to Sales", "❓ Outros"
    ])

    with tab_analise:
        df_para_analise = pd.concat([categorias_dfs.get('atuar', pd.DataFrame()), categorias_dfs.get('avancar', pd.DataFrame())])
        if not df_para_analise.empty:
            lista_doutores = [""] + sorted(df_para_analise[col_map['doctor_name']].tolist())
            doutor_selecionado = st.selectbox("Selecione um doutor para análise:", options=lista_doutores, key="sb_doutor")
            if doutor_selecionado:
                exibir_detalhes_doutor(doutor_selecionado, df_completo, col_map)
        else:
            st.info("Nenhum doutor para análise individual no momento.")

    # Exibição em cards para as outras abas
    for nome_aba, df_aba in {'Farming': categorias_dfs['farming'], 'Waiting': categorias_dfs['waiting'], 'Back to Sales': categorias_dfs['back_to_sales'], 'Outros': categorias_dfs['outros']}.items():
        with locals()[f"tab_{nome_aba.lower().replace(' ', '')}"]:
             st.subheader(f"Clientes em {nome_aba} ({len(df_aba)})")
             if df_aba.empty:
                 st.info(f"Nenhum cliente nesta categoria.")
             else:
                for _, row in df_aba.iterrows():
                    exibir_card_cliente(row, col_map)
