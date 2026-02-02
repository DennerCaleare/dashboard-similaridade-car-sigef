"""
Dashboard de Análise de Similaridade CAR-SIGEF

Este dashboard fornece análise exploratória de dados de similaridade espacial 
entre registros do Cadastro Ambiental Rural (CAR) e do Sistema de Gestão 
Fundiária (SIGEF).

Características principais:
- Análise de similaridade espacial usando Índice de Jaccard
- Cruzamento de titularidade (CPF/CNPJ)
- Visualizações interativas por região, UF, município, tamanho e status
- Performance otimizada com DuckDB
- Cache inteligente para filtros
- Suporte a filtro de município com identificação de duplicatas

Versão: Final UF/Região + Município
Desenvolvido para: Ministério da Gestão e Inovação (MGI)
Autor: Denner Caleare
Data: Janeiro 2026
Última atualização: 02/02/2026
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
import matplotlib.patheffects as path_effects
import seaborn as sns
import zetta_utils as zt
import plotly.express as px
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
    load_metadata, load_filtered_data, get_total_records, get_total_cars_by_year,
    reset_connection, format_number, create_quadrant_background, add_quadrant_labels,
    display_region_filter, display_uf_filter, display_size_filter,
    display_status_filter, display_filter_summary, get_aggregated_stats,
    get_regioes_from_ufs
)

# ═══════════════════════════════════════════════════════════
# CONSTANTES DE CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════

# Alturas fixas para gráficos (evita flickering)
CHART_HEIGHTS = {
    'metrics': (12, 3),
    'bars_normal': (12, 8),     # Aumentado de 6 para 8
    'bars_compact': (12, 8),    # Aumentado de 4.5 para 8
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
# FUNÇÕES CUSTOMIZADAS DE PLOTTING (DO NOTEBOOK)
# ═══════════════════════════════════════════════════════════

import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from typing import Literal

def _ajustar_posicoes_texto(posicoes, min_dist=3.0):
    """Função auxiliar para evitar sobreposição de texto no eixo Y."""
    ordenado = sorted(posicoes, key=lambda k: k['y'], reverse=True)
    if len(ordenado) < 2: return ordenado

    for i in range(1, len(ordenado)):
        anterior = ordenado[i-1]
        atual = ordenado[i]
        dist = anterior['y_ajustado'] - atual['y']
        
        if dist < min_dist:
            novo_y = anterior['y_ajustado'] - min_dist
            atual['y_ajustado'] = novo_y
        else:
            atual['y_ajustado'] = atual['y']
    return ordenado

def plot_evolucao_multi_swd(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str,
    agg: Literal['mean', 'median', 'sum'] = 'median',
    title: str = "",
    subtitle: str = "",
    highlights: list | None = None,
    gray_color: str = "#e0e0e0",
    label_mode: Literal['end', 'both'] = 'end',
    show_y_axis: bool = False,
    palette: dict | str = "viridis", 
    figsize: tuple = (12, 6),
    line_width: float = 2.5,
    y_format: Literal['number', 'percent'] = 'number',
    date_format: str | None = None,
    collision_spacing: float = 3.0,
    ax: plt.Axes | None = None,
) -> plt.Axes:
    
    dados = df.groupby([x, hue])[y].agg(agg).reset_index()
    grupos = dados[hue].unique()
    
    if isinstance(palette, dict):
        color_map = palette
    else:
        cmap = plt.get_cmap(palette)
        cols = cmap(np.linspace(0.2, 0.8, len(grupos)))
        color_map = {g: c for g, c in zip(grupos, cols)}

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    final_labels_data = []
    
    # PLOTAGEM
    for grupo in grupos:
        subset = dados[dados[hue] == grupo].sort_values(x)
        is_highlighted = (highlights is None) or (grupo in highlights)
        
        cor = color_map.get(grupo, "#333333") if is_highlighted else gray_color
        lw = (line_width + 1) if (highlights and is_highlighted) else (1.5 if highlights else line_width)
        alpha = 1.0 if is_highlighted else 0.7
        z_order = 5 if is_highlighted else 1
        font_weight = 'bold' if is_highlighted else 'normal'

        ax.plot(subset[x], subset[y], color=cor, linewidth=lw, alpha=alpha, zorder=z_order)
        
        start_x, start_y = subset[x].iloc[0], subset[y].iloc[0]
        end_x, end_y = subset[x].iloc[-1], subset[y].iloc[-1]
        
        def fmt(val): return f"{val:.0f}%" if y_format == 'percent' else f"{val:.1f}"

        if label_mode == 'both':
            ax.scatter(start_x, start_y, color=cor, s=40, zorder=z_order, edgecolors='white')
            ax.annotate(fmt(start_y), (start_x, start_y), xytext=(-8, 0), textcoords='offset points',
                        color=cor, fontsize=10, fontweight=font_weight, ha='right', va='center')

        s_size = 50 if is_highlighted else 20
        ax.scatter(end_x, end_y, color=cor, s=s_size, zorder=z_order, edgecolors='white')

        label_text = f" {grupo} {fmt(end_y)}" if is_highlighted else f" {grupo}"
        final_labels_data.append({
            'y': end_y, 'y_ajustado': end_y, 'x': end_x,
            'text': label_text, 'color': cor,
            'fontsize': 11 if is_highlighted else 9, 'weight': font_weight
        })

    # ANTI-COLISÃO
    final_labels_data = _ajustar_posicoes_texto(final_labels_data, min_dist=collision_spacing)
    for item in final_labels_data:
        ax.annotate(item['text'], xy=(item['x'], item['y_ajustado']), xytext=(8, 0), 
                    textcoords='offset points', color=item['color'], fontsize=item['fontsize'], 
                    fontweight=item['weight'], ha='left', va='center')

    # ESTILO E EIXOS
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')
    
    # Grid Vertical
    ax.xaxis.grid(True, linestyle='--', alpha=0.5, color='#b0b0b0')
    
    if show_y_axis:
        ax.spines['left'].set_visible(False)
        ax.tick_params(axis='y', colors='grey', labelsize=12, length=0) 
        ax.yaxis.grid(True, linestyle='-', alpha=0.4, color='#b0b0b0')
        
        if y_format == 'percent':
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:.0f}%"))
        elif y_format == 'currency':
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"R${x:,.0f}"))
    else:
        ax.spines['left'].set_visible(False)
        ax.set_yticks([])
        ax.set_ylabel('')

    if date_format:
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    ax.tick_params(axis='x', colors='grey', labelsize=12)    
    ax.set_xlabel('')

    # CONTROLE DE MARGEM
    if pd.api.types.is_datetime64_any_dtype(dados[x]):
        min_date, max_date = dados[x].min(), dados[x].max()
        margin = (max_date - min_date) * 0.15 
        ax.set_xlim(right=max_date + margin)

    if title:
        ax.text(x=0, y=1.12, s=title, transform=ax.transAxes, fontsize=16, fontweight='bold', color='#333333', ha='left')
    if subtitle:
        ax.text(x=0, y=1.06, s=subtitle, transform=ax.transAxes, fontsize=11, color='grey', ha='left')

    plt.tight_layout()
    return ax

def plot_evolucao_combo(
    df: pd.DataFrame,
    x: str,
    y: str,
    df_bars: pd.DataFrame | None = None,
    x_bars: str | None = None,
    y_bars: str | None = None,
    y_bars_total: str | None = None,
    agg: Literal['mean', 'median', 'sum'] = 'median',
    title: str = "",
    subtitle: str = "",
    color_line: str = "#2563eb",
    color_bars: str = "#2563eb",
    color_bars_total: str = "#e0e0e0",
    figsize: tuple = (12, 6),
    line_width: float = 3,
    bar_width: float = 0.6,
    bar_alpha: float = 0.7,
    bar_total_alpha: float = 0.3,
    show_trend: bool = False,
    label_mode: Literal['all', 'end', 'both', 'none'] = 'both',
    show_bar_labels: bool = True,
    show_bar_total_labels: bool = True,
    y_format: Literal['number', 'percent', 'currency'] = 'number',
    y2_format: Literal['number', 'percent', 'currency'] = 'number',
    show_legend: bool = True,
    legend_line_label: str = "Métrica",
    legend_bar_label: str = "Parcial",
    legend_bar_total_label: str = "Total",
    date_format: str | None = None,
    ax: plt.Axes | None = None,
    ylim_line: tuple | None = None,
    ylim_bars: tuple | None = None,
    yscale_line: Literal['linear', 'log', 'symlog'] = 'linear',
    yscale_bars: Literal['linear', 'log', 'symlog'] = 'linear',
) -> plt.Axes:
    
    def format_value(val, fmt):
        if fmt == 'percent':
            return f"{val:.0f}%"
        elif fmt == 'currency':
            if val >= 1_000_000:
                return f"R${val/1_000_000:.1f}M"
            elif val >= 1_000:
                return f"R${val/1_000:.0f}K"
            return f"R${val:.0f}"
        else:
            if val >= 1_000_000:
                return f"{val/1_000_000:.1f}M"
            elif val >= 1_000:
                return f"{val/1_000:.0f}K"
            return f"{val:.0f}"

    # PREPARAÇÃO DOS DADOS
    dados_linha = df.groupby(x)[y].agg(agg).reset_index().sort_values(x)
    x_vals = dados_linha[x]
    y_vals = dados_linha[y]

    if df_bars is not None:
        x_bars = x_bars or x
        dados_barras = df_bars.sort_values(x_bars)
        x_bars_vals = dados_barras[x_bars]
        y_bars_vals = dados_barras[y_bars]

        if y_bars_total is not None:
            y_bars_total_vals = dados_barras[y_bars_total]

    # CRIAR FIGURA
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    ax.set_yscale(yscale_line)

    # PLOTAR BARRAS
    ax2 = None
    if df_bars is not None:
        ax2 = ax.twinx()
        ax2.set_yscale(yscale_bars)

        x_positions = np.arange(len(x_bars_vals))

        if y_bars_total is not None:
            max_bar_val = np.nanmax(y_bars_total_vals.to_numpy())
        else:
            max_bar_val = np.nanmax(y_bars_vals.to_numpy())

        # BARRA DE FUNDO (TOTAL)
        if y_bars_total is not None:
            bars_total = ax2.bar(
                x_positions,
                y_bars_total_vals,
                width=bar_width,
                color=color_bars_total,
                alpha=bar_total_alpha,
                zorder=1,
                edgecolor='white',
                linewidth=0.5
            )

            if show_bar_total_labels:
                for bar, val in zip(bars_total, y_bars_total_vals):
                    height = bar.get_height()
                    label = format_value(val, y2_format)
                    text = ax2.annotate(
                        label,
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9, fontweight='bold', color='#666666',
                        zorder=3
                    )

        # BARRA DA FRENTE (PARCIAL)
        bars = ax2.bar(
            x_positions,
            y_bars_vals,
            width=bar_width,
            color=color_bars,
            alpha=bar_alpha,
            zorder=2,
            edgecolor='white',
            linewidth=0.5
        )

        if show_bar_labels:
            for bar, val in zip(bars, y_bars_vals):
                height = bar.get_height()
                label = format_value(val, y2_format)

                if y_bars_total is not None:
                    # Texto branco com contorno preto para melhor legibilidade
                    text = ax2.annotate(
                        label,
                        xy=(bar.get_x() + bar.get_width() / 2, height / 2),
                        ha='center', va='center',
                        fontsize=10, fontweight='bold', color='white',
                        zorder=10
                    )
                    # Adicionar contorno/sombra ao texto (mais sutil)
                    text.set_path_effects([
                        path_effects.Stroke(linewidth=2.5, foreground='black', alpha=0.4),
                        path_effects.Normal()
                    ])
                else:
                    ax2.annotate(
                        label,
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9, fontweight='bold', color='#333333'
                    )

        # Remover eixos Y (visual)
        ax2.set_yticks([])
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.tick_params(axis='y', left=False, right=False)

        if ylim_bars is not None:
            ax2.set_ylim(ylim_bars)
        else:
            ax2.set_ylim(0, max_bar_val * 1.3)

    # PLOTAR LINHA
    if df_bars is not None:
        x_plot = x_positions
    else:
        x_plot = x_vals

    if show_trend:
        x_numeric = np.arange(len(x_vals))
        z = np.polyfit(x_numeric, y_vals, 1)
        p = np.poly1d(z)
        ax.plot(x_plot, p(x_numeric), color='grey', linestyle='--', alpha=0.4, lw=1, zorder=3)

    ax.plot(x_plot, y_vals, color=color_line, linewidth=line_width, zorder=4)

    if ylim_line is not None:
        ax.set_ylim(ylim_line)

    def fmt_val(val):
        if y_format == 'percent':
            return f"{val:.0f}%"
        elif y_format == 'currency':
            return f"R${val:,.0f}"
        return f"{val:.1f}"

    if label_mode == 'all':
        ax.scatter(x_plot, y_vals, color=color_line, s=50, zorder=5, edgecolors='white', linewidths=2)
        for xv, yv in zip(x_plot, y_vals):
            ax.annotate(
                fmt_val(yv), (xv, yv),
                xytext=(0, 12), textcoords='offset points',
                color=color_line, fontsize=10, fontweight='bold', ha='center', va='bottom'
            )
    else:
        if label_mode in ['both', 'start']:
            start_x = x_plot.iloc[0] if hasattr(x_plot, 'iloc') else x_plot[0]
            ax.scatter(start_x, y_vals.iloc[0], color=color_line, s=60, zorder=5, edgecolors='white', linewidths=2)
            ax.annotate(
                fmt_val(y_vals.iloc[0]),
                (start_x, y_vals.iloc[0]),
                xytext=(-10, 0), textcoords='offset points',
                color=color_line, fontsize=11, fontweight='bold', ha='right', va='center'
            )

        if label_mode in ['both', 'end']:
            end_x = x_plot.iloc[-1] if hasattr(x_plot, 'iloc') else x_plot[-1]
            ax.scatter(end_x, y_vals.iloc[-1], color=color_line, s=60, zorder=5, edgecolors='white', linewidths=2)
            ax.annotate(
                fmt_val(y_vals.iloc[-1]),
                (end_x, y_vals.iloc[-1]),
                xytext=(10, 0), textcoords='offset points',
                color=color_line, fontsize=11, fontweight='bold', ha='left', va='center'
            )

    # ESTILO
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')

    ax.set_yticks([])
    ax.tick_params(axis='y', left=False, labelleft=False)

    if df_bars is not None:
        ax.set_xticks(x_positions)
        ax.set_xticklabels(x_bars_vals, fontsize=10)

    ax.tick_params(axis='x', colors='grey', labelsize=10)
    ax.set_xlabel('')

    ax.xaxis.grid(True, linestyle='--', alpha=0.3, color='#e0e0e0')

    if df_bars is not None:
        ax.set_xlim(-0.5, len(x_positions) - 0.5)

    # LEGENDA
    if show_legend and df_bars is not None:
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch

        legend_elements = [
            Line2D([0], [0], color=color_line, linewidth=line_width, label=legend_line_label),
            Patch(facecolor=color_bars, alpha=bar_alpha, edgecolor='white', label=legend_bar_label),
        ]

        if y_bars_total is not None:
            legend_elements.append(
                Patch(facecolor=color_bars_total, alpha=bar_total_alpha, edgecolor='white', label=legend_bar_total_label)
            )

        ax.legend(
            handles=legend_elements,
            loc='upper center',
            bbox_to_anchor=(0.5, -0.08),
            ncol=3 if y_bars_total else 2,
            frameon=False,
            fontsize=10,
            columnspacing=3,
            handletextpad=0.8
        )

    # TÍTULOS
    if title:
        ax.text(x=0, y=1.12, s=title, transform=ax.transAxes,
                fontsize=16, fontweight='bold', color='#333333', ha='left')
    if subtitle:
        ax.text(x=0, y=1.06, s=subtitle, transform=ax.transAxes,
                fontsize=11, color='grey', ha='left')

    plt.tight_layout()
    return ax

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
    
    # Calcular similaridade mediana por UF
    df_ufs = df.groupby('estado').agg({
        'indice_jaccard': 'median'
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
        margin=dict(l=0, r=0, t=30, b=50),
        height=450,
        coloraxis_colorbar=dict(
            title=dict(text="Similaridade (%)", font=dict(size=10, color='#1D1D1D')),
            tickfont=dict(size=9, color='#1D1D1D'),
            orientation='h',
            len=0.35,
            thickness=12,
            x=0.5,
            xanchor='center',
            y=-0.15,
            yanchor='top'
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
        margin=dict(l=0, r=0, t=30, b=50),
        height=450,
        coloraxis_colorbar=dict(
            title=dict(text="CPF Igual (%)", font=dict(size=10, color='#1D1D1D')),
            tickfont=dict(size=9, color='#1D1D1D'),
            orientation='h',
            len=0.35,
            thickness=12,
            x=0.5,
            xanchor='center',
            y=-0.15,
            yanchor='top'
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
    page_icon="assets/Logo.png",
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
            from src.utils import load_metadata, reset_connection
            # Reset da conexão para garantir que dados atualizados sejam carregados
            reset_connection()
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

st.markdown("""
    <h1 style='background: linear-gradient(90deg, #0d0d0d 0%, #1f5bb8 100%); 
               -webkit-background-clip: text; 
               -webkit-text-fill-color: transparent; 
               background-clip: text;'>
        Análise de Similaridade CAR-SIGEF
    </h1>
