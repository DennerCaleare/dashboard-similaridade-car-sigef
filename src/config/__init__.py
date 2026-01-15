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
    
    /* Limitar altura dos filtros multiselect */
    div[data-baseweb="select"] > div {
        max-height: 120px !important;
        overflow-y: auto !important;
    }
    
    /* Estilizar o container de tags selecionadas */
    .stMultiSelect [data-baseweb="tag"] {
        margin: 2px;
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
    "0-20%": "#e57373",      # Vermelho suave
    "20-40%": "#ffb74d",     # Laranja suave
    "40-60%": "#fff176",     # Amarelo suave
    "60-80%": "#81d4fa",     # Azul claro suave
    "80-100%": "#81c784"     # Verde suave
}

# Cores para tamanhos de imóvel
CORES_TAMANHO = {
    "Pequeno": "#64b5f6",    # Azul suave
    "Médio": "#ffb74d",      # Laranja suave
    "Grande": "#81c784"      # Verde suave
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
    "Igual": "#81c784",      # Verde suave
    "Diferente": "#e57373"   # Vermelho suave
}

# Cores para evolução temporal por tamanho
CORES_EVOLUCAO_TAMANHO = {
    "Pequeno": "#64b5f6",    # Azul suave
    "Médio": "#ffb74d",      # Laranja suave
    "Grande": "#81c784"      # Verde suave
}

# Cores para evolução temporal por região
CORES_EVOLUCAO_REGIAO = {
    "norte": "#64b5f6",         # Azul suave
    "nordeste": "#ffb74d",      # Laranja suave
    "centro_oeste": "#81c784",  # Verde suave
    "sudeste": "#e57373",       # Vermelho suave
    "sul": "#ba68c8"            # Roxo suave
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
JACCARD_LABELS = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]

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

# Caminho para logo do footer
LOGO_FOOTER_PATH = "assets/LogoZetta.png"

# Caminho para dados
DATA_PATH = "data/similaridade_sicar_sigef_brasil.csv"
