"""
Simulation Engine - Wrapper for RBC metabolic simulations
Integrates with existing src/ code for Streamlit interface
"""
import streamlit as st
import numpy as np
from scipy.integrate import solve_ivp
import time
from pathlib import Path
import sys

# Add src to path - calculate from this file's actual location
# __file__ is in streamlit_app/core/simulation_engine.py
# So parent = core, parent.parent = streamlit_app, parent.parent.parent = project root
this_file = Path(__file__).resolve()
project_root = this_file.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


class SimpleFluxTracker:
    """Simple flux tracker compatible with equadiff_brodbar."""
    def __init__(self):
        self.times = []
        self.fluxes = {}
    
    def add_timepoint(self, t: float, flux_dict: dict):
        """Add flux values for a specific timepoint."""
        self.times.append(t)
        for reaction, flux in flux_dict.items():
            if reaction not in self.fluxes:
                self.fluxes[reaction] = []
            self.fluxes[reaction].append(flux)


# Import existing modules
try:
    from equadiff_brodbar import equadiff_brodbar, BRODBAR_METABOLITE_MAP
    from equadiff_brodbar import enable_pH_modulation, disable_pH_modulation
    from equadiff_brodbar import enable_bohr_tracking, disable_bohr_tracking
    from equadiff_brodbar import enable_flux_tracking, disable_flux_tracking
    from curve_fit import curve_fit_ja
    from parse_initial_conditions import parse_initial_conditions
    from ph_perturbation import (PhPerturbation, create_step_perturbation,
                                 create_ramp_perturbation, get_acidosis_scenario,
                                 get_alkalosis_scenario)
    SIMULATION_AVAILABLE = True
    PH_MODULES_AVAILABLE = True
except ImportError as e:
    SIMULATION_AVAILABLE = False
    PH_MODULES_AVAILABLE = False
    import traceback
    error_details = traceback.format_exc()
    st.error(f"❌ Could not import simulation modules:\n```python\n{error_details}\n```")
    
    # Show debugging info
    st.info(f"""🔍 **Path Debug Info:**
- This file: `{this_file}`
- Project root: `{project_root}`
- Src path: `{src_path}`
- Src exists: `{src_path.exists()}`
- equadiff_brodbar.py exists: `{(src_path / 'equadiff_brodbar.py').exists()}`
    """)
    
    st.warning("""💡 **Common Fixes:**
1. Make sure you're in the correct venv
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Verify src/ modules don't have import errors
    """)


