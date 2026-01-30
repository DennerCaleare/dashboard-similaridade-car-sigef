# 🛠️ Comandos Úteis - Dashboard Similaridade CAR-SIGEF

## 🚀 Desenvolvimento Local

### Iniciar aplicação
```bash
streamlit run app.py
```

### Instalar dependências
```bash
pip install -r requirements.txt
```

### Atualizar dependências
```bash
pip freeze > requirements.txt
```

## 🧪 Testes e Validação

### Verificar imports
```python
python -c "from src.utils import *; from src.config import *; print('✓ Imports OK')"
```

### Verificar dataset
```python
python -c "import pandas as pd; df=pd.read_csv('data/similaridade_sicar_sigef_brasil.csv', nrows=10); print(f'✓ CSV OK - {len(df.columns)} colunas')"
```

### Testar DuckDB
```python
python -c "import duckdb; conn=duckdb.connect(':memory:'); print('✓ DuckDB OK')"
```

## 📦 Git

### Status e commit
```bash
git status
git add .
git commit -m "feat: descrição da mudança"
git push origin main
```

### Ver mudanças
```bash
git diff
git log --oneline -10
```

### Limpar arquivos não rastreados
```bash
git clean -fd
```

## 🧹 Manutenção

### Remover cache Python
```bash
# PowerShell
Get-ChildItem -Path . -Include __pycache__,*.pyc -Recurse -Force | Remove-Item -Recurse -Force

# Bash
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Verificar tamanho de arquivos grandes
```bash
# PowerShell
Get-ChildItem -Recurse | Where-Object {$_.Length -gt 10MB} | Select-Object FullName, @{Name="MB";Expression={[math]::Round($_.Length/1MB,2)}}

# Bash
find . -type f -size +10M -exec ls -lh {} \;
```

### Limpar notebooks
```bash
# PowerShell
jupyter nbconvert --clear-output --inplace notebooks/*.ipynb

# Bash
jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
```

## 📊 Análise de Código

### Contar linhas de código
```bash
# PowerShell
(Get-Content app.py).Count
(Get-ChildItem -Recurse -Include *.py | Get-Content | Measure-Object -Line).Lines

# Bash
wc -l app.py
find . -name "*.py" | xargs wc -l
```

### Verificar estilo (flake8)
```bash
pip install flake8
flake8 app.py --max-line-length=120
```

### Verificar tipos (mypy)
```bash
pip install mypy
mypy app.py --ignore-missing-imports
```

## 🔍 Debug

### Streamlit com debug
```bash
streamlit run app.py --logger.level=debug
```

### Ver logs em tempo real
```bash
streamlit run app.py 2>&1 | tee streamlit.log
```

### Profiling de performance
```python
# Adicionar no código
import cProfile
cProfile.run('funcao_lenta()', 'profile_stats')

# Analisar
python -m pstats profile_stats
```

## 📦 Deploy

### Testar requirements cloud
```bash
pip install -r requirements_cloud.txt
streamlit run app.py
```

### Verificar tamanho do repo
```bash
# PowerShell
Get-ChildItem -Recurse | Measure-Object -Property Length -Sum | Select-Object @{Name="Total MB";Expression={[math]::Round($_.Sum/1MB,2)}}

# Bash
du -sh .
```

### Compactar dataset
```bash
# PowerShell
Compress-Archive -Path "data\similaridade_sicar_sigef_brasil.csv" -DestinationPath "data\similaridade_sicar_sigef_brasil.zip" -Force

# Bash
zip -j data/similaridade_sicar_sigef_brasil.zip data/similaridade_sicar_sigef_brasil.csv
```

## 🔐 Segurança

### Verificar .env não está no Git
```bash
git ls-files | grep -i ".env"
# Não deve retornar nada
```

### Gerar .env.example
```bash
# PowerShell
Get-Content .env | ForEach-Object { $_ -replace '=.*', '=<valor_aqui>' } | Set-Content .env.example

# Bash
sed 's/=.*/=<valor_aqui>/' .env > .env.example
```

## 📝 Documentação

### Gerar documentação automática
```bash
pip install pdoc3
pdoc --html --output-dir docs src/
```

### Contar funções
```bash
# PowerShell
Select-String -Path *.py -Pattern "^def " | Measure-Object

# Bash
grep -r "^def " *.py | wc -l
```

## 🎨 Formatação

### Formatar código (black)
```bash
pip install black
black app.py src/
```

### Ordenar imports (isort)
```bash
pip install isort
isort app.py src/
```

## 📈 Monitoramento

### Ver uso de memória (Windows)
```powershell
Get-Process python | Select-Object Name, @{Name="Memory(MB)";Expression={[math]::Round($_.WS/1MB,2)}}
```

### Ver uso de CPU
```powershell
Get-Process python | Select-Object Name, CPU
```

## 🔄 Backup

### Backup rápido
```bash
# PowerShell
$date = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path . -DestinationPath "../backup_$date.zip" -Force

# Bash
tar -czf ../backup_$(date +%Y%m%d_%H%M%S).tar.gz .
```

---

**Dica:** Salve este arquivo para referência rápida! 💡
