# data_analysis.py (VERSÃO 2.0 - ATUALIZADO COM NOVAS REGRAS)

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# ==============================================================================
# NOVAS FUNÇÕES DE LÓGICA DE DADOS E PONTUAÇÃO (V2)
# ==============================================================================

# --- Mapeamento de Colunas e Pontuações ---
# Centraliza os nomes das colunas e as pontuações para fácil manutenção
PONTUACAO_MAP = {
    'secretaria_cad_integracao': {'max': 25, 'cols': ['number_of_secretaries', 'call center setup', 'pms setup']},
    'aplicativo': {'max': 5, 'cols': ['mobile app']},
    'importacao': {'max': 15, 'cols': ['imported 20 patients']},
    'telemedicina': {'max': 15, 'cols': ['online consultation']},
    'pagamentos': {'max': 5, 'cols': ['online_payments_enabled']},
    'pedido_opiniao': {'max': 15, 'cols': ['review request notif']},
    'horas_disponiveis': {'max': 15, 'cols': ['bookable hours']},
    'dias_disponiveis': {'max': 15, 'cols': ['bookable days']},
    'planos_saude': {'max': 20, 'cols': ['min_2_insurers']},
    'perfil_completo': {'max': 5, 'cols': ['70 profile completeness']},
    'preco': {'max': 5, 'cols': ['has_pricing']},
    'whatsapp': {'max': 5, 'cols': ['wap or mess autoresponder']},
    'widget_website': {'max': 10, 'cols': ['widget_or_www_setup']},
    'midias_sociais': {'max': 10, 'cols': ['gmb', 'ig link', 'fb link']},
    'agendamentos': {'max': 80, 'cols': ['admin bookings', 'user bookings']},
    'campanha': {'max': 30, 'cols': ['sent_campaign_onb_period']},
    'opinioes_e_bookings': {'max': 40, 'cols': ['opinions', 'user bookings']},
    'pergunte_especialista': {'max': 20, 'cols': ['public_questions_answered_onb_period']},
    'prontuario': {'max': 0, 'cols': ['ehr episodes']} # Sem pontuação direta, mas importante para análise
}

def analisar_pontuacao_doutor(doutor_series, col_map):
    """
    Analisa a pontuação de um único doutor (uma linha do DataFrame).
    Retorna um dicionário com os pontos atuais, máximos e o que falta.
    """
    pontos_atuais = 0
    acoes_faltantes = []
    plano = str(doutor_series.get(col_map.get('package', ''), '')).lower()

    # Função auxiliar para verificar colunas
    def get_col_value(key):
        # Retorna o valor da primeira coluna encontrada no mapeamento, ou 0 se não encontrar
        for col_normalizada in PONTUACAO_MAP[key]['cols']:
            if col_normalizada in col_map:
                return doutor_series.get(col_map[col_normalizada], 0)
        return 0

    # 1. Configuração Técnica (80 pts)
    # 1.1 Secretária/CAD/Integração
    val_secretaria = get_col_value('secretaria_cad_integracao') > 0
    if val_secretaria:
        pontos_atuais += 25
    else:
        acoes_faltantes.append("Ativar usuário de secretária, CAD ou Integração (+25 pts)")

    # 1.2 Aplicativo
    if plano == 'starter':
        acoes_faltantes.append("Plano STARTER não inclui Aplicativo (potencial de 5 pts em outros planos)")
    elif get_col_value('aplicativo') >= 1:
        pontos_atuais += 5
    else:
        acoes_faltantes.append("Baixar e fazer login no Aplicativo (+5 pts)")

    # 1.3 Importação
    if get_col_value('importacao') >= 1:
        pontos_atuais += 15
    else:
        acoes_faltantes.append("Importar ao menos 20 pacientes (+15 pts)")
        
    # 1.4 Telemedicina
    if plano == 'starter':
         acoes_faltantes.append("Plano STARTER não inclui Telemedicina (potencial de 15 pts em outros planos)")
    elif get_col_value('telemedicina') >= 1:
        pontos_atuais += 15
    else:
        acoes_faltantes.append("Abrir a agenda para Telemedicina (+15 pts)")

    # 1.5 Pagamentos Online
    if get_col_value('pagamentos') >= 1:
        pontos_atuais += 5
    else:
        acoes_faltantes.append("Ativar Doctoralia Pagamentos (+5 pts)")

    # 1.6 Pedido de Opinião
    if get_col_value('pedido_opiniao') >= 1:
        pontos_atuais += 15
    else:
        acoes_faltantes.append("Ativar notificações de Pedido de Opinião (+15 pts)")
        
    # 2. Configuração de Visibilidade (75 pts)
    # Implementar as demais regras aqui seguindo o mesmo padrão...
    # Exemplo: 2.1 60h disponíveis
    if get_col_value('horas_disponiveis') >= 60:
        pontos_atuais += 15
    else:
        acoes_faltantes.append(f"Disponibilizar mais {60 - get_col_value('horas_disponiveis')} horas na agenda nos próximos 30 dias (+15 pts)")
        
    # (As outras regras de pontuação seriam adicionadas aqui, seguindo a mesma lógica)

    return {
        "pontos_atuais": doutor_series.get(col_map.get('onb points', 0), 0), # Usa o ponto da planilha como oficial
        "pontos_calculados": pontos_atuais, # Nosso cálculo para conferência
        "pontos_maximos": 325,
        "acoes_faltantes": acoes_faltantes
    }


