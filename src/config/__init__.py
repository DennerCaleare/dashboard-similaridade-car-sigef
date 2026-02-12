"""
Configurações e constantes do Dashboard de Similaridade CAR-SIGEF

Este módulo contém todas as configurações globais, constantes, paletas de cores,
labels e caminhos de arquivos utilizados no dashboard.

Inclui:
- CSS customizado para estilização da interface
- Paletas de cores consistentes para visualizações
- Labels e categorias padronizadas
- Parâmetros de filtros e limites
- Caminhos para recursos estáticos

Desenvolvido para: Ministério da Gestão e Inovação (MGI)
Última atualização: Janeiro 2026
"""

# ═══════════════════════════════════════════════════════════
# CSS CUSTOMIZADO
# ═══════════════════════════════════════════════════════════

CSS_CUSTOM = """
<style>
    /* Prevenir refluxo e flickering */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Remover toolbar flutuante de gráficos */
    [data-testid="stElementToolbar"] {
        display: none;
    }
    
    /* Estabilizar viewport */
    html, body {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    
    [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    
    /* Fixar gráficos Plotly */
    .js-plotly-plot {
        max-width: 100% !important;
    }
    
    /* Estilo para títulos */
    h1 {
        color: #1f77b4;
        text-align: center;
        padding-bottom: 10px;
    }
    
    h2 {
        color: #2c3e50;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 5px;
    }
    
    h3 {
        color: #34495e;
    }
    
    /* Estilo para métricas */
    .metric-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* ========================================
       MULTISELECT - Melhorias de UX
       ======================================== */
    
    /* Limitar altura do dropdown de opções */
    div[data-baseweb="select"] > div {
        max-height: 120px !important;
        overflow-y: auto !important;
    }
    
    /* Estilizar o container de tags selecionadas - Layout horizontal compacto */
    .stMultiSelect [data-baseweb="tag"] {
        margin: 2px !important;
        font-size: 0.8rem !important;
        padding: 2px 8px !important;
        height: auto !important;
        min-height: 24px !important;
    }
    
    /* Compactar o input do multiselect */
    div[data-baseweb="select"] {
        min-height: 38px !important;
    }
    
    /* Container das tags selecionadas - ÁREA ROLÁVEL com botão fixo */
    div[data-baseweb="select"] > div:first-child {
        display: flex !important;
        flex-wrap: nowrap !important;  /* Não quebrar linha */
        align-items: center !important;
        gap: 4px !important;
    }
    
    /* Container interno das tags - SCROLLABLE */
    div[data-baseweb="select"] > div:first-child > div:first-child {
        display: flex !important;
        flex-wrap: wrap !important;
        max-height: 80px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        flex: 1 !important;
        padding-right: 8px !important;
    }
    
    /* Botão CLEAR ALL (X) - SEMPRE FIXO À DIREITA */
    div[data-baseweb="select"] > div:first-child > div[role="button"] {
        position: sticky !important;
        right: 0 !important;
        flex-shrink: 0 !important;
        margin-left: auto !important;
        background: white !important;
        padding: 4px !important;
        border-radius: 4px !important;
        box-shadow: -2px 0 4px rgba(0,0,0,0.1) !important;
        z-index: 10 !important;
    }
    
    /* Ícone do botão clear - mais visível */
    div[data-baseweb="select"] > div:first-child > div[role="button"] svg {
        width: 20px !important;
        height: 20px !important;
        color: #666 !important;
    }
    
    /* Hover effect no botão clear */
    div[data-baseweb="select"] > div:first-child > div[role="button"]:hover {
        background: #f0f0f0 !important;
        box-shadow: -2px 0 6px rgba(0,0,0,0.15) !important;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        h1 {
            font-size: 1.5rem;
        }
        h2 {
            font-size: 1.3rem;
        }
    }
</style>
"""

# ═══════════════════════════════════════════════════════════
# PALETAS DE CORES
# ═══════════════════════════════════════════════════════════