""", unsafe_allow_html=True)
st.markdown("""
    <h3 style='text-align: center;
               background: linear-gradient(90deg, #0d0d0d 0%, #1f5bb8 100%); 
               -webkit-background-clip: text; 
               -webkit-text-fill-color: transparent; 
               background-clip: text;'>
        Análise Exploratória dos Dados de Similaridade Espacial
    </h3>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FILTROS
# ═══════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("<h3 style='text-align: center;'>Filtros de Dados</h3>", unsafe_allow_html=True)

# Mostrar progresso de carregamento
with st.spinner('Carregando metadados...'):
    metadata = load_metadata()

# Inicializar session state
if 'regioes_auto_selecionadas' not in st.session_state:
    st.session_state.regioes_auto_selecionadas = []

# Usar form para evitar reruns a cada mudança de filtro
with st.form(key="filtros_form"):
    col1, col2, col3, col4, col5 = st.columns(5)

    with col2:
        ufs_originais = sorted([u for u in metadata['estados'] if u is not None]) if metadata['estados'] else []
        ufs_selecionadas = display_uf_filter(ufs_originais)

    with col1:
        regioes_originais = sorted([r for r in metadata['regioes'] if r is not None]) if metadata['regioes'] else []
        # Detectar regiões completas e usar como default
        regioes_detectadas = get_regioes_from_ufs(ufs_selecionadas) if ufs_selecionadas else []
        regioes_selecionadas = display_region_filter(regioes_originais, default=regioes_detectadas)

    with col3:
        municipios_disponiveis = sorted([m for m in metadata['municipios'] if m is not None]) if metadata.get('municipios') else []
        municipios_selecionados = display_municipio_filter(municipios_disponiveis)

    with col4:
        tamanhos_disponiveis = sorted([t for t in metadata['tamanhos'] if t is not None]) if metadata['tamanhos'] else []
        tamanhos_selecionados = display_size_filter(tamanhos_disponiveis)

    with col5:
        status_originais = sorted([s for s in metadata['status'] if s is not None]) if metadata['status'] else []
        status_selecionados = display_status_filter(status_originais)
    
    # Botão para aplicar filtros
    submit_button = st.form_submit_button("Aplicar Filtros", use_container_width=True)

# Verificar se filtros mudaram (evitar recálculo desnecessário)
current_filters = (
    tuple(sorted(regioes_selecionadas)) if regioes_selecionadas else (),
    tuple(sorted(ufs_selecionadas)) if ufs_selecionadas else (),
    tuple(sorted(municipios_selecionados)) if municipios_selecionados else (),
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
        valid_municipios = [m for m in (municipios_selecionados or []) if m]
        valid_tamanhos = [t for t in (tamanhos_selecionados or []) if t]
        valid_status = [s for s in (status_selecionados or []) if s]
        
        # OPÇÃO 1: Priorizar filtro de UF - se UFs selecionadas, ignorar região
        if valid_ufs:
            # Se UFs específicas foram selecionadas, ignorar filtro de região
            regioes_para_filtro = None
        else:
            # Se nenhuma UF selecionada, usar filtro de região normalmente
            regioes_para_filtro = valid_regioes if valid_regioes else None
        
        status_placeholder.info('🔄 Carregando dados filtrados...')
        
        df_filtrado = load_filtered_data(
            regioes=regioes_para_filtro,
            ufs=valid_ufs if valid_ufs else None,
            municipios=valid_municipios if valid_municipios else None,
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
            
            # Detectar regiões completas se houver filtro de UF
            regioes_completas = get_regioes_from_ufs(valid_ufs) if valid_ufs else []
            regioes_para_panorama = valid_regioes if valid_regioes else (regioes_completas if regioes_completas else None)
            
            df_regiao = load_filtered_data(
                regioes=regioes_para_panorama,
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
    num_cols = get_layout_columns(mobile_cols=2, desktop_cols=6)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
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
    
    with col5:
        area_milhoes = stats['total_area'] / 1_000_000
        st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Área Total (M ha)</div>
                <div class='metric-value'>{area_milhoes:.1f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-label'>Titularidade Igual</div>
                <div class='metric-value'>{stats['avg_cpf_ok']:.1f}%</div>
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
        # Determinar se estamos filtrando por município
        tem_filtro_municipio = municipios_selecionados and len(municipios_selecionados) > 0
        
        # Título dinâmico baseado no filtro
        if tem_filtro_municipio:
            titulo = "Similaridade e Titularidade por Município"
            coluna_geo = 'municipio_nome'
        else:
            titulo = "Similaridade e Titularidade por UF"
            coluna_geo = 'estado'
        
        st.markdown(f"<h3 style='text-align: center; margin-bottom: 1rem;'>{titulo}</h3>", unsafe_allow_html=True)
        
        # Opção de visualização temporariamente desabilitada
        # tipo_visualizacao = st.radio(
        #     "Visualização",
        #     options=["Porcentagem", "Valores Absolutos"],
        #     horizontal=True,
        #     label_visibility="collapsed",
        #     key="tipo_viz_uf"
        # )
        # mostrar_porcentagem = tipo_visualizacao == "Porcentagem"
        
        # Fixado em porcentagem por enquanto
        mostrar_porcentagem = True

        # Verificar se a coluna geográfica existe
        if coluna_geo not in df_filtrado.columns:
            st.error(f"❌ Erro: Coluna '{coluna_geo}' não encontrada nos dados.")
        else:
            num_areas = df_filtrado[coluna_geo].nunique()

            # Só mostrar gráficos se houver mais de 1 área geográfica
            if num_areas > 1:
                # Verificar se deve mostrar gráfico regional (só para UF)
                mostrar_grafico_regional = False
                if not tem_filtro_municipio:
                    regioes_completas_detectadas = get_regioes_from_ufs(ufs_selecionadas) if ufs_selecionadas else []
                    mostrar_grafico_regional = len(ufs_selecionadas) == 0 or len(regioes_completas_detectadas) > 0
                
                # Calcular altura dinamicamente baseado no número de áreas
                num_areas_grafico = df_filtrado[coluna_geo].nunique()
                height_bar = max(1.5, min(6, num_areas_grafico * 0.3))
                
                # Ajustar largura baseado no número de áreas (menos áreas = gráfico mais estreito)
                if num_areas_grafico <= 3:
                    width_bar = 8
                elif num_areas_grafico <= 5:
                    width_bar = 10
                else:
                    width_bar = 12
                
                if mostrar_grafico_regional:
                    # Com gráfico regional: usar 2 colunas (só para UF)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Altura dinâmica para evitar barras muito grandes
                        zt.bar_plot(df_filtrado, coluna_geo, percentage=mostrar_porcentagem, figsize=(width_bar, height_bar))
                        # Tamanho da fonte responsivo baseado no número de áreas
                        ax = plt.gca()
                        if num_areas_grafico <= 5:
                            fontsize = 16
                        elif num_areas_grafico <= 10:
                            fontsize = 14
                        elif num_areas_grafico <= 20:
                            fontsize = 12
                        else:
                            fontsize = 10
                        for text in ax.texts:
                            text.set_fontsize(fontsize)
                            text.set_weight('bold')
                        # Centralizar gráfico quando houver poucas áreas
                        if num_areas_grafico <= 5:
                            plt.tight_layout()
                        render_matplotlib(use_container_width=True)
                
                    with col2:
                        # Gráfico por região (TODAS as UFs, sem filtro)
                        if len(df_regiao) > 0:
                            zt.stacked_bar_plot(
                                df_regiao, y="regiao", hue="faixa_jaccard",
                                order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
                                legend_title="Percentual de Similaridade CAR-SIGEF",
                                show_pct_symbol=True, figsize=(12, height_bar), legend_cols=5
                            )
                            # Ajustar tamanho da fonte para melhor legibilidade
                            ax = plt.gca()
                            if num_areas_grafico <= 5:
                                fontsize = 20
                            elif num_areas_grafico <= 10:
                                fontsize = 18
                            elif num_areas_grafico <= 20:
                                fontsize = 16
                            else:
                                fontsize = 14
                            for text in ax.texts:
                                text.set_fontsize(fontsize)
                                text.set_weight('bold')
                                text.set_color('#1D1D1D')
                            render_matplotlib(use_container_width=True)
                        else:
                            st.info("⚠️ Dados insuficientes para o gráfico regional.")
                else:
                    # Sem gráfico regional: gráfico de barras ocupa largura total
                    zt.bar_plot(df_filtrado, coluna_geo, percentage=mostrar_porcentagem, figsize=(width_bar, height_bar))
                    # Tamanho da fonte responsivo baseado no número de áreas
                    ax = plt.gca()
                    if num_areas_grafico <= 5:
                        fontsize = 16
                    elif num_areas_grafico <= 10:
                        fontsize = 14
                    elif num_areas_grafico <= 20:
                        fontsize = 12
                    else:
                        fontsize = 10
                    for text in ax.texts:
                        text.set_fontsize(fontsize)
                        text.set_weight('bold')
                    # Centralizar gráfico quando houver poucas áreas
                    if num_areas_grafico <= 5:
                        plt.tight_layout()
                    render_matplotlib(use_container_width=True)
            # Se apenas 1 área: não mostrar gráfico de barras

        st.markdown("---")

        # Ajustar altura dinamicamente baseado no número de áreas
        num_total = df_filtrado[coluna_geo].nunique()
        height_geo = max(1.5, min(5.5, num_total * 0.35))
        zt.stacked_bar_plot(
            df_filtrado, y=coluna_geo, hue="faixa_jaccard",
            order_hue=JACCARD_LABELS, palette=CORES_FAIXA_JACCARD,
            legend_title="Percentual de Similaridade CAR-SIGEF",
            show_pct_symbol=True, figsize=(12, height_geo), legend_cols=5
        )
        render_matplotlib(use_container_width=True)

        st.markdown("---")

        titulo_titularidade = f"Titularidade por {('Município' if tem_filtro_municipio else 'UF')}"
        st.markdown(f"<h3 style='text-align: center;'>{titulo_titularidade}</h3>", unsafe_allow_html=True)
        # Ajustar altura baseado no número de áreas
        height_titularidade = max(1.5, min(5.5, num_total * 0.35))
        zt.stacked_bar_plot(
            df_filtrado, y=coluna_geo, hue="label_cpf",
            order_hue=["Diferente", "Igual"], palette=CORES_TITULARIDADE,
            legend_title="Titularidade (CPF/CNPJ)",
            show_pct_symbol=True, figsize=(12, height_titularidade)
        )
        render_matplotlib(use_container_width=True)

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
                        
                        # Cores conforme notebook (gráfico de densidade)
                        cores_tamanho_kde = {"Pequeno": "#FF9D89", "Médio": "#E5D950", "Grande": "#7DBA84"}
                        
                        sns.kdeplot(
                            data=df_plot, x="indice_jaccard_pct", hue="class_tam_imovel",
                            hue_order=[t for t in ["Pequeno", "Médio", "Grande"] if t in tamanhos_disponiveis],
                            fill=True, common_norm=False, alpha=0.2, linewidth=3,
                            palette={k: v for k, v in cores_tamanho_kde.items() if k in tamanhos_disponiveis},
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
                            ax.text(2, y_max * 0.15, "Pequeno", color=cores_tamanho_kde["Pequeno"], 
                                   fontsize=14, fontweight='bold')
                        if "Médio" in tamanhos_disponiveis:
                            ax.text(90, y_max * 0.85, "Médio", color=cores_tamanho_kde["Médio"], 
                                   fontsize=14, fontweight='bold', ha='right')
                        if "Grande" in tamanhos_disponiveis:
                            ax.text(90, y_max * 0.70, "Grande", color=cores_tamanho_kde["Grande"], 
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
        # Definir variáveis de filtro usadas nesta seção
        valid_regioes = [r for r in (regioes_selecionadas or []) if r]
        valid_ufs = [u for u in (ufs_selecionadas or []) if u]
        valid_tamanhos = [t for t in (tamanhos_selecionados or []) if t]
        valid_status = [s for s in (status_selecionados or []) if s]
        
        # Determinar filtro de região baseado em UFs
        if valid_ufs:
            regioes_para_filtro = None
        else:
            regioes_para_filtro = valid_regioes if valid_regioes else None
        
        if 'ano_cadastro' in df_filtrado.columns:
            # 1. Preparar dados para gráfico combo (linha + barras)
            df_ano_sim = df_filtrado.groupby('ano_cadastro')['indice_jaccard'].median().reset_index()
            df_ano_sim['ano_cadastro'] = df_ano_sim['ano_cadastro'].astype(int)  # Remove .0
            df_ano_sim['indice_jaccard'] = df_ano_sim['indice_jaccard'] * 100
            
            # Contar CARs ÚNICOS com similaridade por ano (com todos os filtros aplicados)
            # Usar nunique para contar CARs distintos (um CAR pode ter múltiplas correspondências SIGEF)
            df_car_com_simi_por_ano = df_filtrado.groupby('ano_cadastro')['cod_imovel'].nunique().reset_index(name='total_simi')
            df_car_com_simi_por_ano['ano_cadastro'] = df_car_com_simi_por_ano['ano_cadastro'].astype(int)  # Remove .0
            
            # Obter total de registros (correspondências) por ano
            # Isso será sempre >= CARs únicos (barras cinzas maiores que azuis)
            # Aplica apenas filtros geográficos para mostrar contexto total
            df_total_por_ano = get_total_cars_by_year(
                regioes=regioes_para_filtro,
                ufs=valid_ufs if valid_ufs else None,
                tamanhos=valid_tamanhos if valid_tamanhos else None,
                status=valid_status if valid_status else None
            )
            
            if not df_total_por_ano.empty:
                df_total_por_ano['ano_cadastro'] = df_total_por_ano['ano_cadastro'].astype(int)
                df_total_por_ano.columns = ['ano_cadastro', 'total_total']
                
                # Consolidar DataFrames
                df_bars = df_total_por_ano.merge(
                    df_car_com_simi_por_ano,
                    on='ano_cadastro',
                    how='left'
                ).fillna(0)
                
                has_total_data = True
            else:
                # Fallback se não conseguir obter dados totais
                df_bars = df_car_com_simi_por_ano.copy()
                df_bars.columns = ['ano_cadastro', 'total_simi']
                has_total_data = False
            
            # Plotar gráfico combo
            if len(df_ano_sim) > 1:
                st.markdown("<h3 style='text-align: center;'>Evolução da Similaridade Mediana por Ano</h3>", unsafe_allow_html=True)
                
                try:
                    # Calcular largura das barras baseado no número de anos
                    num_anos = len(df_bars)
                    if num_anos <= 5:
                        bar_width = 0.7  # Barras mais largas quando há poucos anos
                    elif num_anos <= 8:
                        bar_width = 0.65
                    else:
                        bar_width = 0.6  # Barras padrão
                    
                    # Calcular ylim dinâmico baseado nos dados reais
                    if has_total_data:
                        max_total = df_bars['total_total'].max()
                        # Adicionar 30% de margem, mas garantir que barras pequenas sejam visíveis
                        ylim_max = max_total * 1.3
                    else:
                        max_simi = df_bars['total_simi'].max()
                        ylim_max = max_simi * 1.3
                    
                    fig, ax = plt.subplots(figsize=(11, 7))
                    plot_evolucao_combo(
                        df=df_ano_sim,
                        x='ano_cadastro',
                        y='indice_jaccard',
                        agg='median',
                        df_bars=df_bars,
                        x_bars='ano_cadastro',
                        y_bars='total_simi',
                        y_bars_total='total_total' if has_total_data else None,
                        color_line='#2563eb',
                        color_bars='#2563eb',
                        color_bars_total='#cccccc',
                        bar_width=bar_width,
                        bar_alpha=0.8,
                        bar_total_alpha=0.3,
                        label_mode='all',
                        show_bar_labels=True,
                        show_bar_total_labels=has_total_data,
                        y_format='percent',
                        y2_format='number',
                        legend_line_label='Similaridade (Mediana)',
                        legend_bar_label='N° de CARs com Similaridade',
                        legend_bar_total_label='N° de CARs Cadastrados' if has_total_data else '',
                        figsize=(11, 7),
                        ylim_line=(61, 100),
                        ylim_bars=(0, ylim_max),
                        ax=ax
                    )
                    st.pyplot(fig)
                    plt.close()
                except Exception as e:
                    st.warning(f"⚠️ Não foi possível gerar gráfico temporal: {str(e)}")
            else:
                st.info("ℹ️ Dados insuficientes para gráfico temporal (necessário pelo menos 2 anos com dados).")
        else:
            st.warning("⚠️ Coluna de data não disponível para análise temporal.")
        
        # Análise por tamanho e região
        st.markdown("---")
        
        if 'ano_cadastro' in df_filtrado.columns and 'class_tam_imovel' in df_filtrado.columns:
            # Verificar se alguma UF foi selecionada
            mostrar_grafico_regiao = not ufs_selecionadas or len(ufs_selecionadas) == 0
            
            if mostrar_grafico_regiao:
                col1, col2 = st.columns(2)
            else:
                col1 = st.container()
            
            with col1:
                st.markdown("<h3 style='text-align: center;'>Evolução por Tamanho</h3>", unsafe_allow_html=True)
                try:
                    # Preparar dados
                    df_tam = df_filtrado[['ano_cadastro', 'indice_jaccard', 'class_tam_imovel']].dropna()
                    
                    if len(df_tam) > 10:
                        df_tam = df_tam.copy()
                        df_tam['ano_cadastro'] = df_tam['ano_cadastro'].astype(int)  # Remove .0
                        df_tam['indice_jaccard'] = df_tam['indice_jaccard'] * 100
                        
                        # Cores conforme notebook
                        cores_tamanho = {"Pequeno": "#2980b9", "Médio": "#8e44ad", "Grande": "#2c3e50"}
                        
                        # Ajustar largura baseado se está sozinho ou não
                        largura = 16 if not mostrar_grafico_regiao else 10
                        fig, ax = plt.subplots(figsize=(largura, 6))
                        plot_evolucao_multi_swd(
                            df=df_tam,
                            x='ano_cadastro',
                            y='indice_jaccard',
                            hue='class_tam_imovel',
                            agg='median',
                            palette=cores_tamanho,
                            y_format='percent',
                            figsize=(largura, 6),
                            label_mode='end',
                            show_y_axis=True,
                            ax=ax
                        )
                        st.pyplot(fig)
                        plt.close()
                    else:
                        st.info("Dados insuficientes para análise por tamanho")
                except Exception as e:
                    st.warning(f"⚠️ Erro ao gerar gráfico: {str(e)}")
            
            if mostrar_grafico_regiao:
                with col2:
                    st.markdown("<h3 style='text-align: center;'>Evolução por Região</h3>", unsafe_allow_html=True)
                    try:
                        # Preparar dados
                        df_reg = df_filtrado[['ano_cadastro', 'indice_jaccard', 'regiao']].dropna()
                        
                        if len(df_reg) > 10:
                            df_reg = df_reg.copy()
                            df_reg['ano_cadastro'] = df_reg['ano_cadastro'].astype(int)  # Remove .0
                            df_reg['indice_jaccard'] = df_reg['indice_jaccard'] * 100
                            
                            # Mapear regiões para nomes com inicial maiúscula
                            mapa_regioes = {
                                'centro_oeste': 'Centro-Oeste',
                                'nordeste': 'Nordeste',
                                'norte': 'Norte',
                                'sudeste': 'Sudeste',
                                'sul': 'Sul'
                            }
                            df_reg['regiao_nome'] = df_reg['regiao'].map(mapa_regioes)
                            
                            # Cores conforme notebook
                            cores_regiao = {
                                "Centro-Oeste": "#2c3e50",
                                "Nordeste": "#2980b9",
                                "Norte": "#27ae60",
                                "Sudeste": "#e67e22",
                                "Sul": "#8e44ad"
                            }
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            plot_evolucao_multi_swd(
                                df=df_reg,
                                x='ano_cadastro',
                                y='indice_jaccard',
                                hue='regiao_nome',
                                agg='median',
                                palette=cores_regiao,
                                y_format='percent',
                                figsize=(10, 6),
                                label_mode='end',
                                show_y_axis=True,
                                ax=ax
                            )
                            st.pyplot(fig)
                            plt.close()
                        else:
                            st.info("Dados insuficientes para análise por região")
                    except Exception as e:
                        st.warning(f"⚠️ Erro ao gerar gráfico: {str(e)}")
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
                autotext.set_color('black')
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
                    ax.annotate(row['estado'], (row['pct_espacial_bom'], row['pct_cpf_igual']),
                                   xytext=(0, 0), textcoords='offset points',
                               fontsize=9, fontweight='bold', color='#333333', ha='center', va='center', zorder=4)

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
