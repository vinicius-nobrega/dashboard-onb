# /workspace/streamlit_template/auth.py
import streamlit as st
from supabase import create_client, Client

# --- Inicialização da Conexão com o Supabase ---
# Tenta conectar usando os "Secrets" do Streamlit Cloud. Se falhar, usa o modo offline.
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(supabase_url, supabase_key)
    st.session_state.supabase_connected = True
except (KeyError, AttributeError):
    st.session_state.supabase_connected = False
    supabase = None

# --- Dados de Demonstração para Modo Offline ---
DEMO_USERS = {
    "lider@exemplo.com": {"password": "lider123", "role": "lider", "team": ["user1@exemplo.com", "user2@exemplo.com"]},
    "user1@exemplo.com": {"password": "user123", "role": "user", "leader_email": "lider@exemplo.com"},
    "user2@exemplo.com": {"password": "user456", "role": "user", "leader_email": "lider@exemplo.com"}
}

# --- Funções de Autenticação ---

def login_form():
    """Exibe o formulário de login e lida com a submissão."""
    st.title("Login - Dashboard ONB")
    if not st.session_state.supabase_connected:
        st.warning("Executando em modo de demonstração. Conexão com o banco de dados não encontrada.")
    
    with st.form("login_form"):
        email = st.text_input("Email", value="lider@exemplo.com" if not st.session_state.supabase_connected else "")
        password = st.text_input("Senha", type="password", value="lider123" if not st.session_state.supabase_connected else "")
        submitted = st.form_submit_button("Login")

        if submitted:
            if st.session_state.supabase_connected:
                # Lógica de login online com Supabase
                try:
                    user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.logged_in = True
                    st.session_state.user = user.user
                    st.rerun()
                except Exception as e:
                    st.error("Email ou senha inválidos.")
            else:
                # Lógica de login offline (modo demonstração)
                if email in DEMO_USERS and DEMO_USERS[email]["password"] == password:
                    st.session_state.logged_in = True
                    # Simula um objeto de usuário para o modo offline
                    st.session_state.user = type('User', (object,), {'email': email})() 
                    st.rerun()
                else:
                    st.error("Email ou senha de demonstração inválidos.")

def get_user_profile(user):
    """Busca o perfil do usuário (role, team, etc.) no banco de dados ou nos dados de demo."""
    if not user:
        return None

    if st.session_state.supabase_connected:
        try:
            # Busca na tabela 'user_roles' pelo email do usuário logado
            response = supabase.table('user_roles').select('*').eq('email', user.email).single().execute()
            return response.data
        except Exception:
            st.error("Não foi possível encontrar um perfil para este usuário. Contate o administrador.")
            return None
    else:
        # Retorna o perfil dos dados de demonstração
        return DEMO_USERS.get(user.email)

def autenticador():
    """Função principal de autenticação. Gerencia o estado de login e retorna o usuário."""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_form()
        return None, None
    else:
        user = st.session_state.get('user')
        user_profile = get_user_profile(user)
        return user, user_profile