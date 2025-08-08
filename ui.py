# ui.py (VERSÃO FINAL)

import streamlit as st
import pandas as pd
from datetime import datetime

from data_analysis import analisar_pontuacao_doutor, calcular_dias_restantes, analisar_respostas_cliente

def exibir_painel_metas(df_completo, col_map):
    """Exibe o painel superior com medidores de metas."""
    st.header("Metas da Carteira")

    metas = {'A': 60, 'A+B': 77, 'Bookable Hours': 50}
    
    # Filtro de data
    hoje = datetime.now()
    inicio_mes = hoje.replace(day=1)
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("Data de Início do Filtro", value=inicio_mes)
    data_fim = col2.date_input("Data de Fim do Filtro", value=hoje)

    onb_end_col = col_map.get('onb end (farming_at_cx)')
    df_filtrado = df_completo[pd.to_datetime(df_completo[onb_end_col], errors='coerce').dt.date.between(data_inicio, data_fim)] if onb_end_col else df_completo

    if df_filtrado.empty:
        st.warning("Nenhum cliente com data de finalização no período selecionado.")
        return

    # Cálculos
    total = len(df_filtrado)
    grade_col = col_map['onb grade']
    nota_a = df_filtrado[df_filtrado[grade_col] == 'A'].shape[0]
    nota_b = df_filtrado[df_filtrado[grade_col] == 'B'].shape[0]
    perc_a = (nota_a / total) * 100
    perc_a_b = ((nota_a + nota_b) / total) * 100
    
    bookable_hours_col = col_map.get('bookable hours')
    avg_bookable_hours = df_filtrado[bookable_hours_col].mean() if bookable_hours_col else 0

    # Exibição das metas
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.write(f"**Meta % em A: {metas['A']}%**")
    st.progress(perc_a / 100)
    kpi1.write(f"Atual: {perc_a:.1f}%")

    kpi2.write(f"**Meta % em A+B: {metas['A+B']}%**")
    st.progress(perc_a_b / 100)
    kpi2.write(f"Atual: {perc_a_b:.1f}%")
    
    kpi3.write(f"**Meta Média de Horas: {metas['Bookable Hours']}%**")
    st.progress(avg_bookable_hours / 100 if avg_bookable_hours <=100 else 1.0) # Normaliza caso a média passe de 100
    kpi3.write(f"Atual: {avg_bookable_hours:.1f}")

    st.markdown("---")

def exibir_detalhes_doutor(doutor_selecionado, df_completo, col_map):
    """Exibe a análise detalhada para um único doutor."""
    doutor_series = df_completo[df_completo[col_map['doctor_name']] == doutor_selecionado].iloc[0]

    with st.form(key=f"form_respostas_{doutor_selecionado}"):
        st.subheader("Análise de Respostas da Reunião")
        texto_reuniao = st.text_area("Cole aqui o texto da primeira reunião para gerar insights automatizados:", height=150)
        submitted = st.form_submit_button("Analisar Respostas e Gerar Insights")

    if submitted and texto_reuniao:
        with st.spinner('Analisando...'):
            insights = analisar_respostas_cliente(texto_reuniao)
            st.subheader("💡 Insights da Reunião:")
            for insight in insights:
                st.info(insight)
    st.markdown("---")

    st.subheader(f"Painel de Ação: {doutor_selecionado}")
    
    # Informações Gerais
    col1, col2, col3 = st.columns(3)
    dias_restantes = calcular_dias_restantes(doutor_series[col_map['onb end (farming_at_cx)']])
    col1.metric("Dias Restantes no Onboarding", value=dias_restantes)
    col2.metric("Curva Atual (ONB Grade)", value=doutor_series[col_map['onb grade']])
    hubspot_link = doutor_series.get(col_map.get('sf or hs link'))
    if hubspot_link and pd.notna(hubspot_link):
        col3.markdown(f"**[Acessar HubSpot]({hubspot_link})**")

    # Análise de Pontuação
    analise_pontos = analisar_pontuacao_doutor(doutor_series, col_map)
    st.subheader("Diagnóstico de Pontuação")

    for categoria, valores in analise_pontos['categorias'].items():
        if valores['atual'] < valores['max']:
            st.warning(f"**{categoria}:** Faltam **{valores['max'] - valores['atual']}** pontos.")
    
    with st.expander("Ver plano de ação detalhado"):
        for acao, pontos in analise_pontos['acoes_faltantes']:
            st.write(f"- {acao} `+{pontos} pts`")


def exibir_card_cliente(cliente_series, col_map):
    """Exibe um 'card' com informações resumidas de um cliente."""
    with st.expander(f"{cliente_series[col_map['doctor_name']]} - Curva: {cliente_series[col_map['onb grade']]}"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Pontos", value=cliente_series.get(col_map.get('onb points'), 'N/A'))
        col2.metric("Plano", value=cliente_series.get(col_map.get('package'), 'N/A'))
        dias_restantes = calcular_dias_restantes(cliente_series.get(col_map.get('onb end (farming_at_cx)')))
        col3.metric("Dias Restantes", value=dias_restantes)


def exibir_dashboard(user_profile, df_completo, categorias_dfs):
    """Função principal que monta a interface do dashboard."""
    col_map = {col.strip().lower(): col for col in df_completo.columns}
    
    exibir_painel_metas(df_completo, col_map)

    tab_analise, tab_farming, tab_waiting, tab_backtosales, tab_outros = st.tabs([
        "🔍 Análise Individual", "🌱 Farming", "⏳ Waiting", "🔙 Back to Sales", "❓ Outros"
    ])

    with tab_analise:
        df_para_analise = pd.concat([categorias_dfs['atuar'], categorias_dfs['avancar']])
        if not df_para_analise.empty:
            lista_doutores = [""] + sorted(df_para_analise[col_map['doctor_name']].tolist())
            doutor_selecionado = st.selectbox("Selecione um doutor para análise:", options=lista_doutores)
            if doutor_selecionado:
                exibir_detalhes_doutor(doutor_selecionado, df_completo, col_map)
        else:
            st.info("Nenhum doutor para análise individual no momento.")

    with tab_farming:
        st.subheader(f"Clientes em Farming ({len(categorias_dfs['farming'])})")
        for index, row in categorias_dfs['farming'].iterrows():
            exibir_card_cliente(row, col_map)

    # (Repetir o padrão de cards para as outras abas)
    with tab_waiting:
        st.subheader(f"Clientes em Espera ({len(categorias_dfs['waiting'])})")
        for index, row in categorias_dfs['waiting'].iterrows():
            exibir_card_cliente(row, col_map)
            
    with tab_backtosales:
        st.subheader(f"Clientes em Back to Sales ({len(categorias_dfs['back_to_sales'])})")
        for index, row in categorias_dfs['back_to_sales'].iterrows():
            exibir_card_cliente(row, col_map)
            
    with tab_outros:
        st.subheader(f"Clientes Sem Categoria ({len(categorias_dfs['outros'])})")
        for index, row in categorias_dfs['outros'].iterrows():
            exibir_card_cliente(row, col_map)
