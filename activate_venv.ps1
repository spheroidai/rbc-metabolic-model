# Script d'activation rapide du venv RBC
# Usage: .\activate_venv.ps1

Write-Host ""
Write-Host "Activation du venv RBC..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERREUR: venv non trouve!" -ForegroundColor Red
    Write-Host "Lance: .\recreate_venv.ps1" -ForegroundColor Yellow
    exit 1
}

# Activer venv
& ".\venv\Scripts\Activate.ps1"

Write-Host "Venv active!" -ForegroundColor Green
Write-Host ""
Write-Host "Python: " -NoNewline -ForegroundColor White
python --version
Write-Host ""
Write-Host "Commandes utiles:" -ForegroundColor Cyan
Write-Host "  python src/main.py --help" -ForegroundColor Yellow
Write-Host "  python src/main.py --curve-fit 0.0 --ph-perturbation alkalosis" -ForegroundColor Yellow
Write-Host "  deactivate  # Pour desactiver le venv" -ForegroundColor Yellow
Write-Host ""