class SimulationEngine:
    """
    RBC Metabolic Model Simulation Engine for Streamlit
    """
    
    def __init__(self):
        self.results = None
        self.status = "idle"
        self.error_message = None
        
    def run_simulation(self, 
                      t_max=42, 
                      curve_fit_strength=1.0,
                      ic_source="JA Final",
                      solver_method="RK45",
                      rtol=1e-6,
                      atol=1e-8,
                      ph_perturbation_type="None",
                      ph_severity="Moderate",
                      ph_target=7.0,
                      ph_duration=6,
                      progress_callback=None):
        """
        Run RBC metabolic simulation
        
        Parameters:
        -----------
        t_max : float
            Maximum simulation time (days)
        curve_fit_strength : float
            Curve fitting strength (0.0 to 1.0)
        ic_source : str
            Initial conditions source
        solver_method : str
            ODE solver method ('RK45', 'BDF', 'LSODA')
        rtol, atol : float
            Relative and absolute tolerances
        progress_callback : callable
            Function(progress, message) for progress updates
        
        Returns:
        --------
        dict : Simulation results
        """
        
        if not SIMULATION_AVAILABLE:
            return {"error": "Simulation modules not available"}
        
        try:
            self.status = "running"
            start_time = time.time()
            
            # Update progress
            if progress_callback:
                progress_callback(0.1, "Loading experimental data...")
            
            # Load experimental data directly like CLI does
            # Same strategy as main.py: load directly from Excel with pandas
            try:
                import pandas as pd
                data_file = project_root / "Data_Brodbar_et_al_exp.xlsx"
                df = pd.read_excel(data_file)
                
                # Extract metabolite names and data (same as CLI main.py)
                experimental_metabolites = df.iloc[:, 0].tolist()  # First column = metabolite names
                metabolites_data = df.iloc[:, 1:].values  # Remaining columns = concentrations
                time_exp = np.array([float(col) for col in df.columns[1:]])  # Column headers = time points
                
                # Keep original shape: (n_metabolites, n_timepoints) like CLI
                # This is the format expected by visualization
                experimental_values = metabolites_data
                
                if progress_callback:
                    progress_callback(0.15, f"Loaded {len(experimental_metabolites)} experimental metabolites")
                
            except Exception as e:
                if progress_callback:
                    progress_callback(0.15, f"Warning: Could not load experimental data: {e}")
                experimental_metabolites = []
                experimental_values = np.array([])
                time_exp = np.array([])
            
            # Load custom validation data if available
            custom_val_metabolites = []
            custom_val_values = np.array([])
            custom_val_time = np.array([])
            
            # Check for custom validation data in session state
            mode = st.session_state.get('uploaded_data_mode', '')
            uploaded_active = st.session_state.get('uploaded_data_active', False)
            
            if uploaded_active and mode == "Use for validation only":
                if 'uploaded_data' in st.session_state:
                    custom_df = st.session_state['uploaded_data']
                    
                    if custom_df is not None and not custom_df.empty:
                        # Extract time and metabolite data
                        if 'Time' in custom_df.columns:
                            custom_val_time = custom_df['Time'].values
                            custom_val_metabolites = [col for col in custom_df.columns if col != 'Time']
                            
                            # Build values array (n_metabolites, n_timepoints)
                            custom_val_values = np.array([custom_df[met].values for met in custom_val_metabolites])
                            
                            if progress_callback:
                                progress_callback(0.17, f"Loaded {len(custom_val_metabolites)} custom metabolites for validation")
            
            if progress_callback:
                progress_callback(0.2, "Setting up initial conditions...")
            
            # Create model structure for Brodbar
            metabolite_list = [''] * 107
            for name, idx in BRODBAR_METABOLITE_MAP.items():
                if idx < 107:
                    metabolite_list[idx] = name
            model = {'metab': metabolite_list}
            
            # Parse initial conditions
            ic_file = src_path / "Initial_conditions_JA_Final.xls"
            x0, x0_names = parse_initial_conditions(model, str(ic_file))
            n_metabolites = len(x0)
            
            if progress_callback:
                progress_callback(0.25, "Configuring pH perturbation...")
            
            # Configure pH perturbation if requested
            ph_perturbation = None
            if ph_perturbation_type != "None" and PH_MODULES_AVAILABLE:
                try:
                    if ph_perturbation_type == "Acidosis":
                        ph_perturbation = get_acidosis_scenario(ph_severity)
                        if progress_callback:
                            progress_callback(0.28, f"pH: Acidosis ({ph_severity})")
                    elif ph_perturbation_type == "Alkalosis":
                        ph_perturbation = get_alkalosis_scenario(ph_severity)
                        if progress_callback:
                            progress_callback(0.28, f"pH: Alkalosis ({ph_severity})")
                    elif ph_perturbation_type == "Step":
                        ph_perturbation = create_step_perturbation(
                            pH_target=ph_target,
                            t_start=2.0
                        )
                        if progress_callback:
                            progress_callback(0.28, f"pH: Step to {ph_target}")
                    elif ph_perturbation_type == "Ramp":
                        ph_perturbation = create_ramp_perturbation(
                            pH_initial=7.4,
                            pH_final=ph_target,
                            t_start=2.0,
                            duration=ph_duration
                        )
                        if progress_callback:
                            progress_callback(0.28, f"pH: Ramp to {ph_target} over {ph_duration}h")
                    
                    if ph_perturbation:
                        # Enable pH modulation in equadiff_brodbar
                        enable_pH_modulation(ph_perturbation)
                        if progress_callback:
                            progress_callback(0.3, "pH modulation enabled")
                except Exception as e:
                    if progress_callback:
                        progress_callback(0.3, f"Warning: pH setup failed - {str(e)}")
                    ph_perturbation = None
            
            # Add pHe to initial conditions if pH perturbation is active
            if ph_perturbation:
                # System needs 108 metabolites: 106 base + pHi + pHe
                # x0 currently has 107 metabolites (106 + pHi)
                # Add pHe at physiological value (7.4)
                x0 = np.append(x0, 7.4)
                n_metabolites = len(x0)
                if progress_callback:
                    progress_callback(0.3, f"Added pHe to initial conditions (108 metabolites)")
            
            # Enable Bohr effect tracking if pH perturbation is active
            bohr_data = None
            if ph_perturbation and PH_MODULES_AVAILABLE:
                try:
                    bohr_data = {}  # Will store Bohr metrics
                    if enable_bohr_tracking(bohr_data):
                        if progress_callback:
                            progress_callback(0.32, "✓ Bohr effect tracking enabled")
                except Exception as e:
                    if progress_callback:
                        progress_callback(0.32, f"⚠️ Bohr tracking unavailable: {e}")
                    bohr_data = None
            
            # Enable flux tracking for all simulations
            flux_tracker = None
            try:
                # Initialize flux tracker
                flux_tracker = SimpleFluxTracker()
                if enable_flux_tracking(flux_tracker):
                    if progress_callback:
                        progress_callback(0.33, "✓ Flux tracking enabled")
            except Exception as e:
                if progress_callback:
                    progress_callback(0.33, f"⚠️ Flux tracking unavailable: {e}")
                flux_tracker = None
            
            if progress_callback:
                progress_callback(0.35, f"Starting integration ({n_metabolites} metabolites)...")
            
            # Time span
            t_span = (0, t_max)
            t_eval = np.linspace(0, t_max, 75)  # 75 time points
            
            # Create ODE function wrapper with curve fitting strength
            # Verify curve_fitting_data availability
            if curve_fit_strength > 0:
                try:
                    from curve_fitting_data import CURVE_FIT_PARAMS
                    if progress_callback:
                        progress_callback(0.35, f"✓ Curve fitting module loaded ({len(CURVE_FIT_PARAMS)} metabolites)")
                except ImportError as e:
                    if progress_callback:
                        progress_callback(0.35, f"⚠️ Curve fitting unavailable: {e}")
            
            def ode_func(t, x):
                return equadiff_brodbar(t, x, thermo_constraints=None, 
                                       custom_params=None,
                                       curve_fit_strength=curve_fit_strength)
            
            if progress_callback:
                progress_callback(0.4, f"Integrating with {solver_method} solver...")
            
            # Solve ODE system
            sol = solve_ivp(
                ode_func,
                t_span,
                x0,
                method=solver_method,
                t_eval=t_eval,
                rtol=rtol,
                atol=atol,
                dense_output=True
            )
            
            if not sol.success:
                raise RuntimeError(f"Integration failed: {sol.message}")
            
            if progress_callback:
                progress_callback(0.8, "Processing results...")
            
            # Get metabolite names in correct index order (not dictionary order!)
            # This is CRITICAL: sol.y columns are ordered by index 0-106, not by dict insertion order
            # Same logic as CLI main.py which builds metabolite_list correctly
            metabolite_names = [''] * 107
            for name, idx in BRODBAR_METABOLITE_MAP.items():
                if idx < 107:
                    metabolite_names[idx] = name
            
            # Add PHE to metabolite names if pH perturbation was active
            if ph_perturbation and n_metabolites == 108:
                metabolite_names.append('PHE')  # Extracellular pH
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Clean up pH modulation, Bohr tracking, and flux tracking after integration
            if ph_perturbation and PH_MODULES_AVAILABLE:
                try:
                    disable_pH_modulation()
                    disable_bohr_tracking()
                except:
                    pass
            
            # Disable flux tracking
            try:
                disable_flux_tracking()
            except:
                pass
            
            if progress_callback:
                progress_callback(1.0, "Simulation completed!")
            
            # Prepare results
            self.results = {
                't': sol.t,
                'x': sol.y.T,  # Transpose to (time, metabolites)
                'metabolite_names': metabolite_names,
                'n_points': len(sol.t),
                'n_metabolites': n_metabolites,
                'duration': duration,
                'success': True,
                'solver': solver_method,
                'curve_fit_strength': curve_fit_strength,
                'ph_perturbation': {
                    'type': ph_perturbation_type,
                    'severity': ph_severity if ph_perturbation_type in ["Acidosis", "Alkalosis"] else None,
                    'target': ph_target if ph_perturbation_type in ["Step", "Ramp"] else None,
                    'duration': ph_duration if ph_perturbation_type == "Ramp" else None,
                    'description': ph_perturbation.get_description() if ph_perturbation else "None"
                },
                'bohr_effect': bohr_data if bohr_data and len(bohr_data.get('time', [])) > 0 else None,
                'flux_data': {'times': flux_tracker.times, 'fluxes': flux_tracker.fluxes} if flux_tracker and len(flux_tracker.times) > 0 else None,
                'experimental_data': {
                    'time': time_exp if time_exp is not None else [],
                    'metabolites': experimental_metabolites,
                    'values': experimental_values
                },
                'custom_validation_data': {
                    'time': custom_val_time,
                    'metabolites': custom_val_metabolites,
                    'values': custom_val_values
                } if len(custom_val_metabolites) > 0 else None
            }
            
            self.status = "completed"
            return self.results
            
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            if progress_callback:
                progress_callback(1.0, f"Error: {str(e)}")
            return {"error": str(e), "success": False}
    
    def get_results(self):
        """Get last simulation results"""
        return self.results
    
    def get_status(self):
        """Get current simulation status"""
        return self.status


