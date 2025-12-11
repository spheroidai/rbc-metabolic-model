"""
Python equivalent of the equadiff_Brodbar.m MATLAB script.
This file defines the differential equations for the RBC metabolic model.
Author: Jorgelindo da Veiga
"""
import numpy as np
import math
import pandas as pd
from typing import Dict, Tuple, Optional
from numpy.typing import NDArray
from pathlib import Path

# Get src directory for data file paths
_THIS_FILE = Path(__file__).resolve()
_SRC_DIR = _THIS_FILE.parent  # This file is in src/
_DATA_FILE = _SRC_DIR / "Data_Brodbar_et_al_exp.xlsx"
_IC_FILE = _SRC_DIR / "Initial_conditions_JA_Final.xls"

# Global flux tracking
_FLUX_TRACKER = None
_TRACK_FLUXES = False

# Global pH perturbation tracking
_PH_PERTURBATION = None
_ENABLE_PH_MODULATION = False

try:
    from ph_sensitivity_params import compute_pH_modulation
    from ph_perturbation import PhPerturbation
    PH_MODULES_AVAILABLE = True
except ImportError:
    PH_MODULES_AVAILABLE = False
    print("Warning: pH perturbation modules not available")

try:
    from bohr_effect import BohrEffect
    BOHR_MODULE_AVAILABLE = True
except ImportError:
    BOHR_MODULE_AVAILABLE = False
    print("Warning: Bohr effect module not available")

# Global Bohr effect tracker
_BOHR_EFFECT = None
_BOHR_TRACKER = None
_TRACK_BOHR = False

def enable_flux_tracking(flux_tracker=None):
    """
    Enable flux tracking during ODE integration.
    
    Parameters:
    -----------
    flux_tracker : FluxTracker, optional
        FluxTracker object to store flux data
    """
    global _FLUX_TRACKER, _TRACK_FLUXES
    _FLUX_TRACKER = flux_tracker
    _TRACK_FLUXES = True

def disable_flux_tracking():
    """Disable flux tracking."""
    global _FLUX_TRACKER, _TRACK_FLUXES
    _FLUX_TRACKER = None
    _TRACK_FLUXES = False

def enable_pH_modulation(ph_perturbation=None):
    """
    Enable pH-dependent enzyme modulation.
    
    Parameters:
    -----------
    ph_perturbation : PhPerturbation, optional
        PhPerturbation object defining extracellular pH dynamics
    """
    global _PH_PERTURBATION, _ENABLE_PH_MODULATION
    if not PH_MODULES_AVAILABLE:
        print("Warning: pH modules not available, modulation disabled")
        return
    _PH_PERTURBATION = ph_perturbation
    _ENABLE_PH_MODULATION = True
    print("✓ pH-dependent enzyme modulation ENABLED")

def disable_pH_modulation():
    """Disable pH-dependent enzyme modulation."""
    global _PH_PERTURBATION, _ENABLE_PH_MODULATION
    _PH_PERTURBATION = None

def enable_bohr_tracking(bohr_tracker=None):
    """
    Enable Bohr effect tracking during ODE integration.
    
    Parameters:
    -----------
    bohr_tracker : dict or object, optional
        Storage for Bohr effect metrics (P50, O2 saturation, etc.)
    """
    global _BOHR_EFFECT, _BOHR_TRACKER, _TRACK_BOHR
    if not BOHR_MODULE_AVAILABLE:
        print("⚠ Bohr effect module not available, tracking disabled")
        return False
    
    _BOHR_EFFECT = BohrEffect()
    
    # Initialize bohr_tracker with all required keys
    if bohr_tracker is None:
        bohr_tracker = {}
    
    # Ensure all required keys exist
    required_keys = ['time', 'pHi', 'pHe', 'BPG_mM', 'P50_mmHg', 'sat_arterial', 'sat_venous', 
                    'O2_extracted_fraction', 'O2_arterial_mL_per_dL', 'O2_venous_mL_per_dL']
    for key in required_keys:
        if key not in bohr_tracker:
            bohr_tracker[key] = []
    
    _BOHR_TRACKER = bohr_tracker
    _TRACK_BOHR = True
    print("✓ Bohr effect tracking ENABLED")
    return True

def disable_bohr_tracking():
    """Disable Bohr effect tracking."""
    global _BOHR_EFFECT, _BOHR_TRACKER, _TRACK_BOHR
    _BOHR_EFFECT = None
    _BOHR_TRACKER = None
    _TRACK_BOHR = False

# from thermodynamic_constraints import ThermodynamicConstraints  # Commented out - missing module
# from parse import parse  # Commented out - not needed for testing

# ===== MODEL STRUCTURE CONSTANTS =====
NUM_BASE_METABOLITES = 106  # Core metabolites from reaction network
NUM_TOTAL_METABOLITES = 108  # 106 base + pHi at index 106 + pHe at index 107
H2O2_INDEX = 79  # H2O2 is part of base metabolites
PHI_INDEX = 106  # Intracellular pH (pHi) dynamic metabolite
PHE_INDEX = 107  # Extracellular pH (pHe) - NEW
B23PG_INDEX = 15  # 2,3-Bisphosphoglycerate (2,3-BPG) for Bohr effect

# ===== NUMERICAL SAFETY BOUNDS =====
MIN_CONCENTRATION = 1e-6  # Minimum metabolite concentration (mM)
MIN_KM = 1e-6  # Minimum Km to prevent division by zero
MIN_LOG_VALUE = 1e-10  # Minimum value for logarithm operations
MAX_DERIVATIVE = 1e3  # Maximum absolute derivative for numerical stability

# ===== PHYSICAL CONSTANTS =====
PHYSIOLOGICAL_PH = 7.2  # Normal intracellular pH for RBC
PHYSIOLOGICAL_PHE = 7.4  # Normal extracellular pH

# ===== pH TRANSPORT PARAMETERS =====
# Parameters for proton transport across RBC membrane
# OPTIMIZED VALUES from ph_calibration.py (Option 3)
K_DIFF_H = 0.099  # Passive H+ diffusion coefficient (pH units/min) [OPTIMIZED: 0.030 → 0.099]
K_NHE = 0.110     # Na+/H+ exchanger activity coefficient [OPTIMIZED: 0.700 → 0.110]
K_AE1 = 2.994     # Cl-/HCO3- exchanger (Band 3) activity coefficient [OPTIMIZED: 1.500 → 2.994]
BETA_BUFFER = 30.0  # Intracellular buffering capacity (mM/pH unit) [OPTIMIZED: 70.0 → 30.0]
                    # Primarily hemoglobin (~65%) + phosphates (~25%) + proteins (~10%)
                    # Lower buffer = faster pHi response to pHe changes


def mm(substrate: float, km: float, hill_coef: float = 1.0) -> float:
    """
    Michaelis-Menten kinetic function with safety checks.
    
    Parameters:
    -----------
    substrate : float
        Substrate concentration
    km : float
        Michaelis-Menten constant
    hill_coef : float, optional
        Hill coefficient (default: 1.0)
    
    Returns:
    --------
    float
        Reaction rate (0.0 to 1.0)
    """
    # Safety checks to prevent infinite loops
    if substrate < 0:
        substrate = 0.0
    if km <= 0:
        km = MIN_KM  # Prevent division by zero
    
    try:
        result = substrate**hill_coef / (km**hill_coef + substrate**hill_coef)
        # Check for NaN or Inf
        if np.isnan(result) or np.isinf(result):
            return 0.0
        return result
    except:
        return 0.0

def logt(t: float) -> float:
    """Helper function for safe logarithm computation.
    
    Parameters:
    -----------
    t : float
        Time or value to compute logarithm of
        
    Returns:
    --------
    float
        Natural logarithm of t (with minimum bound to prevent log(0))
    """
    return math.log(max(t, MIN_LOG_VALUE))  # Avoid log(0)

# Clean MM model - no electrical functions needed

# Load first-column experimental values once for data-driven totals and anchors
EXP_FIRST_VALUES = {}
TOTALS = {
    'A_tot': None,
    'NAD_total': None,
    'NADP_total': None,
    'GSH_tot': None,
    'ELAC_first': None,
    'EGLC_first': None,
}

def _normalize_name(n: str) -> str:
    n = str(n).upper().strip()
    # Remove spaces and plus signs commonly used for cofactors
    n = n.replace(' ', '')
    n = n.replace('+', '')  # e.g., NAD+ -> NAD
    return n

def _load_experimental_first_values(path: str = None) -> None:
    """Load experimental first time point values for conservation pool calculations.
    
    Parameters:
    -----------
    path : str, optional
        Path to Excel file with experimental data. If None, uses default project path.
        
    Returns:
    --------
    None
        Updates global EXP_FIRST_VALUES and TOTALS dictionaries
    """
    global EXP_FIRST_VALUES, TOTALS
    if EXP_FIRST_VALUES:
        return  # already loaded
    
    # Use absolute path from project root if no path specified
    if path is None:
        path = _DATA_FILE
    
    try:
        df = pd.read_excel(path)
        # Normalize names to improve matching (handle NAD+/NADP+ etc.)
        raw_names = df.iloc[:,0].astype(str).tolist()
        names = [_normalize_name(n) for n in raw_names]
        vals = df.iloc[:,1].astype(float).tolist()
        tmp_map = {n:v for n, v in zip(names, vals) if pd.notna(v)}
        # Canonicalize synonyms
        syn = {
            'NADPLUS': 'NAD',
            'NADPPLUS': 'NADP',
            'EGLC': 'EGLC',
            'ELAC': 'ELAC',
        }
        EXP_FIRST_VALUES = {}
        for k, v in tmp_map.items():
            key = syn.get(k, k)
            EXP_FIRST_VALUES[key] = v
        # Compute pool totals if the components exist
        atp = EXP_FIRST_VALUES.get('ATP'); adp = EXP_FIRST_VALUES.get('ADP'); amp = EXP_FIRST_VALUES.get('AMP')
        if atp is not None and adp is not None and amp is not None:
            TOTALS['A_tot'] = float(atp + adp + amp)
        nad = EXP_FIRST_VALUES.get('NAD'); nadh = EXP_FIRST_VALUES.get('NADH')
        if nad is not None and nadh is not None:
            TOTALS['NAD_total'] = float(nad + nadh)
        nadp = EXP_FIRST_VALUES.get('NADP'); nadph = EXP_FIRST_VALUES.get('NADPH')
        if nadp is not None and nadph is not None:
            TOTALS['NADP_total'] = float(nadp + nadph)
        gsh = EXP_FIRST_VALUES.get('GSH'); gssg = EXP_FIRST_VALUES.get('GSSG')
        if gsh is not None and gssg is not None:
            TOTALS['GSH_tot'] = float(gsh + 2.0*gssg)
        # ELAC/EGLC first values for target anchoring if desired
        TOTALS['ELAC_first'] = EXP_FIRST_VALUES.get('ELAC')
        TOTALS['EGLC_first'] = EXP_FIRST_VALUES.get('EGLC')
    except Exception as e:
        # Fallbacks remain None; equadiff will use defaults
        print(f"Warning: could not load experimental first values: {e}")

