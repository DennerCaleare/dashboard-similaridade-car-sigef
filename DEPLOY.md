# 🚀 Guia de Deploy no Streamlit Cloud - SOLUÇÃO IMPLEMENTADA ✅

## 📋 Problema Identificado e Resolvido

O arquivo `data/similaridade_sicar_sigef_brasil.csv` tem **271 MB**, mas o GitHub tem limite de **100 MB por arquivo**. 

## ✅ Solução Implementada: Compactação ZIP

O arquivo foi compactado para **80.4 MB** (redução de 68.9%), ficando **abaixo do limite do GitHub**! 🎉

### 🔧 O que foi feito:

1. ✅ **Arquivo ZIP criado**: `data/similaridade_sicar_sigef_brasil.zip` (80.4 MB)
2. ✅ **Código atualizado**: Descompactação automática na primeira execução
3. ✅ **.gitignore atualizado**: Ignora CSV original, mantém apenas o ZIP no repositório

### 📦 Como funciona:

1. Você faz commit e push do arquivo **ZIP** (80.4 MB) ✅
2. No Streamlit Cloud, o app detecta o ZIP
3. Na primeira execução, descompacta automaticamente para o CSV
4. Carrega os dados normalmente no DuckDB

## 🚀 Passos para Deploy

### 1. Adicionar o ZIP ao repositório

```powershell
# No PowerShell, dentro da pasta do projeto
git add data/similaridade_sicar_sigef_brasil.zip
git add .gitignore
git add src/utils/__init__.py
git commit -m "Adiciona dados compactados para deploy no Streamlit Cloud"
git push origin main
```

### 2. Fazer Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com sua conta GitHub
3. Clique em "New app"
4. Selecione o repositório: `DennerCaleare/dashboard-similaridade-car-sigef`
5. Branch: `main`
6. Main file: `app.py`
7. Clique em "Deploy"!

### 3. Aguardar o Deploy

- O Streamlit vai instalar as dependências (1-2 minutos)
- Na primeira execução, vai descompactar o ZIP (alguns segundos)
- Pronto! O dashboard estará online 🎉

## 🔄 Atualizando os Dados no Futuro

Quando precisar atualizar o arquivo de dados:

```powershell
# 1. Substituir o CSV na pasta data/
# 2. Recriar o ZIP
Compress-Archive -Path "data\similaridade_sicar_sigef_brasil.csv" -DestinationPath "data\similaridade_sicar_sigef_brasil.zip" -CompressionLevel Optimal -Force

# 3. Commit e push
git add data/similaridade_sicar_sigef_brasil.zip
git commit -m "Atualiza dados de similaridade"
git push origin main
```

O Streamlit Cloud vai detectar a mudança e fazer redeploy automaticamente!

## 🆘 Troubleshooting

### Problema: "Arquivo não encontrado" no Streamlit Cloud

**Solução**: Verifique se o ZIP foi commitado corretamente:
```powershell
git ls-files data/
# Deve mostrar: data/similaridade_sicar_sigef_brasil.zip
```

### Problema: Erro de memória ao descompactar

**Solução alternativa**: Use hospedagem externa (Google Drive, Dropbox, S3)
1. Faça upload do CSV
2. Configure a variável `DATA_URL` nos Secrets do Streamlit Cloud
3. O código já está preparado para fazer download automático

## 📊 Estatísticas

- **Arquivo original**: 271 MB
- **Arquivo compactado**: 80.4 MB  
- **Redução**: 68.9%
- **Tempo de descompactação**: ~5-10 segundos
- **Dentro do limite do GitHub**: ✅ Sim (< 100 MB)

---

## ✨ Pronto para Deploy!

O código está totalmente preparado. Basta fazer o commit e push do arquivo ZIP! 🚀

