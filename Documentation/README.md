# 📚 **Documentation - Projet RBC Métabolique avec pH Dynamique**

**Date:** 2025-11-16  
**Organisation:** Documentation consolidée et guides pratiques

---

## 📂 **Structure de la Documentation**

### **🎊 Documentation Principale**

1. **[pH_PROJECT_FINAL_COMPLETE.md](pH_PROJECT_FINAL_COMPLETE.md)** ⭐ **DOCUMENT PRINCIPAL**
   - Vue d'ensemble complète du projet pH
   - Toutes les phases (1-4) et options (1-4)
   - ~630 lignes de documentation détaillée
   - Architecture, fonctionnalités, exemples d'utilisation

2. **[BOHR_INTEGRATION_COMPLETE.md](BOHR_INTEGRATION_COMPLETE.md)**
   - Documentation spécifique à l'effet Bohr
   - Intégration avec le système pH
   - P50 dynamique, saturation O2, livraison O2
   - ~11 KB de documentation

3. **[VENV_GUIDE.md](VENV_GUIDE.md)**
   - Guide pratique pour l'environnement virtuel Python
   - Installation, activation, maintenance
   - Troubleshooting et bonnes pratiques
   - ~3 KB

4. **[CLEANUP_PLAN.md](CLEANUP_PLAN.md)**
   - Plan de nettoyage du projet (historique)
   - Identification des fichiers redondants
   - ~8 KB

---

## 🗂️ **Documentation par Module (Proposée)**

**Note:** Les fichiers suivants sont mentionnés dans `pH_PROJECT_FINAL_COMPLETE.md` comme structure idéale mais n'existent pas encore comme fichiers séparés. Le contenu est actuellement consolidé dans le document principal.

### **Phase 1: Infrastructure pH**
- `PHASE1_COMPLETE_SUMMARY.md` (proposé)
  - Infrastructure pH de base
  - Transport protonique
  - Modulation enzymatique

### **Option 1: Simulations**
- `OPTION1_SIMULATION_GUIDE.md` (proposé)
  - Arguments CLI pour perturbations pH
  - Scénarios prédéfinis (acidose/alcalose)
  - Exemples d'utilisation

### **Option 2: Visualisations**
- `OPTION2_VISUALIZATION_GUIDE.md` (proposé)
  - Plots pH dédiés
  - Analyse temporelle
  - PDF reports

### **Option 3: Calibration**
- `OPTION3_CALIBRATION_GUIDE.md` (proposé)
  - Calibration des paramètres pH
  - Analyse de sensibilité
  - Optimisation

### **Option 4: Extensions**
- `OPTION4_EXTENSIONS_GUIDE.md` (proposé)
  - Effet Bohr intégré
  - Sensibilité enzymatique étendue
  - Transport O2

### **Synthèse Globale**
- `pH_PROJECT_COMPLETE_SUMMARY.md` (proposé)
  - Résumé exécutif du projet
  - Accomplissements
  - Prochaines étapes

---

## 📖 **Comment Utiliser Cette Documentation**

### **Pour Démarrer Rapidement:**
1. Lire `../README.md` à la racine du projet
2. Consulter `VENV_GUIDE.md` pour setup environnement
3. Lire `pH_PROJECT_FINAL_COMPLETE.md` sections pertinentes

### **Pour Développement:**
1. `pH_PROJECT_FINAL_COMPLETE.md` - Architecture complète
2. `BOHR_INTEGRATION_COMPLETE.md` - Si travail sur Bohr effect
3. Code source dans `../src/` avec docstrings

### **Pour Utilisateurs:**
1. Section "Utilisation" dans `pH_PROJECT_FINAL_COMPLETE.md`
2. Exemples de commandes CLI
3. Interprétation des résultats

---

## 🎯 **État Actuel**

### ✅ **Documentation Existante**
- Documentation consolidée complète
- Guides pratiques (venv, Bohr)
- Docstrings dans le code source
- README principal

### 📝 **À Créer (Optionnel)**
Les fichiers proposés ci-dessus peuvent être créés en extrayant les sections pertinentes de `pH_PROJECT_FINAL_COMPLETE.md` si une organisation plus granulaire est souhaitée.

---

## 📍 **Localisation des Ressources**

```
Mario_RBC_up/
├── Documentation/               ← Vous êtes ici
│   ├── README.md               ← Ce fichier
│   ├── pH_PROJECT_FINAL_COMPLETE.md
│   ├── BOHR_INTEGRATION_COMPLETE.md
│   ├── VENV_GUIDE.md
│   └── CLEANUP_PLAN.md
│
├── README.md                   ← README principal du projet
├── src/                        ← Code source avec docstrings
├── Simulations/                ← Résultats de simulations
└── requirements.txt            ← Dépendances Python
```

---

## 🔗 **Liens Utiles**

- **Code Source:** `../src/`
- **Scripts d'Analyse:** `../compare_bohr_scenarios.py`, `../bohr_dashboard.py`
- **Résultats:** `../Simulations/brodbar/`
- **Données:** `../Data_Brodbar_et_al_exp.xlsx`

---

## 📞 **Support**

Pour questions ou contributions:
1. Consulter d'abord `pH_PROJECT_FINAL_COMPLETE.md`
2. Vérifier les docstrings dans le code
3. Examiner les exemples dans `Simulations/`

---

**Dernière mise à jour:** 2025-11-16  
**Version:** 1.0 (Documentation consolidée)
