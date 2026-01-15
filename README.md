# � Dashboard Similaridade CAR-SIGEF
## Solução para Governo Federal - MGI

> **Dashboard de análise de conformidade fundiária que cruza 1,3+ milhões de registros CAR vs SIGEF. Desenvolvido para o Ministério da Gestão e Inovação (MGI) com performance otimizada via DuckDB.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](#)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/Database-DuckDB-informational.svg)](https://duckdb.org/)
[![MGI Federal](https://img.shields.io/badge/Governo-MGI%20Federal-red.svg)](#)

## 🚀 Acesso Rápido

**Desenvolvedor:** Denner Caleare | [GitHub](https://github.com/DennerCaleare) | [LinkedIn](https://linkedin.com/in/dennercaleare)

**Status:** ✅ Versão estável - Pronta para produção

**Última atualização:** Janeiro 2026

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
Streamlit 1.49+         # Framework web responsivo
DuckDB 1.4+            # Motor SQL in-memory de alta performance
Pandas 2.3+            # Processamento de dados
Matplotlib/Seaborn     # Visualizações customizadas
Statsmodels 0.14+      # Mosaic plots e análise estatística
Python 3.11+           # Linguagem base
Zetta Utils            # Biblioteca customizada de visualizações
```

## 🎛️ Performance & Escala

| Métrica | Valor |
|---------|-------|
| Total de registros | 1.3+ milhões |
| Tempo de query | < 2s |
| Memória otimizada | 4GB recomendado |
| Escalabilidade | Preparado para 5M+ registros |
| Cache | Inteligente por filtro |
| Queries SQL | Agregações otimizadas in-memory |

## 📂 Estrutura do Projeto

```
dashboard-similaridade-car-sigef/
├── app.py                              # Aplicação principal
├── requirements.txt                    # Dependências (desenvolvimento local)
├── requirements_cloud.txt              # Dependências (Streamlit Cloud)
├── README.md                           # Este arquivo
├── LICENSE                             # MIT License
├── .gitignore                          # Arquivos ignorados pelo Git
├── .streamlit/
│   └── config.toml                     # Configurações do Streamlit
├── assets/
│   └── LogoZetta.png                   # Logo da Agência Zetta
├── data/
│   └── similaridade_sicar_sigef_brasil.csv  # Dataset principal
└── src/
    ├── __init__.py
    ├── config/
    │   └── __init__.py                 # Constantes e configurações
    └── utils/
        └── __init__.py                 # Funções utilitárias
```

## 🚀 Como Usar

### Instalação Local
```bash
# Clonar o repositório
git clone https://github.com/DennerCaleare/dashboard-similaridade-car-sigef.git
cd dashboard-similaridade-car-sigef

# Criar ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate  # Windows
# ou
source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Executar o dashboard
streamlit run app.py
```

### Deploy no Streamlit Cloud
1. Faça fork deste repositório
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte sua conta do GitHub
4. Selecione o repositório e branch
5. Configure o arquivo principal como `app.py`
6. Use `requirements_cloud.txt` como arquivo de dependências
7. Deploy! 🚀

### Requisitos
- Python 3.11 ou superior
- 4GB de RAM (mínimo)
- Arquivo CSV de dados no caminho `data/similaridade_sicar_sigef_brasil.csv`

## � Saídas do Dashboard

- 📊 **17+ visualizações especializadas** para análise de conformidade
- 🎯 **Filtros dinâmicos em tempo real** por região, UF, tamanho e status
- 💡 **Métricas agregadas otimizadas** via SQL in-memory
- 📉 **Análises temporais** de evolução da similaridade
- 🗺️ **Matriz de maturidade fundiária** por estado
- 🎨 **Visualizações interativas** com gráficos responsivos
- ⚡ **Cache inteligente** para melhor performance

## 🎯 Impacto para MGI

✅ **Conformidade** - Identifica incongruências entre CAR e SIGEF  
✅ **Risco** - Mapeia áreas de baixa qualidade cadastral  
✅ **Decisão** - Suporta estratégias de retificação fundiária  
✅ **Escalabilidade** - Pronto para integração com sistemas federais  
✅ **Documentação** - Metodologia clara e replicável  
✅ **Performance** - Otimizado para grandes volumes de dados

## 👨‍💻 Desenvolvido por

**Denner Caleare**

- � Especialista em dashboards para governo
- ⚡ Performance expert (DuckDB, Streamlit, Python)
- 🏢 Agência Zetta - UFLA

**Contato:**
- GitHub: [@DennerCaleare](https://github.com/DennerCaleare)
- LinkedIn: [dennercaleare](https://linkedin.com/in/dennercaleare)

## 📝 Licença

MIT License - Projeto desenvolvido para o Ministério da Gestão e Inovação (MGI)

Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**Desenvolvido com ❤️ em Lavras, MG | Agência Zetta - UFLA**

**Janeiro 2026**
