# /workspace/streamlit_template/data_analysis.py
import pandas as pd
import streamlit as st

def categorizar_clientes(df):
    """Categoriza os clientes em WAITING, AVANÇAR e ATUAR."""
    if df is None or df.empty:
        return None, None, None

    # Garante que a coluna de data exista e converte para datetime
    if 'ONB Start' not in df.columns or 'ONB grade' not in df.columns:
        st.error("A planilha precisa conter as colunas 'ONB Start' e 'ONB grade'.")
        return None, None, None

    df['ONB Start Date'] = pd.to_datetime(df['ONB Start'], errors='coerce')
    
    # Separa os que não têm data
    waiting_df = df[df['ONB Start Date'].isna()].copy()
    if 'Technical ONB start' in waiting_df.columns:
        waiting_df['Technical ONB start Date'] = pd.to_datetime(waiting_df['Technical ONB start'], errors='coerce')
        waiting_df = waiting_df.sort_values(by='Technical ONB start Date', ascending=True)

    # Separa os que têm data
    com_data_df = df.dropna(subset=['ONB Start Date'])
    
    avancar_df = com_data_df[com_data_df['ONB grade'] == 'A'].copy()
    atuar_df = com_data_df[com_data_df['ONB grade'] != 'A'].copy()

    return waiting_df, avancar_df, atuar_df

def analisar_respostas_cliente(texto):
    """Extrai informações do texto da reunião e gera recomendações."""
    if not texto:
        return None
        
    recomendacoes = []
    # Converte o texto para minúsculas para facilitar a análise
    texto_lower = texto.lower()

    # Análise do plano (considera o caso especial do Starter)
    plano = "não identificado"
    if "plano: starter" in texto_lower:
        plano = "Starter"
        recomendacoes.append("⚠️ **Plano Starter:** Lembre-se que este plano não inclui Prontuário e CAD. Foque em outras áreas para aumentar o score.")
    elif "plano:" in texto_lower:
        plano = "Outro" # Identifica que é um plano que não é o starter
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