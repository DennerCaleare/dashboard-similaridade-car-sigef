"""
Script para atualizar o CSV com total de CARs cadastrados por município+ano.

Consulta o banco MGI e adiciona coluna total_cars_municipio ao CSV.
"""

import psycopg2
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco MGI
DB_CONFIG = {
    'host': os.getenv('MGI_HOST'),
    'port': int(os.getenv('MGI_PORT', 5432)),
    'user': os.getenv('MGI_USER'),
    'password': os.getenv('MGI_PASSWORD'),
    'database': os.getenv('MGI_DATABASE')
}

# Caminho do CSV
CSV_PATH = Path(__file__).parent / 'data' / 'similaridade_sicar_sigef_brasil.csv'

def get_total_cars_por_municipio_ano():
    """Consulta o banco MGI para obter total de CARs por município+ano."""
    print("🔄 Conectando ao banco MGI...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Query para obter total de CARs cadastrados por município+ano
        query = """
        SELECT 
            idt_municipio,
            EXTRACT(YEAR FROM dat_criacao) as ano_cadastro,
            COUNT(DISTINCT cod_imovel) as total_cars_municipio
        FROM regularizacao_ambiental.car_imovel_dados_cadastrais_bruto_atualizado
        WHERE dat_criacao IS NOT NULL
            AND idt_municipio IS NOT NULL
        GROUP BY idt_municipio, EXTRACT(YEAR FROM dat_criacao)
        ORDER BY idt_municipio, ano_cadastro
        """
        
        print("🔄 Executando query no banco MGI (aguarde, pode levar alguns minutos)...")
        cursor.execute(query)
        
        # Converter para DataFrame
        print("🔄 Recuperando resultados...")
        results = cursor.fetchall()
        df_totals = pd.DataFrame(results, columns=['idt_municipio', 'ano_cadastro', 'total_cars_municipio'])
        
        # Converter ano para int
        df_totals['ano_cadastro'] = df_totals['ano_cadastro'].astype(int)
        
        print(f"✅ Query executada! {len(df_totals):,} registros obtidos")
        print(f"   Municípios únicos: {df_totals['idt_municipio'].nunique():,}")
        print(f"   Anos: {df_totals['ano_cadastro'].min()} - {df_totals['ano_cadastro'].max()}")
        
        cursor.close()
        conn.close()
        
        return df_totals
        
    except Exception as e:
        print(f"❌ Erro ao consultar banco: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def update_csv_with_municipio_totals():
    """Atualiza o CSV com os totais por município."""
    
    # 1. Obter dados do banco
    df_totals = get_total_cars_por_municipio_ano()
    if df_totals is None:
        return False
    
    # 2. Carregar CSV atual
    print("🔄 Carregando CSV atual...")
    df_csv = pd.read_csv(CSV_PATH)
    print(f"   CSV carregado: {len(df_csv):,} registros")
    
    # 3. Criar coluna ano_cadastro no CSV se não existir
    if 'ano_cadastro' not in df_csv.columns:
        df_csv['ano_cadastro'] = pd.to_datetime(df_csv['data_cadastro_imovel'], errors='coerce').dt.year
    
    # 4. Fazer merge para adicionar total_cars_municipio
    print("🔄 Fazendo merge dos dados...")
    df_csv = df_csv.merge(
        df_totals,
        on=['idt_municipio', 'ano_cadastro'],
        how='left'
    )
    
    # 5. Verificar resultados
    total_com_dados = df_csv['total_cars_municipio'].notna().sum()
    total_sem_dados = df_csv['total_cars_municipio'].isna().sum()
    
    print(f"✅ Merge concluído:")
    print(f"   Registros com total_cars_municipio: {total_com_dados:,} ({total_com_dados/len(df_csv)*100:.1f}%)")
    print(f"   Registros sem total_cars_municipio: {total_sem_dados:,} ({total_sem_dados/len(df_csv)*100:.1f}%)")
    
    # 6. Salvar CSV atualizado
    print("🔄 Salvando CSV atualizado (isso pode demorar alguns minutos)...")
    try:
        df_csv.to_csv(CSV_PATH, index=False, chunksize=50000)
        print(f"✅ CSV atualizado salvo em: {CSV_PATH}")
    except Exception as e:
        print(f"⚠️ Erro ao salvar CSV completo: {str(e)}")
        print("🔄 Tentando salvar em modo baixa memória...")
        # Tentar salvar em modo de baixa memória
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            df_csv.to_csv(f, index=False, chunksize=10000)
        print(f"✅ CSV atualizado salvo em: {CSV_PATH}")
    
    # 7. Mostrar amostra dos dados
    print("\n📊 Amostra dos dados (Lavras - MG):")
    lavras = df_csv[df_csv['municipio_nome'] == 'Lavras'].groupby('ano_cadastro').agg({
        'cod_imovel': 'count',
        'total_cars_municipio': 'first'
    }).reset_index()
    lavras.columns = ['Ano', 'CARs no Dataset', 'Total CARs Cadastrados']
    print(lavras.to_string(index=False))
    
    return True


if __name__ == '__main__':
    print("="*60)
    print("ATUALIZAÇÃO DE TOTAIS DE CARs POR MUNICÍPIO")
    print("="*60)
    
    success = update_csv_with_municipio_totals()
    
    if success:
        print("\n" + "="*60)
        print("✅ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ ERRO NA ATUALIZAÇÃO")
        print("="*60)