# Comprehensive metabolite mapping for Brodbar experimental data (110 metabolites)
BRODBAR_METABOLITE_MAP = {
    'GLC': 0,
    'G6P': 1,
    'F6P': 2,
    'GL6P': 3,
    'GO6P': 4,
    'RU5P': 5,
    'R5P': 6,
    'X5P': 7,
    'E4P': 8,
    'S7P': 9,
    'GA3P': 10,
    'F16BP': 11,
    'DHCP': 12,
    'B13PG': 13,
    'P3G': 14,
    'B23PG': 15,
    'P2G': 16,
    'PEP': 17,
    'PYR': 18,
    'LAC': 19,
    'MAL': 20,
    'OAA': 21,
    'CIT': 22,
    'COA': 23,
    'SUCCOA': 24,
    'ADE': 25,
    'ADO': 26,
    'INO': 27,
    'HYPX': 28,
    'XAN': 29,
    'URT': 30,
    'GUA': 31,
    'R1P': 32,
    'D2RIBP': 33,
    'DEOXYINO': 34,
    'ATP': 35,
    'ADP': 36,
    'AMP': 37,
    'GTP': 38,
    'GDP': 39,
    'GMP': 40,
    'PRPP': 41,
    'IMP': 42,
    'XMP': 43,
    'ADESUC': 44,
    'CYSTHIO': 45,
    'HCYS': 46,
    'METTHF': 47,
    'MET': 48,
    'THF': 49,
    'ADOMET': 50,
    'SAH': 51,
    'METCYT': 52,
    'ARG': 53,
    'ARGSUC': 54,
    'CITR': 55,
    'ASP': 56,
    'SER': 57,
    'ALA': 58,
    'AKG': 59,
    'GLU': 60,
    'GLN': 61,
    'NH4': 62,
    'GLUAA': 63,
    'AA': 64,
    'OXOP': 65,
    'GLY': 66,
    'CYS': 67,
    'CYSGLY': 68,
    'GLUCYS': 69,
    'GSH': 70,
    'GSSG': 71,
    'ORN': 72,
    'UREA': 73,
    'ACCOA': 74,
    'NAD': 75,
    'NADH': 76,
    'NADP': 77,
    'NADPH': 78,
    'H2O2': 79,
    'O2': 80,
    'FUM': 81,
    'RIB': 82,
    'SUCARG': 83,
    'CYT': 84,
    'EGLC': 85,
    'ENH4': 86,
    'ELAC': 87,
    'EADO': 88,
    'EADE': 89,
    'EINO': 90,
    'EGLN': 91,
    'EGLU': 92,
    'ECYS': 93,
    'EMET': 94,
    'EASP': 95,
    'EUREA': 96,
    'EURT': 97,
    'EPYR': 98,
    'EXAN': 99,
    'EHYPX': 100,
    'EMAL': 101,
    'EFUM': 102,
    'ECIT': 103,
    'EALA': 104,
    'ECYT': 105,
    'PHI': 106,  # pHi (intracellular pH) - dynamically added metabolite
    'PHE': 107   # pHe (extracellular pH) - added when pH perturbation is active
}

def load_brodbar_initial_conditions(data_path: str = None) -> NDArray[np.float64]:
    """Load experimental initial conditions from Brodbar data file.
    
    Parameters:
    -----------
    data_path : str, optional
        Path to Excel file with initial conditions. If None, uses default src path.
        
    Returns:
    --------
    NDArray[np.float64]
        Initial conditions vector for 107 metabolites (106 base + pHi)
    """
    if data_path is None:
        data_path = _IC_FILE
    
    try:
        df = pd.read_excel(data_path, sheet_name=0, header=None)
        # First row contains time points, first column contains metabolite names
        metabolite_names = df.iloc[1:, 0].values  # Skip first row (time)
        first_values = df.iloc[1:, 1].values     # First data column (t=1.0)
        
        # Create initial conditions vector (NUM_TOTAL_METABOLITES states)
        # Note: H2O2 is part of the base metabolites at H2O2_INDEX
        x0 = np.ones(NUM_TOTAL_METABOLITES) * 1.0  # Default value of 1.0 mM
        
        # Set experimental values where available
        set_count = 0
        for i, name in enumerate(metabolite_names):
            if pd.notna(name) and name in BRODBAR_METABOLITE_MAP:
                state_idx = BRODBAR_METABOLITE_MAP[name]
                if state_idx < NUM_TOTAL_METABOLITES and pd.notna(first_values[i]) and first_values[i] > 0:
                    x0[state_idx] = float(first_values[i])
                    set_count += 1
        
        # Set specific values for special metabolites
        if H2O2_INDEX < NUM_TOTAL_METABOLITES:
            x0[H2O2_INDEX] = 0.0001  # H2O2 initial concentration
        x0[PHI_INDEX] = PHYSIOLOGICAL_PH  # pHi (intracellular pH)
        
        print(f"Loaded experimental initial conditions: {set_count} metabolites from {data_path}")
        return x0
        
    except Exception as e:
        print(f"Warning: Could not load experimental data from {data_path}: {e}")
        print("Using default initial conditions")
        # Return default initial conditions
        x0 = np.ones(NUM_TOTAL_METABOLITES) * 1.0
        x0[H2O2_INDEX] = 0.0001  # H2O2
        x0[PHI_INDEX] = PHYSIOLOGICAL_PH  # pHi
        return x0

def _get_param(custom_params: Optional[Dict[str, float]], param_name: str, default_value: float) -> float:
    """Helper function to get parameter value from custom dict or use default.
    
    Parameters:
    -----------
    custom_params : Optional[Dict[str, float]]
        Dictionary of custom parameter values
    param_name : str
        Name of the parameter to retrieve
    default_value : float
        Default value if not in custom_params
        
    Returns:
    --------
    float
        Parameter value (custom or default)
    """
    if custom_params is not None and param_name in custom_params:
        return custom_params[param_name]
    return default_value


