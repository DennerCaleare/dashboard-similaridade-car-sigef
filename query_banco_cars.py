"""
Script para buscar o total de CARs cadastrados por ano no banco MGI
"""
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco
DB_CONFIG = {
    'host': os.getenv('MGI_HOST'),
    'port': os.getenv('MGI_PORT'),
    'database': os.getenv('MGI_DATABASE'),
    'user': os.getenv('MGI_USER'),
    'password': os.getenv('MGI_PASSWORD')
}

print("=" * 70)
print("CONSULTANDO TOTAL DE CARs CADASTRADOS POR ANO NO BANCO MGI")
print("=" * 70)

try:
    # Conectar ao banco
    print("\n1. Conectando ao banco de dados...")
    conn = psycopg2.connect(**DB_CONFIG)
    print(f"   ✓ Conectado a {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # Listar tabelas disponíveis
    print("\n2. Listando tabelas disponíveis...")
    query_tables = """
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_name LIKE '%car%' OR table_name LIKE '%sicar%'
        ORDER BY table_schema, table_name
        LIMIT 20;
    """
    df_tables = pd.read_sql(query_tables, conn)
    print(f"\n   Tabelas relacionadas a CAR:")
    for _, row in df_tables.iterrows():
        print(f"   - {row['table_schema']}.{row['table_name']}")
    
    # Tentar query para obter total de CARs por ano
    print("\n3. Tentando consultar total de CARs por ano...")
    
    # Query 1: Tentar em tabela de similaridade
    try:
        query_car_ano = """
            SELECT 
                EXTRACT(YEAR FROM data_cadastro_imovel) as ano_cadastro,
                COUNT(DISTINCT cod_imovel) as total_cars,
                estado,
                regiao
            FROM public.similaridade_sicar_sigef
            WHERE data_cadastro_imovel IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM data_cadastro_imovel), estado, regiao
            ORDER BY ano_cadastro, estado
            LIMIT 100;
        """
        df_resultado = pd.read_sql(query_car_ano, conn)
        
        if not df_resultado.empty:
            print("\n   ✓ Dados encontrados na tabela de similaridade!")
            print(f"\n   Primeiras linhas:")
            print(df_resultado.head(20).to_string(index=False))
            
            # Salvar resultado
            df_resultado.to_csv('total_cars_por_ano_estado_banco.csv', index=False)
            print(f"\n   ✓ Dados salvos em: total_cars_por_ano_estado_banco.csv")
            
            # Agregado nacional
            df_nacional = df_resultado.groupby('ano_cadastro')['total_cars'].sum().reset_index()
            print(f"\n   Total nacional por ano:")
            print(df_nacional.to_string(index=False))
            
    except Exception as e:
        print(f"\n   ⚠ Erro na query de similaridade: {e}")
        print(f"\n   Tentando buscar em outras tabelas...")
        
        # Listar colunas de tabelas CAR
        query_cols = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name LIKE '%car%' 
            LIMIT 50;
        """
        df_cols = pd.read_sql(query_cols, conn)
        print(f"\n   Colunas disponíveis:")
        print(df_cols.to_string(index=False))
    
    conn.close()
    print("\n" + "=" * 70)
    print("✓ CONSULTA CONCLUÍDA")
    print("=" * 70)
    
except psycopg2.OperationalError as e:
    print(f"\n❌ Erro de conexão: {e}")
    print("\nVerifique:")
    print("  - As credenciais no arquivo .env")
    print("  - Se o servidor está acessível")
    print("  - Se a VPN está conectada (se necessário)")
    
except Exception as e:
    print(f"\n❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
