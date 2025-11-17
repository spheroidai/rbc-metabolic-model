# 🧹 Plan de Nettoyage du Projet RBC

**Date:** 2025-11-15  
**Objectif:** Simplifier l'arborescence avant implémentation dashboard Streamlit

---

## 📊 Analyse Actuelle

**Racine du projet:** 170+ fichiers/dossiers  
**Taille estimée:** ~25 GB (avec Lib/, DLLs/, venv/)

---

## ✅ FICHIERS À GARDER (Essentiels)

### 📁 **Dossiers Core**
```
✓ src/                          # Code source principal
✓ data/ ou DATA_Brodbar/        # Données expérimentales
✓ Doc/                          # Documentation (si pertinente)
```

### 📄 **Fichiers Python Essentiels (Racine)**
```
✓ requirements.txt              # Dependencies
✓ bohr_dashboard.py             # Dashboard Bohr (utilisé)
✓ compare_bohr_scenarios.py     # Comparaison scénarios
✓ analyze_BPG_dynamics.py       # Analyse BPG
```

### 📄 **Documentation à Garder**
```
✓ pH_PROJECT_FINAL_COMPLETE.md      # Documentation principale
✓ README.md                          # Introduction projet
✓ BOHR_INTEGRATION_COMPLETE.md      # Doc Bohr effect
```

### 📁 **Résultats à Garder (html/)**
```
✓ html/brodbar_alkalosis_severe/    # Résultats alcalose (CORRECTED)
✓ html/brodbar_acidosis_severe/     # Résultats acidose (À VENIR)
```

### 📄 **Données Expérimentales**
```
✓ Data_Brodbar_et_al_exp.xlsx
✓ Data_Brodbar_et_al_exp_fitted_params.csv
✓ Initial_conditions_JA_Final.xls
```

---

## ❌ FICHIERS À SUPPRIMER

### 🗑️ **Scripts Temporaires/Debug (20 fichiers)**
```
❌ test_*.py                         # (6 fichiers) - Tests obsolètes
❌ debug_*.py                        # (4 fichiers) - Debug scripts
❌ check_pH_response.py             
❌ analyze_pH_flux_effects.py       # Redondant avec _early version
❌ analyze_pH_simulation.py         # Temporaire
❌ improve_eglc_fitting.py          # Obsolète
❌ regenerate_flux_pdf.py           # Temporaire
❌ get_initial_values.py            # Temporaire
❌ corrected_brodbar_mapping.py     # Obsolète
❌ create_production_v2.py          # Obsolète
❌ detailed_bohr_report.py          # Intégré dans dashboard
❌ monitor_simulations.py           # Temporaire
❌ quick_bohr_summary.py            # Temporaire
```

### 🗑️ **Fichiers Python de Build**
```
❌ python.exe                       # (106 KB)
❌ python3.dll                      # (73 KB)
❌ python313.dll                    # (6 MB)
❌ pythonw.exe                      # (104 KB)
❌ vcruntime140.dll                 # (120 KB)
❌ vcruntime140_1.dll               # (50 KB)
```

### 🗑️ **Dossiers Python Build (GROS!)**
```
❌ DLLs/                           # (43 items, ~50 MB)
❌ Lib/                            # (17291 items, ~500 MB)
❌ include/                        # (264 items, ~10 MB)
❌ libs/                           # (3 items)
❌ tcl/                            # (1012 items, ~50 MB)
❌ share/                          # (2 items)
❌ venv/                           # (vide mais inutile)
❌ __pycache__/                    # Cache Python
```

### 🗑️ **Anciens Résultats HTML**
```
❌ html/brodbar/                   # Résultat intermédiaire (à vérifier)
❌ html/brodbar_clean_mm/          # (vide)
❌ html/optimized/                 # Anciens tests
❌ html/original/                  # Anciens tests
❌ html/refactored/                # Anciens tests
❌ html/*.png                      # (44 fichiers) - Plots d'optimisation obsolètes
```

