# /workspace/streamlit_template/ui.py
import streamlit as st
from data_analysis import categorizar_clientes

def exibir_dashboard_base(df_analise, recomedacoes_personalizadas, filtro_responsavel=None):
    """Função base para exibir os componentes do dashboard."""
    if df_analise is None:
        st.info("Aguardando upload da planilha de clientes para iniciar a análise.")
        return

    try:
        df = pd.read_excel(df_analise)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return

    # Aplica o filtro de responsável se fornecido
    if filtro_responsavel and 'Responsável' in df.columns:
        df = df[df['Responsável'] == filtro_responsavel]
        if df.empty:
            st.warning(f"Nenhum cliente encontrado para o responsável: {filtro_responsavel}")
            return
    
    waiting_df, avancar_df, atuar_df = categorizar_clientes(df)

    if waiting_df is None: # Ocorreu um erro na categorização
        return

    # Exibe recomendações personalizadas se existirem
    if recomedacoes_personalizadas:
        st.subheader("Recomendações da Análise de Reunião")
        for rec in recomedacoes_personalizadas:
            st.markdown(f"- {rec}")
        st.markdown("---")

    # ---- Métricas Gerais ----
    st.subheader("Visão Geral da Carteira")
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes para Atuar", f"{len(atuar_df)}")
    col2.metric("Clientes em Espera (Waiting)", f"{len(waiting_df)}")
    col3.metric("Clientes para Avançar", f"{len(avancar_df)}")
    
    st.markdown("---")

    # ---- Abas de Navegação ----
    tab1, tab2, tab3 = st.tabs(["Para Atuar", "Waiting", "Avançar"])

    with tab1:
        st.subheader(f"Clientes que precisam de atuação ({len(atuar_df)})")
        st.dataframe(atuar_df)
        st.info("Estes clientes possuem data de ONB Start, mas a nota (ONB grade) não é 'A'. O objetivo é atuar para que atinjam a nota máxima.")

    with tab2:
        st.subheader(f"Clientes aguardando data de ONB Start ({len(waiting_df)})")
        st.dataframe(waiting_df)
        st.info("Estes clientes ainda não têm uma data de ONB Start definida. Eles estão ordenados pela data de 'Technical ONB start', do mais antigo para o mais novo.")

    with tab3:
        st.subheader(f"Clientes prontos para avançar ({len(avancar_df)})")
        st.dataframe(avancar_df)
        st.info("Estes clientes já possuem nota 'A' e estão prontos para as próximas etapas do processo.")

def exibir_dashboard_usuario(user, df_analise, recomedacoes_personalizadas):
    """Exibe o dashboard para um usuário comum, filtrando por seu e-mail."""
    exibir_dashboard_base(df_analise, recomedacoes_personalizadas, filtro_responsavel=user.email)

def exibir_dashboard_lider(user_profile, df_analise, recomedacoes_personalizadas):
    """Exibe o dashboard para um líder, com filtros para a equipe."""
    st.sidebar.title("Painel do Líder")
    
    equipe = user_profile.get('team', [])
    equipe_com_lider = [user_profile['email']] + equipe
    
    # Filtro por membro da equipe
    membro_selecionado = st.sidebar.selectbox(
        "Filtrar por membro da equipe:",
        options=["Toda a Equipe"] + equipe_com_lider
    )

    if membro_selecionado == "Toda a Equipe":
        exibir_dashboard_base(df_analise, recomedacoes_personalizadas)
    else:
        exibir_dashboard_base(df_analise, recomedacoes_personalizadas, filtro_responsavel=membro_selecionado)