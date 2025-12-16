"""
Dashboard de Análise de Similaridade CAR-SIGEF
Análise exploratória dos dados de similaridade entre cadastros CAR e SIGEF no Brasil
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import zetta_utils as zt
import duckdb
import os
import base64

# ═══════════════════════════════════════════════════════════
# CONFIGURAÇÕES DA PÁGINA
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Análise CAR-SIGEF",
    page_icon="assets/Logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configurações de performance
import warnings
warnings.filterwarnings('ignore')

# Estilo matplotlib
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'monospace'
plt.ioff()  # Desabilita modo interativo para melhor performance

# CSS customizado para centralização
st.markdown("""
<style>
    /* Centralizar títulos e cabeçalhos */
    h1, h2, h3, h4 {
        text-align: center;
    }
    
    /* Centralizar labels de multiselect */
    label {
        text-align: center;
        display: block;
        font-weight: bold;
    }
    
    /* Centralizar métricas */
    [data-testid="stMetricValue"] {
        text-align: center;
        justify-content: center;
    }
    
    [data-testid="stMetricLabel"] {
        text-align: center;
        justify-content: center;
    }
    
    [data-testid="metric-container"] {
        text-align: center;
    }
    
    /* Centralizar markdown */
    .element-container p {
        text-align: center;
    }
    
    /* Centralizar expanders */
    .streamlit-expanderHeader {
        text-align: center;
    }
    
    /* Ajustar espaçamento */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Centralizar info box */
    .stAlert {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES - DUCKDB
# ═══════════════════════════════════════════════════════════

@st.cache_resource
def get_duckdb_connection():
    """Cria conexão DuckDB em memória"""
    return duckdb.connect(':memory:', read_only=False)

@st.cache_data
def load_metadata():
    """Carrega metadados básicos do CSV para filtros"""
    con = get_duckdb_connection()
    
    metadata = con.execute("""
        SELECT 
            ARRAY_AGG(DISTINCT regiao) as regioes,
            ARRAY_AGG(DISTINCT estado) as estados,
            ARRAY_AGG(DISTINCT class_tam_imovel) as tamanhos,
            ARRAY_AGG(DISTINCT status_imovel) as status
        FROM 'data/similaridade_sicar_sigef_brasil.csv'
    """).df()
    
    return metadata

@st.cache_data(show_spinner=False)
def load_filtered_data(regioes=None, ufs=None, tamanhos=None, status=None):
    """Carrega dados filtrados usando DuckDB - muito mais rápido!"""
    con = get_duckdb_connection()
    
    # Montar query SQL com filtros
    query = """
        SELECT *
        FROM 'data/similaridade_sicar_sigef_brasil.csv'
        WHERE 1=1
    """
    
    params = []
    
    if regioes and len(regioes) > 0:
        placeholders = ','.join(['?' for _ in regioes])
        query += f" AND regiao IN ({placeholders})"
        params.extend(regioes)
    
    if ufs and len(ufs) > 0:
        placeholders = ','.join(['?' for _ in ufs])
        query += f" AND estado IN ({placeholders})"
        params.extend(ufs)
    
    if tamanhos and len(tamanhos) > 0:
        placeholders = ','.join(['?' for _ in tamanhos])
        query += f" AND class_tam_imovel IN ({placeholders})"
        params.extend(tamanhos)
    
    if status and len(status) > 0:
        placeholders = ','.join(['?' for _ in status])
        query += f" AND status_imovel IN ({placeholders})"
        params.extend(status)
    
    # Executar query
    df = con.execute(query, params).df()
    
    # Renomear colunas para manter consistência com código existente
    df.rename(columns={'regiao': 'regiao_analise', 'estado': 'uf'}, inplace=True)
    
    # Aplicar transformações
    df['regiao_analise'] = df['regiao_analise'].replace({
        'centro_oeste': 'Centro-Oeste', 
        'sudeste': 'Sudeste', 
        'nordeste': 'Nordeste', 
        'norte': 'Norte', 
        'sul': 'Sul'
    })
    df['indice_jaccard'] = df['indice_jaccard'] * 100
    
    # Criação de faixas
    bins = [0, 25, 50, 85, 100]
    labels = ["0-25%", "25-50%", "50-85%", "85-100%"]
    df["faixa_jaccard"] = pd.cut(df["indice_jaccard"], bins=bins, labels=labels, include_lowest=True)
    
    # Converter data
    df['data_cadastro_imovel'] = pd.to_datetime(df['data_cadastro_imovel'], errors='coerce')
    df['ano_cadastro'] = df['data_cadastro_imovel'].dt.year
    
    # Validações
    df['cpf_ok'] = df['igualdade_cpf'].apply(lambda x: str(x).upper() == 'TRUE')
    df['geo_ok'] = df['indice_jaccard'] >= 85
    df['coerente'] = (df['cpf_ok']) & (df['geo_ok'])
    
    # Área CAR
    df['area_car_ha'] = df['area_sicar_ha']
    
    # Cálculo de Jaccard
    df['uniao_ha'] = df['area_sicar_ha'] + df['area_sigef_agregado_ha'] - df['area_intersecao_ha']
    df['jaccard_calculado'] = df.apply(
        lambda x: (x['area_intersecao_ha'] / x['uniao_ha'] * 100) if x['uniao_ha'] > 0 else 0, 
        axis=1
    )
    df['jaccard_calculado'] = df['jaccard_calculado'].clip(upper=100)
    
    return df

@st.cache_data(show_spinner=False)
def calculate_metrics(df):
    """Calcula métricas principais com cache"""
    return {
        'mean_jaccard': df['indice_jaccard'].mean(),
        'median_jaccard': df['indice_jaccard'].median(),
        'coerentes': len(df[df['coerente'] == True]),
        'alta_similaridade': len(df[df['indice_jaccard'] >= 85]),
        'total': len(df)
    }

def create_risk_matrix(df):
    """Cria matriz de risco CPF vs Geo"""
    cores_personalizadas = {
        (True, True): '#2ecc71',    # Verde - Coerente
        (True, False): '#e67e22',   # Laranja - Incoerência Espacial
        (False, True): '#f1c40f',   # Amarelo - Incoerência Titularidade
        (False, False): '#e74c3c'   # Vermelho - Incoerente
    }
    
    zt.risk_matrix_plot(
        df,
        row_col='cpf_ok',
        col_col='geo_ok',
        row_title='Titularidade',
        col_title='Similaridade Espacial',
        colors=cores_personalizadas,
        row_labels={True: 'Igual', False: 'Diferente'},
        col_labels={True: '>= 85%', False: '< 85%'},
        title=False,
        count_fontsize=12,
        figsize=(8, 6)
    )

# ═══════════════════════════════════════════════════════════
# CARREGAMENTO DOS DADOS
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# CARREGAMENTO DOS DADOS
# ═══════════════════════════════════════════════════════════

# Carregar metadados para os filtros
metadata = load_metadata()

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════

st.markdown("<h1 style='text-align: center;'>Análise de Similaridade CAR-SIGEF</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Análise Exploratória dos Dados de Similaridade Espacial</h3>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FILTROS
# ═══════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("<h3 style='text-align: center;'>Filtros de Dados</h3>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 0;'>Região</p>", unsafe_allow_html=True)
    regioes_disponiveis = ['centro_oeste', 'norte', 'nordeste', 'sudeste', 'sul']
    regioes_selecionadas = st.multiselect(
        "Região",
        options=regioes_disponiveis,
        default=[],
        placeholder="Selecione as regiões",
        label_visibility="collapsed"
    )

with col2:
    st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 0;'>UF</p>", unsafe_allow_html=True)
    # Lista de UFs do Brasil
    ufs_disponiveis = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 
                       'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']
    ufs_selecionadas = st.multiselect(
        "UF",
        options=ufs_disponiveis,
        default=[],
        placeholder="Selecione as UFs",
        label_visibility="collapsed"
    )

with col3:
    st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 0;'>Tamanho do Imóvel</p>", unsafe_allow_html=True)
    tamanhos_disponiveis = ['Pequeno', 'Médio', 'Grande']
    tamanhos_selecionados = st.multiselect(
        "Tamanho do Imóvel",
        options=tamanhos_disponiveis,
        default=[],
        placeholder="Selecione os tamanhos",
        label_visibility="collapsed"
    )

with col4:
    st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: 0;'>Status do Imóvel</p>", unsafe_allow_html=True)
    status_disponiveis = ['Ativo', 'Cancelado', 'Pendente', 'Suspenso']
    status_selecionados = st.multiselect(
        "Status do Imóvel",
        options=status_disponiveis,
        default=[],
        placeholder="Selecione os status",
        label_visibility="collapsed"
    )

# Aplicar filtros usando DuckDB (ultra-rápido!)
df_filtrado = load_filtered_data(
    regioes=regioes_selecionadas if regioes_selecionadas else None,
    ufs=ufs_selecionadas if ufs_selecionadas else None,
    tamanhos=tamanhos_selecionados if tamanhos_selecionados else None,
    status=status_selecionados if status_selecionados else None
)

# Calcular total de registros (via DuckDB é instantâneo)
con = get_duckdb_connection()
total_registros = con.execute("SELECT COUNT(*) FROM 'data/similaridade_sicar_sigef_brasil.csv'").fetchone()[0]

# Mostrar total de registros filtrados
st.markdown(f"<p style='text-align: center;'><b>Total de registros:</b> {len(df_filtrado):,} de {total_registros:,} ({(len(df_filtrado)/total_registros*100):.1f}%)</p>", unsafe_allow_html=True)

# Aviso se dataset muito grande
if len(df_filtrado) > 100000:
    st.warning(f"Dataset grande ({len(df_filtrado):,} registros). Os gráficos podem demorar para carregar.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# MÉTRICAS PRINCIPAIS
# ═══════════════════════════════════════════════════════════

st.markdown("<h3 style='text-align: center;'>Indicadores Principais</h3>", unsafe_allow_html=True)
st.markdown("")

# Calcular métricas com cache
metrics = calculate_metrics(df_filtrado)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Média Jaccard</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{metrics['mean_jaccard']:.1f}%</p>", unsafe_allow_html=True)

with col2:
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Mediana Jaccard</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{metrics['median_jaccard']:.1f}%</p>", unsafe_allow_html=True)

with col3:
    perc_coerentes = (metrics['coerentes'] / metrics['total']) * 100
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Registros Coerentes</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{perc_coerentes:.1f}%</p>", unsafe_allow_html=True)

with col4:
    perc_alta = (metrics['alta_similaridade'] / metrics['total']) * 100
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Alta Similaridade (≥85%)</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{perc_alta:.1f}%</p>", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════
# TABS PRINCIPAIS
# ═══════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Visão Geral", 
    "Matriz de Risco", 
    "Análise Espacial",
    "Distribuições",
    "Análise Detalhada",
    "Dados"
])

