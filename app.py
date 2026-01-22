"""
Dashboard de Análise de Similaridade CAR-SIGEF

Este dashboard fornece análise exploratória de dados de similaridade espacial 
entre registros do Cadastro Ambiental Rural (CAR) e do Sistema de Gestão 
Fundiária (SIGEF).

Características principais:
- Análise de similaridade espacial usando Índice de Jaccard
- Cruzamento de titularidade (CPF/CNPJ)
- Visualizações interativas por região, UF, tamanho e status
- Performance otimizada com DuckDB
- Cache inteligente para filtros

Desenvolvido para: Ministério da Gestão e Inovação (MGI)
Autor: Denner Caleare
Data: Janeiro 2026
"""

# ═══════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════

# Bibliotecas padrão Python
import os
import base64

# Bibliotecas de terceiros - Data
import pandas as pd
import numpy as np
import duckdb

# Bibliotecas de terceiros - Visualização
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import zetta_utils as zt
import plotly.express as px
import plotly.graph_objects as go
import json

# Imports locais - Configurações
from src.config import (
    CSS_CUSTOM, CORES_FAIXA_JACCARD, CORES_TAMANHO, CORES_STATUS,
    CORES_EVOLUCAO_TAMANHO, CORES_EVOLUCAO_REGIAO, CORES_TITULARIDADE,
    CORES_MATURIDADE_REGIAO, JACCARD_LABELS, LABELS_STATUS, REGIOES_NOME_MAP,
    DISCREPANCIA_MIN, DISCREPANCIA_MAX, LOGO_FOOTER_PATH, ANO_MIN, ANO_MAX
)

# Imports locais - Utilitários
from src.utils import (
    load_metadata, load_filtered_data, get_total_records,
    format_number, create_quadrant_background, add_quadrant_labels,
    display_region_filter, display_uf_filter, display_size_filter,
    display_status_filter, display_filter_summary, get_aggregated_stats
)

# ═══════════════════════════════════════════════════════════
# CONSTANTES DE CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════

# Alturas fixas para gráficos (evita flickering)
CHART_HEIGHTS = {
    'metrics': (12, 3),
    'bars_normal': (12, 6),
    'bars_compact': (12, 4.5),
    'scatter': (12, 10),
    'density': (7, 4.5),
    'map': (7, 5),
    'donut': (7, 4.5),
    'temporal': (12, 6),
    'mosaic': (12, 8),
    'bubble': (16, 8)
}

CONFIG = {
    # Limites de dados para análises
    'MIN_RECORDS_FOR_ANALYSIS': 10,      # Mínimo de registros para análises gerais
    'MIN_RECORDS_FOR_DENSITY': 10,       # Mínimo de registros para gráficos KDE
    
    # Performance e otimização
    'SHOW_DEBUG_INFO': False,            # Mostrar informações de debug
    'PROGRESS_SLEEP': 0.01,              # Intervalo para animação de progresso (segundos)
    'SUCCESS_MESSAGE_DURATION': 0.3,     # Duração de mensagens de sucesso (segundos)
    
    # Configurações visuais
    'DEFAULT_FIGSIZE': (12, 6),          # Tamanho padrão de figuras matplotlib
    'MOBILE_BREAKPOINT': 768,            # Breakpoint para layout mobile (pixels)
}

# ═══════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════

def validate_data(df, section_name: str, min_records: int = 1) -> bool:
    """Valida se há dados suficientes para análise.
    
    Args:
        df: DataFrame a validar
        section_name: Nome da seção para mensagem de erro
        min_records: Número mínimo de registros necessários
        
    Returns:
        True se dados válidos, False caso contrário
    """
    if df is None or len(df) == 0:
        st.warning(f"⚠️ {section_name}: Nenhum registro encontrado com os filtros selecionados.")
        st.info("💡 Ajuste os filtros para visualizar os dados.")
        return False
    
    if len(df) < min_records:
        st.warning(f"⚠️ {section_name}: Dados insuficientes (mínimo {min_records} registros necessários).")
        st.info("💡 Selecione filtros mais abrangentes.")
        return False
    
    return True

def render_matplotlib(fig=None, use_container_width=False):
    """Renderiza gráfico matplotlib com configurações otimizadas para evitar flickering.
    
    Args:
        fig: Figura matplotlib (None usa plt.gcf())
        use_container_width: Se True, usa largura do container
    """
    if fig is None:
        fig = plt.gcf()
    
    plt.tight_layout(pad=0.3)
    st.pyplot(fig, use_container_width=use_container_width)
    plt.close()

def show_progress_bar(message: str = "Carregando dados...", duration: float = 1.0):
    """Exibe barra de progresso animada.
    
    Args:
        message: Mensagem a exibir
        duration: Duração em segundos
    """
    progress_bar = st.progress(0, text=message)
    steps = int(duration / CONFIG['PROGRESS_SLEEP'])
    
    for i in range(steps):
        progress_bar.progress((i + 1) / steps, text=message)
        import time
        time.sleep(CONFIG['PROGRESS_SLEEP'])
    
    progress_bar.empty()

@st.cache_data(ttl=3600)
def load_brazil_geojson():
    """Carrega GeoJSON do Brasil por UF.
    
    Returns:
        dict com GeoJSON dos estados brasileiros
    """
    import urllib.request
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode('utf-8'))