### 🗑️ **Documentation Redondante/Obsolète**
```
❌ AUTOMATED_CURVE_FITTING_DOCUMENTATION.md
❌ CURVE_FITTING_AND_FLUX_TRACKING_GUIDE.md
❌ CURVE_FITTING_IMPROVEMENTS.md
❌ CURVE_FITTING_USER_GUIDE.md
❌ ELECTRICAL_INTEGRATION_SUMMARY.md
❌ FLUX_VISUALIZATION_GUIDE.md
❌ GLYCOLYSIS_CURVE_FITTING_DOCUMENTATION.md
❌ IMPLEMENTATION_SUMMARY.md
❌ MODEL_IMPROVEMENTS.md
❌ MODEL_USAGE.md
❌ NEGATIVE_VALUES_CORRECTION.md
❌ OPTIMIZATION_RESULTS_EXPLAINED.md
❌ OPTION1_SIMULATION_GUIDE.md       # Intégré dans FINAL_COMPLETE
❌ OPTION2_VISUALIZATION_GUIDE.md    # Intégré dans FINAL_COMPLETE
❌ OPTION3_CALIBRATION_GUIDE.md      # Intégré dans FINAL_COMPLETE
❌ OPTION4_EXTENSIONS_GUIDE.md       # Intégré dans FINAL_COMPLETE
❌ PARAMETER_INJECTION_SUMMARY.md
❌ PARAMETER_OPTIMIZATION_README.md
❌ PHASE1_COMPLETE_SUMMARY.md
❌ PRODUCTION_*.md                   # (3 fichiers)
❌ SYSTEMATIC_OPTIMIZATION_SUMMARY.md
❌ TWO_APPROACHES_TO_CURVE_FITTING.md
❌ pH_PROJECT_COMPLETE_SUMMARY.md    # Superseded by FINAL_COMPLETE
❌ expected_bohr_differences.md      # Temporaire
```

### 🗑️ **Fichiers MATLAB Obsolètes (.m)**
```
❌ *.m                              # (25+ fichiers) - Ancien code MATLAB
```

### 🗑️ **Fichiers Excel/Data Redondants**
```
❌ DATA_Bardyn*.xls/xlsx           # (4 fichiers) - Focus sur Brodbar
❌ donnees*.xls                    # (2 fichiers)
❌ param_RBC_aire*.xls             # (5 fichiers) - Anciens params
❌ initial_cond_RBC_aire*.xls      # (5 fichiers) - Anciennes conditions
❌ AA non dans V_growth.xlsx
❌ Parametre_curve_fit.xls
❌ matricepara1.mat
❌ Data_fit_Brodbar.mat
❌ Data_Methode_fit_ja.mat
```

### 🗑️ **Divers**
```
❌ .zip files                      # (2 fichiers: equadiff_Brodbar_1809.zip, src_v1.zip)
❌ *.bat                           # (3 fichiers) - Scripts batch
❌ *.rtf, *.docx                   # (2 fichiers)
❌ *.txt (anciens)                 # NEWS.txt (2 MB!), cellbardyn.txt, etc.
❌ Curve Fits/                     # (vide)
❌ demo_*/                         # (3 dossiers vides)
❌ electrical_*/                   # (1 dossier vide)
❌ outputs/                        # Anciens outputs
❌ production_packages/            # Anciens packages
❌ RBC/                            # Ancien code
❌ Scripts/                        # Anciens scripts
```

---

## 📦 À ARCHIVER (Optionnel - Backup externe)

Si tu veux garder une trace:
```
📦 Doc/                           # Documentation complète (570 items)
📦 *.m files                      # Code MATLAB original
📦 DATA_Bardyn*                   # Données Bardyn (si besoin futur)
📦 html/brodbar/                  # Résultat intermédiaire (si doute)
```

---

## 📊 Impact du Nettoyage

### Avant:
```
Total fichiers: ~170 (racine)
Total dossiers: ~20 grands dossiers
Taille estimée: ~25 GB
```

### Après:
```
Total fichiers: ~30 (racine)
Total dossiers: ~6 essentiels
Taille estimée: ~1-2 GB
```

**Réduction:** ~90% des fichiers, ~95% de l'espace

---

## 🚀 Structure Cible Propre

```
Mario_RBC_up/
│
├── src/                          # Code source (GARDÉ)
├── data/                         # Données (GARDÉ ou renommé)
├── html/
│   ├── brodbar_alkalosis_severe/ # Résultats récents
│   └── brodbar_acidosis_severe/  # (À venir)
│
├── dashboard/                    # (NOUVEAU - pour Streamlit)
│
├── README.md
├── pH_PROJECT_FINAL_COMPLETE.md
├── BOHR_INTEGRATION_COMPLETE.md
├── requirements.txt
│
├── bohr_dashboard.py
├── compare_bohr_scenarios.py
└── analyze_BPG_dynamics.py
```

---

## ⚠️ AVERTISSEMENTS

1. **html/brodbar/** - Vérifier le scénario avant suppression
2. **Doc/** - 570 items, peut contenir info utile
3. **Backup recommandé** avant suppression massive

---

## 🎯 Commandes de Nettoyage

Voir fichier `cleanup_script.ps1` pour automatisation.
