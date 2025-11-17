# 🐍 Guide d'Utilisation du Virtual Environment (venv)

**Date:** 2025-11-15  
**Statut:** ✅ **VENV FONCTIONNEL**

---

## ✅ **Configuration Actuelle**

```
Python: 3.14.0 (système)
venv: c:\Users\Jorgelindo\Desktop\Mario_RBC_up\venv\
Packages: numpy, scipy, pandas, matplotlib, openpyxl, xlrd, lmfit, sympy
```

---

## 🚀 **Utilisation Quotidienne**

### **1. Activer le venv**

```powershell
# Option A: Script automatique
.\activate_venv.ps1

# Option B: Activation manuelle
.\venv\Scripts\Activate.ps1
```

**Résultat:** Le prompt affiche `(venv)` au début

### **2. Lancer une simulation**

```powershell
# Simulation standard
python src/main.py --curve-fit 0.0

# Simulation avec alcalose sévère
python src/main.py --curve-fit 0.0 --ph-perturbation alkalosis --ph-severity severe

# Simulation avec acidose sévère
python src/main.py --curve-fit 0.0 --ph-perturbation acidosis --ph-severity severe
```

### **3. Désactiver le venv**

```powershell
deactivate
```

---

## 🔧 **Maintenance**

### **Recréer le venv (si corrompu)**

```powershell
.\recreate_venv.ps1
```

### **Installer un nouveau package**

```powershell
# Activer venv d'abord
.\venv\Scripts\Activate.ps1

# Installer
pip install streamlit

# Mettre à jour requirements.txt
pip freeze > requirements.txt
```

### **Mettre à jour tous les packages**

```powershell
.\venv\Scripts\Activate.ps1
pip install --upgrade -r requirements.txt
```

---

## 📊 **Résultats de Simulation**

Les résultats sont sauvegardés dans:
```
html/
  ├── brodbar/                    # Simulation standard
  ├── brodbar_alkalosis_severe/   # Alcalose
  └── brodbar_acidosis_severe/    # Acidose
```

Chaque dossier contient:
- **metabolites/**: Plots et CSV des métabolites
- **fluxes/**: Analyse des flux réactionnels
- **bohr_effect/**: Métriques de l'effet Bohr (si activé)

---

## 🎯 **Prochaine Étape: Dashboard Streamlit**

Pour créer le dashboard interactif:

```powershell
# Installer Streamlit
.\venv\Scripts\Activate.ps1
pip install streamlit plotly

# Lancer le dashboard (à venir)
streamlit run dashboard/streamlit_app.py
```

---

## ⚠️ **Troubleshooting**

### **Erreur: "python not found"**
```powershell
# Vérifier que le venv est activé
.\venv\Scripts\Activate.ps1
```

### **Erreur: "Module not found"**
```powershell
# Réinstaller les packages
.\venv\Scripts\pip.exe install -r requirements.txt
```

### **Erreur: "venv corrompu"**
```powershell
# Recréer complètement
.\recreate_venv.ps1
```

---

## 📝 **Notes Importantes**

1. **NE PAS** supprimer le dossier `venv/` manuellement
2. **TOUJOURS** activer le venv avant d'exécuter des scripts
3. **FERMER** tous les terminaux avec `(venv)` actif avant de recréer le venv
4. Le Python embedded (`.\python.exe`) est différent du venv - utilise le venv!

---

## ✅ **Validation**

Pour tester que tout fonctionne:

```powershell
# Activer
.\venv\Scripts\Activate.ps1

# Tester imports
python -c "import numpy, scipy, pandas, matplotlib; print('OK')"

# Tester simulation
python src/main.py --help
```

---

**Venv créé le:** 2025-11-15  
**Python version:** 3.14.0  
**Statut:** ✅ Fonctionnel et testé