def create_brazil_choropleth_map(df, metric='jaccard_medio'):
    """Cria mapa coroplético do Brasil por UF usando Plotly.
    
    Args:
        df: DataFrame com dados por estado
        metric: Métrica a ser visualizada ('jaccard_medio' padrão)
        
    Returns:
        Figura plotly com o mapa
    """
    # Mapa de siglas para nomes completos dos estados
    ESTADOS_NOMES = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
        'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
        'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    
    # Carregar GeoJSON do Brasil
    geojson = load_brazil_geojson()
    
    # Calcular similaridade média por UF
    df_ufs = df.groupby('estado').agg({
        'indice_jaccard': 'mean'
    }).reset_index()
    df_ufs.columns = ['sigla', 'similaridade']
    df_ufs['similaridade'] = df_ufs['similaridade'] * 100  # Converter para percentual
    
    # Adicionar nome completo do estado
    df_ufs['estado_nome'] = df_ufs['sigla'].map(ESTADOS_NOMES)
    
    # Criar mapa com Plotly
    fig = px.choropleth(
        df_ufs,
        geojson=geojson,
        locations='sigla',
        featureidkey='properties.sigla',
        color='similaridade',
        color_continuous_scale=['#e57373', '#ffb74d', '#fff176', '#aed581', '#81c784'],
        range_color=[0, 100],
        labels={'similaridade': 'Similaridade', 'estado_nome': 'Estado'},
        hover_data={'sigla': False, 'similaridade': ':.1f', 'estado_nome': True},
        custom_data=['estado_nome', 'similaridade']
    )
    
    # Personalizar o hover template
    fig.update_traces(
        hovertemplate='<b>%{customdata[0]}</b><br>Similaridade = %{customdata[1]:.1f} %<extra></extra>',
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial",
            font_color="#333333"
        )
    )
    
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showocean=False,
        showlakes=False,
        showrivers=False
    )
    
    fig.update_layout(
        title={'text': 'Similaridade por Estado', 'x': 0.5, 'xanchor': 'center', 'font': {'size': 10}},
        margin=dict(l=0, r=20, t=30, b=0),
        height=300,
        coloraxis_colorbar=dict(
            title=dict(text="Similaridade (%)", font=dict(size=10)),
            tickfont=dict(size=9),
            len=0.7,
            thickness=15,
            x=0.98,
            xanchor='left'
        )
    )
    
    # Adicionar anotações com valores nos estados
    # Coordenadas aproximadas dos centros dos estados (lon, lat)
    coords = {
        'AC': (-70.0, -9.0), 'AL': (-36.5, -9.5), 'AP': (-51.5, 1.0),
        'AM': (-63.0, -5.0), 'BA': (-41.5, -12.5), 'CE': (-39.5, -5.0),
        'DF': (-47.8, -15.8), 'ES': (-40.3, -19.5), 'GO': (-49.5, -15.5),
        'MA': (-45.0, -5.0), 'MT': (-55.5, -12.5), 'MS': (-54.5, -20.5),
        'MG': (-44.5, -18.5), 'PA': (-52.0, -4.0), 'PB': (-36.7, -7.2),
        'PR': (-51.5, -24.5), 'PE': (-37.5, -8.3), 'PI': (-43.0, -7.5),
        'RJ': (-42.8, -22.3), 'RN': (-36.5, -5.8), 'RS': (-53.5, -30.0),
        'RO': (-63.0, -11.0), 'RR': (-61.0, 2.0), 'SC': (-50.5, -27.0),
        'SE': (-37.4, -10.6), 'SP': (-49.0, -22.5), 'TO': (-48.0, -10.0)
    }
    
    for _, row in df_ufs.iterrows():
        if row['sigla'] in coords:
            lon, lat = coords[row['sigla']]
            fig.add_annotation(
                x=lon, y=lat,
                text=f"{row['similaridade']:.1f}%",
                showarrow=False,
                font=dict(size=8, color='black', family='Arial Black'),
                bgcolor='rgba(255, 255, 255, 0.7)',
                borderpad=2
            )
    
    return fig

def create_brazil_titularidade_map(df):
    """Cria mapa coroplético do Brasil por UF mostrando % de titularidade igual.
    
    Args:
        df: DataFrame com dados por estado e coluna cpf_ok
        
    Returns:
        Figura plotly com o mapa
    """
    # Mapa de siglas para nomes completos dos estados
    ESTADOS_NOMES = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
        'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
        'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    
    # Carregar GeoJSON do Brasil
    geojson = load_brazil_geojson()
    
    # Calcular % de CPF igual por UF
    df_ufs = df.groupby('estado').agg({
        'cpf_ok': 'mean'
    }).reset_index()
    df_ufs.columns = ['sigla', 'cpf_igual']
    df_ufs['cpf_igual'] = df_ufs['cpf_igual'] * 100  # Converter para percentual
    
    # Adicionar nome completo do estado
    df_ufs['estado_nome'] = df_ufs['sigla'].map(ESTADOS_NOMES)
    
    # Criar mapa com Plotly
    fig = px.choropleth(
        df_ufs,
        geojson=geojson,
        locations='sigla',
        featureidkey='properties.sigla',
        color='cpf_igual',
        color_continuous_scale=['#e57373', '#ffb74d', '#fff176', '#aed581', '#81c784'],
        range_color=[0, 100],
        labels={'cpf_igual': 'CPF Igual', 'estado_nome': 'Estado'},
        hover_data={'sigla': False, 'cpf_igual': ':.1f', 'estado_nome': True},
        custom_data=['estado_nome', 'cpf_igual']
    )
    
    # Personalizar o hover template
    fig.update_traces(
        hovertemplate='<b>%{customdata[0]}</b><br>CPF Igual = %{customdata[1]:.1f} %<extra></extra>',
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Arial",
            font_color="#333333"
        )
    )
    
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showocean=False,
        showlakes=False,
        showrivers=False
    )
    
    fig.update_layout(
        title={'text': 'Titularidade por Estado', 'x': 0.5, 'xanchor': 'center', 'font': {'size': 10}},
        margin=dict(l=0, r=20, t=30, b=0),
        height=300,
        coloraxis_colorbar=dict(
            title=dict(text="CPF Igual (%)", font=dict(size=10)),
            tickfont=dict(size=9),
            len=0.7,
            thickness=15,
            x=0.98,
            xanchor='left'
        )
    )
    
    # Adicionar anotações com valores nos estados
    coords = {
        'AC': (-70.0, -9.0), 'AL': (-36.5, -9.5), 'AP': (-51.5, 1.0),
        'AM': (-63.0, -5.0), 'BA': (-41.5, -12.5), 'CE': (-39.5, -5.0),
        'DF': (-47.8, -15.8), 'ES': (-40.3, -19.5), 'GO': (-49.5, -15.5),
        'MA': (-45.0, -5.0), 'MT': (-55.5, -12.5), 'MS': (-54.5, -20.5),
        'MG': (-44.5, -18.5), 'PA': (-52.0, -4.0), 'PB': (-36.7, -7.2),
        'PR': (-51.5, -24.5), 'PE': (-37.5, -8.3), 'PI': (-43.0, -7.5),
        'RJ': (-42.8, -22.3), 'RN': (-36.5, -5.8), 'RS': (-53.5, -30.0),
        'RO': (-63.0, -11.0), 'RR': (-61.0, 2.0), 'SC': (-50.5, -27.0),
        'SE': (-37.4, -10.6), 'SP': (-49.0, -22.5), 'TO': (-48.0, -10.0)
    }
    
    for _, row in df_ufs.iterrows():
        if row['sigla'] in coords:
            lon, lat = coords[row['sigla']]
            fig.add_annotation(
                x=lon, y=lat,
                text=f"{row['cpf_igual']:.1f}%",
                showarrow=False,
                font=dict(size=8, color='black', family='Arial Black'),
                bgcolor='rgba(255, 255, 255, 0.7)',
                borderpad=2
            )
    
    return fig

def get_layout_columns(mobile_cols: int = 2, desktop_cols: int = 4) -> int:
    """Retorna número de colunas baseado no tamanho da tela.
    
    Args:
        mobile_cols: Número de colunas para mobile
        desktop_cols: Número de colunas para desktop
        
    Returns:
        Número de colunas a usar
    """
    # Por enquanto, retorna desktop (pode ser expandido com JavaScript)
    return desktop_cols

# ═══════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Dashboard Similaridade CAR-SIGEF",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

st.markdown(CSS_CUSTOM, unsafe_allow_html=True)

# Inicializar session state para cache de dados
if 'last_filters' not in st.session_state:
    st.session_state.last_filters = None
if 'df_cached' not in st.session_state:
    st.session_state.df_cached = None
if 'df_regiao_cached' not in st.session_state:
    st.session_state.df_regiao_cached = None
if 'last_regiao_filters' not in st.session_state:
    st.session_state.last_regiao_filters = None
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

# ═══════════════════════════════════════════════════════════
# INICIALIZAR BANCO (PRIMEIRA VEZ)
# ═══════════════════════════════════════════════════════════

