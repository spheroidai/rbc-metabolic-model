# Plan de Développement - Application Web RBC Metabolic Model
**Date:** 2025-11-16  
**Objectif:** Créer une application web Streamlit pour le modèle RBC avec déploiement sur Streamlit Cloud

---

## 📋 **ARCHITECTURE GLOBALE**

### **Structure Projet (Séparation Local/Web)**

```
Mario_RBC_up/
├── 📁 src/                          # ✅ CODE LOCAL (simulations CLI)
│   ├── main.py                      # Point d'entrée CLI
│   ├── equadiff_brodbar.py          # Équations différentielles
│   ├── curve_fit.py                 # Fitting expérimental
│   ├── solver.py, visualization.py  # Core modules
│   └── [22 modules essentiels]
│
├── 📁 streamlit_app/                # 🌐 NOUVELLE - APPLICATION WEB
│   ├── app.py                       # Point d'entrée Streamlit
│   ├── pages/                       # Pages multi-pages
│   │   ├── 1_🏠_Home.py
│   │   ├── 2_🧪_Simulation.py
│   │   ├── 3_📊_Results.py
│   │   ├── 4_🔬_Bohr_Effect.py
│   │   ├── 5_⚗️_pH_Analysis.py
│   │   └── 6_📈_Advanced.py
│   ├── core/                        # Modules backend réutilisés
│   │   ├── __init__.py
│   │   ├── simulation_engine.py    # Wrapper équations
│   │   ├── data_loader.py          # Chargement données
│   │   ├── plotting.py             # Visualisation Streamlit
│   │   └── cache_manager.py        # Gestion cache
│   ├── assets/                      # Ressources web
│   │   ├── logo.png
│   │   ├── styles.css
│   │   └── README_web.md
│   └── utils/                       # Utilitaires web
│       ├── session_state.py
│       ├── data_validation.py
│       └── export_manager.py
│
├── 📁 data/                         # DONNÉES PARTAGÉES
│   ├── Data_Brodbar_et_al_exp.xlsx
│   ├── Data_Brodbar_et_al_exp_fitted_params.csv
│   └── Initial_conditions_JA_Final.xls
│
├── 📁 Documentation/                # DOCUMENTATION
├── 📁 Simulations/                  # RÉSULTATS (local)
├── 📁 .streamlit/                   # CONFIGURATION STREAMLIT
│   ├── config.toml                  # Thème et paramètres
│   └── secrets.toml                 # Secrets (non versionné)
│
├── requirements.txt                 # Dépendances LOCAL
├── requirements_streamlit.txt       # Dépendances WEB
├── README.md                        # Documentation projet
├── README_streamlit.md              # Guide déploiement web
└── .gitignore                       # Git exclusions

```

---

## 🎯 **PHASE 1: PRÉPARATION & STRUCTURE**

### **1.1 Créer la Structure Web**
```bash
mkdir streamlit_app
mkdir streamlit_app/pages
mkdir streamlit_app/core
mkdir streamlit_app/assets
mkdir streamlit_app/utils
mkdir .streamlit
```

### **1.2 Créer requirements_streamlit.txt**
```txt
# Core dependencies
streamlit>=1.30.0
numpy>=1.26.0
scipy>=1.11.0
pandas>=2.1.0
matplotlib>=3.8.0
plotly>=5.18.0           # Graphiques interactifs
openpyxl>=3.1.0
xlrd>=2.0.1

# Optional for advanced features
scikit-learn>=1.3.0      # ML features
seaborn>=0.13.0          # Visualisations avancées
pillow>=10.1.0           # Images

# Deployment
watchdog                 # Auto-reload
```

### **1.3 Créer .gitignore**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Streamlit
.streamlit/secrets.toml

# Data outputs
Simulations/
*.png
*.pdf

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

## 🚀 **PHASE 2: DÉVELOPPEMENT APPLICATION STREAMLIT**

### **2.1 Point d'Entrée Principal: `streamlit_app/app.py`**

**Fonctionnalités:**
- Page d'accueil avec présentation du modèle
- Navigation multi-pages
- État de session partagé
- Thème personnalisé

