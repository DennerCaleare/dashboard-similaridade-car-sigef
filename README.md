# Dashboard CAR-SIGEF: Análise de Similaridade Espacial

<div align="center">
  <img src="LogoZetta.png" alt="Agência Zetta" width="200"/>
  
  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
  [![DuckDB](https://img.shields.io/badge/DuckDB-Latest-yellow.svg)](https://duckdb.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

## 📋 Sobre o Projeto

Dashboard interativo desenvolvido para análise exploratória de dados de similaridade espacial entre cadastros **CAR (Cadastro Ambiental Rural)** e **SIGEF (Sistema de Gestão Fundiária)**. O sistema utiliza o **Índice de Jaccard** para medir a sobreposição geoespacial entre polígonos e identifica padrões de coerência entre titularidade (CPF) e similaridade geométrica.

### 🎯 Principais Funcionalidades

- **Análise de 1,3+ milhões de registros** em tempo real
- **Filtros dinâmicos** por região, UF, tamanho do imóvel e status
- **Matriz de risco** cruzando validação de CPF e similaridade espacial
- **Visualizações interativas** com gráficos de distribuição, correlação e dispersão
- **Sistema de paginação** para navegação em grandes volumes de dados
- **Exportação de dados** filtrados em formato CSV

## 🚀 Tecnologias Utilizadas

### Core
- **[Streamlit](https://streamlit.io/)** - Framework para criação do dashboard web
- **[DuckDB](https://duckdb.org/)** - Banco de dados analítico em memória para consultas SQL ultra-rápidas
- **[Pandas](https://pandas.pydata.org/)** - Manipulação e análise de dados
- **[NumPy](https://numpy.org/)** - Computação numérica de alta performance

### Visualização
- **[Matplotlib](https://matplotlib.org/)** - Criação de gráficos estáticos
- **[Seaborn](https://seaborn.pydata.org/)** - Visualizações estatísticas avançadas
- **[dc_zetta_utils](https://github.com/datasciencezetta/dc_zetta_utils)** - Biblioteca customizada para gráficos padronizados

### Análise Estatística
- **[SciPy](https://scipy.org/)** - Testes estatísticos (Jarque-Bera, Kruskal-Wallis)

## ⚡ Otimizações de Performance

O projeto implementa diversas estratégias para garantir performance excepcional:

### 1. DuckDB - Consultas SQL Diretas no CSV
```python
# Ao invés de carregar 1GB na memória:
df = pd.read_csv('dados.csv')  # ❌ Lento: 5-10s
df = df[df['uf'] == 'MG']      # ❌ Filtra depois

# Fazemos consultas SQL diretas:
df = con.execute("""
    SELECT * FROM 'dados.csv' 
    WHERE uf = 'MG'
""").df()  # ✅ Rápido: 0.5-1s
```

**Ganhos:**
- **10-20x mais rápido** no carregamento inicial
- **100-200x mais rápido** para agregações (COUNT, SUM, etc.)
- **95% menos memória** (50 MB vs 1 GB)

### 2. Otimização de Tipos de Dados
```python
# Conversões aplicadas:
int64 → int32    # -50% memória em IDs
float64 → float32  # -50% memória em áreas
object → category  # -70-90% em colunas repetitivas
```

**Resultado:**
- De **991 MB** → **367 MB** (-63% de memória)
- Carregamento **2-3x mais rápido**

### 3. Cache Inteligente
Todas as funções críticas usam `@st.cache_data` para evitar recálculos desnecessários.

## 📊 Estrutura do Dashboard

### Aba 1: Visão Geral
- Histograma de distribuição do Índice Jaccard
- Gráfico de rosca por faixa de similaridade
- Distribuição geográfica por UF
- Estatísticas descritivas

### Aba 2: Matriz de Risco
- Cruzamento **Titularidade (CPF) × Similaridade Espacial (≥85%)**
- 4 categorias:
  - 🟢 **Coerente**: CPF igual + Geo ≥85%
  - 🟠 **Incoerência Espacial**: CPF igual + Geo <85%
  - 🟡 **Incoerência de Titularidade**: CPF diferente + Geo ≥85%
  - 🔴 **Incoerente**: CPF diferente + Geo <85%

### Aba 3: Análise Espacial
- Scatter plot de discrepância: Área CAR vs Área SIGEF
- Box plot e violin plot de similaridade por região
- Análise de tendências espaciais

### Aba 4: Distribuições
- Análise por tamanho do imóvel (Pequeno, Médio, Grande)
- Gráficos de distribuição por status (Ativo, Cancelado, Pendente, Suspenso)
- Teste de Kruskal-Wallis para diferença entre grupos

### Aba 5: Análise Detalhada
- Stacked bar plots por status e UF
- Matriz de correlação entre variáveis numéricas
- Validação do cálculo do Índice Jaccard

### Aba 6: Dados
- Navegação paginada (50 registros por página)
- Visualização de todas as colunas
- Exportação de dados filtrados

## 🔧 Instalação e Configuração

### Pré-requisitos
- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)

### Passo 1: Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/NOME_DO_REPO.git
cd NOME_DO_REPO
```

### Passo 2: Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### Passo 3: Instale as dependências
```bash
pip install -r requirements.txt
```

### Passo 4: Configure variáveis de ambiente (opcional)
Se for usar conexão com banco de dados PostgreSQL, crie um arquivo `.env`:
```env
DB_HOST=seu_host
DB_PORT=5432
DB_NAME=seu_database
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

### Passo 5: Adicione os dados
Coloque o arquivo CSV `similaridade_sicar_sigef_brasil.csv` na pasta `data/`:
```bash
# Coloque seu arquivo CSV aqui
data/similaridade_sicar_sigef_brasil.csv
```

**Nota**: O arquivo CSV não está incluído no repositório por ser muito grande (>1GB). Entre em contato para obter o dataset.

### Passo 6: Execute o dashboard
```bash
streamlit run app.py
```

O dashboard abrirá automaticamente em `http://localhost:8501`

## 📁 Estrutura do Projeto

```
car-sigef-similarity-dashboard/
├── app.py                              # Aplicação principal do dashboard
├── assets/                             # Recursos estáticos
│   ├── Logo.png                        # Logo para favicon
│   └── LogoZetta.png                   # Logo da Agência Zetta
├── data/                               # Arquivos de dados
│   ├── .gitkeep                        # Mantém pasta no Git
│   └── similaridade_sicar_sigef_brasil.csv  # Dataset principal (não versionado)
├── notebooks/                          # Análises exploratórias
│   └── eda_similaridade_car_sigef.ipynb
├── scripts/                            # Scripts auxiliares
│   └── otimizar_csv_final.py           # Otimização de tipos de dados
├── requirements.txt                    # Dependências do projeto
├── .gitignore                          # Arquivos ignorados pelo Git
├── .env.example                        # Exemplo de configuração de ambiente
├── LICENSE                             # Licença MIT
└── README.md                           # Documentação do projeto
```

## 🗄️ Otimização do CSV (Opcional)

Para otimizar o arquivo CSV original, execute:

```bash
python scripts/otimizar_csv_final.py
```

Este script aplica as seguintes otimizações:
- Converte `int64 → int32`
- Converte `float64 → float32`
- Converte `object → category` em colunas repetitivas
- Reduz o tamanho do arquivo em ~63%

## 📈 Métricas de Performance

| Operação | Pandas | DuckDB | Ganho |
|----------|--------|--------|-------|
| Carregamento completo | 5-10s | 0.5s | **10-20x** |
| Filtrar 1 UF | 5-10s | 0.8s | **6-12x** |
| COUNT(*) | 5-10s | 0.05s | **100-200x** |
| Valores únicos | 5-10s | 0.2s | **25-50x** |
| Memória (sem filtros) | 930 MB | 50 MB | **-95%** |
| Memória (1 UF filtrada) | 930 MB | 35 MB | **-96%** |

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abrir um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

**Agência Zetta - UFLA**

- Website: [https://agenciazetta.ufla.br/](https://agenciazetta.ufla.br/)
- GitHub: [@datasciencezetta](https://github.com/datasciencezetta)

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através do site da [Agência Zetta](https://agenciazetta.ufla.br/).

---

<div align="center">
  Desenvolvido com ❤️ pela <a href="https://agenciazetta.ufla.br/">Agência Zetta</a>
</div>