if not st.session_state.db_initialized:
    try:
        with st.spinner('🚀 Inicializando banco de dados... (pode levar alguns segundos na primeira vez)'):
            from src.utils import load_metadata
            # Isso força a criação da tabela em memória (descompacta ZIP se necessário)
            metadata_test = load_metadata()
            if metadata_test is None or len(metadata_test) == 0:
                st.error("❌ Erro: Não foi possível carregar os metadados do banco de dados.")
                st.info("💡 Verifique os logs do servidor para mais detalhes.")
                st.stop()
            st.session_state.db_initialized = True
    except FileNotFoundError as e:
        st.error(f"❌ Arquivo de dados não encontrado!")
        st.error(f"Detalhes: {str(e)}")
        st.info("💡 Certifique-se de que o arquivo ZIP está no repositório: data/similaridade_sicar_sigef_brasil.zip")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erro ao inicializar banco de dados")
        st.error(f"Tipo: {type(e).__name__}")
        st.error(f"Mensagem: {str(e)}")
        import traceback
        with st.expander("🔍 Ver traceback completo"):
            st.code(traceback.format_exc())
        st.info("💡 Verifique os logs do Streamlit Cloud para mais detalhes.")
        st.stop()

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════

st.markdown("<h1>Análise de Similaridade CAR-SIGEF</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3 style='text-align: center;'>Análise Exploratória dos Dados de Similaridade Espacial</h3>",
    unsafe_allow_html=True
)

# ═══════════════════════════════════════════════════════════
# FILTROS
# ═══════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("<h3 style='text-align: center;'>Filtros de Dados</h3>", unsafe_allow_html=True)

# Mostrar progresso de carregamento
with st.spinner('Carregando metadados...'):
    metadata = load_metadata()

