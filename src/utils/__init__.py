"""
Funções utilitárias para o Dashboard de Similaridade CAR-SIGEF

Este módulo contém todas as funções auxiliares para:
- Conexão e consultas ao DuckDB (in-memory)
- Carregamento e filtragem de dados
- Criação de visualizações especializadas
- Funções de filtros interativos
- Formatação de números e dados

Performance:
- Utiliza DuckDB para queries otimizadas em memória
- Cache de conexão singleton para evitar recarregamentos
- Queries SQL agregadas para estatísticas rápidas

Desenvolvido para: Ministério da Gestão e Inovação (MGI)
Última atualização: Janeiro 2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import duckdb
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import os
import urllib.request
import zipfile

# Caminho para o arquivo de dados
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "similaridade_sicar_sigef_brasil.csv"
DATA_ZIP_PATH = Path(__file__).parent.parent.parent / "data" / "similaridade_sicar_sigef_brasil.zip"

# URL alternativa para download dos dados (caso não esteja no repositório)
# Configure esta variável de ambiente no Streamlit Cloud com a URL do seu arquivo
DATA_URL = os.getenv("DATA_URL", None)

# Conexão global com DuckDB (in-memory)
_conn = None

# Mapeamentos de nomes amigáveis
REGIOES_MAP = {
    "centro_oeste": "Centro-Oeste",
    "nordeste": "Nordeste",
    "norte": "Norte",
    "sudeste": "Sudeste",
    "sul": "Sul"
}

UFS_MAP = {
    "AC": "AC - Acre",
    "AL": "AL - Alagoas",
    "AP": "AP - Amapá",
    "AM": "AM - Amazonas",
    "BA": "BA - Bahia",
    "CE": "CE - Ceará",
    "DF": "DF - Distrito Federal",
    "ES": "ES - Espírito Santo",
    "GO": "GO - Goiás",
    "MA": "MA - Maranhão",
    "MT": "MT - Mato Grosso",
    "MS": "MS - Mato Grosso do Sul",
    "MG": "MG - Minas Gerais",
    "PA": "PA - Pará",
    "PB": "PB - Paraíba",
    "PR": "PR - Paraná",
    "PE": "PE - Pernambuco",
    "PI": "PI - Piauí",
    "RJ": "RJ - Rio de Janeiro",
    "RN": "RN - Rio Grande do Norte",
    "RS": "RS - Rio Grande do Sul",
    "RO": "RO - Rondônia",
    "RR": "RR - Roraima",
    "SC": "SC - Santa Catarina",
    "SP": "SP - São Paulo",
    "SE": "SE - Sergipe",
    "TO": "TO - Tocantins"
}

STATUS_MAP = {
    "AT": "Ativo",
    "PE": "Pendente",
    "SU": "Suspenso",
    "CA": "Cancelado"
}

# Mapas reversos para converter de volta
REGIOES_MAP_REVERSE = {v: k for k, v in REGIOES_MAP.items()}
UFS_MAP_REVERSE = {v: k for k, v in UFS_MAP.items()}
STATUS_MAP_REVERSE = {v: k for k, v in STATUS_MAP.items()}

# ═══════════════════════════════════════════════════════════
# FUNÇÕES DE DADOS (DUCKDB)
# ═══════════════════════════════════════════════════════════

def reset_connection():
    """Reseta a conexão DuckDB (útil para recarregar dados)."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def _ensure_data_available() -> bool:
    """Garante que os dados estão disponíveis, fazendo download/descompactação se necessário.
    
    Returns:
        True se os dados estão disponíveis, False caso contrário
    """
    # Se o arquivo CSV já existe localmente, está tudo ok
    if DATA_PATH.exists():
        return True
    
    # Verificar se existe arquivo ZIP para descompactar
    if DATA_ZIP_PATH.exists():
        try:
            print(f"📦 Descompactando arquivo de dados... (apenas na primeira vez)")
            
            # Criar diretório se não existir
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Descompactar arquivo
            with zipfile.ZipFile(DATA_ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(DATA_PATH.parent)
            
            if DATA_PATH.exists():
                print(f"✅ Arquivo descompactado com sucesso!")
                return True
            else:
                print(f"❌ Erro: Arquivo descompactado não encontrado após extração.")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao descompactar arquivo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # Se não existe localmente nem compactado, tentar baixar da URL configurada
    if DATA_URL:
        try:
            print(f"📥 Baixando arquivo de dados... (isso pode levar alguns minutos)")
            
            # Criar diretório se não existir
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Baixar arquivo
            urllib.request.urlretrieve(DATA_URL, DATA_PATH)
            print(f"✅ Arquivo baixado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao baixar arquivo de dados: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # Se chegou aqui, não tem arquivo local, nem ZIP, nem URL configurada
    print(f"❌ Arquivo de dados não encontrado:")
    print(f"   • CSV: {DATA_PATH}")
    print(f"   • ZIP: {DATA_ZIP_PATH}")
    print(f"💡 Soluções:")
    print(f"   1. Adicione o arquivo ZIP ao repositório (similaridade_sicar_sigef_brasil.zip)")
    print(f"   2. Configure a variável de ambiente DATA_URL com o link do arquivo CSV")
    return False


def _get_connection():
    """Obtém conexão DuckDB (singleton)."""
    global _conn
    if _conn is None:
        # Garantir que os dados estão disponíveis
        if not _ensure_data_available():
            raise FileNotFoundError(f"Dados não disponíveis e não foi possível fazer download.")
        
        _conn = duckdb.connect(':memory:')
        
        # Carregar dados CSV para memória
        try:
            _conn.execute(f"""
                CREATE TABLE IF NOT EXISTS similaridade AS 
                SELECT 
                    *,
                    regiao as regiao_analise,
                    estado as uf,
                    CASE 
                        WHEN LOWER(CAST(igualdade_cpf AS VARCHAR)) IN ('true', '1', 't') THEN 1
                        ELSE 0
                    END as cpf_ok,
                    CASE 
                        WHEN LOWER(CAST(igualdade_cpf AS VARCHAR)) IN ('true', '1', 't') THEN 'Igual'
                        ELSE 'Diferente'
                    END as label_cpf,
                    YEAR(TRY_CAST(data_cadastro_imovel AS DATE)) as ano_cadastro,
                    CASE
                        WHEN indice_jaccard >= 0 AND indice_jaccard < 0.25 THEN '0-25%'
                        WHEN indice_jaccard >= 0.25 AND indice_jaccard < 0.50 THEN '25-50%'
                        WHEN indice_jaccard >= 0.50 AND indice_jaccard < 0.85 THEN '50-85%'
                        WHEN indice_jaccard >= 0.85 AND indice_jaccard <= 1.00 THEN '85-100%'
                        ELSE NULL
                    END as faixa_jaccard,
                    ((area_sicar_ha - area_sigef_agregado_ha) / NULLIF(area_sigef_agregado_ha, 0)) * 100 as descrepancia
                FROM read_csv_auto('{str(DATA_PATH)}')
            """)
            print(f"✅ Tabela DuckDB criada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao carregar CSV no DuckDB: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
            
    return _conn


def load_metadata() -> Dict[str, List]:
    """Carrega metadados do dataset (regiões, UFs, tamanhos, status disponíveis).
    
    Returns:
        Dicionário com listas de valores únicos para cada dimensão
    """
    try:
        conn = _get_connection()
        
        # Extrair valores únicos de cada coluna relevante
        regioes = conn.execute("SELECT DISTINCT regiao FROM similaridade WHERE regiao IS NOT NULL ORDER BY regiao").fetchdf()['regiao'].tolist()
        estados = conn.execute("SELECT DISTINCT estado FROM similaridade WHERE estado IS NOT NULL ORDER BY estado").fetchdf()['estado'].tolist()
        tamanhos = conn.execute("SELECT DISTINCT class_tam_imovel FROM similaridade WHERE class_tam_imovel IS NOT NULL ORDER BY class_tam_imovel").fetchdf()['class_tam_imovel'].tolist()
        status = conn.execute("SELECT DISTINCT status_imovel FROM similaridade WHERE status_imovel IS NOT NULL ORDER BY status_imovel").fetchdf()['status_imovel'].tolist()
        
        return {
            'regioes': regioes,
            'estados': estados,
            'tamanhos': tamanhos,
            'status': status
        }
    except Exception as e:
        st.error(f"Erro ao carregar metadados: {str(e)}")
        return {'regioes': [], 'estados': [], 'tamanhos': [], 'status': []}


def load_filtered_data(
    regioes: Optional[List[str]] = None,
    ufs: Optional[List[str]] = None,
    tamanhos: Optional[List[str]] = None,
    status: Optional[List[str]] = None
) -> pd.DataFrame:
    """Carrega dados filtrados do DuckDB.
    
    Args:
        regioes: Lista de regiões a filtrar
        ufs: Lista de UFs a filtrar
        tamanhos: Lista de tamanhos a filtrar
        status: Lista de status a filtrar
        
    Returns:
        DataFrame com dados filtrados
    """
    try:
        conn = _get_connection()
        
        # Construir condições de forma mais segura
        conditions = []
        
        # Tratar filtros None, vazios ou com strings vazias
        if regioes and len(regioes) > 0:
            # Filtrar valores None e strings vazias
            safe_regioes = [r.replace("'", "''").strip() for r in regioes if r and str(r).strip()]
            if safe_regioes:
                regioes_str = "', '".join(safe_regioes)
                conditions.append(f"regiao IN ('{regioes_str}')")
        
        if ufs and len(ufs) > 0:
            safe_ufs = [u.replace("'", "''").strip() for u in ufs if u and str(u).strip()]
            if safe_ufs:
                ufs_str = "', '".join(safe_ufs)
                conditions.append(f"estado IN ('{ufs_str}')")
        
        if tamanhos and len(tamanhos) > 0:
            safe_tamanhos = [t.replace("'", "''").strip() for t in tamanhos if t and str(t).strip()]
            if safe_tamanhos:
                tamanhos_str = "', '".join(safe_tamanhos)
                conditions.append(f"class_tam_imovel IN ('{tamanhos_str}')")
        
        if status and len(status) > 0:
            safe_status = [s.replace("'", "''").strip() for s in status if s and str(s).strip()]
            if safe_status:
                status_str = "', '".join(safe_status)
                conditions.append(f"status_imovel IN ('{status_str}')")
        
        # Montar query final
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM similaridade WHERE {where_clause}"
        
        # Executar query
        df = conn.execute(query).fetchdf()
        
        # Retornar DataFrame (vazio ou com dados)
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar dados filtrados: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()


def get_total_records() -> int:
    """Retorna o número total de registros no dataset.
    
    Returns:
        Número total de registros
    """
    try:
        conn = _get_connection()
        result = conn.execute("SELECT COUNT(*) as total FROM similaridade").fetchone()
        return result[0] if result else 0
    except Exception as e:
        st.error(f"Erro ao contar registros: {str(e)}")
        return 0


def get_aggregated_stats(
    regioes: Optional[List[str]] = None,
    ufs: Optional[List[str]] = None,
    tamanhos: Optional[List[str]] = None,
    status: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Calcula estatísticas agregadas usando SQL (muito mais rápido que Pandas).
    
    Args:
        regioes: Lista de regiões a filtrar
        ufs: Lista de UFs a filtrar
        tamanhos: Lista de tamanhos a filtrar
        status: Lista de status a filtrar
        
    Returns:
        Dicionário com estatísticas agregadas
    """
    try:
        conn = _get_connection()
        
        # Construir WHERE clause com sanitização
        where_clauses = []
        
        if regioes and len(regioes) > 0:
            safe_regioes = [r.replace("'", "''").strip() for r in regioes if r and str(r).strip()]
            if safe_regioes:
                regioes_str = "', '".join(safe_regioes)
                where_clauses.append(f"regiao IN ('{regioes_str}')")
        
        if ufs and len(ufs) > 0:
            safe_ufs = [u.replace("'", "''").strip() for u in ufs if u and str(u).strip()]
            if safe_ufs:
                ufs_str = "', '".join(safe_ufs)
                where_clauses.append(f"estado IN ('{ufs_str}')")
        
        if tamanhos and len(tamanhos) > 0:
            safe_tamanhos = [t.replace("'", "''").strip() for t in tamanhos if t and str(t).strip()]
            if safe_tamanhos:
                tamanhos_str = "', '".join(safe_tamanhos)
                where_clauses.append(f"class_tam_imovel IN ('{tamanhos_str}')")
        
        if status and len(status) > 0:
            safe_status = [s.replace("'", "''").strip() for s in status if s and str(s).strip()]
            if safe_status:
                status_str = "', '".join(safe_status)
                where_clauses.append(f"status_imovel IN ('{status_str}')")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT 
                COUNT(*) as total_records,
                AVG(indice_jaccard) as avg_jaccard,
                MEDIAN(indice_jaccard) as median_jaccard,
                COUNT(DISTINCT estado) as num_ufs
            FROM similaridade
            WHERE {where_clause}
        """
        
        result = conn.execute(query).fetchone()
        
        return {
            'total_records': int(result[0]) if result[0] else 0,
            'avg_jaccard': float(result[1] * 100) if result[1] is not None else 0.0,
            'median_jaccard': float(result[2] * 100) if result[2] is not None else 0.0,
            'num_ufs': int(result[3]) if result[3] else 0
        }
        
    except Exception as e:
        st.error(f"Erro ao calcular estatísticas: {str(e)}")
        return {
            'total_records': 0,
            'avg_jaccard': 0.0,
            'median_jaccard': 0.0,
            'num_ufs': 0
        }


# ═══════════════════════════════════════════════════════════
# FUNÇÕES DE FILTROS
# ═══════════════════════════════════════════════════════════

def display_region_filter(regioes: List[str]) -> List[str]:
    """Exibe filtro de regiões.
    
    Args:
        regioes: Lista de regiões disponíveis (formato técnico)
        
    Returns:
        Lista de regiões selecionadas (formato técnico)
    """
    try:
        # Converter para nomes amigáveis
        regioes_display = [REGIOES_MAP.get(r, r.title()) for r in regioes if r]
        
        st.markdown("<p style='text-align: center;'>Região</p>", unsafe_allow_html=True)
        selected_display = st.multiselect(
            "Região",
            options=regioes_display,
            default=None,
            placeholder="Escolha as opções",
            help="Selecione uma ou mais regiões",
            label_visibility="collapsed"
        )
        
        # Converter de volta para formato técnico com segurança
        result = []
        for r in selected_display:
            if r in REGIOES_MAP_REVERSE:
                result.append(REGIOES_MAP_REVERSE[r])
            else:
                # Fallback: tentar converter manualmente
                result.append(r.lower().replace("-", "_").replace(" ", "_"))
        return result
    except Exception as e:
        st.error(f"Erro no filtro de região: {str(e)}")
        return []


def display_uf_filter(ufs: List[str]) -> List[str]:
    """Exibe filtro de UFs.
    
    Args:
        ufs: Lista de UFs disponíveis (formato técnico)
        
    Returns:
        Lista de UFs selecionadas (formato técnico)
    """
    try:
        # Converter para nomes amigáveis
        ufs_display = [UFS_MAP.get(uf, uf) for uf in ufs if uf]
        
        st.markdown("<p style='text-align: center;'>UF</p>", unsafe_allow_html=True)
        selected_display = st.multiselect(
            "UF",
            options=ufs_display,
            default=None,
            placeholder="Escolha as opções",
            help="Selecione uma ou mais UFs",
            label_visibility="collapsed"
        )
        
        # Converter de volta para formato técnico com segurança
        result = []
        for uf in selected_display:
            if uf in UFS_MAP_REVERSE:
                result.append(UFS_MAP_REVERSE[uf])
            else:
                # Fallback: pegar apenas a sigla (primeiros 2 caracteres)
                sigla = uf.split(" ")[0] if " " in uf else uf[:2]
                result.append(sigla)
        return result
    except Exception as e:
        st.error(f"Erro no filtro de UF: {str(e)}")
        return []


def display_size_filter(tamanhos: List[str]) -> List[str]:
    """Exibe filtro de tamanhos.
    
    Args:
        tamanhos: Lista de tamanhos disponíveis
        
    Returns:
        Lista de tamanhos selecionados
    """
    st.markdown("<p style='text-align: center;'>Tamanho do Imóvel</p>", unsafe_allow_html=True)
    return st.multiselect(
        "Tamanho do Imóvel",
        options=tamanhos,
        default=None,
        placeholder="Escolha as opções",
        help="Selecione um ou mais tamanhos",
        label_visibility="collapsed"
    )


def display_status_filter(status_list: List[str]) -> List[str]:
    """Exibe filtro de status.
    
    Args:
        status_list: Lista de status disponíveis (formato técnico)
        
    Returns:
        Lista de status selecionados (formato técnico)
    """
    try:
        # Converter para nomes amigáveis
        status_display = [STATUS_MAP.get(s, s) for s in status_list if s]
        
        st.markdown("<p style='text-align: center;'>Status do Imóvel</p>", unsafe_allow_html=True)
        selected_display = st.multiselect(
            "Status do Imóvel",
            options=status_display,
            default=None,
            placeholder="Escolha as opções",
            help="Selecione um ou mais status",
            label_visibility="collapsed"
        )
        
        # Converter de volta para formato técnico com segurança
        result = []
        for s in selected_display:
            if s in STATUS_MAP_REVERSE:
                result.append(STATUS_MAP_REVERSE[s])
            else:
                # Fallback: usar as 2 primeiras letras em maiúsculas
                result.append(s[:2].upper())
        return result
    except Exception as e:
        st.error(f"Erro no filtro de status: {str(e)}")
        return []


def display_filter_summary(filtered_count: int, total_count: int):
    """Exibe resumo dos filtros aplicados.
    
    Args:
        filtered_count: Número de registros após filtros
        total_count: Número total de registros
    """
    pass


# ═══════════════════════════════════════════════════════════
# FUNÇÕES DE VISUALIZAÇÃO
# ═══════════════════════════════════════════════════════════

def format_number(num: float) -> str:
    """Formata número para exibição compacta.
    
    Args:
        num: Número a formatar
        
    Returns:
        String formatada
    """
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"


def create_quadrant_background(ax, x_min: float, x_max: float, y_min: float, y_max: float, x_div: float, y_div: float):
    """Cria fundo colorido para quadrantes em gráfico de dispersão.
    
    Args:
        ax: Axes do matplotlib
        x_min, x_max: Limites do eixo X
        y_min, y_max: Limites do eixo Y
        x_div: Divisão do eixo X (linha vertical)
        y_div: Divisão do eixo Y (linha horizontal)
    """
    # Quadrante inferior esquerdo (vermelho claro)
    ax.fill_between([x_min, x_div], y_min, y_div, color='#ffcccc', alpha=0.3, zorder=0)
    
    # Quadrante inferior direito (amarelo claro)
    ax.fill_between([x_div, x_max], y_min, y_div, color='#ffffcc', alpha=0.3, zorder=0)
    
    # Quadrante superior esquerdo (amarelo claro)
    ax.fill_between([x_min, x_div], y_div, y_max, color='#ffffcc', alpha=0.3, zorder=0)
    
    # Quadrante superior direito (verde claro)
    ax.fill_between([x_div, x_max], y_div, y_max, color='#ccffcc', alpha=0.3, zorder=0)
    
    # Linhas divisórias
    ax.axvline(x=x_div, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(y=y_div, color='gray', linestyle='--', linewidth=1, alpha=0.5)


def add_quadrant_labels(ax, x_min: float, x_max: float, y_min: float, y_max: float):
    """Adiciona labels aos quadrantes.
    
    Args:
        ax: Axes do matplotlib
        x_min, x_max: Limites do eixo X
        y_min, y_max: Limites do eixo Y
    """
    # Calcular posições centrais
    x_mid = (x_min + x_max) / 2
    y_mid = (y_min + y_max) / 2
    
    # Labels dos quadrantes
    ax.text(
        (x_min + x_mid) / 2, (y_min + y_mid) / 2,
        'CRÍTICO', ha='center', va='center',
        fontsize=12, fontweight='bold', color='red', alpha=0.6
    )
    
    ax.text(
        (x_mid + x_max) / 2, (y_min + y_mid) / 2,
        'ATENÇÃO', ha='center', va='center',
        fontsize=12, fontweight='bold', color='orange', alpha=0.6
    )
    
    ax.text(
        (x_min + x_mid) / 2, (y_mid + y_max) / 2,
        'ATENÇÃO', ha='center', va='center',
        fontsize=12, fontweight='bold', color='orange', alpha=0.6
    )
    
    ax.text(
        (x_mid + x_max) / 2, (y_mid + y_max) / 2,
        'IDEAL', ha='center', va='center',
        fontsize=12, fontweight='bold', color='green', alpha=0.6
    )


def create_risk_matrix(df: pd.DataFrame) -> plt.Figure:
    """Cria matriz de risco (Similaridade vs Titularidade).
    
    Args:
        df: DataFrame com dados
        
    Returns:
        Figure do matplotlib
    """
    import seaborn as sns
    from matplotlib.colors import LinearSegmentedColormap
    
    # Preparar dados (sem cópia - usar apenas colunas necessárias)
    mask = df['indice_jaccard'].notna() & df['label_cpf'].notna()
    df_valido = df[mask]
    
    # Agrupar por bins de Jaccard (escala 0-1)
    jaccard_bin = pd.cut(
        df_valido['indice_jaccard'],
        bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
        include_lowest=True
    )
    
    # Criar tabela de contingência (contagens)
    count_table = pd.crosstab(
        df_valido['label_cpf'], 
        jaccard_bin,
        margins=False
    )
    
    # Criar tabela percentual (normalizado por coluna)
    pct_table = pd.crosstab(
        df_valido['label_cpf'], 
        jaccard_bin,
        normalize='columns',
        margins=False
    ) * 100
    
    # Garantir ordem correta
    row_order = ['Diferente', 'Igual']
    col_order = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    
    count_table = count_table.reindex(index=row_order, columns=col_order, fill_value=0)
    pct_table = pct_table.reindex(index=row_order, columns=col_order, fill_value=0)
    
    # Criar colormap customizado: vermelho (risco alto) -> amarelo -> verde (risco baixo)
    # Quanto maior a similaridade COM mesmo titular = verde (bom)
    # Quanto maior a similaridade SEM mesmo titular = vermelho (suspeito)
    colors_gradient = ['#d62728', '#ff7f0e', '#ffd700', '#90ee90', '#2ca02c']
    cmap = LinearSegmentedColormap.from_list('risk', colors_gradient, N=256)
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plotar heatmap
    sns.heatmap(
        pct_table,
        annot=False,  # Vamos adicionar anotações customizadas
        fmt='.1f',
        cmap=cmap,
        cbar_kws={'label': 'Percentual (%)', 'shrink': 0.8},
        linewidths=2,
        linecolor='white',
        ax=ax,
        vmin=0,
        vmax=100
    )
    
    # Adicionar anotações customizadas (percentual + contagem)
    for i in range(len(row_order)):
        for j in range(len(col_order)):
            pct = pct_table.iloc[i, j]
            count = count_table.iloc[i, j]
            
            # Cor do texto baseado no valor
            text_color = 'white' if pct > 50 else '#333'
            
            # Texto principal (percentual)
            ax.text(j + 0.5, i + 0.4, f'{pct:.1f}%',
                   ha='center', va='center', fontsize=16, 
                   fontweight='bold', color=text_color)
            
            # Texto secundário (contagem formatada)
            if count >= 1000:
                count_text = f'({count/1000:.0f}K)'
            else:
                count_text = f'({int(count)})'
            
            ax.text(j + 0.5, i + 0.65, count_text,
                   ha='center', va='center', fontsize=10, 
                   color=text_color, alpha=0.8)
    
    # Adicionar totais por coluna
    totals = count_table.sum(axis=0)
    pct_totals = (totals / totals.sum()) * 100
    
    for j, (total, pct) in enumerate(zip(totals, pct_totals)):
        if total >= 1000:
            total_text = f'{total/1000:.0f}K'
        else:
            total_text = f'{int(total)}'
            
        ax.text(j + 0.5, len(row_order) + 0.3, 
               f'{total_text}\n({pct:.1f}%)',
               ha='center', va='top', fontsize=9, 
               color='#555', fontweight='bold')
    
    # Adicionar totais por linha (à direita)
    totals_row = count_table.sum(axis=1)
    pct_row = (totals_row / totals_row.sum()) * 100
    
    for i, (total, pct) in enumerate(zip(totals_row, pct_row)):
        if total >= 1000:
            total_text = f'{total/1000:.0f}K'
        else:
            total_text = f'{int(total)}'
            
        ax.text(len(col_order) + 0.2, i + 0.5,
               f'{total_text} ({pct:.1f}%)',
               ha='left', va='center', fontsize=10,
               color='#555', fontweight='bold')
    
    # Configurar labels
    ax.set_xlabel('Similaridade Espacial (Índice Jaccard)', 
                  fontsize=13, fontweight='bold', labelpad=15)
    ax.set_ylabel('Titularidade (CPF/CNPJ)', 
                  fontsize=13, fontweight='bold', labelpad=15)
    ax.set_title('Matriz de Confiabilidade: Espaço vs. Titularidade', 
                fontsize=15, fontweight='bold', pad=20)
    
    # Ajustar ticks
    ax.set_yticklabels(row_order, rotation=0, fontsize=11)
    ax.set_xticklabels(col_order, rotation=0, fontsize=11)
    
    plt.tight_layout()
    return fig
