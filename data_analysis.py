# /workspace/streamlit_template/data_analysis.py
import pandas as pd
import streamlit as st

def categorizar_clientes(df):
    """
    Categoriza os clientes em WAITING, AVANÇAR e ATUAR com base no DataFrame fornecido.
    Esta versão é robusta a variações de maiúsculas/minúsculas e espaços nos nomes das colunas.
    """
    if df is None or df.empty:
        return None, None, None

    # --- INÍCIO DA MELHORIA ---
    # Mapeia os nomes das colunas originais para nomes normalizados (minúsculos e sem espaços)
    col_map = {col.strip().lower(): col for col in df.columns}

    # Define os nomes de coluna normalizados que estamos procurando
    TARGET_START_NORMALIZED = 'onb start (onboarding_at_cx)'
    TARGET_GRADE_NORMALIZED = 'onb grade'
    TARGET_TECH_START_NORMALIZED = 'technical onb start (commercial from date)'

    # Verifica se as colunas essenciais existem no mapeamento
    if TARGET_START_NORMALIZED not in col_map or TARGET_GRADE_NORMALIZED not in col_map:
        st.error("ERRO: A planilha precisa conter colunas que correspondam a 'ONB start (onboarding_at_cx)' e 'ONB grade'.")
        st.info(f"Colunas encontradas no seu arquivo: {list(df.columns)}")
        return None, None, None

    # Obtém os nomes das colunas originais usando o mapeamento
    original_start_col = col_map[TARGET_START_NORMALIZED]
    original_grade_col = col_map[TARGET_GRADE_NORMALIZED]
    # --- FIM DA MELHORIA ---

    # Converte a coluna de data para o formato datetime, usando o nome original da coluna
    df['ONB Start Date'] = pd.to_datetime(df[original_start_col], errors='coerce')
    
    # Separa os que não têm data
    waiting_df = df[df['ONB Start Date'].isna()].copy()
    
    # Ordena o grupo 'WAITING' se a coluna técnica existir
    if TARGET_TECH_START_NORMALIZED in col_map:
        original_tech_start_col = col_map[TARGET_TECH_START_NORMALIZED]
        waiting_df['Technical ONB start Date'] = pd.to_datetime(waiting_df[original_tech_start_col], errors='coerce')
        waiting_df = waiting_df.sort_values(by='Technical ONB start Date', ascending=True)

    # Separa os que têm data
    com_data_df = df.dropna(subset=['ONB Start Date'])
    
    # Categoriza em Avançar (grade A) e Atuar (grade diferente de A)
    avancar_df = com_data_df[com_data_df[original_grade_col] == 'A'].copy()
    atuar_df = com_data_df[com_data_df[original_grade_col] != 'A'].copy()

    return waiting_df, avancar_df, atuar_df

def analisar_respostas_cliente(texto):
    """Extrai informações do texto da reunião e gera recomendações."""
    if not texto:
        return None
        
    recomendacoes = []
    # Converte o texto para minúsculas para facilitar a análise
    texto_lower = texto.lower()

    # Análise do plano (considera o caso especial do Starter)
    if "plano: starter" in texto_lower:
        recomendacoes.append("⚠️ **Plano Starter:** Lembre-se que este plano não inclui Prontuário e CAD. Foque em outras áreas para aumentar o score.")
    elif "plano:" in texto_lower:
        recomendacoes.append("✅ **Plano Completo:** Explore todas as funcionalidades, incluindo Prontuário e CAD, para maximizar a pontuação.")

    # Análise de Teleconsulta
    if "atende por teleconsulta: não" in texto_lower:
        recomendacoes.append("Teleconsulta: Cliente não atende. Avaliar a possibilidade de habilitar para ganhar mais pontos e visibilidade.")
    elif "atende por teleconsulta: sim" in texto_lower:
        recomendacoes.append("Teleconsulta: Já habilitado. Verifique se a agenda online reflete os horários corretamente.")

    # Análise de Horas Semanais
    if "mais de 8h semanais: não" in texto_lower:
        recomendacoes.append("Agenda: Menos de 8h semanais liberadas. Incentive o cliente a liberar mais horários para melhorar o posicionamento.")

    # Análise de Secretária
    if "possui secretária: não" in texto_lower:
        recomendacoes.append("Secretária: Cliente não possui. Destaque a importância do app Doctoralia para gerenciar a agenda e as mensagens de forma autônoma.")

    # Análise do GMN (Gestor de Marketing de Opiniões)
    if "ciente do gmn: não" in texto_lower or "ciente do gmn: nao" in texto_lower:
        recomendacoes.append("GMN: Cliente não ciente. Apresente a ferramenta e explique como ela é crucial para coletar e gerenciar as opiniões dos pacientes.")

    if not recomendacoes:
        return ["Nenhuma recomendação específica pôde ser gerada automaticamente a partir do texto."]

    return recomendacoes
