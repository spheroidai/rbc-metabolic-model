# 🏗️ RBC Metabolic Model - Architecture & Technical Guide

**Version:** 2.0  
**Author:** Jorgelindo da Veiga  
**Based on:** Bordbar et al. (2015) RBC metabolic model

---

## 📁 Project Structure

```
Mario_RBC_up/
├── streamlit_app/                    # Web Application
│   ├── app.py                        # Main entry point
│   ├── .streamlit/
│   │   ├── config.toml               # Theme & server config
│   │   └── secrets.toml              # Supabase credentials (git-ignored)
│   ├── core/                         # Backend modules
│   │   ├── auth.py                   # Authentication manager
│   │   ├── simulation_engine.py      # Simulation orchestration
│   │   ├── plotting.py               # Interactive Plotly visualizations
│   │   ├── data_loader.py            # Data validation and loading
│   │   └── parameter_calibration.py  # Parameter optimization
│   └── pages/                        # Streamlit pages
│       ├── 0_Login.py                # Authentication
│       ├── 1_Simulation.py           # Run simulations
│       ├── 2_Flux_Analysis.py        # Metabolic flux heatmaps
│       ├── 3_Sensitivity_Analysis.py # Compare datasets
│       ├── 4_Data_Upload.py          # Custom data import
│       ├── 5_Parameter_Calibration.py# Model calibration
│       ├── 6_Admin.py                # Admin dashboard
│       └── 7_Pathway_Visualization.py# KEGG-style maps
├── src/                              # CLI Backend
│   ├── main.py                       # CLI entry point
│   ├── equadiff_brodbar.py           # ODE system (108 metabolites)
│   ├── curve_fit.py                  # Experimental data fitting
│   ├── ph_perturbation.py            # pH dynamics
│   ├── ph_sensitivity_params.py      # pH-dependent enzyme modulation
│   ├── bohr_effect.py                # O2 transport modeling
│   ├── flux_visualization.py         # Flux analysis
│   ├── solver.py                     # ODE solver wrapper
│   └── visualization.py              # Matplotlib plots
├── Simulations/                      # Output results
├── Data_Brodbar_et_al_exp.xlsx       # Experimental data
├── Initial_conditions_JA_Final.xls   # Initial metabolite concentrations
├── RBC/Rxn_RBC.txt                   # Reaction network definition
├── requirements.txt                  # Python dependencies
└── SUPABASE_SETUP.sql                # Database schema
```

---

## 🔬 Model Specifications

| Component | Value |
|-----------|-------|
| **Metabolites** | 108 (107 base + pHi dynamics) |
| **Reactions** | ~200 biochemical reactions |
| **Pathways** | 8 major pathways |
| **Data Points** | 14 experimental timepoints |
| **Simulation Duration** | Up to 42 days |

### Metabolic Pathways
- **Glycolysis**: GLC → G6P → F6P → FBP → ... → PYR → LAC
- **Pentose Phosphate**: G6P → GL6P → RU5P → R5P/X5P
- **Rapoport-Luebering Shunt**: BPG13 ↔ BPG23
- **Nucleotide Metabolism**: ATP/ADP/AMP, GTP/GDP
- **Amino Acid Pool**: GLY, SER, ALA, etc.

---

## 🔐 Authentication System

### Technology Stack
- **Backend**: Supabase PostgreSQL
- **Auth**: Supabase Auth (email/password)
- **Security**: Row Level Security (RLS)

### Database Tables

#### `user_profiles`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (refs auth.users) |
| email | TEXT | User email (unique) |
| full_name | TEXT | Display name |
| role | TEXT | 'user' or 'admin' |
| is_active | BOOLEAN | Account status |
| simulation_count | INTEGER | Total simulations |

#### `simulation_history`
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| user_id | UUID | Foreign key |
| simulation_type | TEXT | Type of simulation |
| parameters | JSONB | Simulation config |
| duration_seconds | FLOAT | Execution time |

