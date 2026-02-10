# 🩸 RBC Metabolic Model - Python Implementation

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rbc-metabolic-model.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-spheroidai%2Frbc--metabolic--model-blue?logo=github)](https://github.com/spheroidai/rbc-metabolic-model)

Interactive Red Blood Cell metabolic simulation platform based on **Bordbar et al. (2015)**.
108 metabolites, ~200 reactions, 8 metabolic pathways, with comprehensive pH perturbation analysis and real-time visualization.

## 🚀 Quick Start

### Web Application (Streamlit)

```bash
pip install -r requirements.txt
streamlit run streamlit_app/app.py
```

The Streamlit app provides:

- 🏠 **Dashboard** — Home page with authentication and navigation
- 🧪 **Simulation** — Configure and run ODE-based metabolic simulations
- 🔬 **Flux Analysis** — Interactive metabolic flux heatmaps and time-series
- 📊 **Sensitivity Analysis** — Compare custom experimental data vs Bordbar dataset
- 📤 **Data Upload** — Import custom experimental data with intelligent metabolite mapping
- 🎯 **Parameter Calibration** — Optimize Vmax/Km parameters against experimental data
- 🗺️ **Pathway Visualization** — KEGG-style network graphs, 3D heatmaps, clustering
- ⚙️ **Admin Dashboard** — User management and simulation analytics
- 📈 **Interactive Plots** — Plotly charts with export to CSV

### Command Line Interface

For batch processing and advanced users:

```bash
python src/main.py --curve-fit 1.0 --ph-perturbation acidosis --ph-severity severe
```

## 📁 Project Structure

```
Mario_RBC_up/
├── streamlit_app/                     # Web Application
│   ├── app.py                         # Main Streamlit entry point
│   ├── .streamlit/config.toml         # Theme & server config
│   ├── core/                          # Backend modules
│   │   ├── simulation_engine.py       # ODE simulation orchestration
│   │   ├── auth.py                    # Supabase authentication
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
│   │   ├── reaction_info_complete.py  # Reaction metadata for all ~200 reactions
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
│   ├── equadiff_brodbar.py            # ODE system — 108 metabolites, 100+ injectable params
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
├── tests/                             # Test data and scripts
├── RBC/Rxn_RBC.txt                    # Reaction network definition (~200 reactions)
├── Simulations/                       # Output directory (auto-created)
├── ARCHITECTURE.md                    # Technical architecture guide
├── SUPABASE_SETUP.sql                 # Database schema for authentication
└── requirements.txt                   # Python dependencies
```

## 📖 About

Python conversion of the MATLAB-based RBC metabolic model from **Bordbar et al. (2015)** *"Personalized Whole-Cell Kinetic Models of Metabolism"*, Cell Systems 1(4), 283–292.

The model simulates red blood cell metabolism over up to 42 days of storage, including glycolysis, pentose phosphate pathway, nucleotide metabolism, glutathione redox, amino acid pools, and pH/Bohr effect dynamics.

## ⚙️ Dependencies

```bash
pip install -r requirements.txt
```

Key packages: `numpy`, `scipy`, `pandas`, `streamlit`, `plotly`, `matplotlib`, `openpyxl`, `supabase` (optional, for authentication).

## 🧪 CLI Usage

### Basic Simulation

```bash
python src/main.py --curve-fit 1.0
```

### pH Perturbation Scenarios

```bash
# Acidosis (severe)
python src/main.py --curve-fit 1.0 --ph-perturbation acidosis --ph-severity severe

# Alkalosis (moderate)
python src/main.py --curve-fit 1.0 --ph-perturbation alkalosis --ph-severity moderate

# Custom pH ramp
python src/main.py --curve-fit 1.0 --ph-perturbation ramp --ph-target 6.9 --ph-duration 8
```

### Simulation Output

Results are written to `Simulations/brodbar/`:

```
Simulations/brodbar/
├── metabolites/     # Concentration plots & PDFs
├── fluxes/          # Flux heatmaps, pathway plots
├── ph_analysis/     # pH dynamics plots
└── bohr_effect/     # P50, O₂ saturation metrics
```

## 🔬 Model Highlights

- **108 metabolites** (106 base + pHi + pHe)
- **~200 reactions** across 8 pathways
- **100+ injectable Vmax/Km parameters** via `custom_params` dict
- **Curve fitting**: blend Michaelis-Menten kinetics with experimental trajectories (0–100%)
- **pH dynamics**: 26 pH-sensitive enzymes, proton transport (NHE, AE1, diffusion)
- **Bohr effect**: P50, O₂ saturation, 2,3-BPG coupling

## 📚 References

1. **Bordbar, A., et al. (2015)** — *Personalized Whole-Cell Kinetic Models of Metabolism* — Cell Systems, 1(4), 283–292 — [DOI](https://www.cell.com/cell-systems/fulltext/S2405-4712(15)00149-0)

## 📝 License

MIT License — See LICENSE file