# ═══════════════════════════════════════════════════════════
# TAB 1: VISÃO GERAL
# ═══════════════════════════════════════════════════════════

with tab1:
    st.markdown("<h2 style='text-align: center;'>Visão Geral dos Dados</h2>", unsafe_allow_html=True)
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h4 style='text-align: center;'>Distribuição do Índice Jaccard</h4>", unsafe_allow_html=True)
        with st.spinner('Gerando histograma...'):
            zt.hist_plot(
                df_filtrado, 
                'indice_jaccard', 
                xlabel='% de Similaridade', 
                title='Distribuição do Índice Jaccard'
            )
            fig = plt.gcf()
            st.pyplot(fig)
            plt.close(fig)
        
        # Teste de normalidade
        with st.expander("Teste de Normalidade (Jarque-Bera)"):
            stat_jb, p_value_jb = stats.jarque_bera(df_filtrado['indice_jaccard'])
            st.write(f"**Estatística:** {stat_jb:.4f}")
            st.write(f"**P-valor:** {p_value_jb:.6f}")
            if p_value_jb < 0.05:
                st.error("A distribuição NÃO é normal (rejeita H0)")
            else:
                st.success("A distribuição parece normal")
    
    with col2:
        st.markdown("<h4 style='text-align: center;'>Distribuição por Faixa</h4>", unsafe_allow_html=True)
        zt.donut_plot(
            df_filtrado, 
            'faixa_jaccard', 
            figsize=(8, 5), 
            legend_title='Faixa de Similaridade',
            decimal_places=1
        )
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)
    
    st.markdown("---")
    
    # Distribuição por UF
    st.markdown("<h4 style='text-align: center;'>Distribuição por UF</h4>", unsafe_allow_html=True)
    with st.spinner('Gerando gráfico de barras...'):
        zt.bar_plot(df_filtrado, 'uf', percentage=False)
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)
    
    st.markdown("---")
    
    # Estatísticas descritivas
    st.markdown("<h4 style='text-align: center;'>Estatísticas Descritivas</h4>", unsafe_allow_html=True)
    st.dataframe(df_filtrado[['indice_jaccard', 'area_sicar_ha', 'area_sigef_agregado_ha', 'area_intersecao_ha']].describe().T)

