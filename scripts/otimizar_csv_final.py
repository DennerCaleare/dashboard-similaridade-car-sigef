"""
Script para otimizar o CSV aplicando conversões de tipos de dados
"""

import pandas as pd
import numpy as np
import os

# Caminho do arquivo
csv_path = os.path.join('data', 'similaridade_sicar_sigef_brasil.csv')

print("Carregando CSV original...")
df = pd.read_csv(csv_path)

print(f"Tamanho original: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
print(f"Total de registros: {len(df):,}")

# Otimizar tipos de dados
print("\nAplicando otimizações...")

# 1. int64 → int32 (colunas de IDs e contadores)
int_cols = df.select_dtypes(include=['int64']).columns
for col in int_cols:
    df[col] = df[col].astype('int32')
print(f"✓ Convertidas {len(int_cols)} colunas int64 → int32")

# 2. float64 → float32 (colunas de áreas e índices)
float_cols = df.select_dtypes(include=['float64']).columns
for col in float_cols:
    df[col] = df[col].astype('float32')
print(f"✓ Convertidas {len(float_cols)} colunas float64 → float32")

# 3. object → category (colunas repetitivas)
object_cols = df.select_dtypes(include=['object']).columns
for col in object_cols:
    # Converter para category se tiver menos de 50% de valores únicos
    num_unique = df[col].nunique()
    if num_unique / len(df) < 0.5:
        df[col] = df[col].astype('category')
        print(f"✓ Convertida {col}: object → category ({num_unique} valores únicos)")

print(f"\nTamanho otimizado: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
print(f"Redução de memória: {(1 - df.memory_usage(deep=True).sum() / pd.read_csv(csv_path).memory_usage(deep=True).sum()) * 100:.1f}%")

# Salvar CSV otimizado
print("\nSalvando CSV otimizado...")
df.to_csv(csv_path, index=False)
print("✓ Arquivo otimizado salvo!")

print("\nDtypes finais:")
print(df.dtypes)
