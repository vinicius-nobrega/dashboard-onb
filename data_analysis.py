# data_analysis.py (VERSÃO FINAL COMPLETA)

import pandas as pd
import streamlit as st
from datetime import datetime

PONTUACAO_CATEGORIAS = {
    'Configuração Técnica': 80,
    'Configuração de Visibilidade': 75,
    'Adoção': 80,
    'Recursos Avançados': 90
}

def analisar_pontuacao_doutor(doutor_series, col_map):
    """Analisa a pontuação completa de um único doutor."""
    resumo = {
        'total_atual': int(doutor_series.get(col_map.get('onb points', 0), 0)),
        'total_maximo': sum(PONTUACAO_CATEGORIAS.values()),
        'categorias': {cat: {'atual': 0, 'max': val} for cat, val in PONTUACAO_CATEGORIAS.items()},
        'acoes_faltantes': []
    }
    plano = str(doutor_series.get(col_map.get('package', ''), '')).lower()
    def get_val(col_name_normalizado, default=0):
        return doutor_series.get(col_map.get(col_name_normalizado, ''), default)

    # 1. Configuração Técnica
    cat = 'Configuração Técnica'
    if get_val('number_of_secretaries', 0) > 0 or get_val('call center setup', 0) == 1 or get_val('pms setup', 0) == 1: resumo['categorias'][cat]['atual'] += 25
    else: resumo['acoes_faltantes'].append(("[Técnica] Ativar usuário de secretária, CAD ou Integração", 25))
    if plano != 'starter' and get_val('mobile app', 0) == 1: resumo['categorias'][cat]['atual'] += 5
    elif plano != 'starter': resumo['acoes_faltantes'].append(("[Técnica] Fazer login no Aplicativo", 5))
    if get_val('imported 20 patients', 0) == 1: resumo['categorias'][cat]['atual'] += 15
    else: resumo['acoes_faltantes'].append(("[Técnica] Importar ao menos 20 pacientes", 15))
    if plano != 'starter' and get_val('online consultation', 0) == 1: resumo['categorias'][cat]['atual'] += 15
    elif plano != 'starter': resumo['acoes_faltantes'].append(("[Técnica] Abrir agenda para Telemedicina", 15))
    if get_val('online_payments_enabled', 0) == 1: resumo['categorias'][cat]['atual'] += 5
    else: resumo['acoes_faltantes'].append(("[Técnica] Ativar Doctoralia Pagamentos", 5))
    if get_val('review request notif', 0) == 1: resumo['categorias'][cat]['atual'] += 15
    else: resumo['acoes_faltantes'].append(("[Técnica] Ativar notificações de Pedido de Opinião", 15))

    # 2. Configuração de Visibilidade
    cat = 'Configuração de Visibilidade'
    if get_val('bookable hours', 0) >= 60: resumo['categorias'][cat]['atual'] += 15
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Atingir 60h disponíveis nos próximos 30 dias", 15))
    if get_val('bookable days', 0) >= 10: resumo['categorias'][cat]['atual'] += 15
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Ter horários em pelo menos 10 dias diferentes", 15))
    if get_val('min_2_insurers', 0) == 1: resumo['categorias'][cat]['atual'] += 20
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Configurar ao menos 2 planos de saúde", 20))
    if get_val('70 profile completeness', 0) == 5: resumo['categorias'][cat]['atual'] += 5
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Atingir 70% de perfil completo", 5))
    if get_val('has_pricing', 0) == 1: resumo['categorias'][cat]['atual'] += 5
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Informar preço em ao menos um serviço", 5))
    if get_val('wap or mess autoresponder', 0) == 1: resumo['categorias'][cat]['atual'] += 5
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Ativar mensagem de ausência no WhatsApp", 5))
    if get_val('widget_or_www_setup', 0) == 1: resumo['categorias'][cat]['atual'] += 10
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Instalar Widget no site ou adquirir Website", 10))
    if get_val('gmb', 0) == 1 or pd.notna(get_val('ig link', None)) or pd.notna(get_val('fb link', None)): resumo['categorias'][cat]['atual'] += 10
    else: resumo['acoes_faltantes'].append(("[Visibilidade] Integrar com GMB, Instagram ou Facebook", 10))

    # 3. Adoção
    cat = 'Adoção'
    # Esta pontuação é complexa e geralmente vem direto da plataforma. Usamos o valor existente.
    # Vamos simular um cálculo simples para ilustração, mas o ideal é ter uma coluna com essa pontuação.
    pontos_adocao = min((get_val('admin bookings', 0) + get_val('user bookings', 0)) * 2, 80) # Exemplo: 2 pontos por booking
    resumo['categorias'][cat]['atual'] += pontos_adocao
    if pontos_adocao < 80: resumo['acoes_faltantes'].append(("[Adoção] Aumentar o número de agendamentos via plataforma", 80 - pontos_adocao))

    # 4. Recursos Avançados
    cat = 'Recursos Avançados'
    if get_val('sent_campaign_onb_period', 0) == 1: resumo['categorias'][cat]['atual'] += 30
    else: resumo['acoes_faltantes'].append(("[Avançado] Enviar campanha para pelo menos 10 pacientes", 30))
    # Opiniões e Bookings
    pontos_opiniao_booking = min((get_val('opinions', 0) * 4) + (get_val('user bookings', 0) * 10), 40)
    resumo['categorias'][cat]['atual'] += pontos_opiniao_booking
    if pontos_opiniao_booking < 40: resumo['acoes_faltantes'].append(("[Avançado] Obter mais opiniões e agendamentos de pacientes", 40 - pontos_opiniao_booking))
    # Pergunte ao especialista
    pontos_perguntas = min(get_val('public_questions_answered_onb_period', 0) * 5, 20)
    resumo['categorias'][cat]['atual'] += pontos_perguntas
    if pontos_perguntas < 20: resumo['acoes_faltantes'].append(("[Avançado] Responder mais perguntas no 'Pergunte ao Especialista'", 20 - pontos_perguntas))

    return resumo