### Setup
1. Create Supabase project at [supabase.com](https://supabase.com)
2. Run `SUPABASE_SETUP.sql` in SQL Editor
3. Configure `streamlit_app/.streamlit/secrets.toml`:
```toml
[supabase]
url = "https://your-project.supabase.co"
anon_key = "your-anon-key"
```

### Creating Admin
```sql
UPDATE user_profiles 
SET role = 'admin' 
WHERE email = 'your.email@example.com';
```

---

## 🎯 Parameter Calibration

### Optimization Algorithms
| Method | Use Case | Speed |
|--------|----------|-------|
| **Differential Evolution** | Initial calibration, global search | Slow |
| **L-BFGS-B** | Refinement, local optimization | Fast |
| **Least Squares** | Sum-of-squares problems | Medium |

### Calibration Data Format
```csv
time,ATP,ADP,AMP,G6P,F6P
0,2.50,0.50,0.10,0.15,0.08
24,2.30,0.70,0.18,0.25,0.12
48,2.10,0.90,0.26,0.35,0.16
```

**Requirements:**
- `time` column (hours or days)
- Metabolite columns (concentration in mM)
- Minimum 5 time points
- No missing values

### Interpreting Results
- **R² > 0.95**: Excellent fit
- **R² 0.80-0.95**: Good fit
- **R² < 0.70**: Poor fit (check data/model)

---

## 🗺️ Pathway Visualization

### Features
1. **KEGG-Style Static Map**: Interactive network graph
2. **Animated Pathway**: Temporal concentration dynamics
3. **3D Heatmap**: Multi-metabolite surface plot
4. **Hierarchical Clustering**: Metabolite grouping

### Metabolite Presets
- **Glycolysis**: GLC, G6P, F6P, FBP, GAP, BPG13, PG3, PEP, PYR, LAC
- **Energy**: ATP, ADP, AMP, NAD, NADH, NADP, NADPH
- **PPP**: G6P, GL6P, PGNT6, RU5P, R5P, X5P, S7P, E4P
- **Nucleotides**: IMP, INO, HYP, XAN, ADE, GUA

---

## 🚀 Deployment

### Streamlit Cloud
1. Push to GitHub
2. Deploy at [share.streamlit.io](https://share.streamlit.io)
3. Configure:
   - **Main file**: `streamlit_app/app.py`
   - **Python**: 3.11+
4. Add secrets in Streamlit Cloud dashboard

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run streamlit_app/app.py
```

### Resources (Free Tier)
- **RAM**: 1GB
- **Storage**: Included
- **Uptime**: 24/7

---

## 📊 User Workflows

### Basic Simulation
1. Navigate to **🧪 Simulation**
2. Set duration (default: 42 days)
3. Configure curve fitting (40-60%)
4. Click **▶️ Start Simulation**
5. Export results as CSV

### pH Perturbation Analysis
1. Select perturbation type: Acidosis/Alkalosis/Step/Ramp
2. Set severity: Mild/Moderate/Severe
3. Run simulation
4. View Bohr effect (P50, O2 saturation)

### Custom Data Analysis
1. **Upload**: CSV/Excel with time + metabolites
2. **Map**: Use intelligent column mapping
3. **Analyze**: Compare with Brodbar data
4. **Validate**: Check R², RMSE, MAE

### Flux Analysis
1. Run simulation first
2. Navigate to **🔬 Flux Analysis**
3. View flux distributions & heatmaps
4. Export flux data

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Authentication not configured" | Check `secrets.toml` exists |
| "ModuleNotFoundError" | Run `pip install -r requirements.txt` |
| "File not found" | Use relative paths from project root |
| Simulation slow | Try LSODA solver, reduce duration |
| Memory exceeded | Reduce time points, optimize arrays |
| Admin page hidden | Verify role='admin' in database |

---

## 🧪 pH Dynamics System

### Overview

Dynamic pH perturbation system with pHe (extracellular) and pHi (intracellular) tracking.

### Perturbation Types

| Type | Description | CLI Flag |
|------|-------------|----------|
| **Acidosis** | Blood acidification (pH ↓) | `--ph-perturbation acidosis` |
| **Alkalosis** | Blood alkalinization (pH ↑) | `--ph-perturbation alkalosis` |
| **Step** | Instant pH change | `--ph-perturbation step` |
| **Ramp** | Gradual pH transition | `--ph-perturbation ramp` |

### Severity Levels

- **Mild**: ±0.1 pH units
- **Moderate**: ±0.3 pH units  
- **Severe**: ±0.5 pH units

### Proton Transport Mechanisms

| Transporter | Constant | Function |
|-------------|----------|----------|
| H⁺ Diffusion | K_DIFF_H = 0.099 | Passive proton leak |
| NHE (Na⁺/H⁺) | K_NHE = 0.110 | Active H⁺ extrusion |
| AE1 (Cl⁻/HCO₃⁻) | K_AE1 = 2.994 | Band 3 exchanger |
| Buffer Capacity | BETA = 30.0 mM/pH | Intracellular buffering |

### pH-Sensitive Enzymes (26 total)

**Glycolysis**: HK, PFK, PK, DPGM, LDH  
**PPP**: G6PDH, 6PGDH  
**Nucleotide**: ADA, PNP  
**Redox**: GR, GPx

---

## 🫁 Bohr Effect & O₂ Transport

### Key Constants

```
NORMAL_P50 = 26.8 mmHg      # Normal O₂ affinity
BOHR_COEFFICIENT = -0.48    # ΔlogP50 / ΔpH
BPG_COEFFICIENT = 0.3       # ΔP50 per mM 2,3-BPG
HILL_COEFFICIENT = 2.8      # Cooperativity
```

### P50 Calculation

```
P50 = P50_normal × exp[
    BOHR_COEF × (pH - 7.4) +
    BPG_COEF × ([BPG] - 5.0) / P50_normal
]
```

### Physiological Effects

| Condition | P50 | O₂ Extraction | Clinical Impact |
|-----------|-----|---------------|-----------------|
| **Normal** | 26.8 mmHg | 24% | Baseline |
| **Acidosis** | 28-32 mmHg | 28-32% | ↑ O₂ delivery (compensatory) |
| **Alkalosis** | 24-25 mmHg | 18-22% | ↓ O₂ delivery (hypoxia risk) |

### 2,3-BPG Dynamics

- **Normal**: 4-6 mM
- **Altitude adaptation**: ↑ over days → enhanced O₂ release
- **Stored blood**: ↓ over weeks → impaired O₂ delivery

### Tracked Metrics

- Time, pHi, pHe
- [2,3-BPG] concentration
- P50 (O₂ affinity)
- O₂ saturation (arterial/venous)
- O₂ content (mL O₂/dL blood)
- O₂ extraction fraction

---

## 🔬 CLI Commands

### Basic Simulation

```bash
python src/main.py --curve-fit 1.0
```

### pH Perturbation

```bash
# Acidosis (severe)
python src/main.py --curve-fit 1.0 --ph-perturbation acidosis --ph-severity severe

# Alkalosis (moderate)
python src/main.py --curve-fit 1.0 --ph-perturbation alkalosis --ph-severity moderate

# Custom step
python src/main.py --curve-fit 1.0 --ph-perturbation step --ph-target 7.0 --ph-start 2.0

# Ramp
python src/main.py --curve-fit 1.0 --ph-perturbation ramp --ph-target 6.9 --ph-duration 8
```

### Output Structure

```
Simulations/brodbar/
├── metabolites/           # Concentration plots & PDFs
├── fluxes/               # Flux analysis reports
├── ph_analysis/          # pH dynamics plots
└── bohr_effect/          # O₂ transport metrics
    ├── bohr_metrics.csv
    ├── bohr_effect_dynamics.png
    └── bohr_summary.txt
```

---

## 📚 References

1. **Bordbar, A., et al. (2015)**  
   *Personalized Whole-Cell Kinetic Models of Metabolism*  
   Cell Systems, 1(4), 283-292  
   [DOI](https://www.cell.com/cell-systems/fulltext/S2405-4712(15)00149-0)

2. **KEGG Pathway Database**  
   https://www.genome.jp/kegg/pathway.html

3. **Supabase Documentation**  
   https://supabase.com/docs

4. **Streamlit Documentation**  
   https://docs.streamlit.io

---

## 📝 License

MIT License - See LICENSE file

---

**Last Updated:** December 2025
