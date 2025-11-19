# 🩸 RBC Metabolic Model - Python Implementation

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rbc-metabolic-model.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-spheroidai%2Frbc--metabolic--model-blue?logo=github)](https://github.com/spheroidai/rbc-metabolic-model)

Interactive Red Blood Cell metabolic simulation platform with comprehensive pH perturbation analysis and real-time visualization.

## 🚀 Quick Start

### Web Application (Streamlit)

**Try it online:** [Live Demo](https://your-app-name.streamlit.app)

Or run locally:

```bash
streamlit run streamlit_app/app.py
```

The Streamlit app provides:

- 🏠 **Interactive Dashboard** - User-friendly interface with navigation
- 🚀 **Simulation Engine** - Configure and run metabolic simulations
- 🧪 **pH Perturbation** - Acidosis, alkalosis, step, and ramp scenarios
- 🔬 **Flux Analysis** - Interactive metabolic flux visualization and heatmaps
- 📊 **Sensitivity Analysis** - Compare custom experimental data vs Brodbar dataset
- 📤 **Data Upload** - Import custom experimental data with intelligent metabolite mapping
- 📈 **Real-time Visualization** - Interactive Plotly charts
- 💾 **Data Export** - CSV formats for results and flux data

### Command Line Interface

For batch processing and advanced users:

```bash
python src/main.py --curve-fit 1.0 --ph-perturbation acidosis
```

## 📖 About

This project is a Python conversion of the MATLAB-based RBC (Red Blood Cell) metabolic model simulation, based on **Bordbar et al. (2015)**. The model simulates the metabolic behavior of red blood cells using differential equations and experimental curve-fitting.

## Project Structure

- **`streamlit_app/`** - Web application
  - `app.py` - Streamlit home page
  - `pages/1_Simulation.py` - Interactive simulation interface
  - `core/` - Backend modules
    - `simulation_engine.py` - Simulation orchestration
    - `plotting.py` - Interactive Plotly visualizations
    - `data_loader.py` - Data validation and loading
  - `.streamlit/config.toml` - Streamlit configuration

- **`src/`** - Python CLI source code
  - `main.py` - Main simulation script with CLI arguments
  - `equadiff_brodbar.py` - Bordbar 2015 model with 108 metabolites
  - `curve_fit.py` - Experimental data curve fitting
  - `ph_perturbation.py` - Dynamic pH perturbation system
  - `ph_sensitivity_params.py` - pH-dependent enzyme modulation
  - `bohr_effect.py` - Bohr effect and O2 transport
  - `flux_visualization.py` - Metabolic flux analysis

- **`Documentation/`** - Complete project documentation
  - `pH_PROJECT_FINAL_COMPLETE.md` - Main project documentation
  - `BOHR_INTEGRATION_COMPLETE.md` - Bohr effect integration

- **Data files**
  - `Data_Brodbar_et_al_exp.xlsx` - Experimental time-series data
  - `Initial_conditions_JA_Final.xls` - Initial metabolite concentrations
  - `requirements.txt` - Python dependencies

## Dependencies

The required Python packages are listed in `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

Activate the virtual environment (recommended):

```powershell
.\activate_venv.ps1
```

Run a basic simulation:

```bash
python src/main.py --curve-fit 1.0
```

### pH Perturbation Simulations

**Acidosis (severe):**
```bash
python src/main.py --curve-fit 1.0 --ph-perturbation acidosis --ph-severity severe
```

**Alkalosis (moderate):**
```bash
python src/main.py --curve-fit 1.0 --ph-perturbation alkalosis --ph-severity moderate
```

**Custom pH ramp:**
```bash
python src/main.py --curve-fit 1.0 --ph-perturbation ramp --ph-target 6.9 --ph-duration 8
```

### Simulation Output

The simulation will:
1. Load experimental data (Brodbar et al. 2015)
2. Setup initial conditions (108 metabolites)
3. Solve ODEs with pH perturbations
4. Track metabolic fluxes (89 reactions)
5. Calculate Bohr effect (P50, O2 saturation)
6. Generate plots and PDFs in `Simulations/brodbar/`

### Individual Module Usage

Each module can also be used independently:

```python
# Process experimental data with curve fitting
from curve_fit import curve_fit_ja
meta_names, metabolites, params, times = curve_fit_ja("Data_Bardyn_et_al_ctrl")

# Parse a reaction network file
from parse import parse
model = parse("RBC/Rxn_RBC.txt")

# Load initial conditions
from parse_initial_conditions import parse_initial_conditions
x0, x0_names = parse_initial_conditions(model, "Initial_conditions_JA_Final.xls")

# Solve the system of differential equations
from solver import solver
t, x = solver(x0, [0, 42], model)

# Visualize results
from visualization import plot_metabolite_results
plot_metabolite_results(t, x, model)
```

## Original MATLAB Project

The original MATLAB project consisted of several key files:

- `protocole_RBC_JA2020.m` - Main script for simulation execution and visualization
- `CurvefitJA.m` - Processes data with curve fitting
- `parse.m` - Generates the model from reaction descriptions
- `parse_initcond_ja.m` - Provides initial condition vectors
- `solver.m` - Performs numerical integration using ODE solvers
- `equadiff.m` - Contains the differential equations

## Data Files

The Excel files containing initial conditions and metabolite data remain in their original format and location:

- `Initial_conditions_JA_Final.xls` - Contains the final initial conditions
- `Data_Bardyn_et_al_ctrl.xlsx` and `Data_Brodbar_et_al_exp.xlsx` - Experimental data

## Implementation Notes

### Model Implementation

The Python implementation uses modern scientific computing libraries:

- NumPy for numerical operations
- pandas for data handling
- SciPy for numerical integration
- Matplotlib for visualization

### Differences from MATLAB Version

1. **Object-Oriented Approach**: The Python version uses a more modular structure.
2. **Numerical Integration**: Uses SciPy's `solve_ivp` instead of MATLAB's `ode15s`.
3. **Plotting**: Matplotlib-based plotting functions provide similar visualizations to the MATLAB figures.
4. **Error Handling**: More robust error handling throughout the code.

### Future Improvements

1. Further optimization of the differential equations implementation
2. Addition of parameter estimation capabilities
3. Interactive visualization using modern Python libraries like Plotly
4. Parallel computation for more efficient simulation of large models
