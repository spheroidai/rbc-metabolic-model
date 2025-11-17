# 🚀 Guide de Déploiement Streamlit Community Cloud

Ce guide explique comment déployer l'application RBC Metabolic Model sur Streamlit Community Cloud.

## 📋 Prérequis

✅ Compte GitHub (gratuit)  
✅ Compte Streamlit Cloud (gratuit) - https://streamlit.io/cloud  
✅ Repository Git initialisé

## 🔧 Préparation du Projet

### 1. Fichiers de Configuration

Le projet contient déjà tous les fichiers nécessaires:

```
Mario_RBC_up/
├── streamlit_app/
│   ├── app.py                    # Point d'entrée Streamlit
│   ├── .streamlit/config.toml    # Configuration production
│   └── ...
├── requirements.txt              # Dépendances Python ✅
├── packages.txt                  # Dépendances système (optionnel)
├── .gitignore                    # Fichiers à ignorer ✅
└── README.md                     # Documentation ✅
```

### 2. Structure Requise

Streamlit Cloud nécessite:
- ✅ `requirements.txt` à la racine
- ✅ Application Streamlit dans `streamlit_app/app.py`
- ✅ Fichiers de données (`*.xlsx`, `*.xls`)
- ✅ Code source dans `src/`

## 📤 Étapes de Déploiement

### Étape 1: Pousser sur GitHub

```bash
# Initialiser Git (si pas déjà fait)
git init
git add .
git commit -m "Initial commit - RBC Metabolic Model"

# Créer repository sur GitHub
# Nom suggéré: rbc-metabolic-model

# Lier et pousser
git remote add origin https://github.com/VOTRE_USERNAME/rbc-metabolic-model.git
git branch -M main
git push -u origin main
```

### Étape 2: Déployer sur Streamlit Cloud

1. **Aller sur:** https://share.streamlit.io/

2. **Connecter GitHub:**
   - Cliquer "New app"
   - Autoriser Streamlit à accéder à vos repositories

3. **Configurer l'app:**
   ```
   Repository: votre-username/rbc-metabolic-model
   Branch: main
   Main file path: streamlit_app/app.py
   ```

4. **Options avancées (optionnel):**
   - Python version: 3.11 ou 3.12 (pas 3.14 pour compatibilité)
   - Secrets: Laisser vide (pas nécessaire)

5. **Déployer:**
   - Cliquer "Deploy!"
   - Attendre 2-5 minutes pour le build initial

### Étape 3: Vérifier le Déploiement

Votre app sera disponible à:
```
https://votre-username-rbc-metabolic-model-main-streamlit-appapp-xxx.streamlit.app
```

ou avec un nom personnalisé que vous pouvez configurer dans les settings.

## ⚙️ Configuration Post-Déploiement

### Personnaliser l'URL

Dans Streamlit Cloud:
1. Settings → General
2. App URL: Choisir un nom court
3. Exemple: `rbc-model.streamlit.app`

### Gérer les Resources

Par défaut, Streamlit Cloud fournit:
- **RAM:** 1GB (suffisant pour le modèle)
- **CPU:** Partagé
- **Stockage:** Gratuit

Si l'app est lente:
- Settings → Resource limits
- Considérer upgrade (payant)

### Variables d'Environnement (si nécessaire)

Dans Settings → Secrets:
```toml
# Exemple (pas nécessaire pour cette app)
# API_KEY = "your-key"
```

## 🔄 Mises à Jour

Chaque fois que vous poussez sur GitHub:

```bash
git add .
git commit -m "Update: description des changements"
git push
```

Streamlit Cloud détecte automatiquement et redéploie (1-2 min).

### Forcer un Redéploiement

Si nécessaire:
1. Dashboard Streamlit Cloud
2. Menu (⋮) → Reboot app

## 🐛 Dépannage

### Erreur: "ModuleNotFoundError"

**Solution:** Vérifier `requirements.txt`
```bash
# Tester localement
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

### Erreur: "File not found"

**Cause:** Chemins relatifs incorrects

**Solution:** Utiliser chemins relatifs depuis la racine:
```python
# ❌ Mauvais
data = pd.read_excel("Data_Brodbar_et_al_exp.xlsx")

# ✅ Bon
from pathlib import Path
project_root = Path(__file__).parent.parent
data = pd.read_excel(project_root / "Data_Brodbar_et_al_exp.xlsx")
```

### Build Timeout

**Cause:** Dépendances trop lourdes ou build trop long

**Solutions:**
1. Réduire versions dans `requirements.txt`
2. Retirer packages inutiles
3. Contacter support Streamlit

### Erreur: "Memory limit exceeded"

**Cause:** Simulation trop gourmande

**Solutions:**
1. Réduire nombre de time points
2. Optimiser code numpy
3. Upgrade plan (payant)

## 📊 Monitoring

### Logs

Streamlit Cloud Dashboard:
- Logs → Voir sorties Python/Streamlit
- Errors → Erreurs runtime
- Analytics → Utilisation (visitors, etc.)

### Performance

Surveiller:
- Temps de chargement initial
- Temps de simulation
- Utilisation mémoire

## 🔐 Sécurité

### Fichiers à NE PAS commit

Le `.gitignore` exclut déjà:
- ❌ `venv/` - Environnement virtuel
- ❌ `__pycache__/` - Cache Python
- ❌ `.env` - Variables d'environnement locales
- ❌ Fichiers personnels

### Données Sensibles

Si l'app utilise des données privées:
1. Utiliser Streamlit Secrets
2. Ou déploiement privé (payant)

## 📚 Ressources

- **Documentation Streamlit:** https://docs.streamlit.io/
- **Streamlit Cloud:** https://docs.streamlit.io/streamlit-community-cloud
- **Forum Support:** https://discuss.streamlit.io/
- **Examples:** https://streamlit.io/gallery

## ✅ Checklist Finale

Avant de déployer, vérifier:

- [ ] `requirements.txt` complet et testé
- [ ] App fonctionne localement: `streamlit run streamlit_app/app.py`
- [ ] `.gitignore` exclut fichiers sensibles
- [ ] `README.md` contient instructions claires
- [ ] Fichiers de données dans le repository
- [ ] Pas de chemins absolus dans le code
- [ ] Repository GitHub public ou accès Streamlit Cloud
- [ ] Badge Streamlit ajouté dans README.md

## 🎉 Succès!

Une fois déployé, votre app sera accessible 24/7 gratuitement!

Partager le lien:
```
https://votre-app.streamlit.app
```

**Profitez de votre modèle RBC déployé!** 🩸🚀
