# /workspace/streamlit_template/app.py
import streamlit as st
from auth import autenticador, supabase
from ui import exibir_dashboard_usuario, exibir_dashboard_lider
from data_analysis import analisar_respostas_cliente

def main():
    """Função principal que executa o aplicativo Streamlit."""
    
    # Tenta obter o usuário logado e suas informações de perfil (role, team, etc.)
    user, user_profile = autenticador()

    # Se o usuário não estiver logado (ou seja, 'user' é None), o 'autenticador' já cuidou de mostrar o login.
    # A execução para aqui até que o login seja bem-sucedido.
    if not user or not user_profile:
        return

    # Se o login foi bem-sucedido, podemos prosseguir.
    role = user_profile.get('role')
    
    st.sidebar.success(f"Logado como: {user.email}")
    if st.sidebar.button("Logout"):
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

    st.title("📊 Dashboard de Análise ONB")
    st.markdown("---")

    # ---- Upload do arquivo principal de análise ----
    st.header("1. Análise de Clientes da Planilha")
    uploaded_file = st.file_uploader("Faça upload da sua planilha de clientes (.xlsx)", type=["xlsx"])
    
    df_analise = None
    if uploaded_file:
        df_analise = uploaded_file
        st.success("Planilha de clientes carregada com sucesso!")

    # ---- Upload das respostas do cliente (opcional) ----
    st.header("2. Análise de Respostas da Reunião (Opcional)")
    st.info("Copie e cole aqui as respostas do cliente para obter recomendações personalizadas.")
    respostas_cliente_texto = st.text_area(
        "Cole aqui o texto da primeira reunião (ONBOARDING 1 - REALIZADO COM SUCESSO)",
        height=250,
        key="respostas_cliente"
    )
    
    recomedacoes_personalizadas = None
    if respostas_cliente_texto:
        recomedacoes_personalizadas = analisar_respostas_cliente(respostas_cliente_texto)

    # ---- Exibição do Dashboard ----
    if role == 'lider':
        exibir_dashboard_lider(user_profile, df_analise, recomedacoes_personalizadas)
    elif role == 'user':
        exibir_dashboard_usuario(user, df_analise, recomedacoes_personalizadas)
    else:
        st.error("Seu usuário não tem uma permissão definida (role). Contate o administrador.")

if __name__ == "__main__":
    main()