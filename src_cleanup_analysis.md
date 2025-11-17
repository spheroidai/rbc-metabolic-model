# Analyse Complète des Fichiers src/ - Nettoyage RBC Model
**Date:** 2025-11-16  
**Objectif:** Identifier fichiers essentiels vs obsolètes pour simulations, Bohr effect et pH

---

## ✅ FICHIERS ESSENTIELS (À GARDER - 22 fichiers)

### **Core Simulation (12 fichiers)**
| Fichier | Taille | Raison |
|---------|--------|--------|
| `main.py` | 26 KB | ⭐ **Point d'entrée principal** |
| `equadiff_brodbar.py` | 67 KB | ⭐ **Équations différentielles RBC** |
| `curve_fit.py` | 35 KB | **Fitting expérimental** |
| `parse.py` | 12 KB | **Parser réseau réactions** |
| `parse_initial_conditions.py` | 5 KB | **Conditions initiales** |
| `solver.py` | 3 KB | **Intégration ODE** |
| `visualization.py` | 19 KB | **Plots métabolites** |
| `model.py` | 10 KB | **Chargement modèle** |
| `flux_visualization.py` | 13 KB | **Visualisation flux** |
| `compute_fluxes.py` | 10 KB | **Calcul flux métaboliques** |
| `rbc_equadiff_refactor.py` | 10 KB | **Modèle refactorisé (optionnel)** |
| `adaptive_solver.py` | 8 KB | **Solveur adaptatif** |

### **pH & Bohr Effect (7 fichiers)**
| Fichier | Taille | Raison |
|---------|--------|--------|
| `bohr_effect.py` | 18 KB | ⭐ **Effet Bohr** |
| `ph_perturbation.py` | 16 KB | ⭐ **Perturbations pH** |
| `ph_sensitivity_params.py` | 12 KB | **Sensibilité pH enzymes** |
| `ph_visualization.py` | 24 KB | **Visualisation pH** |
| `ph_calibration.py` | 19 KB | **Calibration pH** |
| `ph_sensitivity_extended.py` | 12 KB | **Sensibilité pH étendue** |
| `bohr_visualization.py` | 12 KB | **Visualisation Bohr** |

### **Analyse & Scripts Utiles (3 fichiers)**
| Fichier | Taille | Raison |
|---------|--------|--------|
| `analyze_BPG_dynamics.py` | 13 KB | **Analyse 2,3-BPG** |
| `bohr_dashboard.py` | 8 KB | **Dashboard Bohr** |
| `compare_bohr_scenarios.py` | 13 KB | **Comparaison scénarios** |

---

## ⚠️ FICHIERS OPTIONNELS (À ÉVALUER - 15 fichiers)

### **Utilities & Helpers**
| Fichier | Taille | Action Suggérée |
|---------|--------|-----------------|
| `flux_analyzer.py` | 13 KB | Garder (analyse flux avancée) |
| `sensitivity_analysis.py` | 17 KB | Garder (analyse sensibilité) |
| `curve_fitting_data.py` | 23 KB | Garder (fitting data utils) |
| `load_ja_initial_conditions.py` | 7 KB | Garder (IC JA Final) |
| `load_experimental_initial_conditions.py` | 3 KB | Garder (IC expérimentales) |

### **Validation & Testing**
| Fichier | Taille | Action Suggérée |
|---------|--------|-----------------|
| `cross_validation.py` | 25 KB | Garder (validation croisée) |
| `comprehensive_cross_validation.py` | 28 KB | Garder (validation complète) |
| `model_comparison_analysis.py` | 17 KB | Garder (comparaison modèles) |
| `INTEGRATION_GUIDE.md` | 8 KB | Garder (documentation) |

### **Advanced Analysis**
| Fichier | Taille | Action Suggérée |
|---------|--------|-----------------|
| `hierarchical_fitter.py` | 26 KB | Garder si ML utilisé |
| `thermodynamic_constraints.py` | 14 KB | Garder (contraintes thermo) |
| `enhanced_model_summary.py` | 8 KB | Garder (résumé modèle) |

### **Data Files**
| Fichier | Taille | Action Suggérée |
|---------|--------|-----------------|
| `initial_conditions_ja_cleaned.csv` | 2 KB | Garder (IC nettoyées) |

---

## ❌ FICHIERS OBSOLÈTES (À SUPPRIMER - 75 fichiers)

### **1. Backups & Archives (7 fichiers - 462 KB)**
```
equadiff_brodbar_backup.py                        17 KB
equadiff_brodbar_backup_20250916_084620.py        81 KB
equadiff_brodbar_backup_20250916_084712.py        81 KB
equadiff_brodbar_redox_backup_20250916_085947.py  90 KB
equadiff_brodbar_2009.zip                         13 KB
equadiff_brodbar_2210.zip                         13 KB
equadiff_brodbar_clean.py                         17 KB
```
**Raison:** Fichiers de backup datés, archivés. Version actuelle dans `equadiff_brodbar.py`.

---

### **2. Variantes Main Obsolètes (3 fichiers - 18 KB)**
```
main_brodbar_clean.py                              7 KB
main_clean_mm.py                                   6 KB
main_optimized.py                                  5 KB
```
**Raison:** Versions alternatives de main.py. Version actuelle dans `main.py`.

---

### **3. Scripts de Debugging (9 fichiers - 53 KB)**
```
debug_initial_conditions.py                        5 KB
debug_nan_inf.py                                   5 KB
debug_simulation_mismatch.py                       6 KB
debug_stability.py                                 8 KB
fix_all_indices.py                                 6 KB
fix_brodbar_mapping.py                             3 KB
fix_initial_values.py                              4 KB
fix_metabolite_mapping.py                          4 KB
verify_model_indices.py                            7 KB
```
**Raison:** Scripts de debug/fix pour problèmes résolus.