**Structure:**
```python
import streamlit as st
from pathlib import Path

# Configuration page
st.set_page_config(
    page_title="RBC Metabolic Model",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF4B4B;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Page d'accueil
st.markdown('<h1 class="main-header">🩸 RBC Metabolic Model</h1>', 
            unsafe_allow_html=True)

st.markdown("""
### Red Blood Cell Metabolic Simulation Platform
**Bordbar et al. (2015) - Interactive Web Application**

This application simulates RBC metabolism with:
- 107 metabolites (106 base + pHi)
- Multiple metabolic pathways (Glycolysis, PPP, Nucleotide, etc.)
- Bohr effect and pH perturbation analysis
- Real-time interactive visualizations
""")

# Colonnes pour features
col1, col2, col3 = st.columns(3)

with col1:
    st.info("🧪 **Simulations**\nRun metabolic simulations with customizable parameters")

with col2:
    st.success("📊 **Analysis**\nVisualize metabolite dynamics and flux distributions")

with col3:
    st.warning("🔬 **Bohr Effect**\nExplore oxygen binding and pH dependencies")

# Sidebar avec infos
with st.sidebar:
    st.image("streamlit_app/assets/logo.png", width=200)
    st.markdown("### Navigation")
    st.markdown("Use the pages on the left to explore different features")
    
    st.markdown("### Quick Stats")
    st.metric("Metabolites", "107")
    st.metric("Reactions", "~200")
    st.metric("Pathways", "8")
```

---

### **2.2 Page Simulation: `streamlit_app/pages/2_🧪_Simulation.py`**

**Fonctionnalités:**
- Configuration paramètres simulation
- Sélection conditions initiales
- Choix intensité curve fitting (0-100%)
- Lancement simulation en temps réel
- Barre de progression
- Téléchargement résultats

**Interface:**
```python
import streamlit as st
import sys
from pathlib import Path

# Ajouter src/ au path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from core.simulation_engine import run_simulation
from core.plotting import plot_metabolites_interactive

st.title("🧪 Run Metabolic Simulation")

# Sidebar avec paramètres
with st.sidebar:
    st.header("⚙️ Simulation Parameters")
    
    # Durée simulation
    t_max = st.slider("Simulation Duration (hours)", 1, 72, 42)
    
    # Curve fitting strength
    curve_fit_strength = st.slider(
        "Curve Fitting Strength (%)", 
        0, 100, 100,
        help="0% = Pure MM kinetics, 100% = Blend with experimental curves"
    )
    
    # Initial conditions
    ic_source = st.selectbox(
        "Initial Conditions Source",
        ["JA Final (Recommended)", "Brodbar Experimental", "Custom"]
    )
    
    # Solver settings
    with st.expander("🔧 Advanced Solver Settings"):
        solver_method = st.selectbox("Method", ["RK45", "BDF", "LSODA"])
        rtol = st.number_input("Relative Tolerance", value=1e-6, format="%.2e")
        atol = st.number_input("Absolute Tolerance", value=1e-8, format="%.2e")

# Zone principale
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Simulation Configuration")
    
    # Afficher résumé
    st.info(f"""
    **Configuration Summary:**
    - Duration: {t_max} hours
    - Curve Fitting: {curve_fit_strength}%
    - Initial Conditions: {ic_source}
    - Solver: {solver_method}
    """)
    
    # Bouton lancement
    if st.button("🚀 Start Simulation", type="primary", use_container_width=True):
        with st.spinner("Running simulation..."):
            # Barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Lancer simulation
            results = run_simulation(
                t_max=t_max,
                curve_fit_strength=curve_fit_strength/100,
                ic_source=ic_source,
                solver_method=solver_method,
                progress_callback=lambda p, msg: (
                    progress_bar.progress(p),
                    status_text.text(msg)
                )
            )
            
            # Sauvegarder dans session state
            st.session_state['results'] = results
            st.session_state['simulation_done'] = True
            
            st.success(f"✅ Simulation completed in {results['duration']:.1f} seconds!")

with col2:
    st.subheader("📊 Quick Stats")
    
    if 'results' in st.session_state:
        results = st.session_state['results']
        st.metric("Time Points", results['n_points'])
        st.metric("Metabolites", results['n_metabolites'])
        st.metric("Duration", f"{results['duration']:.1f}s")

# Afficher résultats si disponibles
if st.session_state.get('simulation_done', False):
    st.divider()
    st.subheader("📈 Results Preview")
    
    results = st.session_state['results']
    
    # Tabs pour différentes vues
    tab1, tab2, tab3 = st.tabs(["📊 Key Metabolites", "🔥 Flux Heatmap", "📥 Export"])
    
    with tab1:
        # Sélection métabolites
        selected_metabolites = st.multiselect(
            "Select Metabolites to Plot",
            options=results['metabolite_names'],
            default=['EGLC', 'ELAC', 'ATP', 'ADP', 'GLC']
        )
        
        # Plot interactif avec Plotly
        fig = plot_metabolites_interactive(results, selected_metabolites)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Heatmap flux
        st.plotly_chart(results['flux_heatmap'], use_container_width=True)
    
    with tab3:
        # Boutons export
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "📥 Download CSV",
                data=results['csv_data'],
                file_name="simulation_results.csv",
                mime="text/csv"
            )
        
        with col2:
            st.download_button(
                "📄 Download PDF Report",
                data=results['pdf_report'],
                file_name="simulation_report.pdf",
                mime="application/pdf"
            )
        
        with col3:
            st.download_button(
                "💾 Download All Data (ZIP)",
                data=results['zip_data'],
                file_name="simulation_complete.zip",
                mime="application/zip"
            )
```