# ═══════════════════════════════════════════════════════════
# TAB 2: MATRIZ DE RISCO
# ═══════════════════════════════════════════════════════════

with tab2:
    st.markdown("<h2 style='text-align: center;'>Matriz de Risco: Titularidade vs Similaridade Espacial</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    Esta matriz cruza a **validação de titularidade (CPF)** com a **similaridade espacial (>= 85%)**:
    
    - **Verde**: Coerente (CPF igual + Geo >= 85%)
    - **Laranja**: Incoerência Espacial (CPF igual + Geo < 85%)
    - **Amarelo**: Incoerência de Titularidade (CPF diferente + Geo >= 85%)
    - **Vermelho**: Incoerente (CPF diferente + Geo < 85%)
    """)
    
    create_risk_matrix(df_filtrado)
    fig = plt.gcf()
    st.pyplot(fig)
    plt.close(fig)
    
    # Análise quantitativa
    st.markdown("---")
    st.markdown("<h4 style='text-align: center;'>Análise Quantitativa</h4>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(df_filtrado)
    coerente = len(df_filtrado[(df_filtrado['cpf_ok']) & (df_filtrado['geo_ok'])])
    incoe_espacial = len(df_filtrado[(df_filtrado['cpf_ok']) & (~df_filtrado['geo_ok'])])
    incoe_titular = len(df_filtrado[(~df_filtrado['cpf_ok']) & (df_filtrado['geo_ok'])])
    incoerente = len(df_filtrado[(~df_filtrado['cpf_ok']) & (~df_filtrado['geo_ok'])])
    
    with col1:
        st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Coerente</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{(coerente/total*100):.1f}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 12px; color: green;'>{coerente:,}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Incoe. Espacial</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{(incoe_espacial/total*100):.1f}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 12px; color: orange;'>{incoe_espacial:,}</p>", unsafe_allow_html=True)
    with col3:
        st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Incoe. Titular</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{(incoe_titular/total*100):.1f}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 12px; color: gold;'>{incoe_titular:,}</p>", unsafe_allow_html=True)
    with col4:
        st.markdown("<p style='text-align: center; font-size: 14px; color: gray; margin-bottom: 0;'>Incoerente</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 36px; font-weight: bold; margin-top: 0;'>{(incoerente/total*100):.1f}%</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 12px; color: red;'>{incoerente:,}</p>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# TAB 3: ANÁLISE ESPACIAL
# ═══════════════════════════════════════════════════════════

with tab3:
    st.markdown("<h2 style='text-align: center;'>Análise Espacial</h2>", unsafe_allow_html=True)
    st.markdown("")
    st.markdown("<h4 style='text-align: center;'>Discrepância: Área CAR vs Área SIGEF</h4>", unsafe_allow_html=True)
    st.markdown("Análise da relação entre área declarada (CAR) e área georreferenciada (SIGEF)")
    
    # Filtro para zoom
    df_zoom = df_filtrado[(df_filtrado['area_sicar_ha'] < 300_000) & (df_filtrado['area_sigef_agregado_ha'] < 300_000)]
    
    with st.spinner(f'Gerando scatter plot ({len(df_zoom):,} registros)...'):
        zt.scatter_plot(
            df_zoom, 
            x='area_sicar_ha',
            y='area_sigef_agregado_ha',
            figsize=(10, 8),
            hue='indice_jaccard',
            legend_title='Similaridade (%)',
            show_trend=True,
            legend_loc='upper right',
            use_suffix_x=True,
            use_suffix_y=True,
            ax_kwargs={'xlabel': 'Área CAR (ha)', 
                       'ylabel': 'Área SIGEF Agregado (ha)'}
        )
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)
    
    st.markdown("---")
    
    # Análise por região
    st.markdown("<h4 style='text-align: center;'>Similaridade por Região</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.spinner('Gerando box plot...'):
            zt.box_plot(
                df_filtrado, 
                y='indice_jaccard', 
                x='regiao_analise',
                title='Distribuição do Índice Jaccard por Região',
                figsize=(8, 6)
            )
            fig = plt.gcf()
            st.pyplot(fig)
            plt.close(fig)
    
    with col2:
        with st.spinner('Gerando violin plot...'):
            zt.violin_plot(
                df_filtrado, 
                y='indice_jaccard', 
                x='regiao_analise',
                title='Distribuição do Índice Jaccard por Região',
                figsize=(8, 6)
            )
            fig = plt.gcf()
            st.pyplot(fig)
            plt.close(fig)

# ═══════════════════════════════════════════════════════════
# TAB 4: DISTRIBUIÇÕES
# ═══════════════════════════════════════════════════════════

with tab4:
    st.markdown("<h2 style='text-align: center;'>Análise de Distribuições</h2>", unsafe_allow_html=True)
    st.markdown("")
    # Por tamanho do imóvel
    st.markdown("<h4 style='text-align: center;'>Distribuição por Tamanho do Imóvel</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        zt.box_plot(
            df_filtrado, 
            y='indice_jaccard', 
            x='class_tam_imovel',
            title='Distribuição do Índice Jaccard por Tamanho do Imóvel',
            figsize=(8, 6)
        )
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)
    
    with col2:
        zt.violin_plot(
            df_filtrado, 
            y='indice_jaccard', 
            x='class_tam_imovel',
            title='Distribuição do Índice Jaccard por Tamanho do Imóvel',
            figsize=(8, 6)
        )
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)
    
    # Teste de Kruskal-Wallis
    with st.expander("Teste de Kruskal-Wallis (Diferença entre grupos)"):
        grupos = [df_filtrado[df_filtrado['class_tam_imovel'] == c]['indice_jaccard'] 
                  for c in df_filtrado['class_tam_imovel'].unique()]
        
        # Verifica se há pelo menos 2 grupos
        if len(grupos) < 2:
            st.warning("É necessário pelo menos 2 grupos diferentes para realizar o teste de Kruskal-Wallis.")
        else:
            H_stat, p_value = stats.kruskal(*grupos)
            
            st.write(f"**Estatística H:** {H_stat:.4f}")
            st.write(f"**P-valor:** {p_value:.6f}")
            
            if p_value < 0.05:
                st.success("Existe diferença significativa entre as medianas dos grupos")
            else:
                st.warning("Não há diferença significativa entre os grupos")
            
            # Tamanho do efeito
            n = len(df_filtrado)
            k = len(df_filtrado['class_tam_imovel'].unique())
            epsilon_squared = (H_stat - k + 1) / (n - k)
            st.write(f"**Epsilon² (Tamanho do Efeito):** {epsilon_squared:.4f}")
            
            if epsilon_squared < 0.01:
                st.info("Associação nula/desprezível")
            elif epsilon_squared < 0.06:
                st.info("Associação pequena")
            elif epsilon_squared < 0.14:
                st.info("Associação média")
            else:
                st.info("Associação forte")
    
    st.markdown("---")
    
    # Por status do imóvel
    st.markdown("<h4 style='text-align: center;'>Distribuição por Status do Imóvel</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        zt.donut_plot(
            df_filtrado, 
            'status_imovel', 
            legend_title='Status do Imóvel', 
            figsize=(8, 6)
        )
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)
    
    with col2:
        zt.donut_plot(
            df_filtrado, 
            'class_tam_imovel', 
            figsize=(8, 6), 
            legend_title='Tamanho do Imóvel', 
            decimal_places=1
        )
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)

# ═══════════════════════════════════════════════════════════
# TAB 5: ANÁLISE DETALHADA
# ═══════════════════════════════════════════════════════════

with tab5:
    st.markdown("<h2 style='text-align: center;'>Análise Detalhada por Categoria</h2>", unsafe_allow_html=True)
    st.markdown("")
    # Stacked bar por Status
    st.markdown("<h4 style='text-align: center;'>Faixas de Similaridade por Status do Imóvel</h4>", unsafe_allow_html=True)
    zt.stacked_bar_plot(
        df_filtrado,
        y="status_imovel",
        hue="faixa_jaccard",
        order_hue=["0-25%", "25-50%", "50-85%", "85-100%"],
        palette=['#FF9D89', '#FFE48F', "#E5FF89", '#B6E4B0'],
        legend_title="Percentual de Similaridade CAR-SIGEF",
        use_suffix=False,
        figsize=(10, 2)
    )
    fig = plt.gcf()
    st.pyplot(fig)
    plt.close(fig)
    
    st.markdown("---")
    
    # Stacked bar por UF
    st.markdown("<h4 style='text-align: center;'>Faixas de Similaridade por UF</h4>", unsafe_allow_html=True)
    zt.stacked_bar_plot(
        df_filtrado,
        y="uf",
        hue="faixa_jaccard",
        order_hue=["0-25%", "25-50%", "50-85%", "85-100%"],
        palette=['#FF9D89', '#FFE48F', "#E5FF89", '#B6E4B0'],
        legend_title="Percentual de Similaridade CAR-SIGEF",
        use_suffix=False,
        figsize=(10, 8)
    )
    fig = plt.gcf()
    st.pyplot(fig)
    plt.close(fig)
    
    st.markdown("---")
    
    # Matriz de correlação
    st.markdown("<h4 style='text-align: center;'>Matriz de Correlação</h4>", unsafe_allow_html=True)
    
    with st.spinner('Calculando matriz de correlação...'):
        # Selecionar apenas colunas numéricas
        numeric_cols = df_filtrado.select_dtypes(include=[np.number]).columns.tolist()
        
        # Calcular correlação
        corr_matrix = df_filtrado[numeric_cols].corr()
        
        # Criar máscara para triângulo superior
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=0)
        
        # Plotar apenas triângulo superior
        plt.figure(figsize=(18, 10))
        sns.heatmap(
            corr_matrix, 
            mask=mask,
            cmap='coolwarm', 
            annot=True, 
            fmt='.1f', 
            linewidths=0.5,
            cbar=True, 
            cbar_kws={'shrink': 0.8},
            square=True
        )
        plt.title('Correlação entre variáveis numéricas', pad=20, fontsize=14, fontweight='bold')
        plt.tight_layout()
        fig = plt.gcf()
        st.pyplot(fig)
        plt.close(fig)
    
    st.markdown("---")
    
    # Validação do índice Jaccard
    st.markdown("<h4 style='text-align: center;'>Validação do Índice Jaccard</h4>", unsafe_allow_html=True)
    st.markdown("Comparação entre o Índice Jaccard fornecido e o calculado manualmente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Índice Jaccard (Fornecido)**")
        st.dataframe(df_filtrado['indice_jaccard'].describe())
    
    with col2:
        st.write("**Índice Jaccard (Calculado)**")
        st.dataframe(df_filtrado['jaccard_calculado'].describe())
    
    # Diferença
    df_filtrado['diff_jaccard'] = abs(df_filtrado['indice_jaccard'] - df_filtrado['jaccard_calculado'])
    st.metric("Diferença Média Absoluta", f"{df_filtrado['diff_jaccard'].mean():.4f}%")

# ═══════════════════════════════════════════════════════════
# TAB 6: DADOS
# ═══════════════════════════════════════════════════════════

with tab6:
    st.markdown("<h2 style='text-align: center;'>Visualização dos Dados</h2>", unsafe_allow_html=True)
    st.markdown("")
    
    # Informações do dataset
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Registros", f"{len(df_filtrado):,}")
    with col2:
        st.metric("Total de Colunas", len(df_filtrado.columns))
    with col3:
        memoria_mb = df_filtrado.memory_usage(deep=True).sum() / 1024**2
        st.metric("Memória", f"{memoria_mb:.1f} MB")
    with col4:
        st.metric("UFs", df_filtrado['uf'].nunique())
    
    st.markdown("---")
    
    # Configurações de paginação
    LINHAS_POR_PAGINA = 50
    todas_colunas = df_filtrado.columns.tolist()
    
    # Opções de ordenação
    col1, col2 = st.columns(2)
    with col1:
        ordenar_por = st.selectbox("Ordenar por:", todas_colunas, index=todas_colunas.index('indice_jaccard') if 'indice_jaccard' in todas_colunas else 0)
    with col2:
        ordem = st.radio("Ordem:", ["Decrescente", "Crescente"], horizontal=True)
    
    # Preparar dados para exibição (todas as colunas)
    ascending = True if ordem == "Crescente" else False
    df_display = df_filtrado.sort_values(by=ordenar_por, ascending=ascending)
    
    # Calcular número de páginas
    total_registros = len(df_display)
    total_paginas = (total_registros + LINHAS_POR_PAGINA - 1) // LINHAS_POR_PAGINA
    
    # Seletor de página
    st.markdown("---")
    st.markdown("### Navegação por Páginas")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pagina_atual = st.number_input(
            f"Página (1 a {total_paginas})",
            min_value=1,
            max_value=total_paginas,
            value=1,
            step=1
        )
    
    # Calcular índices de início e fim
    inicio = (pagina_atual - 1) * LINHAS_POR_PAGINA
    fim = min(inicio + LINHAS_POR_PAGINA, total_registros)
    
    # Exibir informações da página atual
    st.markdown(f"**Exibindo registros {inicio + 1:,} a {fim:,} de {total_registros:,}** | Página {pagina_atual} de {total_paginas}")
    
    # Exibir tabela da página atual
    df_pagina = df_display.iloc[inicio:fim]
    st.dataframe(
        df_pagina,
        use_container_width=True,
        height=600
    )
    
    # Navegação rápida
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("Primeira", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Anterior", use_container_width=True, disabled=(pagina_atual == 1)):
            st.rerun()
    with col3:
        st.markdown(f"<div style='text-align: center; padding: 5px;'><b>{pagina_atual}/{total_paginas}</b></div>", unsafe_allow_html=True)
    with col4:
        if st.button("Próxima", use_container_width=True, disabled=(pagina_atual == total_paginas)):
            st.rerun()
    with col5:
        if st.button("Última", use_container_width=True):
            st.rerun()
    
    # Botão de download
    st.markdown("---")
    st.markdown("### Download dos Dados Filtrados")
    
    col1, col2 = st.columns(2)
    with col1:
        csv_completo = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV (todas as colunas)",
            data=csv_completo,
            file_name=f"car_sigef_completo_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Download apenas da página atual
        csv_pagina = df_pagina.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"Download Página {pagina_atual}",
            data=csv_pagina,
            file_name=f"car_sigef_pagina_{pagina_atual}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════

st.markdown("---")

# Rodapé com logo Zetta
logo_path = "assets/LogoZetta.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    # Rodapé centralizado com logo clicável
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
    st.markdown("<p style='text-align: center; color: #666; font-size: 12px;'>Desenvolvido por Agência Zetta</p>", unsafe_allow_html=True)