def calcular_dias_restantes(data_fim_str):
    """Calcula os dias restantes com base na data final fornecida."""
    if pd.isna(data_fim_str) or data_fim_str == '': return "Sem data final"
    try:
        data_fim = pd.to_datetime(data_fim_str)
        dias_restantes = (data_fim.date() - datetime.now().date()).days
        return dias_restantes if dias_restantes >= 0 else "Finalizado"
    except Exception as e:
        return "Data inválida"

def categorizar_clientes_v2(df):
    """Nova função para categorizar clientes com base no lifecycle_stage e cs_client_stage."""
    if df is None or df.empty: return {}
    col_map = {col.strip().lower(): col for col in df.columns}
    
    required_cols = ['lifecycle_stage', 'cs_client_stage', 'onb grade']
    for col in required_cols:
        if col not in col_map:
            st.error(f"ERRO: A planilha precisa conter a coluna '{col}'.")
            return {}

    categorias = {cat: [] for cat in ['farming', 'back_to_sales', 'waiting', 'atuar', 'avancar', 'outros']}
    
    lifecycle_col, cs_stage_col, grade_col = col_map['lifecycle_stage'], col_map['cs_client_stage'], col_map['onb grade']
    
    for index, row in df.iterrows():
        lifecycle = str(row.get(lifecycle_col, '')).lower()
        cs_stage = str(row.get(cs_stage_col, '')).lower()
        grade = str(row.get(grade_col, ''))

        if 'farming' in lifecycle or 'adoption' in cs_stage: categorias['farming'].append(row)
        elif 'back to sales' in cs_stage: categorias['back_to_sales'].append(row)
        elif 'waiting' in cs_stage: categorias['waiting'].append(row)
        elif cs_stage in ['re-onboarding', 'after first call']:
            if grade == 'A': categorias['avancar'].append(row)
            else: categorias['atuar'].append(row)
        else: categorias['outros'].append(row)

    return {cat: pd.DataFrame(data) if data else pd.DataFrame(columns=df.columns) for cat, data in categorias.items()}
