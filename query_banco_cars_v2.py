"""
Script para buscar total de CARs do banco MGI - Versão 2
"""
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('MGI_HOST'),
    'port': os.getenv('MGI_PORT'),
    'database': os.getenv('MGI_DATABASE'),
    'user': os.getenv('MGI_USER'),
    'password': os.getenv('MGI_PASSWORD')
}

print("=" * 70)
print("BUSCANDO TOTAL DE CARs CADASTRADOS POR ANO")
print("=" * 70)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("\n✓ Conectado ao banco")
    
    # Query para obter total de CARs por ano e estado
    print("\nConsultando tabela regularizacao_ambiental.car_imoveis...")
    
    query = """
        SELECT 
            EXTRACT(YEAR FROM dat_criacao) as ano_cadastro,
            LEFT(CAST(idt_municipio AS VARCHAR), 2) as cod_estado,
            COUNT(DISTINCT idt_imovel) as total_cars
        FROM regularizacao_ambiental.car_imoveis
        WHERE dat_criacao IS NOT NULL
            AND EXTRACT(YEAR FROM dat_criacao) BETWEEN 2014 AND 2025
        GROUP BY EXTRACT(YEAR FROM dat_criacao), LEFT(CAST(idt_municipio AS VARCHAR), 2)
        ORDER BY ano_cadastro, cod_estado;
    """
    
    df = pd.read_sql(query, conn)
    
    # Mapear código de estado para sigla
    cod_to_uf = {
        '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
        '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
        '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
        '41': 'PR', '42': 'SC', '43': 'RS',
        '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
    }
    
    df['estado'] = df['cod_estado'].map(cod_to_uf)
    df['ano_cadastro'] = df['ano_cadastro'].astype(int)
    df['total_cars'] = df['total_cars'].astype(int)
    
    print(f"\n✓ {len(df)} registros encontrados")
    print(f"\nPrimeiros registros:")
    print(df.head(20))
    
    # Salvar
    df[['ano_cadastro', 'estado', 'total_cars']].to_csv('total_cars_por_ano_estado_banco.csv', index=False)
    print(f"\n✓ Dados salvos em: total_cars_por_ano_estado_banco.csv")
    
    # Agregado por ano (nacional)
    df_nacional = df.groupby('ano_cadastro')['total_cars'].sum().reset_index()
    print(f"\n📊 TOTAL NACIONAL POR ANO:")
    print(df_nacional.to_string(index=False))
    
    # Exemplo específico: MG
    df_mg = df[df['estado'] == 'MG'].sort_values('ano_cadastro')
    print(f"\n📊 TOTAL MG POR ANO:")
    print(df_mg[['ano_cadastro', 'total_cars']].to_string(index=False))
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✓ DADOS EXTRAÍDOS COM SUCESSO")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
