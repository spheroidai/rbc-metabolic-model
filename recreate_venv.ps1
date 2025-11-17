# Script pour recreer un venv fonctionnel
# Ferme tous les terminaux avec (venv) actif avant de lancer!

Write-Host ""
Write-Host "Recreation du venv RBC..." -ForegroundColor Cyan
Write-Host ""

# Tuer les processus Python du venv
Write-Host "1. Fermeture des processus Python du venv..." -ForegroundColor Yellow
Get-Process -Name python,pythonw -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*venv*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Supprimer ancien venv
Write-Host "2. Suppression ancien venv..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item "venv" -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path "venv") {
        Write-Host "   ERREUR: Impossible de supprimer venv/" -ForegroundColor Red
        Write-Host "   Ferme TOUS les terminaux et reessaie!" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "   OK - Ancien venv supprime" -ForegroundColor Green

# Verifier Python systeme
Write-Host ""
Write-Host "3. Verification Python systeme..." -ForegroundColor Yellow

# Chercher Python systeme (pas embedded)
$pythonPath = $null
$pythonPaths = @(
    "C:\Users\Jorgelindo\AppData\Local\Programs\Python\Python314\python.exe",
    "C:\Users\Jorgelindo\AppData\Local\Programs\Python\Python313\python.exe",
    "C:\Program Files\Python314\python.exe",
    "C:\Program Files\Python313\python.exe"
)

foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        $pythonPath = $path
        break
    }
}

if (-not $pythonPath) {
    Write-Host "   ERREUR: Python systeme non trouve" -ForegroundColor Red
    Write-Host "   Installe Python depuis: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

$pythonVersion = & $pythonPath --version 2>&1
Write-Host "   OK - $pythonVersion (at $pythonPath)" -ForegroundColor Green

# Creer nouveau venv
Write-Host ""
Write-Host "4. Creation nouveau venv..." -ForegroundColor Yellow
& $pythonPath -m venv venv
if (-not (Test-Path "venv/Scripts/python.exe")) {
    Write-Host "   ERREUR: Venv non cree" -ForegroundColor Red
    exit 1
}
Write-Host "   OK - Venv cree" -ForegroundColor Green

# Activer venv et installer packages
Write-Host ""
Write-Host "5. Installation des packages..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
& ".\venv\Scripts\pip.exe" install -r requirements.txt

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  VENV PRET!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Pour activer:" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pour tester:" -ForegroundColor White
Write-Host "  python src/main.py --help" -ForegroundColor Yellow
Write-Host ""