---

### **2.3 Page Résultats: `streamlit_app/pages/3_📊_Results.py`**

**Fonctionnalités:**
- Visualisation interactive métabolites
- Comparaison données expérimentales
- Zoom et pan sur graphiques
- Filtrage par voies métaboliques
- Statistiques descriptives

---

### **2.4 Page Bohr Effect: `streamlit_app/pages/4_🔬_Bohr_Effect.py`**

**Fonctionnalités:**
- Simulation effet Bohr
- Courbes liaison oxygène
- Analyse BPG (2,3-bisphosphoglycérate)
- Comparaison scénarios (normoxie, hypoxie)
- Dashboard interactif

---

### **2.5 Page pH Analysis: `streamlit_app/pages/5_⚗️_pH_Analysis.py`**

**Fonctionnalités:**
- Perturbations pH (acidose, alcalose)
- Scénarios prédéfinis (step, ramp, sinusoidal)
- Analyse sensibilité enzymes au pH
- Visualisation dynamiques pHi/pHe

---

## 🛠️ **PHASE 3: MODULES BACKEND (Réutilisation Code Existant)**

### **3.1 `streamlit_app/core/simulation_engine.py`**

**Rôle:** Wrapper autour de `equadiff_brodbar.py` pour Streamlit

```python
"""
Simulation Engine - Wrapper pour intégration Streamlit
"""
import sys
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

# Importer modules existants
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
from equadiff_brodbar import equadiff_brodbar, BRODBAR_METABOLITE_MAP
from parse_initial_conditions import parse_initial_conditions
from curve_fit import curve_fit_ja

@st.cache_data(ttl=3600)  # Cache 1 heure
def run_simulation(t_max=42, curve_fit_strength=1.0, ic_source="JA Final", 
                   solver_method="RK45", progress_callback=None):
    """
    Exécute simulation RBC avec gestion progression
    
    Returns:
        dict avec résultats (t, x, métabolites, flux, etc.)
    """
    # Charger données
    if progress_callback:
        progress_callback(0.1, "Loading experimental data...")
    
    # ... (code simulation adapté de main.py)
    
    # Retourner résultats structurés
    return {
        't': t,
        'x': x,
        'metabolite_names': metabolites,
        'n_points': len(t),
        'n_metabolites': x.shape[1],
        'duration': duration,
        'flux_heatmap': create_flux_heatmap(fluxes),
        'csv_data': export_to_csv(t, x, metabolites),
        'pdf_report': generate_pdf_report(...),
        'zip_data': create_zip_archive(...)
    }
```

---

### **3.2 `streamlit_app/core/plotting.py`**

**Rôle:** Graphiques interactifs Plotly pour Streamlit

```python
"""
Plotting utilities for Streamlit with Plotly
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_metabolites_interactive(results, selected_metabolites):
    """
    Crée graphique interactif Plotly pour métabolites sélectionnés
    """
    fig = go.Figure()
    
    for metab in selected_metabolites:
        idx = results['metabolite_names'].index(metab)
        fig.add_trace(go.Scatter(
            x=results['t'],
            y=results['x'][:, idx],
            mode='lines',
            name=metab,
            hovertemplate='%{y:.3f} mM<br>Time: %{x:.1f}h'
        ))
    
    fig.update_layout(
        title="Metabolite Concentrations Over Time",
        xaxis_title="Time (hours)",
        yaxis_title="Concentration (mM)",
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig

def create_flux_heatmap(fluxes):
    """Crée heatmap flux réactionnels"""
    # ... implémentation
    pass
```

---

### **3.3 `streamlit_app/core/data_loader.py`**

**Rôle:** Chargement données avec caching