@st.cache_data(show_spinner=False)
def run_cached_simulation(t_max, curve_fit_strength, ic_source, solver_method, rtol, atol):
    """
    Run simulation with Streamlit caching
    Cached based on parameters for faster repeat runs
    """
    engine = SimulationEngine()
    results = engine.run_simulation(
        t_max=t_max,
        curve_fit_strength=curve_fit_strength,
        ic_source=ic_source,
        solver_method=solver_method,
        rtol=rtol,
        atol=atol
    )
    return results


def get_metabolite_data(results, metabolite_name):
    """
    Extract time series for a specific metabolite
    
    Parameters:
    -----------
    results : dict
        Simulation results
    metabolite_name : str
        Name of metabolite
    
    Returns:
    --------
    tuple : (time_array, concentration_array)
    """
    if not results or 'error' in results:
        return None, None
    
    try:
        idx = results['metabolite_names'].index(metabolite_name)
        return results['t'], results['x'][:, idx]
    except (ValueError, KeyError):
        return None, None


def export_results_csv(results):
    """
    Export simulation results to CSV format
    
    Returns:
    --------
    str : CSV formatted string
    """
    import io
    
    if not results or 'error' in results:
        return ""
    
    output = io.StringIO()
    
    # Header
    output.write("Time," + ",".join(results['metabolite_names']) + "\n")
    
    # Data rows
    for i, t in enumerate(results['t']):
        row = [str(t)] + [str(results['x'][i, j]) for j in range(results['n_metabolites'])]
        output.write(",".join(row) + "\n")
    
    return output.getvalue()
