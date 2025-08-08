# app.py (VERSÃO FINAL)

import streamlit as st
from auth import autenticador
from ui import exibir_dashboard
from data_analysis import categorizar_clientes_v2
import pandas as pd

def main():
    """Função principal que executa o aplicativo Streamlit."""
    
    st.set_page_config(layout="wide") # Deixa a página mais larga
    
    user, user_profile = autenticador()

    if not user or not user_profile:
        return

    st.sidebar.title(f"Bem-vindo(a)!")
    st.sidebar.success(f"Logado como: {user.email}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("📊 Dashboard de Análise de Onboarding")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Faça upload da sua planilha de clientes (.xlsx)", 
        type=["xlsx"]
    )
    
    if uploaded_file:
        try:
            df_original = pd.read_excel(uploaded_file)
            st.success("Planilha de clientes carregada com sucesso!")
            
            # Usa a nova função de categorização V2
            categorias_dfs = categorizar_clientes_v2(df_original.copy())
            
            # Chama a nova função de interface principal
            exibir_dashboard(user_profile, df_original, categorias_dfs)

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
            st.warning("Verifique se o arquivo Excel não está corrompido e se o formato está correto.")

if __name__ == "__main__":
    main()
