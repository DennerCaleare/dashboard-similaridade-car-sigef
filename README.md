# 📊 Dashboard Similaridade CAR-SIGEF

<div align="center">
  <img src="assets/LogoZetta.png" alt="Agência Zetta" width="200"/>
  
  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
  [![DuckDB](https://img.shields.io/badge/DuckDB-Latest-yellow.svg)](https://duckdb.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

## 📖 Sobre o Projeto

Dashboard interativo desenvolvido pela **Agência Zetta** para análise exploratória de dados de similaridade espacial entre cadastros **CAR (Cadastro Ambiental Rural)** e **SIGEF (Sistema de Gestão Fundiária)**. 

O sistema utiliza o **Índice de Jaccard** para medir sobreposição geoespacial entre polígonos e identifica padrões de coerência entre titularidade (CPF/CNPJ) e similaridade geométrica, possibilitando análise de riscos fundiários e validação cadastral.

### 🎯 Principais Funcionalidades

- 📊 **Análise de 1,3+ milhões de registros** com performance otimizada via DuckDB
- 🔍 **Filtros dinâmicos interativos** por região, UF, tamanho do imóvel e status
- 📈 **17 visualizações especializadas** incluindo:
  - Matriz de Confiabilidade (Mosaic Plot)
  - Matriz de Maturidade Fundiária (Scatter com bolhas)
  - Análise temporal de evolução
  - Distribuições KDE e histogramas
  - Análise de densidade por tamanho e status
- ⚠️ **Insights de risco** cruzando validação de CPF e similaridade espacial
- ⚡ **Performance otimizada** com cache inteligente e queries SQL otimizadas

---

## 🚀 Tecnologias

### Core
- **[Streamlit](https://streamlit.io/)** - Framework para dashboard web interativo
- **[DuckDB](https://duckdb.org/)** - Motor SQL analítico in-memory de alta performance
- **[Pandas](https://pandas.pydata.org/)** - Manipulação e análise de dados
- **[NumPy](https://numpy.org/)** - Computação numérica

### Visualização
- **[Matplotlib](https://matplotlib.org/)** - Gráficos estáticos e customizados
- **[Seaborn](https://seaborn.pydata.org/)** - Visualizações estatísticas avançadas
- **[zetta_utils](https://github.com/datasciencezetta/dc_zetta_utils)** - Biblioteca customizada Zetta

### Análise Estatística
- **[statsmodels](https://www.statsmodels.org/)** - Mosaic plots e análise estatística

---

## 📁 Estrutura do Projeto

```
dashboard-similaridade-car-sigef/
│
├── app.py                          # 🎯 Aplicação principal Streamlit
├── requirements.txt                # 📦 Dependências Python
├── README.md                       # 📖 Documentação
├── LICENSE                         # ⚖️ Licença MIT
│
├── .streamlit/
│   └── config.toml                # ⚙️ Configurações do Streamlit
│
├── assets/                         # 🎨 Recursos visuais
│   ├── Logo.png
│   └── LogoZetta.png
│
├── data/                           # 💾 Dados do projeto
│   └── similaridade_sicar_sigef_brasil.csv
│
└── src/                            # 📂 Código-fonte modularizado
    ├── __init__.py
    ├── config/                    # ⚙️ Configurações e constantes
    │   ├── __init__.py
    │   ├── constants.py           # Constantes globais
    │   └── styles.py              # Estilos CSS customizados
    └── utils/                     # 🛠️ Utilitários
        ├── __init__.py
        ├── database.py            # Conexão DuckDB e queries
        ├── filters.py             # Filtros interativos
        └── visualizations.py      # Funções de visualização
```

---

## 🔧 Instalação e Execução

### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/DennerCaleare/dashboard-similaridade-car-sigef.git
cd dashboard-similaridade-car-sigef
```

### 2️⃣ Crie um ambiente virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Instale as dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure os dados

Certifique-se de que o arquivo CSV está no diretório correto:
```
data/similaridade_sicar_sigef_brasil.csv
```

### 5️⃣ Execute o dashboard

```bash
streamlit run app.py
```

O dashboard será aberto automaticamente em `http://localhost:8501` 🚀

---

## 📊 Visualizações Disponíveis

### 1. Panorama Regional e Operacional
- 📍 Distribuição percentual por UF
- 📊 Gráficos empilhados: Região, UF, Tamanho e Status vs Similaridade
- 📈 Densidade KDE por Tamanho e Status

### 2. Evolução Temporal
- 📅 Volume de CARs + Similaridade Mediana
- 📈 Evolução por Tamanho de Imóvel
- 🗺️ Evolução por Região

### 3. Diagnóstico de Similaridade
- 📊 Histograma de Índice Jaccard
- 🍩 Donut: Distribuição por faixa
- 📉 KDE: Discrepância de áreas

### 4. Análise de Risco
- ⚠️ **Matriz de Confiabilidade** (Mosaic Plot)
  - 🟢 Verde: Alta maturidade (CPF igual + alta similaridade)
  - 🟠 Laranja: Erro técnico ou risco jurídico
  - 🔴 Vermelho: Crítico

### 5. Maturidade Fundiária
- 🎯 **Scatter com bolhas** por UF
  - Eixo X: % Similaridade Espacial
  - Eixo Y: % Conformidade Titular
  - Tamanho: Volume de CARs
  - Cor: Região

---

## � Metodologia

### Índice de Jaccard

Mede a similaridade espacial entre dois polígonos:

$$
J(A, B) = \frac{|A \cap B|}{|A \cup B|} = \frac{\text{Área de Interseção}}{\text{Área da União}}
$$

**Interpretação:**
- **85-100%**: Alta confiabilidade ✅
- **50-85%**: Atenção requerida ⚠️
- **0-50%**: Divergência significativa ❌

### Quadrantes de Risco

| Titularidade | Similaridade | Classificação | Ação Recomendada |
|-------------|-------------|---------------|------------------|
| ✅ Igual | ✅ ≥ 85% | **Alta Maturidade** | Monitorar |
| ✅ Igual | ❌ < 85% | **Erro Técnico** | Retificar |
| ❌ Diferente | ✅ ≥ 85% | **Risco Jurídico** | Auditar |
| ❌ Diferente | ❌ < 85% | **Crítico** | Reestruturar |

---

## 🐛 Solução de Problemas

### ❌ Erro ao carregar dados

```python
# Verifique se o arquivo existe
import os
print(os.path.exists('data/similaridade_sicar_sigef_brasil.csv'))
```

### 🐌 Performance lenta

- ✅ Certifique-se de usar DuckDB para queries pesadas
- ✅ Cache está habilitado por padrão
- ✅ Reduza filtros para datasets menores durante testes

### 💾 Erro de memória

- Reduza o tamanho do dataset para testes locais
- No Streamlit Cloud, considere upgrade de plano

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

**Agência Zetta - UFLA**
- 🌐 Website: [agenciazetta.ufla.br](https://agenciazetta.ufla.br/)
- 💻 GitHub: [@datasciencezetta](https://github.com/datasciencezetta)

**Desenvolvedor Principal**
- Denner Caleare - [@DennerCaleare](https://github.com/DennerCaleare)

---

## 📧 Contato

Para dúvidas, sugestões ou parcerias:
- 📧 Email: contato@agenciazetta.com.br
- 💼 LinkedIn: [Agência Zetta](https://www.linkedin.com/company/agenciazetta)

---

## 🙏 Agradecimentos

- Equipe do projeto MGI (Mapeamento Geo-Identitário)
- Ministério da Gestão e Inovação
- UFLA - Universidade Federal de Lavras

---

<div align="center">
  <strong>Desenvolvido com ❤️ pela Agência Zetta</strong>
</div>
