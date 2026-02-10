# 🏗️ RBC Metabolic Model - Architecture & Technical Guide

**Version:** 2.1  
**Author:** Jorgelindo da Veiga  
**Based on:** Bordbar et al. (2015) RBC metabolic model

---

## 📁 Project Structure

```text
Mario_RBC_up/
├── streamlit_app/                     # Web Application
│   ├── app.py                         # Main Streamlit entry point
│   ├── .streamlit/
│   │   ├── config.toml                # Theme & server config
│   │   └── secrets.toml               # Supabase credentials (git-ignored)
│   ├── core/                          # Backend modules
│   │   ├── auth.py                    # Supabase authentication manager
│   │   ├── simulation_engine.py       # ODE simulation orchestration
│   │   ├── plotting.py                # Interactive Plotly visualizations
│   │   ├── data_loader.py             # Data validation and loading
│   │   ├── parameter_calibration.py   # Parameter optimization (DE, L-BFGS-B, LS)
│   │   ├── flux_plotting.py           # Flux heatmaps and distributions
│   │   ├── flux_estimator.py          # Experimental flux estimation
│   │   ├── bohr_plotting.py           # Bohr effect visualizations
│   │   ├── sensitivity_engine.py      # Dataset comparison engine
│   │   ├── sensitivity_plotting.py    # Sensitivity result plots
│   │   ├── pathway_visualization.py   # Network graphs and clustering
│   │   ├── metabolite_mapper.py       # Column name → model metabolite mapping
│   │   ├── data_preprocessor.py       # Uploaded data preprocessing
│   │   ├── reaction_info_complete.py  # Reaction metadata (~200 reactions)
│   │   └── styles.py                  # UI theme and CSS
│   ├── data/
│   │   └── metabolite_synonyms.json   # Name synonym database
│   └── pages/                         # Streamlit pages (0–7)
│       ├── 0_Login.py                 # Authentication
│       ├── 1_Simulation.py            # Run simulations
│       ├── 2_Flux_Analysis.py         # Flux heatmaps and comparison
│       ├── 3_Sensitivity_Analysis.py  # Dataset comparison
│       ├── 4_Data_Upload.py           # Custom data import
│       ├── 5_Parameter_Calibration.py # Model calibration
│       ├── 6_Admin.py                 # User management
│       └── 7_Pathway_Visualization.py # Network visualization
├── src/                               # Core Backend & CLI
│   ├── main.py                        # CLI entry point (argparse)
│   ├── equadiff_brodbar.py            # ODE system — 108 metabolites, 100+ params
│   ├── curve_fit.py                   # Experimental data curve fitting
│   ├── curve_fitting_data.py          # Polynomial fit coefficients (55 metabolites)
│   ├── parse_initial_conditions.py    # Load initial concentrations from Excel
│   ├── ph_perturbation.py             # PhPerturbation class (step/ramp/pulse/sinusoidal)
│   ├── ph_sensitivity_params.py       # pH-dependent enzyme modulation (26 enzymes)
│   ├── bohr_effect.py                 # O₂ affinity, P50, Hill equation
│   ├── model.py                       # Reaction network loader (CLI)
│   ├── parse.py                       # Rxn_RBC.txt parser (CLI)
│   ├── solver.py                      # ODE solver wrapper (CLI, deprecated)
│   ├── visualization.py               # Matplotlib plots (CLI)
│   ├── flux_visualization.py          # FluxTracker + CLI flux plots
│   ├── Data_Bordbar_et_al_exp.xlsx    # Experimental time-series (14 timepoints)
│   └── Initial_conditions_JA_Final.xls# Initial metabolite concentrations
├── tests/                             # Test data and utility scripts
├── RBC/Rxn_RBC.txt                    # Reaction network definition (~200 reactions)
├── Simulations/                       # Output directory (auto-created)
├── requirements.txt                   # Python dependencies
└── SUPABASE_SETUP.sql                 # Database schema
```

---

## 🔬 Model Specifications

| Component | Value |
| --- | --- |
| **Metabolites** | 108 (106 base + pHi + pHe) |
| **Reactions** | ~200 biochemical reactions |
| **Pathways** | 8 major pathways |
| **Data Points** | 14 experimental timepoints |
| **Simulation Duration** | Up to 42 days |

### Metabolic Pathways

