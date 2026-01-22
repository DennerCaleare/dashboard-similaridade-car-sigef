# Script de Deploy Simultaneo - GitHub + Hugging Face
# Uso: .\deploy.ps1 "mensagem do commit"

param(
    [string]$mensagem = "Update dashboard"
)

Write-Host "Iniciando deploy..." -ForegroundColor Cyan

# Verificar se ha mudancas
$status = git status --porcelain
if (-not $status) {
    Write-Host "Nenhuma mudanca para commitar" -ForegroundColor Green
    exit 0
}

# Adicionar todos os arquivos
Write-Host "Adicionando arquivos..." -ForegroundColor Yellow
git add .

# Remover CSV grande se existir (so usar ZIP)
if (Test-Path "data\similaridade_sicar_sigef_brasil.csv") {
    Write-Host "Removendo CSV grande (usando ZIP)..." -ForegroundColor Yellow
    git rm --cached data/similaridade_sicar_sigef_brasil.csv -f
}

# Commit
Write-Host "Fazendo commit: $mensagem" -ForegroundColor Yellow
git commit -m $mensagem

# Push para GitHub
Write-Host "Enviando para GitHub..." -ForegroundColor Magenta
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "GitHub atualizado!" -ForegroundColor Green
    
    # Push para Hugging Face
    Write-Host "Enviando para Hugging Face..." -ForegroundColor Magenta
    git push huggingface main --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Hugging Face atualizado!" -ForegroundColor Green
        Write-Host "" 
        Write-Host "Deploy concluido com sucesso!" -ForegroundColor Cyan
        Write-Host "   GitHub: https://github.com/DennerCaleare/dashboard-similaridade-car-sigef" -ForegroundColor Gray
        Write-Host "   Hugging Face: https://huggingface.co/spaces/DennerCaleare/dashboard" -ForegroundColor Gray
    } else {
        Write-Host "Erro ao enviar para Hugging Face" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Erro ao enviar para GitHub" -ForegroundColor Red
    exit 1
}
