# Estrutura do Projeto

## 📁 Estrutura de Diretórios

```
dashboard-similaridade-car-sigef/
│
├── 📄 app.py                       # Aplicação principal Streamlit
├── 📄 requirements.txt             # Dependências Python (local)
├── 📄 requirements_cloud.txt       # Dependências otimizadas (cloud)
├── 📄 README.md                    # Documentação principal
├── 📄 LICENSE                      # Licença MIT
├── 📄 .gitignore                   # Arquivos ignorados pelo Git
├── 📄 .env.example                 # Exemplo de variáveis de ambiente
│
├── 📁 src/                         # Código fonte
│   ├── 📁 config/                  # Configurações
│   │   └── __init__.py            # Cores, constantes, labels
│   └── 📁 utils/                   # Utilitários
│       └── __init__.py            # Funções DuckDB, filtros, viz
│
├── 📁 data/                        # Dados
│   ├── .gitkeep                   # Mantém pasta no Git
│   ├── similaridade_sicar_sigef_brasil.csv   # Dataset principal
│   └── similaridade_sicar_sigef_brasil.zip   # Dataset compactado
│
├── 📁 notebooks/                   # Análises exploratórias
│   └── eda_similaridade_car_sigef.ipynb
│
├── 📁 assets/                      # Recursos visuais
│   └── logo_zetta.png             # Logo
│
├── 📁 .streamlit/                  # Configuração Streamlit
│   └── config.toml                # Tema e configurações
│
└── 📁 .devcontainer/              # Desenvolvimento em container
    └── devcontainer.json          # Config VSCode Dev Containers
```

## 📦 Arquivos Principais

### Aplicação
- **app.py** - Dashboard principal com toda a lógica de visualização

### Configuração
- **src/config/__init__.py** - Paletas de cores, labels, constantes
- **src/utils/__init__.py** - Funções DuckDB, filtros, visualizações

### Dados
- **data/similaridade_sicar_sigef_brasil.csv** - Dataset completo (1,3M registros)
- **data/similaridade_sicar_sigef_brasil.zip** - Versão compactada para deploy

### Documentação
- **README.md** - Documentação completa do projeto
- **notebooks/eda_similaridade_car_sigef.ipynb** - Análise exploratória

## 🚀 Fluxo de Dados

```
CSV/ZIP → DuckDB (in-memory) → Filtros → Visualizações
```

1. **Carregamento**: CSV é carregado no DuckDB (primeira execução)
2. **Cache**: Tabela fica em memória durante a sessão
3. **Queries**: Filtros executam queries SQL otimizadas
4. **Visualização**: Resultados são plotados com Plotly/Matplotlib

## 🔧 Arquivos de Configuração

### .gitignore
Ignora: .env, .venv, __pycache__, .DS_Store, dados sensíveis

### .env.example
Template para variáveis de ambiente (se necessário)

### requirements.txt
Dependências completas para desenvolvimento local

### requirements_cloud.txt
Dependências otimizadas para Streamlit Cloud

## 📝 Boas Práticas

### Commits
- Use mensagens descritivas
- Prefixos: `feat:`, `fix:`, `docs:`, `refactor:`

### Código
- Docstrings em todas as funções
- Type hints onde aplicável
- Comentários para lógica complexa

### Dados
- Nunca commitar arquivos .env
- CSV grande deve estar zipado no repositório
- Usar .gitkeep em pastas vazias necessárias
