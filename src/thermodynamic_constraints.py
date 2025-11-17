"""
Thermodynamic constraints and conservation laws for RBC metabolic model.
This module implements Gibbs free energy constraints and proper mass conservation.
Author: Jorgelindo da Veiga
"""
import numpy as np
import math

# Thermodynamic constants
R = 8.314  # J/(mol·K) - Gas constant
T = 310.15  # K - Physiological temperature (37°C)
F = 96485  # C/mol - Faraday constant

class ThermodynamicConstraints:
    """Class to handle thermodynamic constraints and conservation laws."""
    
    def __init__(self):
        """Initialize thermodynamic parameters and conservation pools."""
        # Standard Gibbs free energies (kJ/mol) at pH 7.0, 37°C
        self.delta_g_standard = {
            'ATP_hydrolysis': -30.5,  # ATP -> ADP + Pi
            'NADH_oxidation': -220.0,  # NADH -> NAD+ + H+ + 2e-
            'NADPH_oxidation': -220.0,  # NADPH -> NADP+ + H+ + 2e-
            'glucose_phosphorylation': -16.7,  # Glc + ATP -> G6P + ADP
            'pyruvate_to_lactate': -25.1,  # Pyr + NADH -> Lac + NAD+
        }
        
        # Conservation pool totals (mM) - will be set from experimental data
        self.pool_totals = {
            'adenylate': None,  # ATP + ADP + AMP
            'nad': None,        # NAD + NADH  
            'nadp': None,       # NADP + NADPH
            'glutathione': None # GSH + 2*GSSG
        }
        
    def set_pool_totals_from_experimental_data(self, exp_data):
        """Set conservation pool totals from experimental first values."""
        try:
            # Calculate adenylate pool total
            atp = exp_data.get('ATP', 1.0)
            adp = exp_data.get('ADP', 0.5) 
            amp = exp_data.get('AMP', 0.1)
            self.pool_totals['adenylate'] = atp + adp + amp
            
            # Calculate NAD pool total
            nad = exp_data.get('NAD', 2.0)
            nadh = exp_data.get('NADH', 0.5)
            self.pool_totals['nad'] = nad + nadh
            
            # Calculate NADP pool total
            nadp = exp_data.get('NADP', 0.15)
            nadph = exp_data.get('NADPH', 0.05)
            self.pool_totals['nadp'] = nadp + nadph
            
            # Calculate glutathione pool total (accounting for GSSG dimer)
            gsh = exp_data.get('GSH', 1.8)
            gssg = exp_data.get('GSSG', 0.1)
            self.pool_totals['glutathione'] = gsh + 2.0 * gssg
            
        except Exception as e:
            print(f"Warning: Could not set pool totals from experimental data: {e}")
            # Use default physiological values
            self.pool_totals = {
                'adenylate': 1.5,    # mM
                'nad': 2.5,          # mM
                'nadp': 0.2,         # mM
                'glutathione': 2.0   # mM
            }
    
    def enforce_conservation_laws(self, x):
        """
        Enforce mass conservation for cofactor pools.
        
        Parameters:
        -----------
        x : numpy.ndarray
            Current state vector (concentrations)
            
        Returns:
        --------
        numpy.ndarray
            Corrected state vector with conservation laws enforced
        """
        x_corrected = x.copy()
        
        # Adenylate pool conservation: ATP + ADP + AMP = constant
        atp_idx, adp_idx, amp_idx = 35, 36, 37  # From BRODBAR_METABOLITE_MAP
        A_total = self.pool_totals['adenylate']
        
        if A_total is not None:
            current_total = x_corrected[atp_idx] + x_corrected[adp_idx] + x_corrected[amp_idx]
            if current_total > 0:
                # Redistribute proportionally to maintain ratios
                scale_factor = A_total / current_total
                x_corrected[atp_idx] *= scale_factor
                x_corrected[adp_idx] *= scale_factor
                x_corrected[amp_idx] *= scale_factor
            else:
                # Use energy charge to distribute adenylates
                energy_charge = 0.8  # Typical physiological value
                x_corrected[atp_idx] = A_total * energy_charge
                x_corrected[adp_idx] = A_total * (1 - energy_charge) * 0.8
                x_corrected[amp_idx] = A_total * (1 - energy_charge) * 0.2
        
        # NAD pool conservation: NAD + NADH = constant
        nad_idx, nadh_idx = 75, 76  # From BRODBAR_METABOLITE_MAP
        NAD_total = self.pool_totals['nad']
        
        if NAD_total is not None:
            current_nad_total = x_corrected[nad_idx] + x_corrected[nadh_idx]
            if current_nad_total > 0:
                scale_factor = NAD_total / current_nad_total
                x_corrected[nad_idx] *= scale_factor
                x_corrected[nadh_idx] *= scale_factor
            else:
                # Default distribution: 80% NAD+, 20% NADH
                x_corrected[nad_idx] = NAD_total * 0.8
                x_corrected[nadh_idx] = NAD_total * 0.2
        
        # NADP pool conservation: NADP + NADPH = constant  
        nadp_idx, nadph_idx = 77, 78  # From BRODBAR_METABOLITE_MAP
        NADP_total = self.pool_totals['nadp']
        
        if NADP_total is not None:
            current_nadp_total = x_corrected[nadp_idx] + x_corrected[nadph_idx]
            if current_nadp_total > 0:
                scale_factor = NADP_total / current_nadp_total
                x_corrected[nadp_idx] *= scale_factor
                x_corrected[nadph_idx] *= scale_factor
            else:
                # Default distribution: 75% NADP+, 25% NADPH
                x_corrected[nadp_idx] = NADP_total * 0.75
                x_corrected[nadph_idx] = NADP_total * 0.25
        
        # Glutathione pool conservation: GSH + 2*GSSG = constant
        gsh_idx, gssg_idx = 70, 71  # From BRODBAR_METABOLITE_MAP
        GSH_total = self.pool_totals['glutathione']
        
        if GSH_total is not None:
            current_gsh_total = x_corrected[gsh_idx] + 2.0 * x_corrected[gssg_idx]
            if current_gsh_total > 0:
                scale_factor = GSH_total / current_gsh_total
                x_corrected[gsh_idx] *= scale_factor
                x_corrected[gssg_idx] *= scale_factor
            else:
                # Default distribution: 90% GSH, 5% GSSG (accounting for dimer)
                x_corrected[gsh_idx] = GSH_total * 0.9
                x_corrected[gssg_idx] = GSH_total * 0.05
        
        # Ensure all concentrations are positive
        x_corrected = np.maximum(x_corrected, 1e-6)
        
        return x_corrected
    
    def calculate_energy_charge(self, x):
        """
        Calculate adenylate energy charge: (ATP + 0.5*ADP) / (ATP + ADP + AMP)
        
        Parameters:
        -----------
        x : numpy.ndarray
            Current state vector
            
        Returns:
        --------
        float
            Energy charge (0-1)
        """
        atp_idx, adp_idx, amp_idx = 35, 36, 37
        atp = max(x[atp_idx], 1e-6)
        adp = max(x[adp_idx], 1e-6)
        amp = max(x[amp_idx], 1e-6)
        
        total_adenylates = atp + adp + amp
        energy_charge = (atp + 0.5 * adp) / total_adenylates
        
        return np.clip(energy_charge, 0.0, 1.0)
    
    def calculate_redox_ratios(self, x):
        """
        Calculate redox ratios for NAD and NADP systems.
        
        Parameters:
        -----------
        x : numpy.ndarray
            Current state vector
            
        Returns:
        --------
        dict
            Dictionary containing redox ratios
        """
        nad_idx, nadh_idx = 75, 76
        nadp_idx, nadph_idx = 77, 78
        gsh_idx, gssg_idx = 70, 71
        
        nad = max(x[nad_idx], 1e-6)
        nadh = max(x[nadh_idx], 1e-6)
        nadp = max(x[nadp_idx], 1e-6)
        nadph = max(x[nadph_idx], 1e-6)
        gsh = max(x[gsh_idx], 1e-6)
        gssg = max(x[gssg_idx], 1e-6)
        
        return {
            'nad_nadh_ratio': nad / nadh,
            'nadh_nad_ratio': nadh / nad,
            'nadp_nadph_ratio': nadp / nadph,
            'nadph_nadp_ratio': nadph / nadp,
            'gsh_gssg_ratio': gsh / gssg,
            'oxidative_stress': gssg / (gsh + gssg)
        }
    
    def check_gibbs_feasibility(self, reaction_name, reactant_conc, product_conc, n_electrons=0):
        """
        Check if a reaction is thermodynamically feasible.
        
        Parameters:
        -----------
        reaction_name : str
            Name of the reaction
        reactant_conc : float
            Reactant concentration (mM)
        product_conc : float
            Product concentration (mM)
        n_electrons : int
            Number of electrons transferred
            
        Returns:
        --------
        bool
            True if reaction is thermodynamically feasible
        """
        if reaction_name not in self.delta_g_standard:
            return True  # Assume feasible if no data available
        
        delta_g_std = self.delta_g_standard[reaction_name]
        
        # Calculate reaction quotient Q
        Q = product_conc / max(reactant_conc, 1e-6)
        
        # Calculate actual Gibbs free energy
        delta_g = delta_g_std + (R * T / 1000) * math.log(Q)  # Convert to kJ/mol
        
        # Add electrical work if electrons are involved
        if n_electrons > 0:
            # Assume standard redox potential conditions
            delta_g += n_electrons * F * 0.0 / 1000  # No additional potential
        
        # Reaction is feasible if ΔG < 0
        return delta_g < 0
    
    def apply_thermodynamic_corrections(self, flux, reaction_name, reactant_conc, product_conc):
        """
        Apply thermodynamic corrections to reaction fluxes.
        
        Parameters:
        -----------
        flux : float
            Calculated reaction flux
        reaction_name : str
            Name of the reaction
        reactant_conc : float
            Reactant concentration
        product_conc : float
            Product concentration
            
        Returns:
        --------
        float
            Thermodynamically corrected flux
        """
        # Check if reaction is thermodynamically feasible
        is_feasible = self.check_gibbs_feasibility(reaction_name, reactant_conc, product_conc)
        
        if not is_feasible and flux > 0:
            # Reduce flux if reaction is not feasible in forward direction
            return flux * 0.1  # Allow small flux for numerical stability
        elif not is_feasible and flux < 0:
            # Allow reverse flux if forward is not feasible
            return flux
        else:
            # No correction needed
            return flux
    
    def get_conservation_derivatives(self, x, dxdt):
        """
        Calculate derivatives that maintain conservation laws.
        
        Parameters:
        -----------
        x : numpy.ndarray
            Current state vector
        dxdt : numpy.ndarray
            Current derivatives
            
        Returns:
        --------
        numpy.ndarray
            Corrected derivatives that maintain conservation
        """
        dxdt_corrected = dxdt.copy()
        
        # Adenylate pool conservation: d(ATP + ADP + AMP)/dt = 0
        atp_idx, adp_idx, amp_idx = 35, 36, 37
        adenylate_drift = dxdt_corrected[atp_idx] + dxdt_corrected[adp_idx] + dxdt_corrected[amp_idx]
        
        # Distribute correction proportionally to current concentrations
        if adenylate_drift != 0:
            total_adenylates = x[atp_idx] + x[adp_idx] + x[amp_idx]
            if total_adenylates > 0:
                dxdt_corrected[atp_idx] -= adenylate_drift * (x[atp_idx] / total_adenylates)
                dxdt_corrected[adp_idx] -= adenylate_drift * (x[adp_idx] / total_adenylates)
                dxdt_corrected[amp_idx] -= adenylate_drift * (x[amp_idx] / total_adenylates)
        
        # NAD pool conservation: d(NAD + NADH)/dt = 0
        nad_idx, nadh_idx = 75, 76
        nad_drift = dxdt_corrected[nad_idx] + dxdt_corrected[nadh_idx]
        
        if nad_drift != 0:
            total_nad = x[nad_idx] + x[nadh_idx]
            if total_nad > 0:
                dxdt_corrected[nad_idx] -= nad_drift * (x[nad_idx] / total_nad)
                dxdt_corrected[nadh_idx] -= nad_drift * (x[nadh_idx] / total_nad)
        
        # NADP pool conservation: d(NADP + NADPH)/dt = 0
        nadp_idx, nadph_idx = 77, 78
        nadp_drift = dxdt_corrected[nadp_idx] + dxdt_corrected[nadph_idx]
        
        if nadp_drift != 0:
            total_nadp = x[nadp_idx] + x[nadph_idx]
            if total_nadp > 0:
                dxdt_corrected[nadp_idx] -= nadp_drift * (x[nadp_idx] / total_nadp)
                dxdt_corrected[nadph_idx] -= nadp_drift * (x[nadph_idx] / total_nadp)
        
        # Glutathione pool conservation: d(GSH + 2*GSSG)/dt = 0
        gsh_idx, gssg_idx = 70, 71
        gsh_drift = dxdt_corrected[gsh_idx] + 2.0 * dxdt_corrected[gssg_idx]
        
        if gsh_drift != 0:
            total_gsh_equiv = x[gsh_idx] + 2.0 * x[gssg_idx]
            if total_gsh_equiv > 0:
                dxdt_corrected[gsh_idx] -= gsh_drift * (x[gsh_idx] / total_gsh_equiv)
                dxdt_corrected[gssg_idx] -= gsh_drift * (2.0 * x[gssg_idx] / total_gsh_equiv) / 2.0
        
        return dxdt_corrected
    
    def apply_bounds_constraints(self, x, dxdt):
        """
        Apply bounds constraints to prevent negative concentrations.
        
        Parameters:
        -----------
        x : numpy.ndarray
            Current state vector
        dxdt : numpy.ndarray
            Current derivatives
            
        Returns:
        --------
        numpy.ndarray
            Bounded derivatives
        """
        dxdt_bounded = dxdt.copy()
        min_concentration = 1e-6
        
        # Prevent derivatives that would cause negative concentrations
        for i in range(len(x)):
            if x[i] <= min_concentration and dxdt_bounded[i] < 0:
                dxdt_bounded[i] = 0.0  # Stop further decrease
            elif x[i] <= 2 * min_concentration and dxdt_bounded[i] < 0:
                # Apply soft constraint near boundary
                barrier_strength = 1.0 / (x[i] - min_concentration + 1e-12)
                dxdt_bounded[i] += barrier_strength * abs(dxdt_bounded[i])
        
        return dxdt_bounded
