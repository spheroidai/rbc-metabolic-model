# 📦 Requirements Files Guide

Ce projet contient **3 fichiers de dépendances** pour différents usages:

## 📁 Files

### 1. `requirements.txt` ✅ **PRINCIPAL - Streamlit Cloud**
```
Python: 3.11+
Usage: Déploiement Streamlit Cloud
Versions: Compatible production
```

**Utilisé par:**
- ✅ Streamlit Community Cloud (auto-détecté)
- ✅ Déploiement production
- ✅ Installation standard: `pip install -r requirements.txt`

**Contient:**
- streamlit>=1.30.0
- numpy>=1.26.0 (compatible 3.11)
- scipy>=1.11.0
- pandas>=2.1.0
- matplotlib>=3.8.0
- plotly>=5.18.0

---

### 2. `requirements_streamlit.txt` 🔄 **BACKUP Streamlit**
```
Python: 3.11+
Usage: Backup / Alternative Streamlit
```

**Version de backup** avec les mêmes dépendances que `requirements.txt`.

---

### 3. `requirements_cli.txt` 🖥️ **CLI - Développement Local**
```
Python: 3.14+
Usage: CLI local avec dernières versions
```

**Utilisé pour:**
- Développement local avec Python 3.14+
- Scripts CLI (`src/main.py`)
- Dernières versions des packages

**Installation:**
```bash
pip install -r requirements_cli.txt
```

**Contient:**
- numpy>=2.3.0 (dernière version)
- scipy>=1.16.0
- pandas>=2.3.0
- matplotlib>=3.10.0

---

## 🚀 Usage Recommandé

### Pour Streamlit Cloud (Production):
```bash
# Automatique - Streamlit Cloud utilise requirements.txt
# Aucune action nécessaire
```

### Pour Développement Local (Streamlit):
```bash
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

### Pour CLI Local (Dernières versions):
```bash
pip install -r requirements_cli.txt
python src/main.py --curve-fit 1.0
```

---

## ⚠️ Notes

- **Streamlit Cloud** cherche toujours `requirements.txt` à la racine
- **Ne pas renommer** `requirements.txt` si tu veux déployer sur Streamlit Cloud
- Les versions CLI peuvent ne pas fonctionner sur Streamlit Cloud (Python 3.14 non supporté)

---

## 📝 Maintenance

Lors de mises à jour:

1. **Production (Streamlit):** Mettre à jour `requirements.txt`
2. **CLI (Local):** Mettre à jour `requirements_cli.txt`
3. Garder les versions séparées pour compatibilité