def equadiff_brodbar(t: float, 
                     x: NDArray[np.float64], 
                     thermo_constraints: Optional[object] = None,
                     custom_params: Optional[Dict[str, float]] = None,
                     curve_fit_strength: float = 0.0) -> NDArray[np.float64]:
    """Brodbar RBC metabolic model with 108 ODEs (106 base metabolites + pHi + pHe) and adjustable curve fitting.
    
    Parameters:
    -----------
    t : float
        Current time point (hours)
    x : NDArray[np.float64]
        State vector of metabolite concentrations (mM) - length 108 (106 base + pHi + pHe)
    thermo_constraints : Optional[object]
        Thermodynamic constraints object (currently unused)
    custom_params : Optional[Dict[str, float]]
        Dictionary of custom parameter values for optimization.
        Format: {'vmax_VELAC': 0.65, 'km_LAC': 0.8, ...}
        If None, uses hardcoded default values.
    curve_fit_strength : float, optional
        Strength of curve fitting to experimental data (default: 0.0)
        0.0 = Pure Michaelis-Menten kinetics (no curve fitting)
        0.5 = 50% blend of MM kinetics and experimental curves
        1.0 = Full curve fitting (100% toward experimental data)
        Values > 1.0 = Aggressive fitting (not recommended)
        
    Returns:
    --------
    NDArray[np.float64]
        Derivative vector (dxdt) for all 107 metabolites
        
    Raises:
    -------
    ValueError
        If input dimensions are invalid or contain non-finite values
        
    Note:
    -----
    H2O2 is part of the base 106 metabolites at index 79, not a separate dynamic variable.
    pHi (intracellular pH) is the 107th metabolite at index 106.
    pHe (extracellular pH) is the 108th metabolite at index 107.
    
    Parameter Injection:
    -------------------
    Pass custom_params to override default Vmax and Km values for parameter optimization.
    Example: custom_params = {'vmax_VELAC': 0.75, 'km_LAC': 0.9}
    """
    
    # Input validation
    if not isinstance(t, (int, float)):
        raise ValueError(f"Time t must be numeric, got {type(t)}")
    if t < 0:
        raise ValueError(f"Time t must be non-negative, got {t}")
    
    if not isinstance(x, np.ndarray):
        raise ValueError(f"State vector x must be numpy array, got {type(x)}")
    if x.ndim != 1:
        raise ValueError(f"State vector x must be 1-dimensional, got shape {x.shape}")
    if len(x) < NUM_BASE_METABOLITES:
        raise ValueError(f"State vector x must have at least {NUM_BASE_METABOLITES} metabolites, got {len(x)}")
    
    # Initialize thermodynamic constraints if not provided (disabled - missing module)
    # if thermo_constraints is None:
    #     thermo_constraints = ThermodynamicConstraints()
    
    # Clean MM model - no electrical initialization needed
    
    # Skip loading initial conditions on every call for better performance
    # Initial conditions should be set once when starting simulation
    
    # Ensure state vector includes pHi metabolite (x[106])
    # Note: H2O2 is already part of the core 106 metabolites at index 79
    # Load experimental first values for data-driven totals/anchors (only once)
    global EXP_FIRST_VALUES
    if not EXP_FIRST_VALUES:
        _load_experimental_first_values()
    
    # Extend x only if pH perturbation is active (need pHe at index 107)
    if _ENABLE_PH_MODULATION and _PH_PERTURBATION is not None:
        # Need 108 metabolites: 106 base + pHi + pHe
        if len(x) < NUM_TOTAL_METABOLITES:
            x_extended = np.ones(NUM_TOTAL_METABOLITES)
            x_extended[:len(x)] = x
            x_extended[PHI_INDEX] = PHYSIOLOGICAL_PH  # pHi initial value
            x_extended[PHE_INDEX] = PHYSIOLOGICAL_PHE  # pHe initial value
            x = x_extended
    else:
        # Need only 107 metabolites: 106 base + pHi
        if len(x) < (PHI_INDEX + 1):
            x_extended = np.ones(PHI_INDEX + 1)
            x_extended[:len(x)] = x
            x_extended[PHI_INDEX] = PHYSIOLOGICAL_PH  # pHi initial value
            x = x_extended
    
    # Apply concentration bounds to prevent negative values
    x = np.maximum(x, MIN_CONCENTRATION)  # Ensure all concentrations are positive
    
    # Initialize derivatives array AFTER extending x to correct size
    dxdt = np.zeros(len(x))
    
    # Thermodynamically consistent conservation pools
    # Use correct metabolite indices based on differential equation mapping
    ATP = max(x[35], 1e-6)   # ATP at index 35 (confirmed from dxdt[35])
    ADP = max(x[36], 1e-6)   # ADP at index 36 (confirmed from dxdt[36])  
    AMP = max(x[37], 1e-6)   # AMP at index 37 (confirmed from dxdt[37])
    
    # Find NAD/NADH indices from redox metabolites section
    NAD = max(x[75], 1e-6)   # NAD - need to verify this index
    NADH = max(x[76], 1e-6)  # NADH - need to verify this index
    
    NADP = max(x[77], 1e-6)  # NADP - need to verify this index
    NADPH = max(x[78], 1e-6) # NADPH - need to verify this index
    
    GSH = max(x[70], 1e-6)   # GSH - need to verify this index
    GSSG = max(x[71], 1e-6)  # GSSG - need to verify this index
    
    # Initialize conservation pool totals from experimental data if available (disabled)
    # if not hasattr(thermo_constraints, '_pools_initialized'):
    #     # Set pool totals from current concentrations (first call)
    #     exp_data = {
    #         'ATP': ATP, 'ADP': ADP, 'AMP': AMP,
    #         'NAD': NAD, 'NADH': NADH,
    #         'NADP': NADP, 'NADPH': NADPH,
    #         'GSH': GSH, 'GSSG': GSSG
    #     }
    #     thermo_constraints.set_pool_totals_from_experimental_data(exp_data)
    #     thermo_constraints._pools_initialized = True
    
    # ===== PARAMETER INJECTION SYSTEM =====
    # All parameters can be overridden via custom_params dictionary for optimization
    # Format: custom_params = {'vmax_VELAC': 0.65, 'km_LAC': 0.8, ...}
    
    # TRANSPORT PATHWAY - EXTRACELLULAR METABOLITES
    vmax_VELAC = _get_param(custom_params, 'vmax_VELAC', 0.580000)    # Lactate transporter
    vmax_VEADE = _get_param(custom_params, 'vmax_VEADE', 0.010000)    # Adenine transporter
    vmax_VEINO = _get_param(custom_params, 'vmax_VEINO', 0.0001000)   # Inosine transporter
    vmax_VEHYPX = _get_param(custom_params, 'vmax_VEHYPX', 0.002217)  # Hypoxanthine transporter
    vmax_VEMAL = _get_param(custom_params, 'vmax_VEMAL', 0.001227)    # Malate transporter
    
    # GLYCOLYSIS PATHWAY
    vmax_VHK = _get_param(custom_params, 'vmax_VHK', 0.267472)         # Hexokinase
    vmax_VPGI = _get_param(custom_params, 'vmax_VPGI', 0.204493)       # Phosphoglucose isomerase
    vmax_VPFK = _get_param(custom_params, 'vmax_VPFK', 0.391893)       # Phosphofructokinase
    vmax_VFDPA = _get_param(custom_params, 'vmax_VFDPA', 1.156751)     # Fructose-bisphosphate aldolase
    vmax_VTPI = _get_param(custom_params, 'vmax_VTPI', 15.0)           # Triose phosphate isomerase
    vmax_VGAPDH = _get_param(custom_params, 'vmax_VGAPDH', 6.389868)   # Glyceraldehyde-3-phosphate dehydrogenase
    vmax_VPGK = _get_param(custom_params, 'vmax_VPGK', 4.690379)       # Phosphoglycerate kinase
    vmax_VPGM = _get_param(custom_params, 'vmax_VPGM', 1.170854)       # Phosphoglycerate mutase
    vmax_VENOPGM = _get_param(custom_params, 'vmax_VENOPGM', 5.515612) # Enolase
    vmax_VPK = _get_param(custom_params, 'vmax_VPK', 0.936322)         # Pyruvate kinase
    vmax_VLDH = _get_param(custom_params, 'vmax_VLDH', 0.284952)       # Lactate dehydrogenase
    
    # PENTOSE PHOSPHATE PATHWAY
    vmax_VG6PDH = _get_param(custom_params, 'vmax_VG6PDH', 0.408870)   # Glucose-6-phosphate dehydrogenase
    vmax_VPGLS = _get_param(custom_params, 'vmax_VPGLS', 4.111138)     # Phosphogluconolactonase
    vmax_V6PGD = _get_param(custom_params, 'vmax_V6PGD', 10.0)         # 6-phosphogluconate dehydrogenase
    vmax_VR5PI = _get_param(custom_params, 'vmax_VR5PI', 10.0)         # Ribose-5-phosphate isomerase
    vmax_VR5PE = _get_param(custom_params, 'vmax_VR5PE', 8.0)          # Ribulose-5-phosphate 3-epimerase
    vmax_VTKL1 = _get_param(custom_params, 'vmax_VTKL1', 12.0)         # Transketolase 1
    vmax_VTKL2 = _get_param(custom_params, 'vmax_VTKL2', 12.0)         # Transketolase 2
    vmax_VTAL = _get_param(custom_params, 'vmax_VTAL', 14.0)           # Transaldolase
    
    # NUCLEOTIDE METABOLISM
    vmax_VAK = _get_param(custom_params, 'vmax_VAK', 5.0)              # Adenosine kinase
    vmax_VAK2 = _get_param(custom_params, 'vmax_VAK2', 5.0)            # Adenosine kinase 2
    vmax_VAPRT = _get_param(custom_params, 'vmax_VAPRT', 1.087935)     # Adenine phosphoribosyltransferase
    vmax_VADA = _get_param(custom_params, 'vmax_VADA', 2.0)            # Adenosine deaminase
    vmax_VAMPD1 = _get_param(custom_params, 'vmax_VAMPD1', 0.538065)   # AMP deaminase
    vmax_VHGPRT1 = _get_param(custom_params, 'vmax_VHGPRT1', 0.645581) # Hypoxanthine-guanine phosphoribosyltransferase 1
    vmax_VHGPRT2 = _get_param(custom_params, 'vmax_VHGPRT2', 2.5)      # Hypoxanthine-guanine phosphoribosyltransferase 2
    vmax_VGMPS = _get_param(custom_params, 'vmax_VGMPS', 0.379205)     # GMP synthase
    vmax_VH2O2 = _get_param(custom_params, 'vmax_VH2O2', 1.0)          # H2O2 metabolism
    vmax_VADSS = _get_param(custom_params, 'vmax_VADSS', 3.0)          # Adenylosuccinate synthase
    vmax_VIMPH = _get_param(custom_params, 'vmax_VIMPH', 2.0)          # IMP dehydrogenase
    vmax_Vnucleo2 = _get_param(custom_params, 'vmax_Vnucleo2', 1.5)    # Nucleotidase
    vmax_VADSL = _get_param(custom_params, 'vmax_VADSL', 4.0)          # Adenylosuccinate lyase
    vmax_VRKb = _get_param(custom_params, 'vmax_VRKb', 3.0)            # Ribokinase b
    vmax_VXAO = _get_param(custom_params, 'vmax_VXAO', 2.0)            # Xanthine oxidase
    vmax_VXAO2 = _get_param(custom_params, 'vmax_VXAO2', 1.5)          # Xanthine oxidase 2
    vmax_VOPRIBT = _get_param(custom_params, 'vmax_VOPRIBT', 1.0)      # Orotate phosphoribosyltransferase
    vmax_VPNPase1 = _get_param(custom_params, 'vmax_VPNPase1', 2.5)    # Purine nucleoside phosphorylase
    vmax_VRKa = _get_param(custom_params, 'vmax_VRKa', 4.0)            # Ribokinase a
    vmax_VPRPPASe = _get_param(custom_params, 'vmax_VPRPPASe', 5.0)    # Phosphoribosyl pyrophosphate synthetase
    
    # AMINO ACID METABOLISM
    vmax_VEGLN = _get_param(custom_params, 'vmax_VEGLN', 0.001000)     # Glutamine transporter
    vmax_VEGLU = _get_param(custom_params, 'vmax_VEGLU', 0.001000)     # Glutamate transporter
    vmax_VGLNS = _get_param(custom_params, 'vmax_VGLNS', 4.0)          # Glutamine synthetase
    vmax_VECYS = _get_param(custom_params, 'vmax_VECYS', 0.0005000)    # Cysteine transporter
    vmax_VGDH = _get_param(custom_params, 'vmax_VGDH', 5.0)            # Glutamate dehydrogenase
    vmax_VASPTA = _get_param(custom_params, 'vmax_VASPTA', 4.0)        # Aspartate aminotransferase
    vmax_VALATA = _get_param(custom_params, 'vmax_VALATA', 3.5)        # Alanine aminotransferase
    
    # REDOX METABOLISM
    vmax_VGSR = _get_param(custom_params, 'vmax_VGSR', 6.0)            # Glutathione reductase
    vmax_VGPX = _get_param(custom_params, 'vmax_VGPX', 1.079815)       # Glutathione peroxidase
    vmax_VGLUCYS = _get_param(custom_params, 'vmax_VGLUCYS', 3.0)      # Glutamate-cysteine ligase
    vmax_VGSS = _get_param(custom_params, 'vmax_VGSS', 4.0)            # Glutathione synthetase
    
    # TRANSPORT REACTIONS (continued)
    vmax_VEGLC = _get_param(custom_params, 'vmax_VEGLC', 1.077000)     # Glucose transporter
    vmax_VEADO = _get_param(custom_params, 'vmax_VEADO', 2.0)          # Adenosine transport
    vmax_VEPYR = _get_param(custom_params, 'vmax_VEPYR', 3.0)          # Pyruvate transport
    vmax_VEXAN = _get_param(custom_params, 'vmax_VEXAN', 1.0)          # Xanthine transport
    vmax_VECIT = _get_param(custom_params, 'vmax_VECIT', 2.5)          # Citrate transport
    vmax_VEUREA = _get_param(custom_params, 'vmax_VEUREA', 1.5)        # Urea transport
    vmax_VEFUM = _get_param(custom_params, 'vmax_VEFUM', 2.0)          # Fumarate transport
    vmax_VEALA = _get_param(custom_params, 'vmax_VEALA', 2.0)          # Alanine transport
    vmax_VEMET = _get_param(custom_params, 'vmax_VEMET', 2.0)          # Methionine transport
    vmax_VEASP = _get_param(custom_params, 'vmax_VEASP', 2.5)          # Aspartate transport
    vmax_VENH4 = _get_param(custom_params, 'vmax_VENH4', 4.0)          # Ammonia transport
    vmax_VECYT = _get_param(custom_params, 'vmax_VECYT', 1.0)          # Cytidine transport
    vmax_VEURT = _get_param(custom_params, 'vmax_VEURT', 1.5)          # Urate transport
    
    # ADDITIONAL REACTIONS
    vmax_V23DPGP = _get_param(custom_params, 'vmax_V23DPGP', 12.0)     # 2,3-bisphosphoglycerate phosphatase
    vmax_VDPGM = _get_param(custom_params, 'vmax_VDPGM', 10.0)         # Diphosphoglycerate mutase
    vmax_VME = _get_param(custom_params, 'vmax_VME', 3.0)              # Malic enzyme
    vmax_VPC = _get_param(custom_params, 'vmax_VPC', 2.5)              # Pyruvate carboxylase
    vmax_VACLY = _get_param(custom_params, 'vmax_VACLY', 4.0)          # ATP citrate lyase
    vmax_VASTA = _get_param(custom_params, 'vmax_VASTA', 2.0)          # Argininosuccinate synthase
    vmax_VCYSGLY = _get_param(custom_params, 'vmax_VCYSGLY', 3.0)      # Cysteinylglycine dipeptidase
    vmax_VGGT = _get_param(custom_params, 'vmax_VGGT', 3.0)            # Gamma-glutamyltransferase
    vmax_VGGCT = _get_param(custom_params, 'vmax_VGGCT', 2.5)          # Gamma-glutamylcyclotransferase
    vmax_VMESE = _get_param(custom_params, 'vmax_VMESE', 2.0)          # Methionine synthase
    vmax_VSAM = _get_param(custom_params, 'vmax_VSAM', 3.0)            # S-adenosylmethionine synthetase
    vmax_VSAH = _get_param(custom_params, 'vmax_VSAH', 2.5)            # S-adenosylhomocysteine hydrolase
    vmax_VAHCY = _get_param(custom_params, 'vmax_VAHCY', 3.0)          # Adenosylhomocysteinase
    vmax_VCBS = _get_param(custom_params, 'vmax_VCBS', 2.0)            # Cystathionine beta-synthase
    vmax_VCSE = _get_param(custom_params, 'vmax_VCSE', 2.5)            # Cystathionine gamma-lyase
    vmax_VGENASP = _get_param(custom_params, 'vmax_VGENASP', 2.0)      # GTP:oxaloacetate carboxylyase
    vmax_VFUM = _get_param(custom_params, 'vmax_VFUM', 5.0)            # Fumarase
    vmax_VMLD = _get_param(custom_params, 'vmax_VMLD', 4.0)            # Malate dehydrogenase
    vmax_VASL = _get_param(custom_params, 'vmax_VASL', 3.0)            # Argininosuccinate lyase
    vmax_VASS = _get_param(custom_params, 'vmax_VASS', 2.5)            # Argininosuccinate synthase
    vmax_Vpolyam = _get_param(custom_params, 'vmax_Vpolyam', 1.5)      # Polyamine synthesis
    
    # ===== Km PARAMETERS (Michaelis-Menten Constants) =====
    # All Km values injectable for optimization
    
    # TRANSPORT PATHWAY Km VALUES
    km_ELAC = _get_param(custom_params, 'km_ELAC', 6.377583)    # Extracellular lactate
    km_ADE = _get_param(custom_params, 'km_ADE', 0.369082)      # Adenine
    km_EINO = _get_param(custom_params, 'km_EINO', 0.100345)    # Extracellular inosine
    km_EHYPX = _get_param(custom_params, 'km_EHYPX', 9.993970)  # Extracellular hypoxanthine
    km_EMAL = _get_param(custom_params, 'km_EMAL', 9.998876)    # Extracellular malate
    
    # GLYCOLYSIS PATHWAY Km VALUES
    km_GLC = _get_param(custom_params, 'km_GLC', 49.864721)     # Glucose
    km_G6P = _get_param(custom_params, 'km_G6P', 0.146000)      # Glucose-6-phosphate
    km_F6P = _get_param(custom_params, 'km_F6P', 0.207000)      # Fructose-6-phosphate
    km_F16BP = _get_param(custom_params, 'km_F16BP', 0.094000)  # Fructose-1,6-bisphosphate
    km_DHCP = _get_param(custom_params, 'km_DHCP', 0.05)        # Dihydroxyacetone phosphate
    km_GA3P = _get_param(custom_params, 'km_GA3P', 0.02)        # Glyceraldehyde-3-phosphate
    km_B13PG = _get_param(custom_params, 'km_B13PG', 1.013344)  # 1,3-bisphosphoglycerate
    km_P3G = _get_param(custom_params, 'km_P3G', 0.134000)      # 3-phosphoglycerate
    km_P2G = _get_param(custom_params, 'km_P2G', 0.134000)      # 2-phosphoglycerate
    km_PEP = _get_param(custom_params, 'km_PEP', 0.175000)      # Phosphoenolpyruvate
    km_PYR = _get_param(custom_params, 'km_PYR', 0.697000)      # Pyruvate
    km_LAC = _get_param(custom_params, 'km_LAC', 49.862494)     # Lactate
    
    # PENTOSE PHOSPHATE PATHWAY Km VALUES
    km_GO6P = _get_param(custom_params, 'km_GO6P', 0.02)        # Glucono-1,5-lactone-6-phosphate
    km_GL6P = _get_param(custom_params, 'km_GL6P', 0.1)         # 6-phosphogluconate
    km_RU5P = _get_param(custom_params, 'km_RU5P', 0.05)        # Ribulose-5-phosphate
    km_R5P = _get_param(custom_params, 'km_R5P', 0.05)          # Ribose-5-phosphate
    km_X5P = _get_param(custom_params, 'km_X5P', 0.05)          # Xylulose-5-phosphate
    km_E4P = _get_param(custom_params, 'km_E4P', 0.03)          # Erythrose-4-phosphate
    km_S7P = _get_param(custom_params, 'km_S7P', 0.05)          # Sedoheptulose-7-phosphate
    
    # NUCLEOTIDE METABOLISM Km VALUES
    km_HYPX = _get_param(custom_params, 'km_HYPX', 0.355000)    # Hypoxanthine
    km_ADO = _get_param(custom_params, 'km_ADO', 0.1)           # Adenosine
    km_AMP = _get_param(custom_params, 'km_AMP', 0.282865)      # AMP
    km_IMP = _get_param(custom_params, 'km_IMP', 0.231000)      # Inosine monophosphate
    km_XMP = _get_param(custom_params, 'km_XMP', 0.05)          # Xanthosine monophosphate
    km_GMP = _get_param(custom_params, 'km_GMP', 0.085000)      # Guanosine monophosphate
    km_PRPP = _get_param(custom_params, 'km_PRPP', 0.1)         # Phosphoribosyl pyrophosphate
    km_GUA = _get_param(custom_params, 'km_GUA', 0.03)          # Guanine
    km_R1P = _get_param(custom_params, 'km_R1P', 0.05)          # Ribose-1-phosphate
    km_DEOXYINO = _get_param(custom_params, 'km_DEOXYINO', 0.02) # Deoxyinosine
    km_INO = _get_param(custom_params, 'km_INO', 0.1)           # Inosine
    km_URT = _get_param(custom_params, 'km_URT', 0.05)          # Urate
    km_XAN = _get_param(custom_params, 'km_XAN', 0.03)          # Xanthine
    km_RIB = _get_param(custom_params, 'km_RIB', 0.1)           # Ribose
    km_ADESUC = _get_param(custom_params, 'km_ADESUC', 0.05)    # Adenylosuccinate
    
    # AMINO ACID METABOLISM Km VALUES
    km_GLN = _get_param(custom_params, 'km_GLN', 0.5)           # Glutamine
    km_GLU = _get_param(custom_params, 'km_GLU', 0.289000)      # Glutamate
    km_ASP = _get_param(custom_params, 'km_ASP', 0.200958)      # Aspartate
    km_ALA = _get_param(custom_params, 'km_ALA', 0.3)           # Alanine
    km_CYS = _get_param(custom_params, 'km_CYS', 0.1)           # Cysteine
    km_MET = _get_param(custom_params, 'km_MET', 0.1)           # Methionine
    km_SER = _get_param(custom_params, 'km_SER', 0.2)           # Serine
    km_ARG = _get_param(custom_params, 'km_ARG', 0.5)           # Arginine
    
    # REDOX METABOLISM Km VALUES
    km_GSSG = _get_param(custom_params, 'km_GSSG', 1.0)         # Glutathione disulfide
    km_GSH = _get_param(custom_params, 'km_GSH', 0.458000)      # Glutathione
    km_GLUCYS = _get_param(custom_params, 'km_GLUCYS', 0.05)    # Glutamylcysteine
    km_H2O2 = _get_param(custom_params, 'km_H2O2', 0.001)       # Hydrogen peroxide
    
    # COFACTOR Km VALUES
    km_ATP = _get_param(custom_params, 'km_ATP', 0.569395)      # ATP
    km_ADP = _get_param(custom_params, 'km_ADP', 0.402663)      # ADP
    km_NAD = _get_param(custom_params, 'km_NAD', 0.2)           # NAD
    km_NADH = _get_param(custom_params, 'km_NADH', 0.1)         # NADH
    km_NADP = _get_param(custom_params, 'km_NADP', 0.05)        # NADP
    km_NADPH = _get_param(custom_params, 'km_NADPH', 0.02)      # NADPH
    km_GTP = _get_param(custom_params, 'km_GTP', 0.5)           # Guanosine triphosphate
    km_GDP = _get_param(custom_params, 'km_GDP', 0.3)           # Guanosine diphosphate
    
    # EXTRACELLULAR TRANSPORT Km VALUES
    km_EGLC = _get_param(custom_params, 'km_EGLC', 49.484000)   # Extracellular glucose
    km_EADO = _get_param(custom_params, 'km_EADO', 0.1)         # Extracellular adenosine
    km_EADE = _get_param(custom_params, 'km_EADE', 10.0)        # Extracellular adenine
    km_EPYR = _get_param(custom_params, 'km_EPYR', 0.2)         # Extracellular pyruvate
    km_EXAN = _get_param(custom_params, 'km_EXAN', 0.03)        # Extracellular xanthine
    km_ECIT = _get_param(custom_params, 'km_ECIT', 0.2)         # Extracellular citrate
    km_EUREA = _get_param(custom_params, 'km_EUREA', 0.5)       # Extracellular urea
    km_EFUM = _get_param(custom_params, 'km_EFUM', 0.1)         # Extracellular fumarate
    km_EGLN = _get_param(custom_params, 'km_EGLN', 5.000000)    # Extracellular glutamine
    km_EGLU = _get_param(custom_params, 'km_EGLU', 5.000000)    # Extracellular glutamate
    km_EALA = _get_param(custom_params, 'km_EALA', 0.3)         # Extracellular alanine
    km_ECYS = _get_param(custom_params, 'km_ECYS', 5.000000)    # Extracellular cysteine
    km_EMET = _get_param(custom_params, 'km_EMET', 0.1)         # Extracellular methionine
    km_EASP = _get_param(custom_params, 'km_EASP', 0.2)         # Extracellular aspartate
    km_ENH4 = _get_param(custom_params, 'km_ENH4', 0.1)         # Extracellular ammonia
    km_ECYT = _get_param(custom_params, 'km_ECYT', 0.05)        # Extracellular cytidine
    km_EURT = _get_param(custom_params, 'km_EURT', 0.05)        # Extracellular urate
    
    # ADDITIONAL METABOLITE Km VALUES
    km_B23PG = _get_param(custom_params, 'km_B23PG', 1.013344)  # 2,3-bisphosphoglycerate
    km_CYSTHIO = _get_param(custom_params, 'km_CYSTHIO', 0.02) # Cystathionine
    km_HCYS = _get_param(custom_params, 'km_HCYS', 0.05)       # Homocysteine
    km_METTHF = _get_param(custom_params, 'km_METTHF', 0.02)   # N5-methyltetrahydrofolate
    km_THF = _get_param(custom_params, 'km_THF', 0.02)         # Tetrahydrofolate
    km_ADOMET = _get_param(custom_params, 'km_ADOMET', 0.1)    # S-adenosylmethionine
    km_SAH = _get_param(custom_params, 'km_SAH', 0.05)         # S-adenosylhomocysteine
    km_METCYT = _get_param(custom_params, 'km_METCYT', 0.02)   # N5-methylcytidine
    km_ARGSUC = _get_param(custom_params, 'km_ARGSUC', 0.05)   # Argininosuccinate
    km_CITR = _get_param(custom_params, 'km_CITR', 0.1)        # Citrulline
    km_AKG = _get_param(custom_params, 'km_AKG', 0.2)          # Alpha-ketoglutarate
    km_NH4 = _get_param(custom_params, 'km_NH4', 0.1)          # Ammonia
    km_GLUAA = _get_param(custom_params, 'km_GLUAA', 0.05)     # Glutamyl-amino acid
    km_AA = _get_param(custom_params, 'km_AA', 0.1)            # Amino acid
    km_OXOP = _get_param(custom_params, 'km_OXOP', 0.05)       # 5-oxoproline
    km_GLY = _get_param(custom_params, 'km_GLY', 0.2)          # Glycine
    km_CYSGLY = _get_param(custom_params, 'km_CYSGLY', 0.05)   # Cysteinylglycine
    km_ORN = _get_param(custom_params, 'km_ORN', 0.1)          # Ornithine
    km_UREA = _get_param(custom_params, 'km_UREA', 0.5)        # Urea
    km_ACCOA = _get_param(custom_params, 'km_ACCOA', 0.02)     # Acetyl-CoA
    km_O2 = _get_param(custom_params, 'km_O2', 0.2)            # Oxygen
    km_FUM = _get_param(custom_params, 'km_FUM', 0.1)          # Fumarate
    km_SUCARG = _get_param(custom_params, 'km_SUCARG', 0.05)    # N-succinylarginine
    km_CYT = _get_param(custom_params, 'km_CYT', 0.05)          # Cytidine
    km_OAA = _get_param(custom_params, 'km_OAA', 0.05)          # Oxaloacetate
    km_CIT = _get_param(custom_params, 'km_CIT', 0.2)           # Citrate
    km_COA = _get_param(custom_params, 'km_COA', 0.02)          # Coenzyme A
    km_SUCCOA = _get_param(custom_params, 'km_SUCCOA', 0.05)    # Succinyl-CoA
    km_MAL = _get_param(custom_params, 'km_MAL', 0.1)           # Malate
    
    # ===== PARAMETER INJECTION COMPLETE =====
    # All 100+ Vmax and Km parameters are now fully injectable via custom_params!
    # Example usage:
    #   custom_params = {'vmax_VELAC': 0.75, 'km_LAC': 0.9}
    #   dxdt = equadiff_brodbar(t, x, custom_params=custom_params)
    #
    # This enables ML-based parameter optimization without modifying source code.
    
    # Ratio-based Km values for regulatory effects
    km_NAD_NADH = 1.0    # NAD/NADH ratio effect
    km_NADH_NAD = 1.0    # NADH/NAD ratio effect
    km_NADP_NADPH = 1.0  # NADP/NADPH ratio effect
    km_ADP_ATP = 1.0     # ADP/ATP ratio effect
    
    # ===== pH-DEPENDENT ENZYME MODULATION =====
    # Extract pH values
    pHi = x[PHI_INDEX]  # Intracellular pH
    pHe = x[PHE_INDEX] if len(x) > PHE_INDEX else PHYSIOLOGICAL_PHE  # Extracellular pH
    
    # Compute pH modulation factors for key enzymes (if enabled)
    if _ENABLE_PH_MODULATION and PH_MODULES_AVAILABLE:
        f_pH_VHK = compute_pH_modulation(pHi, 'VHK')
        f_pH_VPFK = compute_pH_modulation(pHi, 'VPFK')
        f_pH_VPK = compute_pH_modulation(pHi, 'VPK')
        f_pH_VLDH = compute_pH_modulation(pHi, 'VLDH')
        f_pH_VGAPDH = compute_pH_modulation(pHi, 'VGAPDH')
        f_pH_VDPGM = compute_pH_modulation(pHi, 'VDPGM')
        f_pH_V23DPGP = compute_pH_modulation(pHi, 'V23DPGP')
        f_pH_VG6PDH = compute_pH_modulation(pHi, 'VG6PDH')
        f_pH_VPGK = compute_pH_modulation(pHi, 'VPGK')
        f_pH_VENOPGM = compute_pH_modulation(pHi, 'VENOPGM')
    else:
        # No pH modulation - all factors = 1.0
        f_pH_VHK = f_pH_VPFK = f_pH_VPK = f_pH_VLDH = 1.0
        f_pH_VGAPDH = f_pH_VDPGM = f_pH_V23DPGP = 1.0
        f_pH_VG6PDH = f_pH_VPGK = f_pH_VENOPGM = 1.0
    
    # ===== CALCULATE ENZYMATIC REACTION RATES (MICHAELIS-MENTEN WITH pH MODULATION) =====
    # All metabolic fluxes use MM kinetics, modulated by pH if enabled
    
    # Glycolysis pathway reactions (with pH modulation)
    VHK = f_pH_VHK * vmax_VHK * mm(x[0], km_GLC)  # Hexokinase: GLC -> G6P [pH-modulated]
    VPGI = vmax_VPGI * mm(x[1], km_G6P)  # PGI: G6P -> F6P
    VPFK = f_pH_VPFK * vmax_VPFK * mm(x[2], km_F6P)  # PFK: F6P -> F16BP [pH-modulated - MOST SENSITIVE!]
    VFDPA = vmax_VFDPA * mm(x[11], km_F16BP)  # FDPA: F16BP -> DHCP + GA3P
    VTPI = vmax_VTPI * mm(x[12], km_DHCP)  # TPI: DHCP <-> GA3P
    VGAPDH = f_pH_VGAPDH * vmax_VGAPDH * mm(x[10], km_GA3P) * mm(NAD/(NADH+1e-6), km_NAD_NADH)  # GAPDH [pH-modulated]
    VPGK = f_pH_VPGK * vmax_VPGK * mm(x[13], km_B13PG) * mm(ADP/(ATP+1e-6), km_ADP_ATP)  # PGK [pH-modulated]
    VPGM = vmax_VPGM * mm(x[14], km_P3G)  # PGM: P3G -> P2G
    VPK = f_pH_VPK * vmax_VPK * mm(x[17], km_PEP) * mm(ADP/(ATP+1e-6), km_ADP_ATP)  # PK [pH-modulated]
    VLDH = f_pH_VLDH * vmax_VLDH * mm(x[18], km_PYR) * mm(NADH/(NAD+1e-6), km_NADH_NAD)  # LDH [pH-modulated]
    
    # Pentose phosphate pathway (with pH modulation)
    VG6PDH = f_pH_VG6PDH * vmax_VG6PDH * mm(x[1], km_G6P) * mm(NADP/(NADPH+1e-6), km_NADP_NADPH)  # G6PDH [pH-modulated]
    VPGLS = vmax_VPGLS * mm(x[4], km_GO6P)  # PGLS: GO6P -> GL6P
    V6PGD = vmax_V6PGD * mm(x[3], km_GL6P) * mm(NADP/(NADPH+1e-6), km_NADP_NADPH)  # 6PGD: GL6P -> RU5P
    VTKL1 = vmax_VTKL1 * mm(x[6], km_R5P) * mm(x[7], km_X5P)  # TKL1
    VTKL2 = vmax_VTKL2 * mm(x[8], km_E4P) * mm(x[7], km_X5P)  # TKL2
    VTAL = vmax_VTAL * mm(x[10], km_GA3P) * mm(x[9], km_S7P)  # TAL
    
    # Transport reactions (removed - defined later in complete section)
    
    # Nucleotide metabolism
    VAK = vmax_VAK * mm(x[26], km_ADO) * mm(max(ATP,1e-6), km_ATP)  # Adenosine kinase
    VAK2 = vmax_VAK2 * mm(x[26], km_ADO) * mm(max(ATP,1e-6), km_ATP)  # Adenosine kinase 2
    VAPRT = vmax_VAPRT * mm(x[25], km_ADE) * mm(x[41], km_PRPP)  # APRT
    VADA = vmax_VADA * mm(x[26], km_ADO)  # Adenosine deaminase
    VAMPD1 = vmax_VAMPD1 * mm(max(AMP,1e-6), km_AMP)  # AMP deaminase
    
    # Pentose phosphate pathway (missing reactions)
    VR5PI = vmax_VR5PI * mm(x[5], km_RU5P)  # RU5P = R5P
    VR5PE = vmax_VR5PE * mm(x[5], km_RU5P)  # RU5P = X5P
    
    # Glycolysis and 2,3-BPG shunt (with pH modulation)
    VENOPGM = f_pH_VENOPGM * vmax_VENOPGM * mm(x[16], km_P2G)  # P2G = PEP [pH-modulated]
    V23DPGP = f_pH_V23DPGP * vmax_V23DPGP * mm(x[15], km_B23PG)  # B23PG => P3G [pH-modulated]
    VDPGM = f_pH_VDPGM * vmax_VDPGM * mm(x[13], km_B13PG)  # B13PG => B23PG [pH-modulated - CRITICAL FOR O2 AFFINITY!]
    
    # Nucleotide metabolism (complete)
    VHGPRT1 = vmax_VHGPRT1 * mm(x[41], km_PRPP) * mm(x[28], km_HYPX)  # PRPP + HYPX => IMP
    VADA = vmax_VADA * mm(x[26], km_ADO)  # ADO => INO + NH4
    VAPRT = vmax_VAPRT * mm(x[25], km_ADE) * mm(x[41], km_PRPP)  # ADE + PRPP => AMP
    VAMPD1 = vmax_VAMPD1 * mm(max(AMP,1e-6), km_AMP)  # AMP => IMP + NH4
    VADSS = vmax_VADSS * mm(x[42], km_IMP) * mm(x[56], km_ASP) * mm(x[38], km_GTP)  # IMP + ASP + GTP => ADESUC + GDP
    VIMPH = vmax_VIMPH * mm(x[42], km_IMP) * mm(max(NAD,1e-6), km_NAD)  # IMP + NAD => XMP + NADH
    Vnucleo2 = vmax_Vnucleo2 * mm(x[42], km_IMP)  # IMP => INO
    VADSL = vmax_VADSL * mm(x[44], km_ADESUC)  # ADESUC = FUM + AMP
    VGMPS = vmax_VGMPS * mm(x[43], km_XMP) * mm(x[61], km_GLN) * mm(max(ATP,1e-6), km_ATP)  # XMP + GLN + ATP => GMP + AMP
    VHGPRT2 = vmax_VHGPRT2 * mm(x[31], km_GUA) * mm(max(AMP,1e-6), km_AMP) * mm(x[41], km_PRPP)  # GUA + AMP + PRPP => GMP
    VRKb = vmax_VRKb * mm(x[32], km_R1P)  # R1P = R5P
    VAK = vmax_VAK * mm(max(ADP,1e-6), km_ADP)  # 2 ADP = AMP + ATP
    VXAO = vmax_VXAO * mm(x[28], km_HYPX)  # HYPX => XAN + H2O2
    VXAO2 = vmax_VXAO2 * mm(x[29], km_XAN)  # XAN => URT
    VOPRIBT = vmax_VOPRIBT * mm(x[34], km_DEOXYINO)  # DEOXYINO = HYPX + D2RIBP
    VPNPase1 = vmax_VPNPase1 * mm(x[27], km_INO)  # INO = HYPX + R1P
    VRKa = vmax_VRKa * mm(x[82], km_RIB) * mm(max(ATP,1e-6), km_ATP)  # RIB + ATP = R5P + ADP
    VPRPPASe = vmax_VPRPPASe * mm(x[6], km_R5P) * mm(max(ATP,1e-6), km_ATP)  # R5P + ATP = PRPP + AMP
    
    # Transport reactions (complete all extracellular)
    # ML-optimized glucose consumption: EGLC -> GLC (consumption from extracellular pool)
    VEGLC = vmax_VEGLC * mm(x[85], km_EGLC)  # EGLC consumption (ML-optimized)
    # ML-optimized lactate production: LAC -> ELAC (lactate efflux)
    VELAC = vmax_VELAC * mm(x[19], km_LAC)  # LAC efflux (ML-optimized)
    VEADO = vmax_VEADO * (mm(x[26], km_ADO) - mm(x[88], km_EADO))  # ADO = EADO
    # ML-optimized adenine production: ADE -> EADE (adenine efflux)
    VEADE = vmax_VEADE * mm(x[25], km_ADE)  # ADE efflux (ML-optimized)
    # ML-optimized inosine production: INO -> EINO (inosine efflux)
    VEINO = vmax_VEINO * mm(x[27], km_INO)  # INO efflux (ML-optimized)
    # ML-optimized hypoxanthine production: HYPX -> EHYPX (hypoxanthine efflux)
    VEHYPX = vmax_VEHYPX * mm(x[28], km_HYPX)  # HYPX efflux (ML-optimized)
    VEURT = vmax_VEURT * (mm(x[30], km_URT) - mm(x[97], km_EURT))  # URT = EURT
    VEPYR = vmax_VEPYR * (mm(x[18], km_PYR) - mm(x[98], km_EPYR))  # PYR = EPYR
    VEXAN = vmax_VEXAN * (mm(x[29], km_XAN) - mm(x[99], km_EXAN))  # XAN = EXAN
    VECIT = vmax_VECIT * (mm(x[22], km_CIT) - mm(x[103], km_ECIT))  # CIT = ECIT
    VEUREA = vmax_VEUREA * (mm(x[73], km_UREA) - mm(x[96], km_EUREA))  # UREA = EUREA
    VEFUM = vmax_VEFUM * (mm(x[81], km_FUM) - mm(x[102], km_EFUM))  # FUM = EFUM
    # ML-optimized malate production: MAL -> EMAL (malate efflux)
    VEMAL = vmax_VEMAL * mm(x[20], km_MAL)  # MAL efflux (ML-optimized)
    # ML-optimized amino acid production (efflux)
    VEGLN = vmax_VEGLN * mm(x[61], km_GLN)  # GLN efflux (ML-optimized)
    VEGLU = vmax_VEGLU * mm(x[60], km_GLU)  # GLU efflux (ML-optimized)
    VEALA = vmax_VEALA * (mm(x[58], km_ALA) - mm(x[104], km_EALA))  # ALA = EALA (bidirectional)
    VECYS = vmax_VECYS * mm(x[67], km_CYS)  # CYS efflux (ML-optimized)
    VEMET = vmax_VEMET * (mm(x[48], km_MET) - mm(x[94], km_EMET))  # MET = EMET
    VEASP = vmax_VEASP * (mm(x[56], km_ASP) - mm(x[95], km_EASP))  # ASP = EASP
    VENH4 = vmax_VENH4 * (mm(x[62], km_NH4) - mm(x[86], km_ENH4))  # NH4 = ENH4
    VECYT = vmax_VECYT * (mm(x[84], km_CYT) - mm(x[105], km_ECYT))  # CYT = ECYT
    
    # Amino acid and one-carbon metabolism
    VME = vmax_VME * mm(x[20], km_MAL) * mm(max(NADP,1e-6), km_NADP)  # MAL + NADP = PYR + NADPH
    VPC = vmax_VPC * mm(x[18], km_PYR) * mm(max(ATP,1e-6), km_ATP)  # PYR + ATP = OAA + ADP
    VACLY = vmax_VACLY * mm(x[21], km_OAA) * mm(x[74], km_ACCOA)  # OAA + ACCOA = CIT + COA + ATP
    VASTA = vmax_VASTA * mm(x[24], km_SUCCOA) * mm(x[53], km_ARG)  # SUCCOA + ARG = COA + SUCARG
    VCYSGLY = vmax_VCYSGLY * mm(x[68], km_CYSGLY)  # CYSGLY => CYS + GLY
    VGDH = vmax_VGDH * mm(x[59], km_AKG) * mm(max(NADPH,1e-6), km_NADPH) * mm(x[62], km_NH4)  # AKG + NADPH + NH4 = GLU + NADP
    VGLNS = vmax_VGLNS * mm(x[60], km_GLU) * mm(max(ATP,1e-6), km_ATP) * mm(x[62], km_NH4)  # GLU + ATP + NH4 = GLN + ADP
    VGLUCYS = vmax_VGLUCYS * mm(x[60], km_GLU) * mm(x[67], km_CYS) * mm(max(ATP,1e-6), km_ATP)  # GLU + CYS + ATP => GLUCYS + ADP
    VGSS = vmax_VGSS * mm(x[69], km_GLUCYS) * mm(x[66], km_GLY) * mm(max(ATP,1e-6), km_ATP)  # GLUCYS + GLY + ATP => GSH + ADP
    VGSR = vmax_VGSR * mm(max(GSSG,1e-6), km_GSSG) * mm(max(NADPH,1e-6), km_NADPH)  # GSSG + NADPH = 2 GSH + NADP
    VGGT = vmax_VGGT * mm(max(GSH,1e-6), km_GSH) * mm(x[64], km_AA)  # GSH + AA => GLUAA + CYSGLY
    VGGCT = vmax_VGGCT * mm(x[63], km_GLUAA)  # GLUAA => OXOP + AA
    VMESE = vmax_VMESE * mm(x[46], km_HCYS) * mm(x[47], km_METTHF)  # HCYS + METTHF => MET + THF
    VSAM = vmax_VSAM * mm(x[48], km_MET) * mm(max(ATP,1e-6), km_ATP)  # MET + ATP => ADOMET
    VSAH = vmax_VSAH * mm(x[50], km_ADOMET) * mm(x[84], km_CYT)  # ADOMET + CYT => SAH + METCYT
    VAHCY = vmax_VAHCY * mm(x[51], km_SAH)  # SAH = HCYS + ADO
    VCBS = vmax_VCBS * mm(x[46], km_HCYS) * mm(x[57], km_SER)  # HCYS + SER => CYSTHIO
    VCSE = vmax_VCSE * mm(x[45], km_CYSTHIO)  # CYSTHIO = CYS + AKG + NH4
    VASPTA = vmax_VASPTA * mm(x[56], km_ASP) * mm(x[59], km_AKG)  # ASP + AKG = OAA + GLU
    VALATA = vmax_VALATA * mm(x[58], km_ALA) * mm(x[59], km_AKG)  # ALA + AKG = PYR + GLU
    VGENASP = vmax_VGENASP * mm(x[21], km_OAA) * mm(x[38], km_GTP)  # OAA + GTP => PEP + GDP
    VFUM = vmax_VFUM * mm(x[81], km_FUM)  # FUM = MAL
    VMLD = vmax_VMLD * mm(x[20], km_MAL) * mm(max(NAD,1e-6), km_NAD)  # MAL + NAD = OAA + NADH
    VASL = vmax_VASL * mm(x[54], km_ARGSUC) * mm(max(ATP,1e-6), km_ATP)  # ARGSUC + ATP = ARG + ADP + FUM
    VASS = vmax_VASS * mm(x[55], km_CITR) * mm(x[56], km_ASP) * mm(max(ATP,1e-6), km_ATP)  # CITR + ASP + ATP = ARGSUC + AMP
    Vpolyam = vmax_Vpolyam * mm(x[53], km_ARG)  # ARG => ORN + UREA
    
    # Redox and detoxification
    VH2O2 = vmax_VH2O2 * mm(x[79], km_H2O2)  # H2O2 => O2
    VGPX = vmax_VGPX * mm(x[79], km_H2O2) * mm(max(GSH,1e-6), km_GSH)  # Glutathione peroxidase (implied)
    
    # ===== COMPUTE DIFFERENTIAL EQUATIONS =====
    # Now calculate the derivatives for each metabolite using pure MM kinetics
    
    # Glycolysis metabolites
    dxdt[0] = VEGLC - VHK  # GLC (receives glucose from EGLC consumption)
    dxdt[1] = VHK - VPGI - VG6PDH  # G6P
    dxdt[2] = VPGI - VPFK + VTKL2 + VTAL  # F6P
    dxdt[3] = VPGLS - V6PGD  # GL6P
    dxdt[4] = VG6PDH - VPGLS  # GO6P
    dxdt[5] = V6PGD - VR5PI - VR5PE  # RU5P
    dxdt[6] = VR5PI + VRKb + VRKa - VTKL1 - VPRPPASe  # R5P
    dxdt[7] = VR5PE - VTKL1 - VTKL2  # X5P
    dxdt[8] = VTKL2 - VTAL  # E4P
    dxdt[9] = VTKL1 - VTAL  # S7P
    dxdt[10] = VFDPA + VTPI - VGAPDH + VTKL1 + VTKL2 - VTAL  # GA3P
    dxdt[11] = VPFK - VFDPA  # F16BP
    dxdt[12] = VFDPA - VTPI  # DHCP
    dxdt[13] = VGAPDH - VPGK - VDPGM  # B13PG
    dxdt[14] = VPGK - VPGM + V23DPGP  # P3G
    dxdt[15] = VDPGM - V23DPGP  # B23PG
    dxdt[16] = VPGM - VENOPGM  # P2G
    dxdt[17] = VENOPGM - VPK + VGENASP  # PEP
    dxdt[18] = VPK - VLDH - VEPYR + VME + VALATA - VPC  # PYR
    dxdt[19] = VLDH - VELAC  # LAC
    dxdt[20] = VFUM - VMLD - VEMAL  # MAL
    dxdt[21] = VPC + VMLD + VASPTA - VACLY - VGENASP  # OAA
    dxdt[22] = VACLY - VECIT  # CIT
    dxdt[23] = VACLY + VASTA  # COA (simplified)
    dxdt[24] = -VASTA  # SUCCOA (simplified)
    
    # Nucleotide metabolites
    dxdt[25] = -VEADE - VAPRT - VADA  # ADE (adenine decreases due to efflux)
    dxdt[26] = VEADO - VAK - VAK2 + VADA + VAHCY  # ADO
    dxdt[27] = VADA + Vnucleo2 - VEINO - VPNPase1  # INO
    dxdt[28] = VXAO + VPNPase1 + VOPRIBT - VHGPRT1 - VEHYPX  # HYPX
    dxdt[29] = VXAO - VXAO2 - VEXAN  # XAN
    dxdt[30] = VXAO2 - VEURT  # URT
    dxdt[31] = -VHGPRT2  # GUA
    dxdt[32] = VPNPase1 - VRKb  # R1P
    dxdt[33] = -VOPRIBT  # D2RIBP
    dxdt[34] = -VOPRIBT  # DEOXYINO
    dxdt[35] = VPGK + VPK + VAK + VACLY - VHK - VPFK - VAK2 - VAPRT - VHGPRT1 - VPC - VGLNS - VGLUCYS - VGSS - VSAM - VASL - VASS - VRKa - VPRPPASe  # ATP
    dxdt[36] = VHK + VPFK + VAK2 + VPC + VGLNS + VGLUCYS + VGSS + VASL + VRKa - VPGK - VPK - VAK  # ADP
    # AMP is algebraically determined: dxdt[37] = 0.0 (already set above)
    dxdt[38] = VADSS - VHGPRT2 - VGENASP  # GTP
    dxdt[39] = VGENASP - VADSS  # GDP
    dxdt[40] = VGMPS + VHGPRT2  # GMP
    dxdt[41] = VPRPPASe - VAPRT - VHGPRT1 - VHGPRT2  # PRPP
    dxdt[42] = VHGPRT1 + VAMPD1 - VADSS - VIMPH - Vnucleo2  # IMP
    dxdt[43] = VIMPH - VGMPS  # XMP
    dxdt[44] = VADSS - VADSL  # ADESUC
    
    # Amino acid and one-carbon metabolism
    dxdt[45] = VCBS - VCSE  # CYSTHIO
    dxdt[46] = VMESE + VAHCY - VCBS  # HCYS
    dxdt[47] = -VMESE  # METTHF
    dxdt[48] = VMESE - VSAM - VEMET  # MET
    dxdt[49] = VMESE  # THF
    dxdt[50] = VSAM - VSAH  # ADOMET
    dxdt[51] = VSAH - VAHCY  # SAH
    dxdt[52] = VSAH  # METCYT
    dxdt[53] = VASL - VASTA - Vpolyam  # ARG
    dxdt[54] = VASS - VASL  # ARGSUC
    dxdt[55] = -VASS  # CITR
    dxdt[56] = VADSL + VCSE - VADSS - VASS - VASPTA - VEASP  # ASP
    dxdt[57] = -VCBS  # SER
    dxdt[58] = VALATA - VEALA  # ALA
    dxdt[59] = VGDH + VCSE - VASPTA - VALATA  # AKG
    dxdt[60] = VASPTA + VALATA - VGDH - VGLNS - VGLUCYS - VEGLU  # GLU
    dxdt[61] = VGLNS - VGMPS - VEGLN  # GLN
    dxdt[62] = VADA + VAMPD1 + VCSE + VGLNS - VGDH - VENH4  # NH4
    dxdt[63] = VGGT - VGGCT  # GLUAA
    dxdt[64] = VGGCT - VGGT  # AA
    dxdt[65] = VGGCT  # OXOP
    dxdt[66] = VCYSGLY + VGSS  # GLY
    dxdt[67] = VCYSGLY + VCSE - VGLUCYS - VECYS  # CYS
    dxdt[68] = VGGT - VCYSGLY  # CYSGLY
    dxdt[69] = VGLUCYS - VGSS  # GLUCYS
    dxdt[70] = 2*VGSR + VGSS - 2*VGPX - VGGT  # GSH
    dxdt[71] = VGPX - VGSR  # GSSG
    dxdt[72] = Vpolyam  # ORN
    dxdt[73] = Vpolyam - VEUREA  # UREA
    dxdt[74] = -VACLY  # ACCOA
    
    # Redox and cofactor metabolites (75-84)
    dxdt[75] = VGAPDH + VMLD + VIMPH - VG6PDH - V6PGD - VLDH  # NAD
    dxdt[76] = VG6PDH + V6PGD + VLDH - VGAPDH - VMLD - VIMPH  # NADH
    dxdt[77] = VME + VGDH + VGSR - VG6PDH - V6PGD  # NADP
    dxdt[78] = VG6PDH + V6PGD - VME - VGDH - VGSR  # NADPH
    dxdt[79] = VXAO - VH2O2 - VGPX  # H2O2 (first instance)
    dxdt[80] = VH2O2  # O2
    dxdt[81] = VADSL + VASL - VFUM - VEFUM  # FUM
    dxdt[82] = -VRKa  # RIB
    dxdt[83] = VASTA  # SUCARG
    dxdt[84] = -VSAH - VECYT  # CYT
    
    # Extracellular metabolites (85-105)
    dxdt[85] = -VEGLC  # EGLC (consumption - negative flux)
    dxdt[86] = -VENH4  # ENH4
    dxdt[87] = VELAC   # ELAC
    dxdt[88] = -VEADO  # EADO
    dxdt[89] = VEADE   # EADE (adenine efflux - positive production)
    dxdt[90] = VEINO   # EINO (inosine efflux - positive production)
    dxdt[91] = VEGLN   # EGLN (glutamine efflux - positive production)
    dxdt[92] = VEGLU   # EGLU (glutamate efflux - positive production)
    dxdt[93] = VECYS   # ECYS (cysteine efflux - positive production)
    dxdt[94] = -VEMET  # EMET
    dxdt[95] = -VEASP  # EASP
    dxdt[96] = -VEUREA # EUREA
    dxdt[97] = -VEURT  # EURT
    dxdt[98] = -VEPYR  # EPYR
    dxdt[99] = -VEXAN  # EXAN
    dxdt[100] = VEHYPX  # EHYPX (hypoxanthine efflux - positive production)
    dxdt[101] = VEMAL   # EMAL (malate efflux - positive production)
    dxdt[102] = -VEFUM  # EFUM
    dxdt[103] = -VECIT  # ECIT
    dxdt[104] = -VEALA  # EALA
    dxdt[105] = -VECYT  # ECYT
    
    # ===== DYNAMIC pH REGULATION =====
    # pHi (intracellular pH) - index 106
    # Influenced by: 1) metabolic H+ production, 2) membrane transport, 3) buffering
    if _ENABLE_PH_MODULATION and PH_MODULES_AVAILABLE:
        # H+ production from glycolysis (lactate + NADH production)
        P_glycolysis = 0.1 * (VPK + VLDH)  # Pyruvate/lactate production generates H+
        
        # H+ consumption from oxidative reactions
        P_oxidation = 0.05 * (VG6PDH + V6PGD)  # NADPH production consumes H+
        
        # ATP hydrolysis (minor H+ production)
        P_ATP_hydrolysis = 0.01 * (VHK + VPFK)  # ATP consumption
        
        # Passive H+ diffusion (driven by pH gradient)
        # Positive when pHe > pHi (H+ flows IN, making cell more acidic, pH DOWN)
        J_H_passive = K_DIFF_H * (pHe - pHi) / 60.0  # Convert min to hours
        
        # Na+/H+ exchanger (exports H+ when pHi rises)
        # Positive when pHi > 7.2 (exports H+, making cell less acidic, pH UP)
        J_NHE = K_NHE * 0.1 * (pHi - 7.2) / 60.0  # Active when pHi > 7.2
        
        # Cl-/HCO3- exchanger (Band 3 - exports H+ via HCO3- import)
        # Positive when pHi > 7.2 (exports H+, making cell less acidic, pH UP)
        J_AE1 = K_AE1 * 0.15 * (pHi - 7.2) / 60.0  # Active when pHi > 7.2
        
        # Net change in pHi (buffered by hemoglobin and phosphates)
        # Sign convention: dpH/dt > 0 means pH rises (becomes more alkaline)
        #   - Metabolic H+ production → lowers pH (negative term)
        #   - J_H_passive > 0 when pHe > pHi → H+ export → pH rises (POSITIVE term)
        #   - J_NHE, J_AE1 > 0 when pHi > 7.2 → H+ export → pH rises (positive terms)
        dpHi_dt = (1.0 / BETA_BUFFER) * (
            -P_glycolysis + P_oxidation - P_ATP_hydrolysis  # Metabolic H+ balance
            + J_H_passive + J_NHE + J_AE1                    # Membrane transport (ALL POSITIVE for H+ export!)
        )
        
        dxdt[PHI_INDEX] = dpHi_dt
    else:
        # Simplified pH dynamics (original equation)
        dxdt[PHI_INDEX] = 0.01 * (0.1 * (VPK + VLDH) - 0.05 * (VG6PDH + V6PGD) - 0.2 * (pHi - 7.2))
    
    # pHe (extracellular pH) - index 107
    # Only compute if system has 108 metabolites (with pH perturbation)
    if len(x) > PHE_INDEX:
        # Determined by perturbation configuration if pH modulation is enabled
        if _ENABLE_PH_MODULATION and _PH_PERTURBATION is not None:
            # pHe follows the perturbation profile
            pHe_target = _PH_PERTURBATION.get_pHe(t)
            # Smooth transition to target (fast equilibration, ~1 min time constant)
            dxdt[PHE_INDEX] = (pHe_target - pHe) / (1.0/60.0)  # hours
        else:
            # No perturbation: pHe remains constant at physiological value
            dxdt[PHE_INDEX] = 0.0
    
    # ===== SIMPLIFIED CONSTRAINTS FOR CLEAN MM MODEL =====
    
    # Step 1: Enforce essential conservation laws (keep basic mass conservation) - DISABLED
    # try:
    #     # Initialize thermo_constraints if available
    #     constraints = ThermodynamicConstraints()
    #     dxdt = constraints.get_conservation_derivatives(x, dxdt)
    # except Exception as e:
    #     pass  # Skip if conservation constraints cause issues
    
    # Step 2: Eliminate ODEs for algebraically determined metabolites
    # AMP is determined by adenylate pool conservation: AMP = A_total - ATP - ADP
    dxdt[37] = 0.0  # AMP ODE eliminated (always enforced)
    
    # Step 3: Apply bounds constraints to prevent negative concentrations (safety net) - DISABLED
    # try:
    #     constraints = ThermodynamicConstraints()
    #     dxdt = constraints.apply_bounds_constraints(x, dxdt)
    # except Exception as e:
    #     pass  # Skip if bounds constraints cause issues
    
    # Step 4: Apply curve fitting corrections (if enabled)
    if curve_fit_strength > 0:
        try:
            from curve_fitting_data import get_curve_fit_correction, CURVE_FIT_PARAMS, compute_target_concentration
            
            # Apply corrections for ALL metabolites with experimental data (55 total)
            # Generated automatically from Data_Brodbar_et_al_exp.xlsx
            metabolite_corrections = {
                # Nucleotides and purines (intracellular)
                'ADE': 25,    # Adenine
                'ADO': 26,    # Adenosine (forced constant)
                'ADP': 36,    # Adenosine diphosphate
                'AMP': 37,    # Adenosine monophosphate
                'ATP': 35,    # Adenosine triphosphate
                'GMP': 40,    # Guanosine monophosphate
                'HYPX': 28,   # Hypoxanthine
                'IMP': 42,    # Inosine monophosphate
                'INO': 27,    # Inosine
                'URT': 30,    # Urate
                'XAN': 29,    # Xanthine
                
                # Amino acids (intracellular)
                'ALA': 58,    # Alanine
                'ARG': 53,    # Arginine
                'ASN': None,  # Asparagine (not in model, skip)
                'ASP': 56,    # Aspartate
                'CIT': 22,    # Citrate (TCA intermediate)
                'CITR': 55,   # Citrulline
                'GLN': 61,    # Glutamine
                'GLU': 60,    # Glutamate
                'SAH': 51,    # S-adenosylhomocysteine
                'SER': 57,    # Serine
                
                # Glycolysis and energy metabolites (intracellular)
                'B13PG': 13,  # 1,3-bisphosphoglycerate
                'B23PG': 15,  # 2,3-bisphosphoglycerate
                'E4P': 8,     # Erythrose 4-phosphate (forced constant)
                'F16BP': 11,  # Fructose 1,6-bisphosphate
                'F6P': 2,     # Fructose 6-phosphate
                'G6P': 1,     # Glucose 6-phosphate
                'GLC': 0,     # Glucose
                'GO6P': 4,    # 6-phosphogluconate
                'GSH': 70,    # Glutathione (reduced)
                'GSSG': 71,   # Glutathione (oxidized)
                'LAC': 19,    # Lactate
                'MAL': 20,    # Malate
                'NADH': 76,   # NADH (forced constant)
                'NADPH': 78,  # NADPH (forced constant)
                'OXOP': 65,   # 5-oxoproline
                'P2G': 16,    # 2-phosphoglycerate
                'P3G': 14,    # 3-phosphoglycerate
                'PEP': 17,    # Phosphoenolpyruvate
                'PYR': 18,    # Pyruvate
                
                # Extracellular metabolites
                'EADE': 89,   # Extracellular adenine
                'EALA': 104,  # Extracellular alanine (forced to zero)
                'EASN': None, # Extracellular asparagine (not in model)
                'ECIT': 103,  # Extracellular citrate
                'ECYS': 93,   # Extracellular cysteine
                'EFUM': 102,  # Extracellular fumarate
                'EGLC': 85,   # Extracellular glucose
                'EGLN': 91,   # Extracellular glutamine
                'EGLU': 92,   # Extracellular glutamate
                'EGSSG': None,# Extracellular GSSG (not in model)
                'EGSH': None, # Extracellular GSH (not in model)
                'EHYPX': 100, # Extracellular hypoxanthine
                'EINO': 90,   # Extracellular inosine
                'ELAC': 87,   # Extracellular lactate
                'EMAL': 101,  # Extracellular malate
                'ENH4': 86,   # Extracellular ammonia (forced to zero)
                'EARG': None, # Extracellular arginine (not in model)
                'EOXOP': None,# Extracellular oxoproline (not in model)
                'ESER': None, # Extracellular serine (not in model)
                'EUREA': 96,  # Extracellular urea (forced constant)
                'EURT': 97,   # Extracellular urate
                'EXAN': 99,   # Extracellular xanthine
            }
            
            for metabolite_name, idx in metabolite_corrections.items():
                # Skip metabolites not present in the model (idx=None)
                if idx is None:
                    continue
                if metabolite_name in CURVE_FIT_PARAMS and idx < len(dxdt):
                    # Get target concentration and current error
                    target_conc = compute_target_concentration(metabolite_name, t)
                    if target_conc is not None:
                        current_conc = x[idx]
                        error = target_conc - current_conc
                        
                        # Get feedback strength for this metabolite
                        params = CURVE_FIT_PARAMS[metabolite_name]
                        feedback = params['feedback']
                        
                        # At 100% curve fitting: REPLACE MM derivative with direct forcing
                        # At 0% curve fitting: Use pure MM derivative
                        # Interpolate between them
                        mm_derivative = dxdt[idx]  # Original MM kinetics
                        forcing_derivative = feedback * error  # Pure experimental forcing
                        
                        # Blend: at strength=1.0 use 100% forcing, at strength=0.0 use 100% MM
                        dxdt[idx] = (1.0 - curve_fit_strength) * mm_derivative + curve_fit_strength * forcing_derivative
                    
        except ImportError:
            # curve_fitting_data module not available - skip curve fitting
            pass
        except Exception as e:
            # Don't let curve fitting errors crash the simulation
            print(f"Warning: Curve fitting error at t={t:.2f}: {e}")
    
    # Step 5: Final numerical stability check (essential for integration)
    # Ensure all derivatives are finite and reasonable
    dxdt = np.nan_to_num(dxdt, nan=0.0, posinf=1e6, neginf=-1e6)
    
    # Clip extreme derivatives to prevent numerical instability
    dxdt = np.clip(dxdt, -MAX_DERIVATIVE, MAX_DERIVATIVE)
    
    # Step 6: Track fluxes if enabled
    if _TRACK_FLUXES and _FLUX_TRACKER is not None:
        flux_dict = {
            # Glycolysis
            'VHK': VHK, 'VPGI': VPGI, 'VPFK': VPFK, 'VFDPA': VFDPA,
            'VTPI': VTPI, 'VGAPDH': VGAPDH, 'VPGK': VPGK, 'VPGM': VPGM,
            'VENOPGM': VENOPGM, 'VPK': VPK, 'VLDH': VLDH,
            # Pentose Phosphate Pathway
            'VG6PDH': VG6PDH, 'VPGLS': VPGLS, 'V6PGD': V6PGD,
            'VR5PI': VR5PI, 'VR5PE': VR5PE, 'VTKL1': VTKL1,
            'VTKL2': VTKL2, 'VTAL': VTAL,
            # 2,3-BPG shunt
            'VDPGM': VDPGM, 'V23DPGP': V23DPGP,
            # Purine metabolism
            'VAPRT': VAPRT, 'VHGPRT1': VHGPRT1, 'VHGPRT2': VHGPRT2,
            'VADA': VADA, 'VAK': VAK, 'VAK2': VAK2,
            'VAMPD1': VAMPD1, 'VIMPH': VIMPH, 'VXAO': VXAO,
            'VGMPS': VGMPS, 'VADSS': VADSS, 'VADSL': VADSL,
            'VPNPase1': VPNPase1, 'VXAO2': VXAO2, 'Vnucleo2': Vnucleo2,
            'VRKa': VRKa, 'VRKb': VRKb, 'VPRPPASe': VPRPPASe,
            'VOPRIBT': VOPRIBT,
            # Amino acid metabolism
            'VGDH': VGDH, 'VGLNS': VGLNS, 'VGLUCYS': VGLUCYS,
            'VGSS': VGSS, 'VGSR': VGSR, 'VGGT': VGGT, 'VGGCT': VGGCT,
            'VMESE': VMESE, 'VSAM': VSAM, 'VSAH': VSAH, 'VAHCY': VAHCY,
            'VCBS': VCBS, 'VCSE': VCSE, 'VASPTA': VASPTA, 'VALATA': VALATA,
            'VGENASP': VGENASP, 'VFUM': VFUM, 'VMLD': VMLD,
            'VASL': VASL, 'VASS': VASS, 'Vpolyam': Vpolyam,
            'VASTA': VASTA, 'VCYSGLY': VCYSGLY,
            # Other
            'VH2O2': VH2O2, 'VGPX': VGPX, 'VME': VME, 'VPC': VPC,
            'VACLY': VACLY,
            # Transport
            'VEGLC': VEGLC, 'VELAC': VELAC, 'VEPYR': VEPYR,
            'VEGLN': VEGLN, 'VEGLU': VEGLU, 'VECYS': VECYS,
            'VEADE': VEADE, 'VEINO': VEINO, 'VEADO': VEADO,
            'VEHYPX': VEHYPX, 'VEXAN': VEXAN, 'VEURT': VEURT,
            'VECIT': VECIT, 'VEMAL': VEMAL, 'VEFUM': VEFUM,
            'VEUREA': VEUREA, 'VENH4': VENH4, 'VEASP': VEASP,
            'VEMET': VEMET, 'VECYT': VECYT, 'VEALA': VEALA
        }
        _FLUX_TRACKER.add_timepoint(t, flux_dict)
    
    # Step 7: Track Bohr effect if enabled
    if _TRACK_BOHR and _BOHR_EFFECT is not None and _BOHR_TRACKER is not None:
        # Extract current pHi, pHe, and 2,3-BPG concentration
        current_pHi = x[PHI_INDEX] if len(x) > PHI_INDEX else PHYSIOLOGICAL_PH
        current_pHe = x[PHE_INDEX] if len(x) > PHE_INDEX else PHYSIOLOGICAL_PHE
        current_bpg = x[B23PG_INDEX] if len(x) > B23PG_INDEX else 5.0  # mM
        
        # Calculate P50 based on current pHi and BPG
        # NOTE: Using pHi because P50 is determined by RBC internal environment
        P50 = _BOHR_EFFECT.calculate_P50(pH=current_pHi, bpg_conc=current_bpg)
        
        # Calculate O2 saturations at typical arterial and venous pO2
        # IMPORTANT: Use pHe for blood pH since O2 binding occurs at RBC surface
        # where external pH matters for CO2/HCO3- equilibrium
        # Arterial: pO2 ~100 mmHg, use current pHe (extracellular environment)
        # Venous: pO2 ~40 mmHg, pHe slightly more acidic due to tissue CO2
        pO2_arterial = 100.0  # mmHg
        pO2_venous = 40.0   # mmHg
        pH_arterial = current_pHe  # Use actual extracellular pH
        pH_venous = current_pHe - 0.05  # Tissue CO2 addition (~0.05 pH drop)
        
        sat_arterial = _BOHR_EFFECT.oxygen_saturation(pO2_arterial, pH_arterial, current_bpg)
        sat_venous = _BOHR_EFFECT.oxygen_saturation(pO2_venous, pH_venous, current_bpg)
        
        # Calculate O2 delivery metrics
        O2_delivery = _BOHR_EFFECT.oxygen_delivery_to_tissues(
            arterial_pO2=pO2_arterial,
            venous_pO2=pO2_venous,
            pH_arterial=pH_arterial,
            pH_venous=pH_venous,
            bpg_conc=current_bpg
        )
        
        # Store Bohr metrics
        _BOHR_TRACKER['time'].append(t)
        _BOHR_TRACKER['pHi'].append(current_pHi)
        _BOHR_TRACKER['pHe'].append(current_pHe)  # Track extracellular pH
        _BOHR_TRACKER['BPG_mM'].append(current_bpg)
        _BOHR_TRACKER['P50_mmHg'].append(P50)
        _BOHR_TRACKER['sat_arterial'].append(sat_arterial)
        _BOHR_TRACKER['sat_venous'].append(sat_venous)
        _BOHR_TRACKER['O2_extracted_fraction'].append(O2_delivery['extraction_fraction'])
        _BOHR_TRACKER['O2_arterial_mL_per_dL'].append(O2_delivery['O2_arterial_mL_per_dL'])
        _BOHR_TRACKER['O2_venous_mL_per_dL'].append(O2_delivery['O2_venous_mL_per_dL'])
    
    return dxdt