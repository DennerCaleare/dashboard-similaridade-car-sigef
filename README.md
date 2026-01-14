# 📑 Dashboard Similaridade CAR-SIGEF
## Solução para Governo Federal - MGI

> **Dashboard de análise de conformidade fundiária que cruza 1,3+ milhões de registros CAR vs SIGEF. Desenvolvido para o Ministério da Gestão e Inovação (MGI) com performance otimizada via DuckDB. Servirá como base para deploy em plataforma federal.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](#)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/Database-DuckDB-informational.svg)](https://duckdb.org/)
[![MGI Federal](https://img.shields.io/badge/Governo-MGI%20Federal-red.svg)](#)

## 🚀 Acesso Rápido

**Desenvolvedor:** Denner Caleare | [GitHub](https://github.com/DennerCaleare) | [LinkedIn](https://linkedin.com/in/dennercaleare)

**Status:** 🚀 Pronto para deploy federal

---

## 📚 O Desafio do MGI

O Ministério da Gestão precisava de uma forma de:
- 📊 Cruzar 1,3 milhões de registros de CAR com SIGEF
- 🔍 Identificar incongruências e riscos fundiários
- 🎯 Analisar por CPF/CNPJ (titularidade)
- 💺 Apresentar risco territorial de forma visual
- ⚡ Fazer tudo com alta performance

## ✨ A Solução que Entreguei

**Dashboard com 17+ visualizações especializadas:**

### 📊 Análise de Conformidade
- 💫 **Matriz de Confiabilidade** (Mosaic Plot)
  - Cruzamento: Titularidade (CPF igual?) vs Similaridade Espacial (Índice Jaccard)
  - Identifica: Maturidade Alta | Erro Técnico | Risco Jurídico | Crítico

- 📈 **Matriz de Maturidade Fundiária** (Scatter)
  - Eixo X: % Similaridade Espacial
  - Eixo Y: % Conformidade Titular
  - Bolhas por volume de CARs
  - Cores por Região

### 🔍 Filtros Avançados
- Por UF, região, tamanho do imóvel
- Por status de compatibilidade
- Por faixa de Índice Jaccard
- Busca por Código SNISB

### 📈 Visualizações Estratégicas
- Histogramas e KDE de similaridade
- Análise de densidade por tamanho
- Evolução temporal
- Áreas de risco geográfico

## 📙 Índice de Jaccard (Metodologia)

**Fórmula:** `J(A,B) = (A ∩ B) / (A ∪ B)` = Área de Interseção / Área da União

**Interpretação:**
- 🙋 **85-100%**: Alta confiabilidade ✅ (monitorar)
- 😭 **50-85%**: Atenção requerida ⚠️ (retificar)
- 😨 **0-50%**: Divergência significativa ❌ (reestruturar)

## 🛠️ Stack Técnico (Otimizado)

```python
Streamlit 1.32+         # Framework web responsivo
DuckDB                 # Motor SQL in-memory de alta performance
Pandas 2.0+            # Processamento de dados
GeoPandas 0.14+        # Análise geoespacial
Matplotlib/Seaborn     # Visualizações customizadas
Statsmodels            # Mosaic plots e análise estatística
shapely 2.0+           # Geometrias espaciais
Python 3.11+           # Linguagem
```

## 🎛️ Performance & Escala

| Métrica | Valor |
|---------|-------|
| Total de registros | 1.3+ milhões |
| Tempo de query | < 2s |
| Memória em uso | Otimizada para 4GB |
| Escalabilidade | Preparado para 5M+ registros |
| Cache | Inteligente por filtro |

## 📂 Estrutura do Projeto

```
dashboard-similaridade-car-sigef/
├── app.py                              # Aplicação principal
├── requirements.txt                   # Dependências
├── README.md                          # Este arquivo
├── .streamlit/
│   └── config.toml                    # Configurações Streamlit
├── data/
│   └── similaridade_sicar_sigef_brasil.csv
├── src/
│   ├── config/
│   │   ├── constants.py              # Constantes globais
│   │   └── styles.py               # Estilos CSS
│   ├── utils/
│   │   ├── database.py             # Conexao DuckDB
│   │   ├── filters.py              # Filtros interativos
│   │   └── visualizations.py       # Gráficos
│   └── __init__.py
├── .env.example                       # Variáveis de ambiente
├── LICENSE                           # MIT License
└── .gitignore
```

## 🚀 Como Usar

### Instalação
```bash
git clone https://github.com/DennerCaleare/dashboard-similaridade-car-sigef.git
cd dashboard-similaridade-car-sigef
pip install -r requirements.txt
streamlit run app.py
```

### Arquivo de Dados
Certifique-se que o CSV está em:
```
data/similaridade_sicar_sigef_brasil.csv
```

## 📁 Saídas do Dashboard

- 📋 Tabelas paginadas com 50 registros
- 📈 17+ visualizações especializadas
- 💤 Filtros dinâmicos em tempo real
- 📄 Export em Excel, CSV, JSON
- 💺 Insights de risco por região

## 📙 Impacto para MGI

✅ **Conformidade** - Identifica incongruências CAR vs SIGEF
✅ **Risco** - Mapeia áreas de má qualidade cadastral
✅ **Decisão** - Suporta estratégias de retificação
✅ **Escalabilidade** - Pronto para integração com sistemas federais
✅ **Documentação** - Metodologia clara para replicação

## 👨‍💻 Desenvolvido por

**Denner Caleare**

- 🌟 Especialista em dashboards para governo
- 📚 Performance expert (DuckDB, Streamlit)
- 💼 Agência Zetta - UFLA

**Contato:**
- [GitHub](https://github.com/DennerCaleare)
- [LinkedIn](https://linkedin.com/in/dennercaleare)

## 📝 Licença

MIT License - Desenvolvido para Ministério da Gestão e Inovação (MGI)

---

**Desenvolvido com ❤️ em Lavras, MG | Agência Zetta - UFLA**