def calcular_dias_restantes(data_inicio_str):
    """Calcula os dias restantes para o fim do onboarding (28 dias)."""
    if pd.isna(data_inicio_str):
        return "Data de início não definida"
    try:
        data_inicio = pd.to_datetime(data_inicio_str)
        data_fim = data_inicio + timedelta(days=28)
        dias_restantes = (data_fim - datetime.now()).days
        return dias_restantes if dias_restantes >= 0 else "Finalizado"
    except:
        return "Data em formato inválido"


def categorizar_clientes_v2(df):
    """
    Nova função para categorizar clientes com base nas regras de lifecycle e cs_client_stage.
    """
    if df is None or df.empty:
        return {}

    # Normaliza nomes de colunas para robustez
    col_map = {col.strip().lower(): col for col in df.columns}
    
    # Colunas necessárias para a lógica
    required_cols = ['lifecycle_stage', 'cs_client_stage', 'onb grade']
    for col in required_cols:
        if col not in col_map:
            st.error(f"ERRO: A planilha precisa conter a coluna '{col}'.")
            return {}

    # DataFrames para cada categoria
    categorias = {
        'farming': pd.DataFrame(columns=df.columns),
        'back_to_sales': pd.DataFrame(columns=df.columns),
        'waiting': pd.DataFrame(columns=df.columns),
        'atuar': pd.DataFrame(columns=df.columns),
        'avancar': pd.DataFrame(columns=df.columns),
        'outros': pd.DataFrame(columns=df.columns)
    }

    # Mapeamento dos nomes de colunas originais
    lifecycle_col = col_map['lifecycle_stage']
    cs_stage_col = col_map['cs_client_stage']
    grade_col = col_map['onb grade']
    
    for index, row in df.iterrows():
        lifecycle = str(row[lifecycle_col]).lower()
        cs_stage = str(row[cs_stage_col]).lower()
        grade = str(row[grade_col])

        # A lógica de decisão com base nas suas regras
        if lifecycle == 'farming' or cs_stage == 'adoption':
            categorias['farming'] = pd.concat([categorias['farming'], row.to_frame().T], ignore_index=True)
        elif cs_stage == 'back to sales':
            categorias['back_to_sales'] = pd.concat([categorias['back_to_sales'], row.to_frame().T], ignore_index=True)
        elif cs_stage == 'waiting':
            categorias['waiting'] = pd.concat([categorias['waiting'], row.to_frame().T], ignore_index=True)
        elif cs_stage in ['re-onboarding', 'after first call']:
            if grade == 'A':
                categorias['avancar'] = pd.concat([categorias['avancar'], row.to_frame().T], ignore_index=True)
            else:
                categorias['atuar'] = pd.concat([categorias['atuar'], row.to_frame().T], ignore_index=True)
        else: # Casos não previstos
             categorias['outros'] = pd.concat([categorias['outros'], row.to_frame().T], ignore_index=True)

    return categorias

# Manter a função antiga para análise de texto, pois ainda será útil
def analisar_respostas_cliente(texto):
    """Extrai informações do texto da reunião e gera recomendações."""
    if not texto:
        return None
    # (código desta função permanece o mesmo da versão anterior)
    return ["Análise de texto ainda a ser implementada no novo layout."]