---

### **4. Variantes equadiff Obsolètes (5 fichiers - 77 KB)**
```
equadiff_brodbar_simple.py                         3 KB
equadiff_brodbar_clean_mm.py                      17 KB
equadiff_brodbar_electrical.py                    15 KB
equadiff_simplified.py                            12 KB
homogeneous_metabolic_equations.py                21 KB
```
**Raison:** Variantes expérimentales de equadiff. Version production: `equadiff_brodbar.py`.

---

### **5. Scripts Fitting/Optimization Anciens (28 fichiers - 424 KB)**
```
apply_curve_fit.py                                 9 KB
auto_fit_optimizer.py                             16 KB
brodbar_data_fit.py                                7 KB
clean_mm_optimizer.py                             37 KB
curve_fitting_data_auto.py                        20 KB
curve_fitting_data_manual_backup.py               14 KB
enhanced_extracellular_optimizer.py               20 KB
fast_parameter_fitting.py                         15 KB
final_stable_fit.py                               11 KB
global_local_fit.py                               13 KB
improved_fitter.py                                15 KB
ml_parameter_optimizer.py                         17 KB
model_optimizer.py                                 9 KB
optimize_brodbar_model.py                          9 KB
optimize_extracellular.py                         10 KB
parameter_optimizer.py                            12 KB
production_parameter_fitting.py                   24 KB
refactored_fitter.py                              11 KB
robust_fit.py                                     10 KB
run_curve_fitting_with_flux_tracking.py           16 KB
run_elac_optimization.py                          11 KB
run_refactored_fitting.py                          6 KB
streamlined_fit.py                                 8 KB
tune_kinetic_params.py                            10 KB
direct_model_enhancement.py                       13 KB
extend_metabolite_enhancements.py                 17 KB
enhance_redox_system.py                           24 KB
electrical_metabolic_framework.py                 24 KB
```
**Raison:** Scripts d'optimisation/fitting expérimentaux. Fitting actuel: `curve_fit.py`.

---

### **6. Scripts Test (13 fichiers - 119 KB)**
```
minimal_test.py                                    3 KB
quick_model_check.py                               6 KB
run_brodbar_fixed.py                               4 KB
run_brodbar_simple.py                              7 KB
run_brodbar_simple_test.py                         3 KB
simple_curve_fit_test.py                           7 KB
simple_enhanced_validation.py                      7 KB
simple_fit_test.py                                 6 KB
test_complete_hierarchical_system.py               9 KB
test_curve_fitting.py                              9 KB
test_electrical_integration.py                     9 KB
test_enhanced_model_validation.py                 11 KB
test_hierarchical_fitter.py                       20 KB
test_implementation.py                             5 KB
test_improved_fitting.py                           4 KB
test_parameter_injection.py                        5 KB
```
**Raison:** Scripts de test pour développement. Tests réussis, code intégré.

---

### **7. Utilitaires Redondants (10 fichiers - 86 KB)**
```
compare_data_sources.py                            5 KB
demo_electrical_framework.py                      17 KB
examine_data.py                                    2 KB
examine_initial_conditions.py                      3 KB
extract_brodbar_params.py                          3 KB
production_package.py                             10 KB
read_excel_files.py                                2 KB
visualization_fixed.py                             9 KB
visualization_updated.py                          18 KB
```
**Raison:** Utilitaires redondants ou intégrés ailleurs.

---

## 📊 RÉSUMÉ NETTOYAGE

| Catégorie | Fichiers | Taille | Action |
|-----------|----------|--------|--------|
| **Essentiels** | 22 | ~360 KB | ✅ GARDER |
| **Optionnels** | 15 | ~240 KB | ⚠️ ÉVALUER |
| **Obsolètes** | 75 | ~1.24 MB | ❌ SUPPRIMER |
| **Total** | 112 | ~1.84 MB | |

---

## 🎯 GAIN ESTIMÉ

**Espace à libérer:** ~1.24 MB (67% des fichiers)  
**Fichiers à garder:** 22-37 (selon options)  
**Réduction:** 112 → 22-37 fichiers

---

## 🚀 RECOMMANDATION FINALE

### **Supprimer Immédiatement (Sûr à 100%):**
1. ✅ Tous les backups (7 fichiers)
2. ✅ Variantes main obsolètes (3 fichiers)  
3. ✅ Scripts debugging (9 fichiers)
4. ✅ Variantes equadiff (5 fichiers)
5. ✅ Archives ZIP (2 fichiers)

**Total Phase 1:** 26 fichiers, ~540 KB

### **Évaluer Selon Usage:**
- Scripts fitting anciens (28 fichiers) - Garder si optimisation paramètres nécessaire
- Scripts test (13 fichiers) - Supprimer si tests terminés
- Utilitaires (10 fichiers) - Évaluer usage individuel

---

## 📝 STRUCTURE FINALE RECOMMANDÉE

```
src/
├── Core (12 fichiers)
│   ├── main.py
│   ├── equadiff_brodbar.py
│   ├── curve_fit.py
│   ├── parse.py
│   ├── solver.py
│   └── ...
├── pH & Bohr (7 fichiers)
│   ├── bohr_effect.py
│   ├── ph_perturbation.py
│   └── ...
├── Analysis (3 fichiers)
│   ├── analyze_BPG_dynamics.py
│   └── ...
└── Utils (optionnels - 15 fichiers)
    ├── flux_analyzer.py
    ├── sensitivity_analysis.py
    └── ...
```

**Total:** 22-37 fichiers essentiels