# Cores para faixas de índice Jaccard (similaridade)
# Gradiente suavizado do vermelho (baixa) ao verde (alta similaridade)
CORES_FAIXA_JACCARD = {
    "0-25%": "#FF9D89",      # Vermelho claro
    "25-50%": "#FFE48F",     # Amarelo
    "50-85%": "#E5FF89",     # Verde claro amarelado
    "85-100%": "#B6E4B0"     # Verde suave
}

# Cores para tamanhos de imóvel (conforme notebook)
CORES_TAMANHO = {
    "Pequeno": "#2980b9",    # Azul vibrante
    "Médio": "#8e44ad",      # Roxo
    "Grande": "#2c3e50"      # Azul escuro
}

# Cores para status do imóvel
CORES_STATUS = {
    "AT": "#81c784",         # Ativo - Verde suave
    "PE": "#ffb74d",         # Pendente - Laranja suave
    "SU": "#e57373",         # Suspenso - Vermelho suave
    "CA": "#bdbdbd"          # Cancelado - Cinza suave
}

# Cores para titularidade (mesmo titular ou diferente)
CORES_TITULARIDADE = {
    "Diferente": "#e57373",  # Vermelho suave (CPF diferente = problema)
    "Igual": "#a5d6a7"       # Verde mais claro (CPF igual = bom)
}

# Cores para evolução temporal por tamanho (conforme notebook)
CORES_EVOLUCAO_TAMANHO = {
    "Pequeno": "#2980b9",    # Azul vibrante
    "Médio": "#8e44ad",      # Roxo
    "Grande": "#2c3e50"      # Azul escuro
}

# Cores para evolução temporal por região (conforme notebook)
CORES_EVOLUCAO_REGIAO = {
    "norte": "#27ae60",         # Verde
    "nordeste": "#2980b9",      # Azul vibrante
    "centro_oeste": "#2c3e50",  # Azul escuro
    "sudeste": "#e67e22",       # Laranja
    "sul": "#8e44ad"            # Roxo
}

# Cores para matriz de maturidade por região
CORES_MATURIDADE_REGIAO = {
    "norte": "#64b5f6",         # Azul suave
    "nordeste": "#ffb74d",      # Laranja suave
    "centro_oeste": "#81c784",  # Verde suave
    "sudeste": "#e57373",       # Vermelho suave
    "sul": "#ba68c8"            # Roxo suave
}

# Mapeamento de nomes de regiões (do CSV para exibição)
REGIOES_NOME_MAP = {
    "norte": "Norte",
    "nordeste": "Nordeste",
    "centro_oeste": "Centro-Oeste",
    "sudeste": "Sudeste",
    "sul": "Sul"
}

# ═══════════════════════════════════════════════════════════
# LABELS E CATEGORIAS
# ═══════════════════════════════════════════════════════════

# Labels ordenadas para faixas de Jaccard
JACCARD_LABELS = ["0-25%", "25-50%", "50-85%", "85-100%"]

# Labels para códigos de status
LABELS_STATUS = {
    "AT": "Ativo",
    "PE": "Pendente",
    "SU": "Suspenso",
    "CA": "Cancelado"
}

# ═══════════════════════════════════════════════════════════
# PARÂMETROS DE FILTROS
# ═══════════════════════════════════════════════════════════

# Limites para discrepância de área
DISCREPANCIA_MIN = -100  # Percentual mínimo
DISCREPANCIA_MAX = 100   # Percentual máximo

# Limites para anos
ANO_MIN = 2000
ANO_MAX = 2030

# ═══════════════════════════════════════════════════════════
# CAMINHOS DE ARQUIVOS
# ═══════════════════════════════════════════════════════════

from pathlib import Path

# Diretório base do projeto
_BASE_DIR = Path(__file__).parent.parent.parent

# Caminho para logo do footer
LOGO_FOOTER_PATH = _BASE_DIR / "assets" / "LogoZetta.png"

# Caminho para dados
DATA_PATH = _BASE_DIR / "data" / "similaridade_sicar_sigef_brasil.csv"
