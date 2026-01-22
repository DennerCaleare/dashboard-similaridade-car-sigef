# Script de Deploy Simultâneo - GitHub + Hugging Face
# Uso: .\deploy.ps1 "mensagem do commit"

param(
    [string]$mensagem = "Update dashboard"
)

Write-Host "🚀 Iniciando deploy..." -ForegroundColor Cyan

# Verificar se há mudanças
$status = git status --porcelain
if (-not $status) {
    Write-Host "✅ Nenhuma mudança para commitar" -ForegroundColor Green
    exit 0
}

# Adicionar todos os arquivos
Write-Host "📝 Adicionando arquivos..." -ForegroundColor Yellow
git add .

# Remover CSV grande se existir (só usar ZIP)
if (Test-Path "data\similaridade_sicar_sigef_brasil.csv") {
    Write-Host "🗑️  Removendo CSV grande (usando ZIP)..." -ForegroundColor Yellow
    git rm --cached data/similaridade_sicar_sigef_brasil.csv -f
}

# Commit
Write-Host "💾 Fazendo commit: $mensagem" -ForegroundColor Yellow
git commit -m $mensagem

# Push para GitHub
Write-Host "📤 Enviando para GitHub..." -ForegroundColor Magenta
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ GitHub atualizado!" -ForegroundColor Green
    
# Preparar README para Hugging Face
if (Test-Path "README_HF.md") {
    Write-Host "📄 Preparando README para Hugging Face..." -ForegroundColor Yellow
    Copy-Item README.md README_BACKUP.md -Force
    Copy-Item README_HF.md README.md -Force
    git add README.md
    git commit -m "Update README for Hugging Face" --no-verify
}

# Push para Hugging Face
Write-Host "📤 Enviando para Hugging Face..." -ForegroundColor Magenta
git push huggingface main --force

# Restaurar README original
if (Test-Path "README_BACKUP.md") {
    Copy-Item README_BACKUP.md README.md -Force
    Remove-Item README_BACKUP.md -Force
    git add README.md
    git commit -m "Restore original README" --no-verify
    git push origin main --no-verify
}
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Hugging Face atualizado!" -ForegroundColor Green
        Write-Host "" 
        Write-Host "🎉 Deploy concluído com sucesso!" -ForegroundColor Cyan
        Write-Host "   GitHub: https://github.com/DennerCaleare/dashboard-similaridade-car-sigef" -ForegroundColor Gray
        Write-Host "   Hugging Face: https://huggingface.co/spaces/DennerCaleare/dashboard" -ForegroundColor Gray
    } else {
        Write-Host "❌ Erro ao enviar para Hugging Face" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Erro ao enviar para GitHub" -ForegroundColor Red
    exit 1
}