- **Glycolysis**: GLC → G6P → F6P → FBP → ... → PYR → LAC
- **Pentose Phosphate**: G6P → GL6P → RU5P → R5P/X5P (NADPH production)
- **Rapoport-Luebering Shunt**: B13PG ↔ B23PG (O₂ affinity control)
- **Nucleotide Metabolism**: ATP/ADP/AMP, GTP/GDP, purine salvage
- **Amino Acid Pool**: GLY, SER, ALA, GLU, GLN, ASP, ARG, MET, CYS
- **Glutathione System**: GSH/GSSG, GR, GPx (antioxidant defense)
- **One-Carbon Metabolism**: THF, METTHF, SAM/SAH
- **Transport**: All E-prefixed metabolites (EGLC, ELAC, etc.)

---

## 🔐 Authentication System

### Technology Stack

- **Backend**: Supabase PostgreSQL
- **Auth**: Supabase Auth (email/password)
- **Security**: Row Level Security (RLS)

### Database Tables

#### `user_profiles`

| Column | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key (refs auth.users) |
| email | TEXT | User email (unique) |
| full_name | TEXT | Display name |
| role | TEXT | 'user' or 'admin' |
| is_active | BOOLEAN | Account status |
| simulation_count | INTEGER | Total simulations |

#### `simulation_history`

| Column | Type | Description |
| --- | --- | --- |
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
| --- | --- | --- |
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
- **R² 0.80–0.95**: Good fit
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

1. Navigate to **Simulation**
2. Set duration (default: 42 days)
3. Configure curve fitting (40–60%)
4. Click **Start Simulation**
5. Export results as CSV

### pH Perturbation Analysis

1. Select perturbation type: Acidosis/Alkalosis/Step/Ramp
2. Set severity: Mild/Moderate/Severe
3. Run simulation
4. View Bohr effect (P50, O₂ saturation)

### Custom Data Analysis

1. **Upload**: CSV/Excel with time + metabolites
2. **Map**: Use intelligent column mapping
3. **Analyze**: Compare with Bordbar data
4. **Validate**: Check R², RMSE, MAE

### Flux Analysis

1. Run simulation first
2. Navigate to **Flux Analysis**
3. View flux distributions and heatmaps
4. Export flux data

---

## 🔧 Troubleshooting

| Issue | Solution |
| --- | --- |
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
| --- | --- | --- |
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
| --- | --- | --- |
| H⁺ Diffusion | K_DIFF_H = 0.099 | Passive proton leak |
| NHE (Na⁺/H⁺) | K_NHE = 0.110 | Active H⁺ extrusion |
| AE1 (Cl⁻/HCO₃⁻) | K_AE1 = 2.994 | Band 3 exchanger |
| Buffer Capacity | BETA = 30.0 mM/pH | Intracellular buffering |

### pH-Sensitive Enzymes (26 total)

- **Glycolysis**: HK, PFK, PK, DPGM, LDH
- **PPP**: G6PDH, 6PGDH
- **Nucleotide**: ADA, PNP
- **Redox**: GR, GPx

---

## 🫁 Bohr Effect & O₂ Transport

### Key Constants

```python
NORMAL_P50 = 26.8       # mmHg — Normal O₂ affinity
BOHR_COEFFICIENT = -0.48 # ΔlogP50 / ΔpH
BPG_COEFFICIENT = 0.3    # ΔP50 per mM 2,3-BPG
HILL_COEFFICIENT = 2.8   # Cooperativity
```

### P50 Calculation

```text
P50 = P50_normal × exp[
    BOHR_COEF × (pH - 7.4) +
    BPG_COEF × ([BPG] - 5.0) / P50_normal
]
```

### Physiological Effects

| Condition | P50 | O₂ Extraction | Clinical Impact |
| --- | --- | --- | --- |
| **Normal** | 26.8 mmHg | 24% | Baseline |
| **Acidosis** | 28–32 mmHg | 28–32% | ↑ O₂ delivery (compensatory) |
| **Alkalosis** | 24–25 mmHg | 18–22% | ↓ O₂ delivery (hypoxia risk) |

### 2,3-BPG Dynamics

- **Normal**: 4–6 mM
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

## 📚 References

1. **Bordbar, A., et al. (2015)** — *Personalized Whole-Cell Kinetic Models of Metabolism* — Cell Systems, 1(4), 283–292 — [DOI](https://www.cell.com/cell-systems/fulltext/S2405-4712(15)00149-0)
2. **KEGG Pathway Database** — [genome.jp/kegg](https://www.genome.jp/kegg/pathway.html)
3. **Supabase Documentation** — [supabase.com/docs](https://supabase.com/docs)
4. **Streamlit Documentation** — [docs.streamlit.io](https://docs.streamlit.io)

---

## 📝 License

MIT License — See LICENSE file

---

**Last Updated:** February 2026
