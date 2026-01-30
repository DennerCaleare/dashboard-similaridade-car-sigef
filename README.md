# 🗺️ Dashboard Similaridade CAR-SIGEF

## Análise Espacial de Sobreposições Fundiárias

> **Dashboard interativo para análise de similaridade espacial entre registros do Cadastro Ambiental Rural (CAR) e Sistema de Gestão Fundiária (SIGEF). Desenvolvido para apoiar decisões estratégicas do Ministério da Gestão e Inovação.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dashboard-similaridade-car-sigef.streamlit.app/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MGI - Gov](https://img.shields.io/badge/Desenvolvido%20para-MGI%20Federal-green.svg)](#)

## 🚀 Acesso Rápido

**Veja em ação:** [Dashboard Online](https://dashboard-similaridade-car-sigef.streamlit.app/)

**Desenvolvedor:** Denner Caleare | [GitHub](https://github.com/DennerCaleare) | [LinkedIn](https://linkedin.com/in/dennercaleare)

---

## 📚 O Desafio

O Ministério da Gestão e Inovação precisava de uma solução para:

- 🔍 Analisar sobreposições espaciais entre CAR e SIGEF
- 📊 Identificar padrões de similaridade geométrica usando Índice de Jaccard
- 📈 Visualizar evolução temporal da qualidade dos cadastros
- 🗺️ Segmentar análises por região, estado, tamanho e status
- ⚡ Processar 1,3M+ registros com performance otimizada

## ✨ A Solução Entregue

**Dashboard analítico com processamento otimizado e visualizações interativas:**

### 🔍 Análise de Similaridade

- **Índice de Jaccard** para medir sobreposição espacial
- Faixas de similaridade: 0-25%, 25-50%, 50-85%, 85-100%
- Análise de titularidade (concordância de CPF/CNPJ)
- Detecção de discrepâncias de área entre cadastros

### 📊 Visualizações Multidimensionais

- **Gráfico temporal** - Evolução da similaridade mediana por ano
- **Análise regional** - Comparação entre as 5 regiões do Brasil
- **Distribuição por UF** - Ranking e análise estadual
- **Segmentação por tamanho** - Pequeno, Médio, Grande
- **Status dos imóveis** - Ativo, Pendente, Suspenso, Cancelado

### ⚡ Performance Otimizada

- **DuckDB in-memory** - Queries SQL otimizadas
- **Cache inteligente** - Carregamento instantâneo de filtros
- **1,3M+ registros** processados em segundos
- Agregações SQL para estatísticas rápidas

### 📈 Insights Principais

- Similaridade mediana nacional: **~88%**
- Taxa de concordância CPF/CNPJ: **~85%**
- Evolução temporal de 2014 a 2025
- 27 estados e 5 regiões analisados

## 📊 Estatísticas do Dataset

| Métrica             | Valor          |
| -------------------- | -------------- |
| Total de Registros   | 1.361.843      |
| Estados Analisados   | 27 UFs         |
| Período Temporal    | 2014-2025      |
| Similaridade Mediana | 88%            |
| Área Total (CAR)    | ~500M hectares |

## 🛠️ Stack Técnico

```python
Streamlit 1.32+         # Framework web interativo
DuckDB 0.9+            # Banco in-memory SQL otimizado
Plotly Express         # Visualizações interativas
Matplotlib/Seaborn     # Gráficos estatísticos
Pandas/NumPy           # Processamento de dados
GeoPandas              # Análise geoespacial
zetta_utils            # Biblioteca customizada
Python 3.9+            # Linguagem
```

## 📂 Estrutura do Projeto

```
dashboard-similaridade-car-sigef/
├── app.py                          # Aplicação principal Streamlit
├── requirements.txt                # Dependências Python
├── requirements_cloud.txt          # Dependências cloud (otimizado)
├── README.md                       # Este arquivo
├── LICENSE                         # Licença MIT
├── src/
│   ├── config/
│   │   └── __init__.py            # Configurações e constantes
│   └── utils/
│       └── __init__.py            # Funções DuckDB e visualização
├── data/
│   └── similaridade_sicar_sigef_brasil.csv  # Dataset principal
├── assets/                        # Logos e recursos visuais
├── notebooks/
│   └── eda_similaridade_car_sigef.ipynb    # Análise exploratória
└── DashboardMGI/                  # Documentação adicional
```

## 🚀 Como Usar

### Acessar Online

```
https://dashboard-similaridade-car-sigef.streamlit.app/
```

### Rodar Localmente

```bash
# Clonar repositório
git clone https://github.com/DennerCaleare/dashboard-similaridade-car-sigef.git
cd dashboard-similaridade-car-sigef

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py
```

### Requisitos

- Python 3.9 ou superior
- 8GB RAM (recomendado para dataset completo)
- Navegador moderno (Chrome, Firefox, Edge)

## 📊 Faixas de Similaridade (Índice de Jaccard)

| Faixa   | Interpretação         | Cor         |
| ------- | ----------------------- | ----------- |
| 85-100% | Similaridade Muito Alta | 🟢 Verde    |
| 50-85%  | Similaridade Alta       | 🔵 Azul     |
| 25-50%  | Similaridade Média     | 🟡 Amarelo  |
| 0-25%   | Similaridade Baixa      | 🔴 Vermelho |

**Índice de Jaccard:** Mede a razão entre área de interseção e união de dois polígonos.

- 100% = sobreposição perfeita
- 0% = nenhuma sobreposição

## 🎯 Funcionalidades Principais

### 1. Filtros Dinâmicos

- ✅ Seleção por **Região** (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)
- ✅ Filtro por **Estado** (27 UFs)
- ✅ Classificação por **Tamanho** (Pequeno, Médio, Grande)
- ✅ Status do Imóvel (Ativo, Pendente, Suspenso, Cancelado)

### 2. Análises Temporais

- 📈 Evolução da similaridade mediana (2014-2025)
- 📊 Número de CARs cadastrados por ano
- 🎯 Tendências por tamanho de imóvel
- 🗺️ Evolução por região geográfica

### 3. Análises Estatísticas

- 📊 Distribuições de similaridade (KDE plots)
- 🎯 Correlações entre variáveis
- 📈 Métricas agregadas por segmento
- 🗺️ Rankings estaduais e regionais

### 4. Visualizações Avançadas

- 🗺️ Mapas coropléticos regionais
- 📊 Gráficos de barras empilhadas
- 📈 Séries temporais com múltiplas linhas
- 🎨 Paletas de cores customizadas

## 📚 Fontes de Dados

### Dataset Principal

- **Origem:** Cruzamento CAR × SIGEF
- **Registros:** 1.361.843 correspondências espaciais
- **Período:** 2014-2025
- **Cobertura:** Todo o território nacional

### Variáveis Incluídas

- `indice_jaccard` - Similaridade espacial (0-1)
- `igualdade_cpf` - Concordância de titularidade
- `area_sicar_ha` - Área declarada no CAR (hectares)
- `area_sigef_agregado_ha` - Área no SIGEF (hectares)
- `class_tam_imovel` - Classificação por tamanho
- `status_imovel` - Status cadastral
- `regiao`, `estado` - Localização geográfica
- `ano_cadastro` - Ano de cadastramento

## 🎨 Paleta de Cores

```python
# Faixas de Jaccard
CORES_JACCARD = {
    '85-100%': '#10b981',  # Verde
    '50-85%':  '#3b82f6',  # Azul
    '25-50%':  '#f59e0b',  # Amarelo
    '0-25%':   '#ef4444'   # Vermelho
}

# Regiões
CORES_REGIAO = {
    'Norte':        '#8b5cf6',  # Roxo
    'Nordeste':     '#f59e0b',  # Laranja
    'Centro-Oeste': '#10b981',  # Verde
    'Sudeste':      '#3b82f6',  # Azul
    'Sul':          '#ec4899'   # Rosa
}
```

## 💡 Casos de Uso

### Para Gestores Públicos

- ✅ Identificar regiões com cadastros de baixa qualidade
- ✅ Monitorar evolução da qualidade ao longo do tempo
- ✅ Planejar ações de regularização fundiária
- ✅ Validar políticas de governança territorial

### Para Analistas de Dados

- ✅ Explorar distribuições estatísticas
- ✅ Identificar padrões e anomalias
- ✅ Gerar relatórios automatizados
- ✅ Exportar dados filtrados

### Para Pesquisadores

- ✅ Analisar qualidade de bases cadastrais
- ✅ Estudar sobreposições territoriais
- ✅ Validar metodologias de análise espacial
- ✅ Publicar insights baseados em dados reais

## 📈 Performance

| Operação                 | Tempo  |
| -------------------------- | ------ |
| Carregamento inicial       | ~3s    |
| Aplicação de filtros     | <1s    |
| Geração de gráficos     | <2s    |
| Queries agregadas (DuckDB) | <500ms |

*Testes realizados com dataset completo (1,3M registros)*

## 🔒 Segurança e Privacidade

- ✅ Dados agregados e anonimizados
- ✅ Sem informações pessoais identificáveis
- ✅ Conformidade com LGPD
- ✅ Código fonte aberto e auditável

## 📝 Changelog

### v2.0.0 (Janeiro 2026)

- ✨ Migração para DuckDB (50x mais rápido)
- ✨ Cache inteligente de filtros
- 🐛 Correção de barras temporais com filtros
- 📊 Novos gráficos de evolução por tamanho/região
- 🎨 Interface redesenhada

### v1.0.0 (Dezembro 2025)

- 🚀 Lançamento inicial
- 📊 Análises básicas de similaridade
- 🗺️ Filtros por região e UF

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 👨‍💻 Desenvolvido por

**Denner Caleare**

- 🌟 Especialista em dashboards geoespaciais e análise de dados
- 📊 Desenvolvedor de soluções para órgãos governamentais
- 🎓 Pesquisador em ciência de dados espaciais
- 💼 Agência Zetta - UFLA

**Contato:**

- GitHub: [@DennerCaleare](https://github.com/DennerCaleare)
- LinkedIn: [/in/dennercaleare](https://linkedin.com/in/dennercaleare)
- Email: denner.caleare@estudante.ufla.br

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos

- **Ministério da Gestão e Inovação (MGI)** - Demanda e validação
- **Agência Zetta** - Suporte técnico e infraestrutura
- **UFLA** - Apoio institucional
- **Comunidade Open Source** - Bibliotecas e ferramentas

---

**Desenvolvido com ❤️ em Lavras, MG | Janeiro 2026**

*"Transformando dados espaciais em insights estratégicos para a gestão fundiária brasileira"*
