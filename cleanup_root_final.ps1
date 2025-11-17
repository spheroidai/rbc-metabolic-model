# Nettoyage Racine - Final
# Supprime scripts de nettoyage obsoletes

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Nettoyage Racine - Final" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$scriptsToRemove = @(
    "cleanup_src_phase1.ps1",
    "cleanup_src_phase2.ps1",
    "cleanup_src_step1.ps1"
)

$optionalFiles = @(
    "src_cleanup_analysis.md",
    "root_files_analysis.md"
)

Write-Host "SCRIPTS OBSOLETES (taches terminees):" -ForegroundColor Yellow
Write-Host ""

$existingScripts = @()
$totalSize = 0

foreach ($file in $scriptsToRemove) {
    if (Test-Path $file) {
        $item = Get-Item $file
        $sizeKB = [math]::Round($item.Length / 1KB, 2)
        $totalSize += $sizeKB
        
        $existingScripts += [PSCustomObject]@{
            Fichier = $item.Name
            Taille = "$sizeKB KB"
            Status = "Tache terminee"
        }
    }
}

if ($existingScripts.Count -gt 0) {
    $existingScripts | Format-Table -AutoSize
    Write-Host "Total scripts: $($existingScripts.Count) fichiers, $([math]::Round($totalSize, 2)) KB" -ForegroundColor White
} else {
    Write-Host "Aucun script obsolete trouve" -ForegroundColor Green
}

Write-Host ""
Write-Host "FICHIERS TEMPORAIRES (optionnels):" -ForegroundColor Yellow
Write-Host ""

$existingOptional = @()
$optionalSize = 0

foreach ($file in $optionalFiles) {
    if (Test-Path $file) {
        $item = Get-Item $file
        $sizeKB = [math]::Round($item.Length / 1KB, 2)
        $optionalSize += $sizeKB
        
        $existingOptional += [PSCustomObject]@{
            Fichier = $item.Name
            Taille = "$sizeKB KB"
            Description = switch ($item.Name) {
                "src_cleanup_analysis.md" { "Analyse src/ (Phase 1/2)" }
                "root_files_analysis.md" { "Analyse racine (actuelle)" }
                default { "Documentation temporaire" }
            }
        }
    }
}

if ($existingOptional.Count -gt 0) {
    $existingOptional | Format-Table -AutoSize
    Write-Host "Total optionnels: $($existingOptional.Count) fichiers, $([math]::Round($optionalSize, 2)) KB" -ForegroundColor White
} else {
    Write-Host "Aucun fichier optionnel trouve" -ForegroundColor Green
}

Write-Host ""
Write-Host "FICHIERS ESSENTIELS PRESERVES:" -ForegroundColor Green
Write-Host "  - Data_Brodbar_et_al_exp.xlsx (donnees experimentales)" -ForegroundColor White
Write-Host "  - Data_Brodbar_et_al_exp_fitted_params.csv (parametres fitting)" -ForegroundColor White
Write-Host "  - Initial_conditions_JA_Final.xls (conditions initiales)" -ForegroundColor White
Write-Host "  - README.md (documentation)" -ForegroundColor White
Write-Host "  - requirements.txt (dependances)" -ForegroundColor White
Write-Host "  - activate_venv.ps1 (activation venv)" -ForegroundColor White
Write-Host "  - recreate_venv.ps1 (recreation venv)" -ForegroundColor White
Write-Host ""

$totalFiles = $existingScripts.Count + $existingOptional.Count
$totalSizeKB = $totalSize + $optionalSize

if ($totalFiles -eq 0) {
    Write-Host "OK - Racine deja nettoyee!" -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host "TOTAL A SUPPRIMER:" -ForegroundColor Cyan
Write-Host "  - Scripts obsoletes: $($existingScripts.Count) fichiers" -ForegroundColor White
Write-Host "  - Fichiers temporaires: $($existingOptional.Count) fichiers" -ForegroundColor White
Write-Host "  - Taille totale: $([math]::Round($totalSizeKB, 2)) KB" -ForegroundColor White
Write-Host ""

Write-Host "OPTIONS:" -ForegroundColor Cyan
Write-Host "  1 - Supprimer TOUT (scripts + temporaires)" -ForegroundColor Yellow
Write-Host "  2 - Supprimer scripts SEULEMENT (garder analyses .md)" -ForegroundColor Yellow
Write-Host "  3 - Annuler" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "Choisir une option (1/2/3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "Suppression de TOUT..." -ForegroundColor Yellow
    Write-Host ""
    
    $allFiles = $scriptsToRemove + $optionalFiles
    $successCount = 0
    $failCount = 0
    
    foreach ($file in $allFiles) {
        if (Test-Path $file) {
            try {
                Remove-Item -Path $file -Force -ErrorAction Stop
                Write-Host "  OK - $file" -ForegroundColor Green
                $successCount++
            } catch {
                Write-Host "  ERREUR - $file : $($_.Exception.Message)" -ForegroundColor Red
                $failCount++
            }
        }
    }
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Nettoyage Racine termine!" -ForegroundColor Green
    Write-Host "  Supprimes: $successCount fichiers" -ForegroundColor Green
    Write-Host "  Erreurs: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
    Write-Host "  Espace libere: ~$([math]::Round($totalSizeKB, 2)) KB" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Compter fichiers restants
    $remainingFiles = (Get-ChildItem -File | Where-Object { $_.Extension -ne ".ps1" -or $_.Name -eq "activate_venv.ps1" -or $_.Name -eq "recreate_venv.ps1" }).Count
    Write-Host "Fichiers essentiels a la racine: $remainingFiles" -ForegroundColor Green
    Write-Host ""
    
} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "Suppression des scripts SEULEMENT..." -ForegroundColor Yellow
    Write-Host ""
    
    $successCount = 0
    $failCount = 0
    
    foreach ($file in $scriptsToRemove) {
        if (Test-Path $file) {
            try {
                Remove-Item -Path $file -Force -ErrorAction Stop
                Write-Host "  OK - $file" -ForegroundColor Green
                $successCount++
            } catch {
                Write-Host "  ERREUR - $file : $($_.Exception.Message)" -ForegroundColor Red
                $failCount++
            }
        }
    }
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Nettoyage Racine termine!" -ForegroundColor Green
    Write-Host "  Supprimes: $successCount scripts" -ForegroundColor Green
    Write-Host "  Erreurs: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })
    Write-Host "  Espace libere: ~$([math]::Round($totalSize, 2)) KB" -ForegroundColor Green
    Write-Host "  Fichiers .md gardes pour reference" -ForegroundColor Yellow
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "Nettoyage annule" -ForegroundColor Yellow
    Write-Host ""
}