```python
"""
Data loading utilities with Streamlit caching
"""
import streamlit as st
import pandas as pd
from pathlib import Path

@st.cache_data
def load_experimental_data():
    """Charge données expérimentales Brodbar"""
    data_path = Path(__file__).parent.parent.parent / "data"
    df = pd.read_excel(data_path / "Data_Brodbar_et_al_exp.xlsx")
    return df

@st.cache_data
def load_fitted_parameters():
    """Charge paramètres fitting"""
    data_path = Path(__file__).parent.parent.parent / "data"
    df = pd.read_csv(data_path / "Data_Brodbar_et_al_exp_fitted_params.csv")
    return df
```

---

## 🎨 **PHASE 4: CONFIGURATION & THÈME**

### **4.1 `.streamlit/config.toml`**

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

---

## 🚀 **PHASE 5: DÉPLOIEMENT STREAMLIT CLOUD**

### **5.1 Préparer Repository GitHub**

```bash
# Initialiser Git (si pas déjà fait)
git init

# Ajouter remote GitHub
git remote add origin https://github.com/YOUR_USERNAME/rbc-metabolic-model.git

# Premier commit
git add .
git commit -m "Initial commit - RBC Metabolic Model Web App"
git push -u origin main
```

### **5.2 Déployer sur Streamlit Cloud**

**Étapes:**
1. Aller sur https://share.streamlit.io
2. Connecter compte GitHub
3. Sélectionner repository: `rbc-metabolic-model`
4. Définir:
   - Main file: `streamlit_app/app.py`
   - Python version: `3.11`
   - Requirements: `requirements_streamlit.txt`
5. Cliquer "Deploy"!

**URL finale:** `https://YOUR_USERNAME-rbc-metabolic-model.streamlit.app`

---

## 📊 **PHASE 6: FONCTIONNALITÉS AVANCÉES**

### **6.1 Comparaison Scénarios**
- Lancer plusieurs simulations en parallèle
- Comparer effet paramètres
- Analyse sensibilité automatique

### **6.2 Export & Partage**
- Génération liens partageables
- Export résultats JSON/CSV/PDF
- Sauvegarde configurations

### **6.3 Authentification (Optionnel)**
- Login utilisateur
- Historique simulations
- Sauvegarde configurations personnelles

---

## ✅ **CHECKLIST COMPLÈTE**

### **Phase 1: Structure** (1-2 heures)
- [ ] Créer dossiers `streamlit_app/`
- [ ] Créer `requirements_streamlit.txt`
- [ ] Configurer `.gitignore`
- [ ] Créer `.streamlit/config.toml`

### **Phase 2: Application Core** (4-6 heures)
- [ ] Développer `app.py` (page accueil)
- [ ] Développer `pages/2_🧪_Simulation.py`
- [ ] Développer `pages/3_📊_Results.py`
- [ ] Développer `pages/4_🔬_Bohr_Effect.py`

### **Phase 3: Backend** (3-4 heures)
- [ ] Créer `core/simulation_engine.py`
- [ ] Créer `core/plotting.py`
- [ ] Créer `core/data_loader.py`
- [ ] Tests intégration

### **Phase 4: Déploiement** (1 heure)
- [ ] Push GitHub
- [ ] Configurer Streamlit Cloud
- [ ] Tests production
- [ ] Documentation déploiement

**TOTAL ESTIMÉ: 10-15 heures de développement**

---

## 📝 **SÉPARATION LOCAL vs WEB**

### **Utilisation Locale (`src/main.py`):**
```bash
# Activer venv
.\activate_venv.ps1

# Simulation CLI locale
python src/main.py --curve-fit 1.0
```

### **Utilisation Web (Streamlit):**
```bash
# Développement local
streamlit run streamlit_app/app.py

# Production
# → Automatique via Streamlit Cloud après push GitHub
```

### **Avantages Séparation:**
✅ Code local inchangé (CLI reste fonctionnel)  
✅ Application web optimisée pour interface utilisateur  
✅ Déploiement indépendant  
✅ Maintenance séparée  
✅ Performance optimisée pour chaque usage

---

## 🎯 **PROCHAINES ÉTAPES RECOMMANDÉES**

1. **Commencer par Phase 1** - Structure de base (30 min)
2. **Développer page accueil** - `app.py` simple (1h)
3. **Wrapper simulation basique** - `simulation_engine.py` minimal (2h)
4. **Test local** - `streamlit run app.py` (15 min)
5. **Push GitHub + Deploy** - Premier déploiement (30 min)
6. **Itérations** - Ajouter fonctionnalités progressivement

---

**Prêt à démarrer? On commence par Phase 1 (Structure)?** 🚀