# Usar form para evitar reruns a cada mudança de filtro
with st.form(key="filtros_form"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        regioes_originais = sorted([r for r in metadata['regioes'] if r is not None]) if metadata['regioes'] else []
        regioes_selecionadas = display_region_filter(regioes_originais)

    with col2:
        ufs_originais = sorted([u for u in metadata['estados'] if u is not None]) if metadata['estados'] else []
        ufs_selecionadas = display_uf_filter(ufs_originais)

    with col3:
        tamanhos_disponiveis = sorted([t for t in metadata['tamanhos'] if t is not None]) if metadata['tamanhos'] else []
        tamanhos_selecionados = display_size_filter(tamanhos_disponiveis)

    with col4:
        status_originais = sorted([s for s in metadata['status'] if s is not None]) if metadata['status'] else []
        status_selecionados = display_status_filter(status_originais)
    
    # Botão para aplicar filtros
    submit_button = st.form_submit_button("Aplicar Filtros", use_container_width=True)

# Verificar se filtros mudaram (evitar recálculo desnecessário)
current_filters = (
    tuple(sorted(regioes_selecionadas)) if regioes_selecionadas else (),
    tuple(sorted(ufs_selecionadas)) if ufs_selecionadas else (),
    tuple(sorted(tamanhos_selecionados)) if tamanhos_selecionados else (),
    tuple(sorted(status_selecionados)) if status_selecionados else ()
)

filters_changed = current_filters != st.session_state.last_filters

# Aplicar filtros somente quando botão for clicado ou na primeira carga
if (submit_button and filters_changed) or st.session_state.df_cached is None:
    status_placeholder = st.empty()
    
    try:
        # Validar que não há filtros vazios inválidos
        valid_regioes = [r for r in (regioes_selecionadas or []) if r]
        valid_ufs = [u for u in (ufs_selecionadas or []) if u]
        valid_tamanhos = [t for t in (tamanhos_selecionados or []) if t]
        valid_status = [s for s in (status_selecionados or []) if s]
        
        status_placeholder.info('🔄 Carregando dados filtrados...')
        
        df_filtrado = load_filtered_data(
            regioes=valid_regioes if valid_regioes else None,
            ufs=valid_ufs if valid_ufs else None,
            tamanhos=valid_tamanhos if valid_tamanhos else None,
            status=valid_status if valid_status else None
        )
        
        # Verificar se query retornou dados válidos
        if df_filtrado is None or (isinstance(df_filtrado, pd.DataFrame) and df_filtrado.empty):
            st.session_state.df_cached = pd.DataFrame()
            st.session_state.last_filters = current_filters
            status_placeholder.warning('⚠️ Nenhum dado encontrado para os filtros selecionados.')
        else:
            st.session_state.df_cached = df_filtrado
            st.session_state.last_filters = current_filters
            status_placeholder.success(f'✅ {len(df_filtrado):,} registros carregados!')
            import time
            time.sleep(0.5)
            status_placeholder.empty()
        
    except Exception as e:
        status_placeholder.error(f'❌ Erro ao carregar dados: {str(e)}')
        st.error("Por favor, tente novamente ou simplifique os filtros.")
        st.session_state.df_cached = pd.DataFrame()
        st.stop()
else:
    df_filtrado = st.session_state.df_cached

# Carregar dados para gráfico de região APENAS se necessário e com cache separado
# (quando há filtro de UF e precisa mostrar panorama regional completo)
need_region_data = ufs_selecionadas and len(ufs_selecionadas) > 0

if need_region_data:
    # Criar filtros para região (sem UF)
    regiao_filters = (
        tuple(sorted(regioes_selecionadas)) if regioes_selecionadas else (),
        tuple(sorted(tamanhos_selecionados)) if tamanhos_selecionados else (),
        tuple(sorted(status_selecionados)) if status_selecionados else ()
    )
    
    # Verificar se precisa recarregar df_regiao
    if regiao_filters != st.session_state.last_regiao_filters or st.session_state.df_regiao_cached is None:
        status_regional = st.empty()
        try:
            status_regional.info('🔄 Carregando panorama regional...')
            df_regiao = load_filtered_data(
                regioes=regioes_selecionadas if regioes_selecionadas else None,
                ufs=None,  # Sem filtro de UF para panorama completo
                tamanhos=tamanhos_selecionados if tamanhos_selecionados else None,
                status=status_selecionados if status_selecionados else None
            )
            # Garantir que df_regiao não é None
            if df_regiao is None or (isinstance(df_regiao, pd.DataFrame) and df_regiao.empty):
                df_regiao = df_filtrado  # Usar dados filtrados como fallback
            st.session_state.df_regiao_cached = df_regiao
            st.session_state.last_regiao_filters = regiao_filters
            status_regional.empty()
        except Exception as e:
            status_regional.error(f'❌ Erro ao carregar panorama regional: {str(e)}')
            df_regiao = df_filtrado  # Fallback
    else:
        df_regiao = st.session_state.df_regiao_cached
else:
    df_regiao = df_filtrado  # Usar mesmos dados se não há filtro de UF

# Exibir resumo
total_registros = get_total_records()
display_filter_summary(len(df_filtrado), total_registros)

# ═══════════════════════════════════════════════════════════
# MÉTRICAS RÁPIDAS (SQL AGREGADO - SUPER RÁPIDO)
# ═══════════════════════════════════════════════════════════

with st.container():
    # Layout responsivo para métricas
    num_cols = get_layout_columns(mobile_cols=2, desktop_cols=4)
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcular métricas direto no DuckDB (muito mais rápido que Pandas)
    stats = get_aggregated_stats(
        regioes=regioes_selecionadas if regioes_selecionadas else None,
        ufs=ufs_selecionadas if ufs_selecionadas else None,
        tamanhos=tamanhos_selecionados if tamanhos_selecionados else None,
        status=status_selecionados if status_selecionados else None
    )
    
    st.markdown("""
        <style>
        .metric-container {
            text-align: center;
            background: transparent;
            border: none;
            box-shadow: none;
        }
        .metric-label {
            font-size: 14px;
            color: #31333F;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: 600;
            color: #31333F;
        }
        div[data-testid="column"] {
            background: transparent;
            border: none;
            box-shadow: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with col1:
        st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Total de Registros</div>
                <div class='metric-value'>{stats['total_records']:,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Similaridade Média</div>
                <div class='metric-value'>{stats['avg_jaccard']:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Similaridade Mediana</div>
                <div class='metric-value'>{stats['median_jaccard']:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>UFs Representadas</div>
                <div class='metric-value'>{stats['num_ufs']}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# MAPA DO BRASIL - SIMILARIDADE POR UF
# ═══════════════════════════════════════════════════════════

with st.expander("Mapa de Similaridade por Estado", expanded=True):
    if not validate_data(df_filtrado, "Mapa de Similaridade", min_records=1):
        pass
    else:
        try:
            # Dois mapas lado a lado
            col1, col2 = st.columns(2)
            
            with col1:
                fig_mapa = create_brazil_choropleth_map(df_filtrado)
                st.plotly_chart(fig_mapa, use_container_width=True)
            
            with col2:
                fig_titularidade = create_brazil_titularidade_map(df_filtrado)
                st.plotly_chart(fig_titularidade, use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Erro ao criar mapa: {str(e)}")
            st.info("💡 Verifique se há dados suficientes para todos os estados.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# 1. PANORAMA REGIONAL E OPERACIONAL
# ═══════════════════════════════════════════════════════════

with st.expander("Panorama Regional e Operacional", expanded=True):
    if not validate_data(df_filtrado, "Panorama Regional", min_records=1):
        pass  # Mensagem já exibida pela função
    else:
        st.markdown("<h3 style='text-align: center;'>Similaridade e Titularidade por UF</h3>", unsafe_allow_html=True)

        # Verificar se há mais de 1 UF selecionada e se a coluna existe
        if 'estado' not in df_filtrado.columns:
            st.error("❌ Erro: Coluna 'estado' não encontrada nos dados.")
        else:
            num_ufs = df_filtrado['estado'].nunique()

            # Só mostrar gráficos de UF se houver mais de 1 UF
            if num_ufs > 1:
                # Verificar se deve mostrar gráfico regional (só quando não há filtro de UF)
                mostrar_grafico_regional = len(ufs_selecionadas) == 0
                
                if mostrar_grafico_regional:
                    # Com gráfico regional: usar 2 colunas
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Altura fixa para evitar flickering
                        zt.bar_plot(df_filtrado, 'estado', percentage=True, figsize=CHART_HEIGHTS['bars_compact'])
                        # Tamanho da fonte responsivo baseado no número de UFs
                        ax = plt.gca()
                        num_ufs_grafico = df_filtrado['estado'].nunique()
                        # Quando poucas UFs: fonte maior (10-12), quando muitas: fonte menor (6-7)
                        if num_ufs_grafico <= 5:
                            fontsize = 10
                        elif num_ufs_grafico <= 10:
                            fontsize = 8
                        elif num_ufs_grafico <= 20:
                            fontsize = 6
                        else:
                            fontsize = 5
                        for text in ax.texts:
                            text.set_fontsize(fontsize)
                            text.set_weight('bold')
                        render_matplotlib(use_container_width=True)
                
                    with col2:
                        # Gráfico por região (TODAS as UFs, sem filtro)
                        if len(df_regiao) > 0:
                            zt.stacked_bar_plot(
                                df_regiao, y="regiao", hue="faixa_jaccard",
                                order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
                                legend_title="Percentual de Similaridade CAR-SIGEF",
                                show_pct_symbol=True, figsize=CHART_HEIGHTS['bars_compact'], legend_cols=5
                            )
                            render_matplotlib(use_container_width=True)
                        else:
                            st.info("Sem dados para panorama regional.")
                else:
                    # Sem gráfico regional: gráfico de barras ocupa largura total
                    zt.bar_plot(df_filtrado, 'estado', percentage=True, figsize=CHART_HEIGHTS['bars_compact'])
                    # Tamanho da fonte responsivo baseado no número de UFs
                    ax = plt.gca()
                    num_ufs_grafico = df_filtrado['estado'].nunique()
                    if num_ufs_grafico <= 5:
                        fontsize = 10
                    elif num_ufs_grafico <= 10:
                        fontsize = 8
                    elif num_ufs_grafico <= 20:
                        fontsize = 6
                    else:
                        fontsize = 5
                    for text in ax.texts:
                        text.set_fontsize(fontsize)
                        text.set_weight('bold')
                    render_matplotlib()
            # Se apenas 1 UF: não mostrar gráfico de barras por UF

        st.markdown("---")

        # Ajustar altura dinamicamente baseado no número de UFs
        num_ufs_total = df_filtrado['estado'].nunique()
        height_estado = max(2, min(7, num_ufs_total * 0.25))
        zt.stacked_bar_plot(
            df_filtrado, y="estado", hue="faixa_jaccard",
            order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
            legend_title="Percentual de Similaridade CAR-SIGEF",
            show_pct_symbol=True, figsize=CHART_HEIGHTS['bars_normal'], legend_cols=5
        )
        render_matplotlib()

        st.markdown("---")

        st.markdown("<h3 style='text-align: center;'>Titularidade por UF</h3>", unsafe_allow_html=True)
        # Altura fixa para titularidade
        zt.stacked_bar_plot(
            df_filtrado, y="estado", hue="label_cpf",
            order_hue=["Diferente", "Igual"], palette=CORES_TITULARIDADE,
            legend_title="Titularidade (CPF/CNPJ)",
            show_pct_symbol=True, figsize=CHART_HEIGHTS['bars_compact']
        )
        render_matplotlib()

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<h3 style='text-align: center;'>Titularidade vs Similaridade</h3>", unsafe_allow_html=True)
            zt.stacked_bar_plot(
                df_filtrado, y='faixa_jaccard', hue='label_cpf',
                order_hue=["Diferente", "Igual"], palette=CORES_TITULARIDADE,
                legend_title="Titularidade (CPF/CNPJ)", show_pct_symbol=True, figsize=CHART_HEIGHTS['density']
            )
            render_matplotlib(use_container_width=True)

        with col2:
            st.markdown("<h3 style='text-align: center;'>Classe de Tamanho vs Similaridade</h3>", unsafe_allow_html=True)
            zt.stacked_bar_plot(
                df_filtrado, y="class_tam_imovel", hue="faixa_jaccard",
                order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
                legend_title="Percentual de Similaridade CAR-SIGEF",
                show_pct_symbol=True, figsize=CHART_HEIGHTS['density'], legend_cols=5
            )
            render_matplotlib(use_container_width=True)

        st.markdown("---")

        st.markdown("<h3 style='text-align: center;'>Análise de Densidade</h3>", unsafe_allow_html=True)

        # Verificar se há dados suficientes
        if validate_data(df_filtrado, "Análise de Densidade KDE", min_records=CONFIG['MIN_RECORDS_FOR_DENSITY']):
            # KDE plots lado a lado usando DuckDB para filtros otimizados
            col1, col2 = st.columns(2)
        
            with col1:
                st.markdown("<h4 style='text-align: center;'>Densidade por Tamanho</h4>", unsafe_allow_html=True)
                try:
                    # Query DuckDB otimizada
                    query_tam = """
                    SELECT 
                        indice_jaccard * 100 as indice_jaccard_pct,
                        class_tam_imovel
                    FROM df_filtrado
                    WHERE indice_jaccard IS NOT NULL 
                      AND class_tam_imovel IS NOT NULL
                    """
                    df_plot = duckdb.query(query_tam).df()
                    tamanhos_disponiveis = df_plot['class_tam_imovel'].unique()
                    
                    if len(df_plot) >= 10 and len(tamanhos_disponiveis) > 0:
                        fig, ax = plt.subplots(figsize=(7, 4.5))
                        
                        sns.kdeplot(
                            data=df_plot, x="indice_jaccard_pct", hue="class_tam_imovel",
                            hue_order=[t for t in ["Pequeno", "Médio", "Grande"] if t in tamanhos_disponiveis],
                            fill=True, common_norm=False, alpha=0.2, linewidth=3,
                            palette={k: v for k, v in CORES_TAMANHO.items() if k in tamanhos_disponiveis},
                            clip=(0, 100), legend=False, ax=ax, warn_singular=False
                        )
                        
                        # Estilo minimalista - remover eixo Y
                        ax.set_yticks([])
                        ax.set_ylabel("")
                        ax.set_xlabel("Similaridade (%)", fontsize=11, color="grey")
                        sns.despine(left=True, ax=ax)
                        
                        # Labels diretos nas curvas (sem caixa de legenda)
                        y_max = ax.get_ylim()[1]
                        if "Pequeno" in tamanhos_disponiveis:
                            ax.text(2, y_max * 0.15, "Pequeno", color=CORES_TAMANHO["Pequeno"], 
                                   fontsize=14, fontweight='bold')
                        if "Médio" in tamanhos_disponiveis:
                            ax.text(90, y_max * 0.85, "Médio", color=CORES_TAMANHO["Médio"], 
                                   fontsize=14, fontweight='bold', ha='right')
                        if "Grande" in tamanhos_disponiveis:
                            ax.text(90, y_max * 0.70, "Grande", color=CORES_TAMANHO["Grande"], 
                                   fontsize=14, fontweight='bold', ha='right')
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("Dados de tamanho não disponíveis.")
                except Exception as e:
                    st.warning("⚠️ Erro ao gerar gráfico de densidade por tamanho.")
                    plt.close()
            
            with col2:
                st.markdown("<h4 style='text-align: center;'>Densidade por Status</h4>", unsafe_allow_html=True)
                try:
                    # Query DuckDB otimizada
                    query_status = """
                    SELECT 
                        indice_jaccard * 100 as indice_jaccard_pct,
                        status_imovel
                    FROM df_filtrado
                    WHERE indice_jaccard IS NOT NULL 
                      AND status_imovel IS NOT NULL
                    """
                    df_plot = duckdb.query(query_status).df()
                    status_disponiveis = df_plot['status_imovel'].unique()
                    
                    if len(df_plot) >= 10 and len(status_disponiveis) > 0:
                        fig, ax = plt.subplots(figsize=(7, 4.5))
                        
                        sns.kdeplot(
                            data=df_plot, x="indice_jaccard_pct", hue="status_imovel",
                            fill=True, common_norm=False, alpha=0.2, linewidth=3,
                            palette={k: v for k, v in CORES_STATUS.items() if k in status_disponiveis},
                            clip=(0, 100), legend=False, ax=ax, warn_singular=False
                        )
                        
                        # Estilo minimalista - remover eixo Y
                        ax.set_yticks([])
                        ax.set_ylabel("")
                        ax.set_xlabel("Similaridade (%)", fontsize=11, color="grey")
                        sns.despine(left=True, ax=ax)
                        
                        # Labels diretos nas curvas (sem caixa de legenda)
                        y_max = ax.get_ylim()[1]
                        y_positions = {'SU': 0.15, 'PE': 0.85, 'AT': 0.70}
                        x_positions = {'SU': 2, 'PE': 90, 'AT': 90}
                        ha_align = {'SU': 'left', 'PE': 'right', 'AT': 'right'}
                        
                        for status_code in status_disponiveis:
                            if status_code in CORES_STATUS:
                                ax.text(
                                    x=x_positions.get(status_code, 50),
                                    y=y_max * y_positions.get(status_code, 0.5),
                                    s=LABELS_STATUS.get(status_code, status_code),
                                    color=CORES_STATUS[status_code],
                                    fontsize=14, fontweight='bold',
                                    ha=ha_align.get(status_code, 'center')
                                )
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("Dados de status não disponíveis.")
                except Exception as e:
                    st.warning("⚠️ Erro ao gerar gráfico de densidade por status.")
                    plt.close()

        st.markdown("---")

        st.markdown("<h3 style='text-align: center;'>Status vs Similaridade</h3>", unsafe_allow_html=True)
        zt.stacked_bar_plot(
            df_filtrado, y="status_imovel", hue="faixa_jaccard",
            order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
            legend_title="Percentual de Similaridade CAR-SIGEF",
            show_pct_symbol=True, figsize=(12, 3), legend_cols=5
        )
        st.pyplot(plt.gcf())
        plt.close()

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# 2. EVOLUÇÃO TEMPORAL
# ═══════════════════════════════════════════════════════════

with st.expander("Evolução Temporal", expanded=True):
    if not validate_data(df_filtrado, "Evolução Temporal", min_records=CONFIG['MIN_RECORDS_FOR_ANALYSIS']):
        pass  # Mensagem já exibida pela função
    else:
        # Usar agregação SQL para economizar memória
        if 'ano_cadastro' in df_filtrado.columns:
            # Dados já agregados - apenas filtrar
            df_ano_total = df_filtrado.groupby('ano_cadastro').size().reset_index(name='total')
            df_ano_sim = df_filtrado.groupby('ano_cadastro')['indice_jaccard'].median().reset_index()
            df_ano_sim['indice_jaccard'] = df_ano_sim['indice_jaccard'] * 100
            df_ano_total.columns = ['ano', 'total']
            df_ano_sim.columns = ['ano', 'indice_jaccard']
            
            if len(df_ano_total) > 0:
                st.markdown("<h3 style='text-align: center;'>Volume de CARs e Similaridade Mediana por Ano</h3>", unsafe_allow_html=True)
                
                # Validar dados antes de plotar
                if len(df_ano_total) > 1 and df_ano_total['total'].max() > 0:
                    fig, ax1 = plt.subplots(figsize=(12, 6))
                    x_pos = np.arange(len(df_ano_total))
                    
                    # Barras (volume)
                    bars = ax1.bar(x_pos, df_ano_total['total'], color='#e0e0e0', alpha=0.6, width=0.6)
                    for bar, val in zip(bars, df_ano_total['total']):
                        height = bar.get_height()
                        label = f"{val/1000:.0f}K" if val >= 1000 else str(val)
                        ax1.text(bar.get_x() + bar.get_width()/2, height, label,
                                ha='center', va='bottom', fontsize=8, color='#888888')
                    
                    ax1.set_ylabel('Total de CARs', fontsize=10, color='#888888')
                    ax1.tick_params(axis='y', labelcolor='#888888', labelsize=9)
                    ax1.set_ylim(0, df_ano_total['total'].max() * 1.15)
                    
                    # Linha (similaridade)
                    ax2 = ax1.twinx()
                    ax2.plot(x_pos, df_ano_sim['indice_jaccard'], color='#2563eb', linewidth=3,
                            marker='o', markersize=8, markeredgecolor='white', markeredgewidth=2, zorder=3)
                    
                    for x, y in zip(x_pos, df_ano_sim['indice_jaccard']):
                        ax2.text(x, y, f"{y:.0f}%", ha='center', va='bottom',
                                fontsize=9, fontweight='bold', color='#2563eb')
                    
                    ax2.set_ylabel('Similaridade Mediana (%)', fontsize=10, color='#2563eb')
                    ax2.tick_params(axis='y', labelcolor='#2563eb', labelsize=9)
                    
                    ax1.set_xticks(x_pos)
                    ax1.set_xticklabels(df_ano_total['ano'].astype(int), fontsize=10)
                    ax1.set_xlabel('')
                    ax1.spines['top'].set_visible(False)
                    ax2.spines['top'].set_visible(False)
                    ax1.grid(axis='x', linestyle='--', alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("ℹ️ Dados insuficientes para gráfico temporal (necessário pelo menos 2 anos com dados).")
        else:
            st.warning("⚠️ Coluna de data não disponível para análise temporal.")
        
        # Análise por tamanho e região - simplificada
        st.markdown("---")
        
        if 'ano_cadastro' in df_filtrado.columns and 'class_tam_imovel' in df_filtrado.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<h3 style='text-align: center;'>Evolução por Tamanho</h3>", unsafe_allow_html=True)
                try:
                    # Agregar por ano e tamanho
                    df_tam_ano = df_filtrado.groupby(['ano_cadastro', 'class_tam_imovel'])['indice_jaccard'].median().reset_index()
                    df_tam_ano['indice_jaccard'] = df_tam_ano['indice_jaccard'] * 100
                    
                    fig, ax = plt.subplots(figsize=(7, 4.5))
                    for tamanho in ["Pequeno", "Médio", "Grande"]:
                        df_t = df_tam_ano[df_tam_ano['class_tam_imovel'] == tamanho]
                        if len(df_t) > 1:
                            ax.plot(df_t['ano_cadastro'].astype(int), df_t['indice_jaccard'],
                                   color=CORES_EVOLUCAO_TAMANHO.get(tamanho, '#333'),
                                   linewidth=2.5, label=tamanho, marker='o', markersize=6)
                    
                    ax.set_xlabel('Ano', fontsize=10, color='grey')
                    ax.set_ylabel('Similaridade Mediana (%)', fontsize=10)
                    ax.legend(loc='best', frameon=False, fontsize=9)
                    ax.grid(axis='both', linestyle='--', alpha=0.3)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                except Exception as e:
                    st.warning(f"⚠️ Dados insuficientes para análise por tamanho")
            
            with col2:
                st.markdown("<h3 style='text-align: center;'>Evolução por Região</h3>", unsafe_allow_html=True)
                try:
                    # Agregar por ano e região
                    df_reg_ano = df_filtrado.groupby(['ano_cadastro', 'regiao'])['indice_jaccard'].median().reset_index()
                    df_reg_ano['indice_jaccard'] = df_reg_ano['indice_jaccard'] * 100
                    
                    fig, ax = plt.subplots(figsize=(7, 4.5))
                    for regiao in df_reg_ano['regiao'].unique():
                        df_r = df_reg_ano[df_reg_ano['regiao'] == regiao]
                        if len(df_r) > 1:
                            ax.plot(df_r['ano_cadastro'].astype(int), df_r['indice_jaccard'],
                                   color=CORES_EVOLUCAO_REGIAO.get(regiao, '#333'),
                                   linewidth=2.5, label=regiao.title(), marker='o', markersize=6)
                    
                    ax.set_xlabel('Ano', fontsize=10, color='grey')
                    ax.set_ylabel('Similaridade Mediana (%)', fontsize=10)
                    ax.legend(loc='best', frameon=False, fontsize=9)
                    ax.grid(axis='both', linestyle='--', alpha=0.3)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                except Exception as e:
                    st.warning(f"⚠️ Dados insuficientes para análise por região")
        else:
            st.info("Dados de ano de cadastro não disponíveis para análise temporal.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# 3. DIAGNÓSTICO DE SIMILARIDADE ESPACIAL
# ═══════════════════════════════════════════════════════════

with st.expander("Diagnóstico de Similaridade Espacial", expanded=True):
    if len(df_filtrado) == 0:
        st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados. Ajuste os filtros para visualizar os dados.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<h3 style='text-align: center;'>Histograma</h3>", unsafe_allow_html=True)
            df_hist = df_filtrado.copy()
            df_hist['indice_jaccard_pct'] = df_hist['indice_jaccard'] * 100
            zt.hist_plot(df_hist, 'indice_jaccard_pct', xlabel='% de Similaridade', title='', figsize=(7, 4.5))
            st.pyplot(plt.gcf())
            plt.close()

        with col2:
            st.markdown("<h3 style='text-align: center;'>Distribuição por Faixa</h3>", unsafe_allow_html=True)
            
            # Calcular contagens mantendo a ordem das faixas (menor para maior)
            faixa_counts = df_filtrado['faixa_jaccard'].value_counts()
            
            # Reindexar para garantir a ordem correta
            faixa_counts = faixa_counts.reindex(JACCARD_LABELS, fill_value=0)
            
            # Criar gráfico donut manualmente com ordem controlada
            fig, ax = plt.subplots(figsize=(7, 4.5))
            
            # Cores por faixa
            colors = [CORES_FAIXA_JACCARD.get(faixa, '#999') for faixa in JACCARD_LABELS]
            
            # Criar gráfico de pizza/donut
            wedges, texts, autotexts = ax.pie(
                faixa_counts.values,
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                pctdistance=0.75,
                wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
            )
            
            # Estilizar os percentuais para centralizar melhor
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
                autotext.set_weight('bold')
                autotext.set_horizontalalignment('center')
                autotext.set_verticalalignment('center')
            
            # Adicionar texto central com total
            total = faixa_counts.sum()
            ax.text(0, 0, f'{format_number(total)}\nTotal', 
                   ha='center', va='center', fontsize=16, fontweight='bold')
            
            # Criar legenda personalizada com ordem correta
            legend_labels = [
                f"{faixa} ({format_number(faixa_counts[faixa])} - {faixa_counts[faixa]/total*100:.1f}%)"
                for faixa in JACCARD_LABELS
            ]
            ax.legend(wedges, legend_labels, title="Faixa de Similaridade",
                     loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                     frameon=False, fontsize=9)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        st.markdown("---")

        st.markdown("<h3 style='text-align: center;'>Análise de Áreas</h3>", unsafe_allow_html=True)
        
        # Verificar se coluna descrepancia existe
        if 'descrepancia' not in df_filtrado.columns:
            st.info("ℹ️ Dados de discrepância de área não disponíveis.")
        else:
            try:
                # Usar DuckDB para filtrar dados eficientemente
                query_area = f"""
                SELECT descrepancia
                FROM df_filtrado
                WHERE descrepancia IS NOT NULL
                  AND descrepancia >= {DISCREPANCIA_MIN}
                  AND descrepancia <= {DISCREPANCIA_MAX}
                """
                filtro_visual = duckdb.query(query_area).df()

                if len(filtro_visual) > 10:
                    fig, ax = plt.subplots(figsize=(14, 5))
                    sns.kdeplot(data=filtro_visual, x='descrepancia', fill=True,
                                color="#34495e", alpha=0.1, linewidth=2, ax=ax)
                    
                    ymax = ax.get_ylim()[1]
                    ax.axvspan(-10, 10, color='#2ecc71', alpha=0.15, label='Zona de Precisão')
                    ax.text(0, ymax * 0.90, 'ALTA PRECISÃO\n(Conformidade)', ha='center',
                            color='#27ae60', fontweight='bold')
                    ax.axvline(0, color='#27ae60', linestyle='--', linewidth=2)
                    
                    ax.text(35, ymax * 0.4, 'CAR > SIGEF\n(Superestimado)', ha='center',
                            color='#e74c3c', fontweight='bold')
                    ax.annotate('', xy=(45, ymax*0.35), xytext=(25, ymax*0.35),
                                arrowprops=dict(arrowstyle="->", color='#e74c3c', lw=1.5))
                    
                    ax.text(-35, ymax * 0.4, 'CAR < SIGEF\n(Subestimado)', ha='center',
                            color='#f39c12', fontweight='bold')
                    ax.annotate('', xy=(-45, ymax*0.35), xytext=(-25, ymax*0.35),
                                arrowprops=dict(arrowstyle="->", color='#f39c12', lw=1.5))
                    
                    sns.despine(left=True, ax=ax)
                    ax.set_yticks([])
                    ax.set_xlabel('Divergência de Área (%)', fontsize=12, labelpad=10)
                    ax.set_ylabel('')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.warning("⚠️ Dados insuficientes para análise de discrepância.")
            except Exception as e:
                st.error(f"❌ Erro ao gerar análise de áreas: {str(e)}")
                plt.close()

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# 5. MATRIZ DE CONFIABILIDADE (MOSAIC PLOT)
# ═══════════════════════════════════════════════════════════
# Visualização estratégica mostrando a relação entre similaridade
# espacial e titularidade através de um gráfico de mosaico.
# Identifica 4 quadrantes de risco/confiabilidade.
# ═══════════════════════════════════════════════════════════

with st.expander("Matriz de Confiabilidade: Espaço vs. Titularidade", expanded=True):
    if not validate_data(df_filtrado, "Matriz de Confiabilidade", min_records=CONFIG['MIN_RECORDS_FOR_ANALYSIS']):
        pass  # Mensagem já exibida pela função
    else:
        try:
            # Importar mosaic - disponível em statsmodels ou matplotlib 3.3+
            try:
                from statsmodels.graphics.mosaicplot import mosaic
            except ImportError:
                from matplotlib.pyplot import mosaic
        except ImportError:
            st.error("⚠️ Biblioteca necessária não encontrada. Instale: pip install statsmodels")
            st.stop()
        
        # Preparar dados para mosaic plot
        # Criar coluna label_geo baseada no indice_jaccard
        df_mosaic = df_filtrado[['label_cpf', 'indice_jaccard']].copy()
        df_mosaic['label_geo'] = df_mosaic['indice_jaccard'].apply(
            lambda x: '>= 85%' if x >= 0.85 else '< 85%'
        )
        
        data_mosaic = df_mosaic.groupby(['label_cpf', 'label_geo']).size()
        
        # Definir cores por categoria
        colors = {
            ('Igual', '>= 85%'):     '#2ecc71',  # Verde
            ('Igual', '< 85%'):      '#f39c12',  # Laranja
            ('Diferente', '>= 85%'): '#f1c40f',  # Amarelo
            ('Diferente', '< 85%'):  '#e74c3c'   # Vermelho
        }
        
        # Labels de ação para cada categoria
        action_labels = {
            ('Igual', '>= 85%'):     'MATURIDADE ALTA\n(Monitorar)',
            ('Igual', '< 85%'):      'ERRO TÉCNICO\n(Retificar)',
            ('Diferente', '>= 85%'): 'RISCO JURÍDICO\n(Auditar)',
            ('Diferente', '< 85%'):  'CRÍTICO/BAIXA PRIOR.\n(Reestruturar)'
        }
        
        def props(key):
            return {'color': colors.get(key, '#999999'), 'linewidth': 2}
        
        total = data_mosaic.sum()
        
        def labelizer(key):
            count = data_mosaic.get(key, 0)
            perc = (count / total) * 100
            
            # Formatação do número
            if count > 1000000:
                count_str = f'{count/1000000:.1f}M'
            elif count > 1000:
                count_str = f'{count/1000:.0f}K'
            else:
                count_str = f'{count:.0f}'
            
            # Busca a frase de ação
            acao = action_labels.get(key, '')
            
            return f"{acao}\n\n{count_str}\n({perc:.1f}%)"
        
        # Criar figura
        fig, ax = plt.subplots(figsize=(12, 10))
        
        mosaic(data_mosaic, gap=0.015, properties=props, labelizer=labelizer, 
               ax=ax, title='', horizontal=True)
        
        # Estilização dos labels internos
        for text in ax.texts:
            text.set_color('white')
            text.set_fontsize(10.5)
            text.set_fontweight('bold')
            text.set_horizontalalignment('center')
        
        # Ajustes de eixos
        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()
        ax.set_xlabel('Titularidade (CPF/CNPJ)', fontsize=13, fontweight='bold', 
                      labelpad=15, color='#333333')
        ax.set_ylabel('Similaridade Espacial', fontsize=13, fontweight='bold', 
                      labelpad=15, color='#333333')
        
        # Adicionar totais por coluna (CPF)
        totais_cpf = df_mosaic.groupby('label_cpf').size()
        col_order = ['Diferente', 'Igual']
        pos_x = 0
        
        for cpf_label in col_order:
            if cpf_label in totais_cpf:
                count = totais_cpf[cpf_label]
                largura = count / total
                centro_x = pos_x + largura / 2
                perc = (count / total) * 100
                count_str = f'{count/1000:.0f}K' if count > 1000 else f'{count:.0f}'
                
                ax.text(centro_x, -0.06, f'{count_str}\n({perc:.1f}%)', 
                        ha='center', va='top', fontsize=11, fontweight='bold', 
                        color='#555555', transform=ax.transAxes)
                pos_x += largura + 0.015
        
        # Adicionar totais por linha (Geo)
        totais_geo = df_mosaic.groupby('label_geo').size()
        row_order = ['< 85%', '>= 85%']
        pos_y = 0
        
        for geo_label in row_order:
            if geo_label in totais_geo:
                count = totais_geo[geo_label]
                altura = count / total
                centro_y = pos_y + altura / 2
                perc = (count / total) * 100
                count_str = f'{count/1000:.0f}K' if count > 1000 else f'{count:.0f}'
                
                ax.text(1.02, centro_y, f'{count_str}\n({perc:.1f}%)', 
                        ha='left', va='center', fontsize=11, fontweight='bold', 
                        color='#555555', transform=ax.transAxes)
                pos_y += altura + 0.015
        
        # Limpeza visual
        sns.despine(left=True, bottom=True, top=True, right=True)
        ax.tick_params(axis='both', which='both', length=0)
        
        plt.subplots_adjust(top=0.85, bottom=0.1, right=0.9, left=0.05)
        
        st.pyplot(fig)
        plt.close()

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# MATRIZ DE MATURIDADE FUNDIÁRIA
# ═══════════════════════════════════════════════════════════

with st.expander("Matriz de Maturidade Fundiária por UF", expanded=True):
    if not validate_data(df_filtrado, "Matriz de Maturidade", min_records=1):
        pass  # Mensagem já exibida pela função
    else:
        # Dados já vem tratados do DuckDB com cpf_ok como int (0 ou 1)
        uf_stats = df_filtrado.groupby('estado').agg(
            pct_espacial_bom=('indice_jaccard', lambda x: (x >= 0.85).mean() * 100),
            pct_cpf_igual=('cpf_ok', lambda x: x.mean() * 100),
            regiao=('regiao', 'first'),
            total_cars=('estado', 'count')
        ).reset_index()

        if len(uf_stats) >= 1:
            try:
                x_min, x_max, y_min, y_max = 25, 75, 25, 75
                x_div, y_div = 50, 50

                fig = plt.figure(figsize=(16, 8))
                ax = fig.add_axes([0.08, 0.1, 0.65, 0.8])

                # Criar fundo dos quadrantes
                create_quadrant_background(ax, x_min, x_max, y_min, y_max, x_div, y_div)
                add_quadrant_labels(ax, x_min, x_max, y_min, y_max)

                # Normalizar tamanhos das bolhas
                sizes = uf_stats['total_cars']
                size_min, size_max = 100, 800
                
                # Evitar divisão por zero quando há apenas 1 UF
                if sizes.min() == sizes.max():
                    sizes_normalized = pd.Series([size_min] * len(sizes), index=sizes.index)
                else:
                    sizes_normalized = ((sizes - sizes.min()) / (sizes.max() - sizes.min())) * (size_max - size_min) + size_min

                # Plotar bolhas por região
                regioes_presentes = []
                for regiao_key in uf_stats['regiao'].unique():
                    mask = uf_stats['regiao'] == regiao_key
                    masked_data = uf_stats.loc[mask]
                    
                    # Só plotar se houver dados
                    if len(masked_data) > 0 and regiao_key is not None:
                        ax.scatter(
                            masked_data['pct_espacial_bom'],
                            masked_data['pct_cpf_igual'],
                            s=sizes_normalized[mask],
                            c=CORES_MATURIDADE_REGIAO.get(regiao_key, '#999999'),
                            alpha=0.75, edgecolors='white', linewidths=2, zorder=3
                        )
                        regioes_presentes.append(regiao_key)

                # Adicionar labels das UFs
                for idx, row in uf_stats.iterrows():
                    x_offset = 1.5 if row['pct_espacial_bom'] <= (x_max - 10) else -1.5
                    ha = 'left' if row['pct_espacial_bom'] <= (x_max - 10) else 'right'
                    ax.annotate(row['estado'], (row['pct_espacial_bom'], row['pct_cpf_igual']),
                                   xytext=(x_offset, 1.5), textcoords='offset points',
                               fontsize=9, fontweight='bold', color='#333333', zorder=4)

                # Configurar eixos
                ax.set_xlim(x_min, x_max)
                ax.set_ylim(y_min, y_max)
                ax.set_xlabel('Similaridade Espacial (%)', fontsize=13, fontweight='bold', labelpad=15)
                ax.set_ylabel('Conformidade Titular (%)', fontsize=13, fontweight='bold', labelpad=15)
                ax.set_xticks(range(x_min, x_max + 1, 10))
                ax.set_yticks(range(y_min, y_max + 1, 10))
                ax.grid(True, linestyle='--', alpha=0.3, zorder=0)
                
                for spine in ['top', 'right']:
                    ax.spines[spine].set_visible(False)
                for spine in ['left', 'bottom']:
                    ax.spines[spine].set_color('#BDBDBD')

                # Legendas (usando patches apenas para regiões presentes)
                from matplotlib.patches import Patch
                region_handles = [
                    Patch(facecolor=CORES_MATURIDADE_REGIAO[regiao_key], edgecolor='white', linewidth=1.5, 
                          label=REGIOES_NOME_MAP.get(regiao_key, regiao_key.title()))
                    for regiao_key in regioes_presentes if regiao_key in CORES_MATURIDADE_REGIAO
                ]
                
                if region_handles:
                    fig.legend(handles=region_handles, title='Região', loc='upper left',
                              bbox_to_anchor=(0.75, 0.88), frameon=True, fontsize=10,
                              title_fontsize=11, framealpha=1, edgecolor='#CCCCCC')

                # Legenda de tamanho (apenas se houver variação)
                if len(uf_stats) > 1 and sizes.min() != sizes.max():
                    size_legend_values = [int(sizes.min()), int(sizes.quantile(0.5)), int(sizes.max())]
                    # Usar Line2D ao invés de scatter vazio
                    from matplotlib.lines import Line2D
                    size_handles = [
                        Line2D([0], [0], marker='o', color='w', 
                               markerfacecolor='gray', alpha=0.5, 
                               markersize=((v - sizes.min()) / (sizes.max() - sizes.min())) * 15 + 8,
                               markeredgecolor='white', markeredgewidth=1)
                        for v in size_legend_values
                    ]
                    fig.legend(handles=size_handles, labels=[format_number(v) for v in size_legend_values],
                              title='Nº CARs', loc='upper left', bbox_to_anchor=(0.75, 0.67),
                              frameon=True, fontsize=10, title_fontsize=11, labelspacing=1.8,
                              handletextpad=2.0, framealpha=1, edgecolor='#CCCCCC')

                st.pyplot(fig)
                plt.close()
            except Exception as e:
                st.error(f"⚠️ Erro ao gerar Matriz de Maturidade: {str(e)}")
                st.info("💡 Tente ajustar os filtros para obter dados mais abrangentes.")
                plt.close()
        else:
            st.warning("⚠️ Dados insuficientes. Selecione filtros mais abrangentes.")
st.markdown("---")

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════

if os.path.exists(LOGO_FOOTER_PATH):
    with open(LOGO_FOOTER_PATH, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <div style="text-align: center; padding: 10px 0 5px 0;">
            <p style="margin: 0 0 5px 0; color: #666; font-size: 12px;">Desenvolvido por</p>
            <a href="https://agenciazetta.ufla.br/" target="_blank">
                <img src="data:image/png;base64,{img_data}" 
                     style="width: 100px; background: transparent; cursor: pointer;" 
                     alt="Agência Zetta">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<p style='text-align: center; color: #666; font-size: 12px;'>Desenvolvido por Agência Zetta</p>",
        unsafe_allow_html=True
    )
