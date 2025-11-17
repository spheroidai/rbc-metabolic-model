"""
Compute Enzyme Fluxes from RBC Model State

Extract all Michaelis-Menten reaction fluxes from the state vector
without modifying the core equadiff_brodbar.py

This allows flux tracking while keeping MM kinetics intact.

Author: Jorgelindo da Veiga
Date: October 2025
"""

import numpy as np
from numpy.typing import NDArray
from typing import Dict, Optional


def mm(S: float, Km: float) -> float:
    """Michaelis-Menten saturation term: S/(Km + S)"""
    return S / (Km + S) if (Km + S) > 0 else 0.0


def compute_all_fluxes(x: NDArray[np.float64], 
                       custom_params: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Compute all enzyme fluxes from current state vector.
    
    This function extracts all Michaelis-Menten reaction rates
    for flux analysis and tracking.
    
    Parameters:
    -----------
    x : NDArray[np.float64]
        State vector (107 metabolites)
    custom_params : Optional[Dict[str, float]]
        Custom parameters (Vmax/Km values)
        
    Returns:
    --------
    Dict[str, float]
        Dictionary of {reaction_name: flux_value} for all reactions
    """
    
    def _get_param(param_name: str, default_value: float) -> float:
        """Get parameter from custom dict or use default."""
        if custom_params is not None and param_name in custom_params:
            return custom_params[param_name]
        return default_value
    
    # Extract all Vmax parameters
    vmax_VELAC = _get_param('vmax_VELAC', 0.580000)
    vmax_VEADE = _get_param('vmax_VEADE', 0.010000)
    vmax_VEINO = _get_param('vmax_VEINO', 0.0001000)
    vmax_VEHYPX = _get_param('vmax_VEHYPX', 0.002217)
    vmax_VEMAL = _get_param('vmax_VEMAL', 0.001227)
    vmax_VHK = _get_param('vmax_VHK', 0.267472)
    vmax_VPGI = _get_param('vmax_VPGI', 0.204493)
    vmax_VPFK = _get_param('vmax_VPFK', 0.391893)
    vmax_VFDPA = _get_param('vmax_VFDPA', 1.156751)
    vmax_VTPI = _get_param('vmax_VTPI', 15.0)
    vmax_VGAPDH = _get_param('vmax_VGAPDH', 6.389868)
    vmax_VPGK = _get_param('vmax_VPGK', 4.690379)
    vmax_VPGM = _get_param('vmax_VPGM', 1.170854)
    vmax_VENOPGM = _get_param('vmax_VENOPGM', 5.515612)
    vmax_VPK = _get_param('vmax_VPK', 0.936322)
    vmax_VLDH = _get_param('vmax_VLDH', 0.284952)
    vmax_VG6PDH = _get_param('vmax_VG6PDH', 0.408870)
    vmax_VPGLS = _get_param('vmax_VPGLS', 4.111138)
    vmax_V6PGD = _get_param('vmax_V6PGD', 10.0)
    
    # Extract Km parameters
    km_LAC = _get_param('km_LAC', 49.862494)
    km_ADE = _get_param('km_ADE', 0.369082)
    km_GLC = _get_param('km_GLC', 49.864721)
    km_G6P = _get_param('km_G6P', 0.146000)
    km_F6P = _get_param('km_F6P', 0.207000)
    km_ATP = _get_param('km_ATP', 0.569395)
    km_ADP = _get_param('km_ADP', 0.402663)
    
    # Metabolite concentrations
    LAC = x[19]  # Intracellular lactate
    ELAC = x[87]  # Extracellular lactate
    ADE = x[2]  # Adenine
    EADE = x[84]  # Extracellular adenine
    GLC = x[34]  # Glucose
    EGLC = x[85]  # Extracellular glucose
    G6P = x[30]  # Glucose-6-phosphate
    F6P = x[28]  # Fructose-6-phosphate
    F16BP = x[27]  # Fructose-1,6-bisphosphate
    GA3P = x[29]  # Glyceraldehyde-3-phosphate
    DHCP = x[22]  # Dihydroxyacetone phosphate
    B13PG = x[13]  # 1,3-bisphosphoglycerate
    P3G = x[66]  # 3-phosphoglycerate
    P2G = x[65]  # 2-phosphoglycerate
    PEP = x[67]  # Phosphoenolpyruvate
    PYR = x[69]  # Pyruvate
    ATP = x[11]  # ATP
    ADP = x[7]  # ADP
    NAD = x[56]  # NAD
    NADP = x[58]  # NADP
    GO6P = x[31]  # 6-Phosphogluconolactone
    GL6P = x[32]  # 6-Phosphogluconate
    
    # Compute conservation pools
    A_tot = 1.5  # Total adenylate pool
    NAD_tot = 0.5  # Total NAD pool
    NADP_tot = 0.2  # Total NADP pool
    
    AMP = max(A_tot - ATP - ADP, 0.0)
    NADH = max(NAD_tot - NAD, 0.0)
    NADPH = max(NADP_tot - NADP, 0.0)
    
    # Initialize flux dictionary
    fluxes = {}
    
    # ===== TRANSPORT REACTIONS =====
    # Lactate transport (bidirectional)
    VELAC_out = vmax_VELAC * mm(LAC, km_LAC)  # Efflux
    VELAC_in = vmax_VELAC * mm(ELAC, km_LAC)  # Influx
    fluxes['VELAC'] = VELAC_out - VELAC_in  # Net flux
    
    # Adenine transport
    VEADE = vmax_VEADE * mm(EADE, km_ADE)
    fluxes['VEADE'] = VEADE
    
    # Glucose transport
    vmax_VEGLC = _get_param('vmax_VEGLC', 1.077000)
    km_EGLC = _get_param('km_EGLC', 49.484000)
    VEGLC = vmax_VEGLC * mm(EGLC, km_EGLC)
    fluxes['VEGLC'] = VEGLC
    
    # ===== GLYCOLYSIS PATHWAY =====
    # Hexokinase: GLC + ATP -> G6P + ADP
    VHK = vmax_VHK * mm(GLC, km_GLC) * mm(ATP, km_ATP)
    fluxes['VHK'] = VHK
    
    # Phosphoglucose isomerase: G6P <-> F6P
    VPGI = vmax_VPGI * mm(G6P, km_G6P)
    fluxes['VPGI'] = VPGI
    
    # Phosphofructokinase: F6P + ATP -> F16BP + ADP
    # With allosteric regulation
    atp_inhibition = 1.0 / (1.0 + (ATP / 2.0)**2)
    amp_activation = 1.0 + 2.0 * (AMP / 0.1)
    VPFK = vmax_VPFK * mm(F6P, km_F6P) * mm(ATP, km_ATP) * atp_inhibition * amp_activation
    fluxes['VPFK'] = VPFK
    
    # Aldolase: F16BP <-> GA3P + DHCP
    km_F16BP = _get_param('km_F16BP', 0.094000)
    VFDPA = vmax_VFDPA * mm(F16BP, km_F16BP)
    fluxes['VFDPA'] = VFDPA
    
    # Triose phosphate isomerase: DHCP <-> GA3P
    km_DHCP = _get_param('km_DHCP', 0.05)
    VTPI = vmax_VTPI * mm(DHCP, km_DHCP)
    fluxes['VTPI'] = VTPI
    
    # GAPDH: GA3P + NAD + Pi -> B13PG + NADH
    km_GA3P = _get_param('km_GA3P', 0.02)
    km_NAD = _get_param('km_NAD', 0.2)
    VGAPDH = vmax_VGAPDH * mm(GA3P, km_GA3P) * mm(NAD, km_NAD)
    fluxes['VGAPDH'] = VGAPDH
    
    # Phosphoglycerate kinase: B13PG + ADP <-> P3G + ATP
    km_B13PG = _get_param('km_B13PG', 1.013344)
    VPGK = vmax_VPGK * mm(B13PG, km_B13PG) * mm(ADP, km_ADP)
    fluxes['VPGK'] = VPGK
    
    # Phosphoglycerate mutase: P3G <-> P2G
    km_P3G = _get_param('km_P3G', 0.134000)
    VPGM = vmax_VPGM * mm(P3G, km_P3G)
    fluxes['VPGM'] = VPGM
    
    # Enolase: P2G <-> PEP
    km_P2G = _get_param('km_P2G', 0.134000)
    VENOPGM = vmax_VENOPGM * mm(P2G, km_P2G)
    fluxes['VENOPGM'] = VENOPGM
    
    # Pyruvate kinase: PEP + ADP -> PYR + ATP
    km_PEP = _get_param('km_PEP', 0.175000)
    VPK = vmax_VPK * mm(PEP, km_PEP) * mm(ADP, km_ADP)
    fluxes['VPK'] = VPK
    
    # Lactate dehydrogenase: PYR + NADH <-> LAC + NAD
    km_PYR = _get_param('km_PYR', 0.697000)
    km_NADH = _get_param('km_NADH', 0.1)
    VLDH_forward = vmax_VLDH * mm(PYR, km_PYR) * mm(NADH, km_NADH)
    VLDH_reverse = vmax_VLDH * 0.1 * mm(LAC, km_LAC) * mm(NAD, km_NAD)  # Reverse rate
    fluxes['VLDH'] = VLDH_forward - VLDH_reverse
    
    # ===== PENTOSE PHOSPHATE PATHWAY =====
    # G6PDH: G6P + NADP -> GO6P + NADPH
    km_NADP = _get_param('km_NADP', 0.05)
    VG6PDH = vmax_VG6PDH * mm(G6P, km_G6P) * mm(NADP, km_NADP)
    fluxes['VG6PDH'] = VG6PDH
    
    # Phosphogluconolactonase: GO6P -> GL6P
    km_GO6P = _get_param('km_GO6P', 0.02)
    VPGLS = vmax_VPGLS * mm(GO6P, km_GO6P)
    fluxes['VPGLS'] = VPGLS
    
    # 6PGD: GL6P + NADP -> RU5P + NADPH + CO2
    km_GL6P = _get_param('km_GL6P', 0.1)
    V6PGD = vmax_V6PGD * mm(GL6P, km_GL6P) * mm(NADP, km_NADP)
    fluxes['V6PGD'] = V6PGD
    
    # Add more reactions as needed...
    
    return fluxes


def track_fluxes_during_simulation(t_span: tuple, 
                                   x0: NDArray[np.float64],
                                   t_eval: NDArray[np.float64],
                                   custom_params: Optional[Dict] = None) -> Dict[str, np.ndarray]:
    """
    Run simulation and track all fluxes at specified time points.
    
    Parameters:
    -----------
    t_span : tuple
        (t_start, t_end) for simulation
    x0 : NDArray[np.float64]
        Initial conditions
    t_eval : NDArray[np.float64]
        Time points to evaluate fluxes
    custom_params : Optional[Dict]
        Custom Vmax/Km parameters
        
    Returns:
    --------
    Dict[str, np.ndarray]
        Dictionary with:
        - 'times': time points
        - 'solution': metabolite concentrations (107 x n_timepoints)
        - 'fluxes': dict of {reaction_name: flux_array}
    """
    from scipy.integrate import solve_ivp
    from equadiff_brodbar import equadiff_brodbar
    
    # Run simulation
    print("Running simulation...")
    solution = solve_ivp(
        lambda t, x: equadiff_brodbar(t, x, thermo_constraints=None, custom_params=custom_params),
        t_span=t_span,
        y0=x0,
        method='RK45',
        t_eval=t_eval,
        max_step=1.0
    )
    
    if not solution.success:
        raise ValueError(f"Simulation failed: {solution.message}")
    
    print(f"Simulation complete. Computing fluxes at {len(solution.t)} time points...")
    
    # Compute fluxes at each time point
    flux_dict = {}
    for i, t in enumerate(solution.t):
        x_current = solution.y[:, i]
        fluxes = compute_all_fluxes(x_current, custom_params)
        
        # Initialize arrays on first iteration
        if i == 0:
            for rxn_name in fluxes.keys():
                flux_dict[rxn_name] = np.zeros(len(solution.t))
        
        # Store fluxes
        for rxn_name, flux_value in fluxes.items():
            flux_dict[rxn_name][i] = flux_value
    
    print("Flux computation complete!")
    
    return {
        'times': solution.t,
        'solution': solution.y,
        'fluxes': flux_dict
    }


# Example usage
if __name__ == "__main__":
    print("Flux Computation Module")
    print("="*70)
    print("\nThis module computes all enzyme fluxes from the state vector")
    print("while maintaining Michaelis-Menten kinetics.")
    print("\nKey functions:")
    print("  - compute_all_fluxes(x, custom_params)")
    print("  - track_fluxes_during_simulation(t_span, x0, t_eval, custom_params)")
