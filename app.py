"""
Dashboard de Análise de Similaridade CAR-SIGEF
Análise exploratória de dados de similaridade espacial entre registros CAR e SIGEF.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import zetta_utils as zt
import os
import base64
import matplotlib.patches as mpatches

# Imports locais
from src.config import (
    CSS_CUSTOM, CORES_FAIXA_JACCARD, CORES_TAMANHO, CORES_STATUS,
    CORES_EVOLUCAO_TAMANHO, CORES_EVOLUCAO_REGIAO, CORES_TITULARIDADE,
    CORES_MATURIDADE_REGIAO, JACCARD_LABELS, LABELS_STATUS,
    DISCREPANCIA_MIN, DISCREPANCIA_MAX, LOGO_FOOTER_PATH, ANO_MIN, ANO_MAX
)
from src.utils import (
    load_metadata, load_filtered_data, get_total_records, create_risk_matrix,
    format_number, create_quadrant_background, add_quadrant_labels,
    display_region_filter, display_uf_filter, display_size_filter,
    display_status_filter, display_filter_summary, get_aggregated_stats
)

# ═══════════════════════════════════════════════════════════
# CONSTANTES DE CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════

CONFIG = {
    'MIN_RECORDS_FOR_ANALYSIS': 10,
    'MIN_RECORDS_FOR_DENSITY': 10,
    'SHOW_DEBUG_INFO': False,
    'DEFAULT_FIGSIZE': (12, 6),
    'MOBILE_BREAKPOINT': 768,  # pixels
    'PROGRESS_SLEEP': 0.01,
    'SUCCESS_MESSAGE_DURATION': 0.3
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
    page_icon="�",
    layout="wide",
    initial_sidebar_state="collapsed"
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
        with st.spinner('🚀 Inicializando banco de dados... (apenas na primeira vez)'):
            from src.utils import load_metadata
            # Isso força a criação da tabela em memória
            metadata_test = load_metadata()
            if metadata_test is None or len(metadata_test) == 0:
                st.error("❌ Erro: Não foi possível carregar os metadados do banco de dados.")
                st.stop()
            st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        st.info("💡 Verifique se o arquivo de dados existe no caminho correto.")
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

metadata = load_metadata()

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

# Verificar se filtros mudaram (evitar recálculo desnecessário)
current_filters = (
    tuple(regioes_selecionadas) if regioes_selecionadas else None,
    tuple(ufs_selecionadas) if ufs_selecionadas else None,
    tuple(tamanhos_selecionados) if tamanhos_selecionados else None,
    tuple(status_selecionados) if status_selecionados else None
)

filters_changed = current_filters != st.session_state.last_filters

# Aplicar filtros (com cache inteligente)
if filters_changed or st.session_state.df_cached is None:
    status_placeholder = st.empty()
    progress_container = st.empty()
    
    try:
        # Progress bar animada
        with progress_container:
            progress_bar = st.progress(0, text='🔄 Carregando dados filtrados...')
            for i in range(100):
                progress_bar.progress(i + 1, text=f'🔄 Carregando dados... {i+1}%')
                import time
                time.sleep(CONFIG['PROGRESS_SLEEP'])
        
        df_filtrado = load_filtered_data(
            regioes=regioes_selecionadas if regioes_selecionadas else None,
            ufs=ufs_selecionadas if ufs_selecionadas else None,
            tamanhos=tamanhos_selecionados if tamanhos_selecionados else None,
            status=status_selecionados if status_selecionados else None
        )
        
        st.session_state.df_cached = df_filtrado
        st.session_state.last_filters = current_filters
        
        progress_container.empty()
        status_placeholder.success(f'✅ {len(df_filtrado):,} registros carregados!')
        time.sleep(CONFIG['SUCCESS_MESSAGE_DURATION'])
        status_placeholder.empty()
        
    except Exception as e:
        status_placeholder.error(f'❌ Erro: {str(e)}')
        st.stop()
else:
    df_filtrado = st.session_state.df_cached

# Carregar dados para gráfico de região APENAS se necessário e com cache separado
# (quando há filtro de UF e precisa mostrar panorama regional completo)
need_region_data = ufs_selecionadas and len(ufs_selecionadas) > 0

if need_region_data:
    # Criar filtros para região (sem UF)
    regiao_filters = (
        tuple(regioes_selecionadas) if regioes_selecionadas else None,
        tuple(tamanhos_selecionados) if tamanhos_selecionados else None,
        tuple(status_selecionados) if status_selecionados else None
    )
    
    # Verificar se precisa recarregar df_regiao
    if regiao_filters != st.session_state.last_regiao_filters or st.session_state.df_regiao_cached is None:
        status_regional = st.empty()
        try:
            status_regional.info('Carregando panorama regional...')
            df_regiao = load_filtered_data(
                regioes=regioes_selecionadas if regioes_selecionadas else None,
                ufs=None,  # Sem filtro de UF para panorama completo
                tamanhos=tamanhos_selecionados if tamanhos_selecionados else None,
                status=status_selecionados if status_selecionados else None
            )
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
    
    with col1:
        st.metric("Total de Registros", f"{stats['total_records']:,}")
    
    with col2:
        st.metric("Similaridade Média", f"{stats['avg_jaccard']:.1f}%")
    
    with col3:
        st.metric("Mediana Jaccard", f"{stats['median_jaccard']:.1f}%")
    
    with col4:
        st.metric("UFs Representadas", stats['num_ufs'])

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# 1. PANORAMA REGIONAL E OPERACIONAL
# ═══════════════════════════════════════════════════════════

with st.expander("Panorama Regional e Operacional", expanded=True):
    if not validate_data(df_filtrado, "Panorama Regional", min_records=1):
        pass  # Mensagem já exibida pela função
    else:
        st.markdown("<h3 style='text-align: center;'>Similaridade e Titularidade por UF</h3>", unsafe_allow_html=True)

        # Verificar se há mais de 1 UF selecionada
        num_ufs = df_filtrado['uf'].nunique()

        if num_ufs > 1:
            col1, col2 = st.columns(2)
            
            with col1:
                zt.bar_plot(df_filtrado, 'uf', percentage=True, figsize=(7, 5))
                st.pyplot(plt.gcf())
                plt.close()
            
            with col2:
                # Gráfico por região SEM filtro de UF (dados completos)
                if len(df_regiao) > 0:
                    zt.stacked_bar_plot(
                        df_regiao, y="regiao_analise", hue="faixa_jaccard",
                        order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
                        legend_title="Percentual de Similaridade CAR-SIGEF",
                        use_suffix=False, figsize=(7, 5)
                    )
                    st.pyplot(plt.gcf())
                    plt.close()
                else:
                    st.info("Sem dados para panorama regional.")
        else:
            # Quando apenas 1 UF selecionada, mostrar apenas o gráfico por região
            if len(df_regiao) > 0:
                zt.stacked_bar_plot(
                    df_regiao, y="regiao_analise", hue="faixa_jaccard",
                    order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
                    legend_title="Percentual de Similaridade CAR-SIGEF",
                    use_suffix=False, figsize=(12, 4)
                )
                st.pyplot(plt.gcf())
                plt.close()
            else:
                st.info("Sem dados para panorama regional.")

        st.markdown("---")

        zt.stacked_bar_plot(
            df_filtrado, y="uf", hue="faixa_jaccard",
            order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
            legend_title="Percentual de Similaridade CAR-SIGEF",
            use_suffix=False, figsize=(12, 6)
        )
        st.pyplot(plt.gcf())
        plt.close()

        st.markdown("---")

        st.markdown("<h3 style='text-align: center;'>Titularidade por UF</h3>", unsafe_allow_html=True)
        zt.stacked_bar_plot(
            df_filtrado, y="uf", hue="label_cpf",
            order_hue=["Diferente", "Igual"], palette=CORES_TITULARIDADE,
            legend_title="Titularidade (CPF/CNPJ)",
            use_suffix=False, figsize=(12, 6)
        )
        st.pyplot(plt.gcf())
        plt.close()

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<h3 style='text-align: center;'>Titularidade vs Similaridade</h3>", unsafe_allow_html=True)
            zt.stacked_bar_plot(
                df_filtrado, y='faixa_jaccard', hue='label_cpf',
                order_hue=["Diferente", "Igual"], palette=CORES_TITULARIDADE,
                legend_title="Titularidade (CPF/CNPJ)", figsize=(7, 5)
            )
            st.pyplot(plt.gcf())
            plt.close()

        with col2:
            st.markdown("<h3 style='text-align: center;'>Classe de Tamanho vs Similaridade</h3>", unsafe_allow_html=True)
            zt.stacked_bar_plot(
                df_filtrado, y="class_tam_imovel", hue="faixa_jaccard",
                order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
                legend_title="Percentual de Similaridade CAR-SIGEF",
                use_suffix=False, figsize=(7, 5)
            )
            st.pyplot(plt.gcf())
            plt.close()

        st.markdown("---")

        st.markdown("<h3 style='text-align: center;'>Análise de Densidade</h3>", unsafe_allow_html=True)

        # Verificar se há dados suficientes
        if validate_data(df_filtrado, "Análise de Densidade KDE", min_records=CONFIG['MIN_RECORDS_FOR_DENSITY']):
            # KDE plots lado a lado
            col1, col2 = st.columns(2)
        
            with col1:
                st.markdown("<h4 style='text-align: center;'>Densidade por Tamanho</h4>", unsafe_allow_html=True)
                try:
                    fig, ax = plt.subplots(figsize=(7, 4))
                    
                    # Verificar quais tamanhos existem nos dados
                    tamanhos_disponiveis = df_filtrado['class_tam_imovel'].dropna().unique()
                    
                    if len(tamanhos_disponiveis) > 0:
                        sns.kdeplot(
                            data=df_filtrado, x="indice_jaccard", hue="class_tam_imovel",
                            hue_order=["Pequeno", "Médio", "Grande"],
                            fill=True, common_norm=False, alpha=0.2, linewidth=2,
                            palette=list(CORES_TAMANHO.values()),
                            clip=(0, 100), legend=False, ax=ax
                        )
                        ax.set_yticks([])
                        ax.set_ylabel("")
                        ax.set_xlabel("Percentual de Similaridade", fontsize=9, color="grey")
                        sns.despine(left=True, ax=ax)
                        
                        # Adicionar labels apenas para tamanhos presentes nos dados
                        y_max = ax.get_ylim()[1]
                        if "Pequeno" in tamanhos_disponiveis:
                            ax.text(5, y_max * 0.15, "Pequeno", color=CORES_TAMANHO["Pequeno"], 
                                   fontsize=10, fontweight='bold')
                        if "Médio" in tamanhos_disponiveis:
                            ax.text(85, y_max * 0.85, "Médio", color=CORES_TAMANHO["Médio"], 
                                   fontsize=10, fontweight='bold', ha='right')
                        if "Grande" in tamanhos_disponiveis:
                            ax.text(85, y_max * 0.70, "Grande", color=CORES_TAMANHO["Grande"], 
                                   fontsize=10, fontweight='bold', ha='right')
                        
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
                    fig, ax = plt.subplots(figsize=(7, 4))
                    status_disponiveis = df_filtrado['status_imovel'].dropna().unique()
                    
                    if len(status_disponiveis) > 0:
                        sns.kdeplot(
                            data=df_filtrado, x="indice_jaccard", hue="status_imovel",
                            fill=True, common_norm=False, alpha=0.2, linewidth=2,
                            palette=CORES_STATUS, clip=(0, 100), legend=False, ax=ax
                        )
                        ax.set_yticks([])
                        ax.set_ylabel("")
                        ax.set_xlabel("Percentual de Similaridade", fontsize=9, color="grey")
                        sns.despine(left=True, ax=ax)
                        
                        # Adicionar labels dinamicamente com base nos dados
                        y_max = ax.get_ylim()[1]
                        y_positions = {'SU': 0.15, 'PE': 0.85, 'AT': 0.70}
                        x_positions = {'SU': 5, 'PE': 85, 'AT': 85}
                        ha_align = {'SU': 'left', 'PE': 'right', 'AT': 'right'}
                        
                        for status_code in status_disponiveis:
                            if status_code in CORES_STATUS:
                                ax.text(
                                    x=x_positions.get(status_code, 50),
                                    y=y_max * y_positions.get(status_code, 0.5),
                                    s=LABELS_STATUS.get(status_code, status_code),
                                    color=CORES_STATUS[status_code],
                                    fontsize=10, fontweight='bold',
                                    ha=ha_align.get(status_code, 'center')
                                )
                        
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
            use_suffix=False, figsize=(12, 3)
        )
        st.pyplot(plt.gcf())
        plt.close()

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# 2. EVOLUÇÃO TEMPORAL
# ═══════════════════════════════════════════════════════════

with st.expander("Evolução da Similaridade", expanded=True):
    if len(df_filtrado) == 0:
        st.warning("⚠️ Nenhum registro encontrado com os filtros selecionados. Ajuste os filtros para visualizar os dados.")
    elif 'ano_cadastro' in df_filtrado.columns and df_filtrado['ano_cadastro'].notna().any():
        df_tempo = df_filtrado[df_filtrado['ano_cadastro'].notna()].copy()
        df_tempo['ano'] = df_tempo['ano_cadastro'].astype(int)
        df_tempo = df_tempo[(df_tempo['ano'] >= ANO_MIN) & (df_tempo['ano'] <= ANO_MAX)]
        
        if len(df_tempo) > 0 and df_tempo['ano'].nunique() > 1:
            st.markdown("<h3 style='text-align: center;'>Volume de CARs e Similaridade Mediana por Ano</h3>", unsafe_allow_html=True)
            
            df_ano_total = df_tempo.groupby('ano').size().reset_index(name='total')
            df_ano_sim = df_tempo.groupby('ano')['indice_jaccard'].median().reset_index()
            
            if len(df_ano_total) > 1:
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
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h3 style='text-align: center;'>Evolução por Tamanho</h3>", unsafe_allow_html=True)
            if 'class_tam_imovel' in df_tempo.columns:
                fig, ax = plt.subplots(figsize=(7, 4.5))
                linhas_plotadas = False
                
                for tamanho in ["Pequeno", "Médio", "Grande"]:
                    df_tam = df_tempo[df_tempo['class_tam_imovel'] == tamanho]
                    if len(df_tam) > 0:
                        sim_por_ano = df_tam.groupby('ano')['indice_jaccard'].median().reset_index()
                        if len(sim_por_ano) > 1:
                            ax.plot(sim_por_ano['ano'].astype(int), sim_por_ano['indice_jaccard'],
                                   color=CORES_EVOLUCAO_TAMANHO.get(tamanho, '#333'),
                                   linewidth=2.5, label=tamanho, marker='o', markersize=6)
                            linhas_plotadas = True
                
                if linhas_plotadas:
                    ax.set_xlabel('Ano', fontsize=10, color='grey')
                    ax.set_ylabel('Similaridade Mediana (%)', fontsize=10)
                    ax.legend(loc='best', frameon=False, fontsize=9)
                    ax.grid(axis='both', linestyle='--', alpha=0.3)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("Dados insuficientes para análise temporal por tamanho")
        
        with col2:
            st.markdown("<h3 style='text-align: center;'>Evolução por Região</h3>", unsafe_allow_html=True)
            
            # Carregar dados SEM filtro de UF (apenas região, tamanho e status)
            df_tempo_regiao = load_filtered_data(
                regioes=regioes_selecionadas if regioes_selecionadas else None,
                ufs=None,  # Sem filtro de UF
                tamanhos=tamanhos_selecionados if tamanhos_selecionados else None,
                status=status_selecionados if status_selecionados else None
            )
            
            # Filtrar por ano
            if 'ano_cadastro' in df_tempo_regiao.columns:
                df_tempo_regiao = df_tempo_regiao[df_tempo_regiao['ano_cadastro'].notna()].copy()
                df_tempo_regiao['ano'] = df_tempo_regiao['ano_cadastro'].astype(int)
                df_tempo_regiao = df_tempo_regiao[(df_tempo_regiao['ano'] >= ANO_MIN) & (df_tempo_regiao['ano'] <= ANO_MAX)]
            
            if 'regiao_analise' in df_tempo_regiao.columns and len(df_tempo_regiao) > 0:
                fig, ax = plt.subplots(figsize=(7, 4.5))
                linhas_plotadas = False
                
                for regiao in ["Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"]:
                    df_reg = df_tempo_regiao[df_tempo_regiao['regiao_analise'] == regiao]
                    if len(df_reg) > 0:
                        sim_por_ano = df_reg.groupby('ano')['indice_jaccard'].median().reset_index()
                        if len(sim_por_ano) > 1:
                            ax.plot(sim_por_ano['ano'].astype(int), sim_por_ano['indice_jaccard'],
                                   color=CORES_EVOLUCAO_REGIAO.get(regiao, '#333'),
                                   linewidth=2.5, label=regiao, marker='o', markersize=6)
                            linhas_plotadas = True
                
                if linhas_plotadas:
                    ax.set_xlabel('Ano', fontsize=10, color='grey')
                    ax.set_ylabel('Similaridade Mediana (%)', fontsize=10)
                    ax.legend(loc='best', frameon=False, fontsize=9)
                    ax.grid(axis='both', linestyle='--', alpha=0.3)
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.info("Dados insuficientes para análise temporal por região")
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
            zt.hist_plot(df_filtrado, 'indice_jaccard', xlabel='% de Similaridade', title='', figsize=(7, 4.5))
            st.pyplot(plt.gcf())
            plt.close()

        with col2:
            st.markdown("<h3 style='text-align: center;'>Distribuição por Faixa</h3>", unsafe_allow_html=True)
            
            # Garantir ordem correta das faixas na legenda
            df_plot = df_filtrado.copy()
            df_plot['faixa_jaccard'] = pd.Categorical(
                df_plot['faixa_jaccard'], 
                categories=JACCARD_LABELS, 
                ordered=True
            )
            # Ordenar o DataFrame pela categoria ordenada
            df_plot = df_plot.sort_values('faixa_jaccard')
            
            zt.donut_plot(df_plot, 'faixa_jaccard', figsize=(7, 4.5),
                          legend_title='Faixa de Similaridade', decimal_places=1)
            st.pyplot(plt.gcf())
            plt.close()

        st.markdown("---")

        st.markdown("<h3 style='text-align: center;'>Análise de Áreas</h3>", unsafe_allow_html=True)
        filtro_visual = df_filtrado[
            (df_filtrado['descrepancia'] >= DISCREPANCIA_MIN) & 
            (df_filtrado['descrepancia'] <= DISCREPANCIA_MAX)
        ]

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

st.markdown("---")
# ═══════════════════════════════════════════════════════════
# 5. MATRIZ DE CONFIABILIDADE
# ═══════════════════════════════════════════════════════════

with st.expander("Matriz de Confiabilidade: Espaço vs. Titularidade", expanded=True):
    if not validate_data(df_filtrado, "Matriz de Confiabilidade", min_records=CONFIG['MIN_RECORDS_FOR_ANALYSIS']):
        pass  # Mensagem já exibida pela função
    else:
        fig = create_risk_matrix(df_filtrado)
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
        uf_stats = df_filtrado.groupby('uf').agg(
            pct_espacial_bom=('indice_jaccard', lambda x: (x >= 85).mean() * 100),
            pct_cpf_igual=('cpf_ok', lambda x: x.mean() * 100),
            regiao=('regiao_analise', 'first'),
            total_cars=('uf', 'count')
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
                for regiao in uf_stats['regiao'].unique():
                    mask = uf_stats['regiao'] == regiao
                    masked_data = uf_stats.loc[mask]
                    
                    # Só plotar se houver dados
                    if len(masked_data) > 0:
                        ax.scatter(
                            masked_data['pct_espacial_bom'],
                            masked_data['pct_cpf_igual'],
                            s=sizes_normalized[mask],
                            c=CORES_MATURIDADE_REGIAO.get(regiao, '#999999'),
                            alpha=0.75, edgecolors='white', linewidths=2, zorder=3
                        )

                # Adicionar labels das UFs
                for idx, row in uf_stats.iterrows():
                    x_offset = 1.5 if row['pct_espacial_bom'] <= (x_max - 10) else -1.5
                    ha = 'left' if row['pct_espacial_bom'] <= (x_max - 10) else 'right'
                    ax.annotate(row['uf'], (row['pct_espacial_bom'], row['pct_cpf_igual']),
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

                # Legendas (usando patches ao invés de scatter vazio)
                from matplotlib.patches import Patch
                region_handles = [
                    Patch(facecolor=cor, edgecolor='white', linewidth=1.5, label=regiao)
                    for regiao, cor in CORES_MATURIDADE_REGIAO.items()
                ]
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
