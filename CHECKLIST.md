# 📋 Checklist de Deploy no Streamlit Cloud

## ✅ Alterações Implementadas

### 1. **Código atualizado** 
- [x] `src/utils/__init__.py` - Descompactação automática do ZIP
- [x] `.gitignore` - Ignora CSV original, mantém ZIP
- [x] Teste local bem-sucedido ✅

### 2. **Arquivos criados**
- [x] `data/similaridade_sicar_sigef_brasil.zip` (80.4 MB)
- [x] `DEPLOY.md` - Guia completo de deploy
- [x] `test_unzip.py` - Script de teste (pode deletar depois)

### 3. **Documentação atualizada**
- [x] `README.md` - Referência ao DEPLOY.md

---

## 🚀 Próximos Passos para Deploy

### Passo 1: Commit e Push

```powershell
# No PowerShell, dentro da pasta do projeto
cd "c:\Users\Zetta\Documents\Códigos\Similaridade"

# Adicionar arquivos ao Git
git add data/similaridade_sicar_sigef_brasil.zip
git add src/utils/__init__.py
git add .gitignore
git add DEPLOY.md
git add README.md

# Verificar o que vai ser commitado
git status

# Fazer commit
git commit -m "🚀 Prepara deploy com dados compactados (80MB)

- Adiciona ZIP compactado dos dados (271MB → 80MB)
- Implementa descompactação automática no primeiro uso
- Atualiza .gitignore para ignorar CSV original
- Adiciona guia completo de deploy (DEPLOY.md)
- Código testado localmente e funcionando ✅"

# Enviar para o GitHub
git push origin main
```

### Passo 2: Verificar no GitHub

1. Acesse: https://github.com/DennerCaleare/dashboard-similaridade-car-sigef
2. Verifique se o arquivo aparece: `data/similaridade_sicar_sigef_brasil.zip`
3. Tamanho deve ser ~80 MB

### Passo 3: Deploy no Streamlit Cloud

1. Acesse: https://share.streamlit.io
2. Login com GitHub
3. Clique em "New app"
4. Configurar:
   - Repository: `DennerCaleare/dashboard-similaridade-car-sigef`
   - Branch: `main`
   - Main file path: `app.py`
   - Python version: `3.11`
5. Click "Deploy"!

### Passo 4: Aguardar Deploy

- ⏱️ Instalação de dependências: ~2 minutos
- 📦 Descompactação automática: ~10 segundos (apenas primeira vez)
- ✅ App online e funcionando!

---

## 🔍 Verificação de Sucesso

Quando o app estiver online, você deve ver:

1. ✅ Mensagem de inicialização do banco
2. ✅ Mensagem de descompactação (primeira vez apenas)
3. ✅ Dashboard carregando normalmente
4. ✅ Dados disponíveis para filtrar

Se aparecer erro "Table not found", verifique os logs do Streamlit Cloud.

---

## 🆘 Troubleshooting

### Erro: "arquivo ZIP muito grande"
- O arquivo tem 80MB, está dentro do limite
- Verifique se o Git LFS não está ativado (não precisa!)

### Erro: "Table with name similaridade does not exist"
- Verifique se o ZIP foi enviado corretamente
- Rode: `git ls-files data/` - deve mostrar o ZIP

### Erro: "Memory error" ao descompactar
- Streamlit Cloud tem 1GB RAM grátis
- Considere usar plano pago ou hospedar CSV externamente

---

## 📊 Estatísticas Finais

- **Arquivo original**: 271 MB
- **Arquivo compactado**: 80.4 MB
- **Redução**: 68.9%
- **Tempo descompactação**: ~10s
- **GitHub limit**: ✅ Dentro (< 100 MB)

---

## ✨ Pronto!

Agora é só fazer o push e o deploy! 🚀

**Comando rápido:**
```powershell
git add . ; git commit -m "🚀 Deploy ready" ; git push
```
