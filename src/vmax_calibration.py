"""
ML-based Vmax Recalibration for the RBC Metabolic Model
========================================================
Multi-phase Bayesian Optimization (optuna TPE) with normalized RMSE loss.
Falls back to scipy differential_evolution if optuna is not available.

Phases:
  1. Core glycolysis & transport (8 params)  — fixes GLC, LAC, ATP, B23PG
  2. Nucleotide metabolism (10 params)        — fixes IMP, HYPX, GMP, ADE
  3. Amino acids, redox & remaining (12 params) — fixes GLU, GSH, MAL

Usage:
    python src/vmax_calibration.py                          # Run all phases
    python src/vmax_calibration.py --phases 1               # Phase 1 only
    python src/vmax_calibration.py --phases 1,2 --n-trials 300
    python src/vmax_calibration.py --load-params best_params.json  # Resume from saved
"""

import sys
import os
import json
import time
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

# Ensure src is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from equadiff_brodbar import equadiff_brodbar, BRODBAR_METABOLITE_MAP
from parse_initial_conditions import parse_initial_conditions

# Try to import optuna for Bayesian optimization
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False
    from scipy.optimize import differential_evolution

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path(__file__).parent
OUT_DIR = Path(__file__).parent.parent / 'Simulations' / 'brodbar' / 'calibration'

# Experimental metabolite name -> model index mapping
# Only metabolites with BOTH experimental data AND model representation
EXP_TO_MODEL = {
    'GLC': 0, 'G6P': 1, 'F6P': 2, 'GO6P': 4,
    'F16BP': 11, 'B13PG': 13, 'P3G': 14, 'B23PG': 15,
    'P2G': 16, 'PEP': 17, 'PYR': 18, 'LAC': 19, 'MAL': 20,
    'CIT': 22, 'ADE': 25, 'INO': 27, 'HYPX': 28, 'XAN': 29, 'URT': 30,
    'ATP': 35, 'ADP': 36, 'AMP': 37, 'GMP': 40, 'IMP': 42,
    'SAH': 51, 'ARG': 53, 'CITR': 55, 'ASP': 56, 'SER': 57,
    'ALA': 58, 'GLU': 60, 'GLN': 61, 'OXOP': 65,
    'GSH': 70, 'GSSG': 71,
    'EGLC': 85, 'ELAC': 87, 'EADE': 89, 'EINO': 90,
    'EGLN': 91, 'EGLU': 92, 'ECYS': 93,
    'EURT': 97, 'EXAN': 99, 'EHYPX': 100, 'EMAL': 101,
    'EFUM': 102, 'ECIT': 103,
}

EXTRACELLULAR_TARGET_METABOLITES = {
    name for name in EXP_TO_MODEL if name.startswith('E')
}

# Metabolites to weight more heavily in loss (critical for physiology)
HIGH_WEIGHT_METABOLITES = {
    'GLC', 'G6P', 'ATP', 'ADP', 'AMP', 'LAC', 'PYR',
    'B23PG', 'EGLC', 'ELAC', 'GSH', 'GSSG',
}

# Extra-high weight metabolites that were previously sacrificed by the optimizer
CRITICAL_WEIGHT_METABOLITES = {
    'PEP': 5.0,   # Optimizer was ignoring PEP due to nRMSE cap; force attention
    'P2G': 3.0,   # Prevent accumulation shifting upstream when VENOPGM is reduced
    'ATP': 10.0,  # Force optimizer to maintain adenylate pool (was crashing to 0, exp declines 50% over 42d)
    'ADP': 10.0,  # Adenylate pool conservation — ADP crashes with ATP
    'AMP': 5.0,   # Adenylate pool conservation — was accumulating to 2.0 (all pool shifted to AMP)
}

# Cap per-metabolite nRMSE so structural outliers don't dominate the loss.
# Metabolites with nRMSE > cap are likely structural model issues, not fixable
# by Vmax tuning alone. Capping lets the optimizer focus on tractable improvements.
NRMSE_CAP = 50.0

# ============================================================================
# PARAMETER PHASE DEFINITIONS
# Each: param_name -> (default, lower_bound, upper_bound)
# Bounds are biochemically informed (0.01x to 50x of default typically)
# ============================================================================

PHASE1_PARAMS = {
    # Core glycolysis & transport — controls GLC, LAC, ATP, B23PG, EGLC, ELAC
    'vmax_VHK':     (0.267472, 0.2,   5.0),    # Floor raised: HK must keep up with glucose import to prevent GLC accumulation
    'vmax_VPFK':    (0.391893, 0.8,   5.0),    # Floor raised: F6P accumulating nRMSE 60.6, PFK must keep up with HK+PGI
    'vmax_VFDPA':   (1.156751, 0.5,  10.0),   # Aldolase: F16BP → GA3P+DHCP (R6 fix: was uncalibrated at 1.16 while VPFK=3.42 → F16BP nRMSE 25.7)
    'vmax_VPK':     (0.936322, 0.1,  50.0),   # widened — PEP accumulation fix
    'vmax_VPGK':    (4.690379, 0.5,  50.0),   # ATP producer (B13PG + ADP -> P3G + ATP)
    'vmax_VLDH':    (0.284952, 0.5,  10.0),    # Floor raised: PYR accumulating nRMSE 3.62, LDH was 0.24 (very high activity enzyme)
    'vmax_VEGLC':   (1.077000, 0.5,   3.5),    # Tightened: was 3.33 causing GLC accumulation (import >> consumption)
    'vmax_VELAC':   (0.580000, 0.05, 10.0),
    'vmax_VENOPGM': (5.515612, 2.0,  50.0),   # Enolase — floor raised: optimizer was killing it (0.21) causing P2G accumulation
    'vmax_VDPGM':   (2.5,      0.1,   5.0),    # Capped: was 19.0 causing B23PG accumulation (108x vs V23DPGP)
    'vmax_V23DPGP': (3.0,      0.5,  30.0),    # Floor raised: B23PG phosphatase was 0.18, B23PG accumulating 40x
    # F16BP allosteric activation of PK (feedforward regulation)
    'ka_F16BP_PK':     (0.005,  0.0005, 0.1),  # Half-max activation [mM]
    'alpha_F16BP_PK':  (10.0,   1.0,   100.0), # Max fold-activation above basal
    # PEP phosphatase (ADP-independent PEP sink — bypasses VPK bottleneck when ADP depleted)
    'vmax_VPEP_PASE':  (0.1,    0.01,  10.0),  # PEP => PYR [non-specific phosphatase]
    # Km calibration — glycolysis (controls ATP production rate)
    'km_GLC_HK':    (0.05,    0.005, 5.0),    # HK Km(glucose) — lit: 0.04-0.1 mM (split from transport km_GLC=49.86)
    'km_B13PG':     (1.013,   0.001, 5.0),    # PGK Km(1,3-BPG) — lit: 0.002 mM (current 1.013 is 500x too high!)
    'km_ADP_ATP':   (1.0,     0.05, 10.0),    # ADP/ATP ratio Km for PGK & PK — controls ATP production sensitivity
    'km_PYR':       (0.697,   0.01, 5.0),     # LDH Km(pyruvate) — lit: 0.07-0.15 mM (current 5-10x too high)
    'km_ATP_HK':    (0.5,     0.05, 2.0),     # HK-specific ATP Km — lit: 0.5-1.0 mM (decoupled from shared km_ATP=4.24 throttle)
    'km_ATP_PFK':   (0.1,     0.01, 1.0),     # PFK-specific ATP substrate Km — lit: 0.05-0.2 mM (very high affinity)
}

PHASE2_PARAMS = {
    # Nucleotide metabolism — controls IMP, HYPX, GMP, ADE, INO, GTP
    'vmax_VAMPD1':   (0.538065, 0.001, 0.1),  # AMPD1 has very low activity in stored RBCs; was 1.62 draining adenylate pool
    'vmax_VADSS':    (0.3,      0.01, 5.0),   # IMP + ASP + GTP -> ADESUC + GDP (controls GTP sink and AMP regeneration branch)
    'vmax_VIMPH':    (0.2,      0.01, 5.0),   # IMP + NAD -> XMP + NADH (controls IMP partitioning toward GMP branch)
    'vmax_VRKa':     (0.4,      0.01, 3.0),   # Ribokinase a
    'vmax_VPRPPASe': (0.5,      0.05, 3.0),    # Phosphoribosyl pyrophosphate synthetase
    'vmax_VAK':      (0.8,      0.05, 8.0),
    'vmax_VAK2':     (0.5,      0.01, 5.0),
    'vmax_VHGPRT1':  (0.645581, 0.01, 6.0),
    'vmax_VHGPRT2':  (0.25,     0.001, 1.0),  # GUA + PRPP => GMP (no longer consumes AMP)
    'vmax_Vnucleo2': (0.15,     0.005, 2.0),
    'vmax_VGMPS':    (0.379205, 0.01, 4.0),
    'vmax_VPNPase1': (0.25,     0.1,  1.0),   # INO → HYPX + R1P (capped: was 1.55, HYPX accumulating nRMSE 8.1)
    'vmax_VXAO':     (0.2,      0.1,  1.0),   # HYPX → XAN (R6 fix: capped 2.0→1.0, was 0.66 causing XAN 2263x. Must be ≤ VXAO2+VEXAN)
    'vmax_VXAO2':    (0.15,     0.05, 3.0),   # XAN → URT (R6 fix: ceiling 0.5→3.0, floor 0.01→0.05. Was 0.046 vs VXAO=0.66 → XAN 16:1 imbalance)
    'vmax_VEXAN':    (0.15,     0.001, 0.5),   # XAN → EXAN (R6 fix: ceiling 0.01→0.5. XAN export is real pathway, was near-zero causing XAN 2263x)
    'vmax_VEURT':    (0.15,     0.01, 1.0),  # URT → EURT efflux (widened: was capped 0.05 but VXAO2=0.30 >> VEURT=0.01 → URT 592x. Must match VXAO2)
    'vmax_VEINO':    (0.0001,   0.0001, 0.003), # INO → EINO efflux (recapped: was 0.005, EINO sim=0.009 vs exp=0.003 nRMSE 4.17)
    'vmax_VADA':     (0.3,      0.01, 1.0),   # ADO → INO + NH4 (capped: was 4.59 → INO accumulation nRMSE 186)
    'vmax_VGMPK':    (0.15,     0.01, 5.0),   # GMP + ATP → GDP + ADP (GMP kinase — GMP had NO consumer)
    'vmax_VAPRT':    (1.088,    0.1, 10.0),   # ADE + PRPP → AMP salvage (EADE 94x over: ADE has NO producer, VAPRT consumes ADE before it leaks to EADE)
    'vmax_VNDPK':    (1.0,      0.01, 10.0),  # GDP + ATP → GTP + ADP (nucleoside diphosphate kinase — GTP had NO producer)
    'vmax_VNDPK_rev': (1.0,     0.01, 10.0),  # GTP + ADP → GDP + ATP (NDPK reverse — prevents GTP over-accumulation, recycles ATP)
    'vmax_VAK_rev':  (0.5,      0.01, 5.0),   # AMP + ATP → 2 ADP (adenylate kinase reverse — prevents AMP dead-end accumulation)
    'vmax_Vnucleo_GMP': (0.15,  0.01, 0.5),   # GMP → GUA + R1P (capped: was 2.90, GMP depleted to 0.0003 vs exp 0.009)
    'vmax_VGDA':     (0.15,     0.01, 0.5),   # GUA → XAN + NH4 (capped: was 1.18 → XAN accumulation nRMSE 315)
    # Km calibration — nucleotide metabolism (controls ATP drain rate)
    'km_ATP':       (0.569,   0.05, 5.0),     # Shared Km(ATP) for all ATP-consuming reactions
    'km_AMP':       (0.283,   0.05, 3.0),     # AMPD1 Km(AMP) — lit: 0.5-2.0 mM (current is low → AMPD1 too aggressive)
}

PHASE3_PARAMS = {
    # Amino acids, redox, one-carbon & remaining transport
    'vmax_VGDH':    (0.5,   0.01, 2.0),     # Capped: was 3.24, main GLU producer driving GLU accumulation nRMSE 6.9
    'vmax_VGDH_rev': (0.1,  0.01, 5.0),   # Reverse GDH: GLU + NADP → AKG + NADPH + NH4 (oxidative deamination — GLU had NO recycling path)
    'vmax_VALATA':  (0.35,  0.01, 2.0),     # Ceiling raised: forward must balance reverse to prevent ALA over-accumulation
    'vmax_VASPTA':  (0.4,   0.01, 4.0),
    'vmax_VGLNS':   (0.4,   0.01, 4.0),
    'vmax_VEGLN':   (0.001, 0.01, 2.0),    # R6 fix: ceiling 0.1→2.0, floor→0.01. GLN export is major RBC pathway. Was 0.004 vs VGLNS=1.39 → GLN 25x
    'vmax_VEGLU':   (0.001, 0.0001, 2.0),   # Widened: GLU accumulates 24x exp after VACO added (storage lesion efflux)
    'vmax_VGSR':    (1.0,   0.05, 10.0),
    'vmax_VGPX':    (1.079815, 0.05, 10.0),
    'vmax_VME':     (0.3,   0.01, 3.0),
    'vmax_VFUM':    (0.5,   0.01, 5.0),
    'vmax_VMLD':    (0.4,   0.01, 4.0),
    'vmax_VECIT':   (0.25,  0.005, 2.5),
    'vmax_VASPTA_rev': (0.2, 0.01, 5.0),  # OAA + GLU → ASP + AKG (reverse transaminase — ASP had NO producer, kills IMP salvage)
    'vmax_VALATA_rev': (0.15, 0.05, 0.5), # PYR + GLU → ALA + AKG (capped: was 1.18 → ALA 8.23 vs exp 0.61, nRMSE 9.7)
    'vmax_VSHMT':   (0.1,  0.01, 1.0),    # SER + THF → GLY + METTHF (ceiling raised: SER's main consumer, must match VPHGDH)
    'vmax_VPHGDH':  (0.1,  0.05, 0.5),    # P3G + NAD + GLU → SER + AKG + NADH (capped: was 0.91, overproducing SER 30x nRMSE 99.7)
    'vmax_VOPLAH':  (0.15, 0.01, 5.0),    # OXOP + ATP → GLU + ADP (5-oxoprolinase — OXOP had NO consumer, closes gamma-glutamyl cycle)
    # Km calibration — redox & amino acid
    'km_GSSG':      (1.0,   0.01, 5.0),     # GR Km(GSSG) — lit: 0.05-0.1 mM (current 10-20x too high, limits GSH recycling)
    'km_GLU':       (0.289, 0.01, 3.0),     # Shared Km(glutamate) — used by transaminases, GDH, GLNS, glutathione
    # Extracellular transport — previously uncalibrated
    'vmax_VEADE':   (0.01,  0.0001, 0.001),  # ADE → EADE (EADE 100x over: sim=0.47, exp=0.005 — cap export)
    'vmax_VEHYPX':  (0.002, 0.01, 3.0),   # HYPX → EHYPX (floor lowered: was 0.1 → overshot sim=1.25 vs exp=0.38. Let optimizer find balance)
    'vmax_VEFUM':   (0.2,   0.001, 5.0),   # FUM ↔ EFUM (EFUM near zero: sim≈0, exp=0.02)
    'vmax_VEMAL':   (0.001, 0.0001, 1.0),  # MAL → EMAL (EMAL 5x under: sim=0.04, exp=0.18)
}

PHASE_MAP = {1: PHASE1_PARAMS, 2: PHASE2_PARAMS, 3: PHASE3_PARAMS}
PHASE_NAMES = {
    1: "Core Glycolysis & Transport",
    2: "Nucleotide Metabolism",
    3: "Amino Acids, Redox & Transport",
}

# Restrict optimization to extracellular transport/export Vmax values only.
# This excludes internal catalytic steps (e.g., VENOPGM) even if names start with "VE".
TRANSPORT_ONLY_PARAM_NAMES = {
    'vmax_VEGLC',
    'vmax_VELAC',
    'vmax_VEXAN',
    'vmax_VEURT',
    'vmax_VEINO',
    'vmax_VEADE',
    'vmax_VEHYPX',
    'vmax_VEMAL',
    'vmax_VEFUM',
    'vmax_VECIT',
    'vmax_VEGLN',
    'vmax_VEGLU',
}


# ============================================================================
# DATA LOADING
# ============================================================================

def load_experimental_data():
    """Load Bordbar et al. experimental data."""
    df = pd.read_excel(DATA_DIR / 'Data_Bordbar_et_al_exp.xlsx')
    exp_names = [str(n).strip().upper() for n in df.iloc[:, 0].tolist()]
    exp_values = df.iloc[:, 1:].values.astype(float)
    time_exp = np.array([float(c) for c in df.columns[1:]])
    name_to_row = {n: i for i, n in enumerate(exp_names)}
    return time_exp, exp_values, name_to_row


def load_initial_conditions():
    """Load initial conditions using the model metabolite map."""
    metabolite_list = [''] * 107
    for name, idx in BRODBAR_METABOLITE_MAP.items():
        if idx < 107:
            metabolite_list[idx] = name
    model = {'metab': metabolite_list}
    x0, _ = parse_initial_conditions(model, str(DATA_DIR / 'Initial_conditions_JA_Final.xls'))
    return x0


def get_phase_params(phase_num, param_scope='all'):
    """Return parameter bounds for one phase with optional scope filtering."""
    phase_params = PHASE_MAP[phase_num]
    if param_scope == 'all':
        return phase_params
    if param_scope == 'transport_only':
        return {
            name: bounds
            for name, bounds in phase_params.items()
            if name in TRANSPORT_ONLY_PARAM_NAMES
        }
    raise ValueError(f"Unsupported param_scope: {param_scope}")


# ============================================================================
# OBJECTIVE FUNCTION
# ============================================================================

class ObjectiveFunction:
    """
    Normalized RMSE objective for Vmax calibration.
    
    Loss = weighted mean of per-metabolite nRMSE values.
    nRMSE_i = RMSE_i / max(mean(|exp_i|), epsilon)
    
    This ensures each metabolite contributes equally regardless of concentration scale.
    """
    
    def __init__(
        self,
        x0,
        time_exp,
        exp_values,
        name_to_row,
        t_max=46,
        target_scope='all',
        atp_focus=False,
        atp_floor=0.15,
        adp_floor=0.05,
        adenylate_target=0.65,
        atp_penalty_weight=8.0,
        pool_penalty_weight=10.0,
    ):
        self.x0 = x0
        self.time_exp = time_exp
        self.exp_values = exp_values
        self.name_to_row = name_to_row
        self.t_max = t_max
        if target_scope not in {'all', 'extracellular'}:
            raise ValueError(f"Unsupported target_scope: {target_scope}")
        self.target_scope = target_scope
        self.atp_focus = atp_focus
        self.atp_floor = atp_floor
        self.adp_floor = adp_floor
        self.adenylate_target = adenylate_target
        self.atp_penalty_weight = atp_penalty_weight
        self.pool_penalty_weight = pool_penalty_weight
        self.t_eval_dense = np.linspace(1, t_max, 200)
        # For optimization speed: only solve at experimental timepoints
        # Start at t=1 to match production code (main.py, simulation_engine.py)
        self.t_eval_fast = np.sort(np.unique(np.concatenate(([1], time_exp))))
        
        # Pre-compute experimental targets and weights
        self.target_names = []
        self.target_indices = []
        self.target_exp = []
        self.target_weights = []
        
        for ename, midx in EXP_TO_MODEL.items():
            if self.target_scope == 'extracellular' and ename not in EXTRACELLULAR_TARGET_METABOLITES:
                continue
            if ename in name_to_row:
                row = name_to_row[ename]
                self.target_names.append(ename)
                self.target_indices.append(midx)
                self.target_exp.append(exp_values[row, :])
                if ename in CRITICAL_WEIGHT_METABOLITES:
                    w = CRITICAL_WEIGHT_METABOLITES[ename]
                elif ename in HIGH_WEIGHT_METABOLITES:
                    w = 2.0
                else:
                    w = 1.0
                self.target_weights.append(w)

        if not self.target_names:
            raise ValueError(f"No experimental targets found for target_scope='{self.target_scope}'")
        
        self.target_exp = np.array(self.target_exp)  # (n_targets, n_timepoints)
        self.target_weights = np.array(self.target_weights)
        self.n_targets = len(self.target_names)
        
        # Pre-compute normalization factors (mean of absolute experimental values)
        self.norm_factors = np.maximum(np.mean(np.abs(self.target_exp), axis=1), 1e-4)

        # Energy pools for ATP-focused penalties
        self.atp_idx = 35
        self.adp_idx = 36
        self.amp_idx = 37
        self.init_adenylate_pool = float(
            max(x0[self.atp_idx] + x0[self.adp_idx] + x0[self.amp_idx], 1e-8)
        )
        
        # Call counter
        self.n_calls = 0
        self.best_loss = float('inf')
        self.best_params = None
    
    def __call__(self, custom_params):
        """Evaluate the objective function."""
        self.n_calls += 1
        
        try:
            sol = solve_ivp(
                lambda t, y: equadiff_brodbar(t, y, custom_params=custom_params, curve_fit_strength=0.0),
                (1, self.t_max), self.x0,
                method='LSODA',
                t_eval=self.t_eval_fast,
                rtol=1e-4, atol=1e-6,
            )
            
            if not sol.success:
                return 100.0  # Penalty for failed integration
            
            # Clamp to non-negative
            y = np.maximum(sol.y, 0.0)
            
            # Interpolate simulation at experimental time points
            nrmses = np.zeros(self.n_targets)
            for i, midx in enumerate(self.target_indices):
                sim_at_exp = np.interp(self.time_exp, sol.t, y[midx])
                rmse = np.sqrt(np.mean((sim_at_exp - self.target_exp[i]) ** 2))
                cap = 50.0 if (self.atp_focus and self.target_names[i] in {'ATP', 'ADP', 'AMP'}) else NRMSE_CAP
                nrmses[i] = min(rmse / self.norm_factors[i], cap)
            
            # Weighted mean nRMSE (capped per metabolite)
            loss = np.average(nrmses, weights=self.target_weights)
            
            # Add mild L2 regularization to prevent extreme parameter values
            # (penalize deviations from defaults)
            reg = 0.0
            for pname, pval in custom_params.items():
                for phase_params in PHASE_MAP.values():
                    if pname in phase_params:
                        default = phase_params[pname][0]
                        # Log-space deviation penalty
                        if pval > 0 and default > 0:
                            log_ratio = np.log10(pval / default)
                            reg += 0.005 * log_ratio ** 2
            
            total_loss = loss + reg

            if self.atp_focus:
                atp = y[self.atp_idx]
                adp = y[self.adp_idx]
                amp = y[self.amp_idx]

                min_atp = float(np.min(atp))
                min_adp = float(np.min(adp))
                final_pool_ratio = float((atp[-1] + adp[-1] + amp[-1]) / self.init_adenylate_pool)

                atp_floor_pen = max(0.0, (self.atp_floor - min_atp) / max(self.atp_floor, 1e-8))
                adp_floor_pen = max(0.0, (self.adp_floor - min_adp) / max(self.adp_floor, 1e-8))
                pool_pen = max(0.0, (self.adenylate_target - final_pool_ratio) / max(self.adenylate_target, 1e-8))

                total_loss += self.atp_penalty_weight * (atp_floor_pen + 0.5 * adp_floor_pen)
                total_loss += self.pool_penalty_weight * pool_pen
            
            if total_loss < self.best_loss:
                self.best_loss = total_loss
                self.best_params = custom_params.copy()
            
            return total_loss
            
        except Exception as e:
            return 100.0  # Penalty
    
    def detailed_report(self, custom_params):
        """Generate detailed per-metabolite RMSE report."""
        sol = solve_ivp(
            lambda t, y: equadiff_brodbar(t, y, custom_params=custom_params, curve_fit_strength=0.0),
            (1, self.t_max), self.x0,
            method='LSODA', t_eval=self.t_eval_dense,
            rtol=1e-5, atol=1e-7,
        )
        y = np.maximum(sol.y, 0.0)
        
        report = []
        for i, (ename, midx) in enumerate(zip(self.target_names, self.target_indices)):
            sim_at_exp = np.interp(self.time_exp, sol.t, y[midx])
            rmse = np.sqrt(np.mean((sim_at_exp - self.target_exp[i]) ** 2))
            nrmse = rmse / self.norm_factors[i]
            report.append({
                'name': ename, 'idx': midx,
                'rmse': rmse, 'nrmse': nrmse,
                'sim_final': y[midx, -1],
                'exp_final': self.target_exp[i, -1],
            })
        return sorted(report, key=lambda r: r['nrmse'], reverse=True)


# ============================================================================
# OPTIMIZATION ENGINES
# ============================================================================

def optimize_optuna(objective, phase_params, fixed_params, n_trials=200, study_name=None):
    """Bayesian Optimization using optuna TPE sampler."""
    
    param_names = list(phase_params.keys())
    
    def optuna_objective(trial):
        custom_params = fixed_params.copy()
        for pname, (default, lo, hi) in phase_params.items():
            # Sample in log-space for better exploration
            val = trial.suggest_float(pname, lo, hi, log=True)
            custom_params[pname] = val
        return objective(custom_params)
    
    sampler = optuna.samplers.TPESampler(
        seed=42,
        n_startup_trials=min(30, n_trials // 4),
        multivariate=True,
    )
    
    study = optuna.create_study(
        direction='minimize',
        sampler=sampler,
        study_name=study_name or 'vmax_calibration',
    )
    
    # Enqueue loaded calibrated values (clipped to bounds) as first trial,
    # falling back to hardcoded defaults if no loaded value exists.
    # This seeds the optimizer near the best known solution.
    seed_trial = {}
    for pname, (default, lo, hi) in phase_params.items():
        loaded_val = fixed_params.get(pname, default)
        seed_trial[pname] = float(np.clip(loaded_val, lo, hi))
    study.enqueue_trial(seed_trial)
    
    study.optimize(optuna_objective, n_trials=n_trials, show_progress_bar=True)
    
    best = study.best_params
    best_val = study.best_value
    
    return best, best_val, study


def optimize_de(objective, phase_params, fixed_params, max_iter=150):
    """Differential Evolution fallback when optuna is not available."""
    
    param_names = list(phase_params.keys())
    bounds = [(lo, hi) for _, (_, lo, hi) in phase_params.items()]
    
    def de_objective(x):
        custom_params = fixed_params.copy()
        for i, pname in enumerate(param_names):
            custom_params[pname] = x[i]
        return objective(custom_params)
    
    result = differential_evolution(
        de_objective, bounds,
        maxiter=max_iter,
        popsize=20,
        strategy='best1bin',
        mutation=(0.5, 1.5),
        recombination=0.8,
        seed=42,
        tol=1e-6,
        polish=True,
        workers=1,
    )
    
    best = {pname: result.x[i] for i, pname in enumerate(param_names)}
    return best, result.fun, result


# ============================================================================
# VISUALIZATION
# ============================================================================

def plot_comparison(objective, params, title_suffix="", save_path=None):
    """Plot simulation vs experimental for key metabolites."""
    
    t_dense = np.linspace(1, objective.t_max, 200)
    sol = solve_ivp(
        lambda t, y: equadiff_brodbar(t, y, custom_params=params, curve_fit_strength=0.0),
        (1, objective.t_max), objective.x0,
        method='LSODA', t_eval=t_dense, rtol=1e-5, atol=1e-7,
    )
    y = np.maximum(sol.y, 0.0)
    
    # Also run with defaults for comparison
    sol_def = solve_ivp(
        lambda t, y: equadiff_brodbar(t, y, custom_params=None, curve_fit_strength=0.0),
        (1, objective.t_max), objective.x0,
        method='LSODA', t_eval=t_dense, rtol=1e-5, atol=1e-7,
    )
    y_def = np.maximum(sol_def.y, 0.0)
    
    # Select key metabolites for plotting
    plot_mets = [
        ('GLC', 0), ('LAC', 19), ('ATP', 35), ('ADP', 36),
        ('B23PG', 15), ('EGLC', 85), ('ELAC', 87), ('GSH', 70),
        ('GSSG', 71), ('GLU', 60), ('HYPX', 28), ('IMP', 42),
        ('MAL', 20), ('ADE', 25), ('PYR', 18), ('ALA', 58),
    ]
    
    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    fig.suptitle(f'Vmax Calibration Results {title_suffix}', fontsize=14, fontweight='bold')
    axes = axes.flatten()
    
    for i, (mname, midx) in enumerate(plot_mets):
        ax = axes[i]
        
        # Experimental data
        exp_key = mname.upper()
        if exp_key in objective.name_to_row:
            row = objective.name_to_row[exp_key]
            ax.scatter(objective.time_exp, objective.exp_values[row, :],
                      color='black', s=40, zorder=5, label='Experimental', marker='o')
        
        # Default (uncalibrated)
        ax.plot(sol_def.t, y_def[midx], color='red', linewidth=1, alpha=0.5,
                linestyle='--', label='Default Vmax')
        
        # Calibrated
        ax.plot(sol.t, y[midx], color='blue', linewidth=2, label='Calibrated')
        
        ax.set_title(f'{mname} (idx {midx})', fontsize=10)
        ax.set_xlabel('Time (days)', fontsize=8)
        ax.set_ylabel('mM', fontsize=8)
        ax.legend(fontsize=6, loc='best')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  Plot saved: {save_path}")
    plt.close(fig)


# ============================================================================
# MAIN CALIBRATION PIPELINE
# ============================================================================

def run_calibration(
    phases=None,
    n_trials=200,
    load_params=None,
    target_scope='all',
    param_scope='all',
    atp_focus=False,
    atp_floor=0.15,
    adp_floor=0.05,
    adenylate_target=0.65,
    atp_penalty_weight=8.0,
    pool_penalty_weight=10.0,
):
    """Run multi-phase Vmax calibration."""
    
    if phases is None:
        phases = [1, 2, 3]
    
    print("=" * 70)
    print("RBC Metabolic Model — ML-based Vmax Recalibration")
    print(f"Optimizer: {'optuna TPE (Bayesian)' if HAS_OPTUNA else 'scipy DE (fallback)'}")
    print(f"Phases: {phases}")
    print(f"Trials per phase: {n_trials}")
    print(f"Target scope: {target_scope}")
    print(f"Parameter scope: {param_scope}")
    if atp_focus:
        print(
            "ATP focus: ON "
            f"(ATP floor={atp_floor}, ADP floor={adp_floor}, "
            f"adenylate target={adenylate_target})"
        )
    print("=" * 70)
    
    # Load data
    print("\n[1/4] Loading data...")
    time_exp, exp_values, name_to_row = load_experimental_data()
    x0 = load_initial_conditions()
    print(f"  Experimental: {len(name_to_row)} metabolites, {len(time_exp)} timepoints")
    print(f"  Time range: {time_exp[0]}-{time_exp[-1]} days")
    
    # Create objective function
    objective = ObjectiveFunction(
        x0,
        time_exp,
        exp_values,
        name_to_row,
        target_scope=target_scope,
        atp_focus=atp_focus,
        atp_floor=atp_floor,
        adp_floor=adp_floor,
        adenylate_target=adenylate_target,
        atp_penalty_weight=atp_penalty_weight,
        pool_penalty_weight=pool_penalty_weight,
    )
    print(f"  Target metabolites for loss: {objective.n_targets}")
    
    # Load previous parameters if resuming
    current_params = {}
    if load_params:
        with open(load_params, 'r') as f:
            current_params = json.load(f)
        print(f"  Loaded {len(current_params)} params from {load_params}")
        
        # Clip loaded params to current bounds (bounds may have changed between rounds)
        all_bounds = {}
        for phase_params in PHASE_MAP.values():
            all_bounds.update(phase_params)
        clipped_count = 0
        for pname in list(current_params.keys()):
            if pname in all_bounds:
                _, lo, hi = all_bounds[pname]
                old_val = current_params[pname]
                current_params[pname] = float(np.clip(old_val, lo, hi))
                if current_params[pname] != old_val:
                    clipped_count += 1
        if clipped_count > 0:
            print(f"  Clipped {clipped_count} params to updated bounds")
    
    # Evaluate baseline
    baseline_loss = objective(current_params if current_params else {})
    print(f"\n  Baseline loss (nRMSE): {baseline_loss:.4f}")
    
    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Plot baseline
    plot_comparison(objective, current_params, "(Baseline)",
                   save_path=str(OUT_DIR / 'baseline.png'))
    
    # Run phases
    print(f"\n[2/4] Running optimization phases...")
    all_results = {}
    optimized_phase_count = 0
    
    for phase_num in phases:
        phase_params = get_phase_params(phase_num, param_scope=param_scope)
        phase_name = PHASE_NAMES[phase_num]
        if not phase_params:
            print(f"\n{'='*60}")
            print(f"  Phase {phase_num}: {phase_name}")
            print(f"  Skipping (no parameters in scope '{param_scope}')")
            continue
        
        print(f"\n{'='*60}")
        print(f"  Phase {phase_num}: {phase_name}")
        print(f"  Parameters: {list(phase_params.keys())}")
        print(f"  Optimizing {len(phase_params)} parameters...")
        optimized_phase_count += 1
        
        t_start = time.time()
        
        if HAS_OPTUNA:
            best, best_val, study = optimize_optuna(
                objective, phase_params, current_params,
                n_trials=n_trials,
                study_name=f'phase{phase_num}_{phase_name.replace(" ", "_")}',
            )
        else:
            best, best_val, _ = optimize_de(
                objective, phase_params, current_params,
                max_iter=max(100, n_trials // 3),
            )
        
        elapsed = time.time() - t_start
        
        # Update current params with optimized values
        current_params.update(best)
        
        # Evaluate with all accumulated params
        new_loss = objective(current_params)
        
        print(f"\n  Phase {phase_num} Results:")
        print(f"    Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
        print(f"    Best trial loss: {best_val:.4f}")
        print(f"    Cumulative loss: {new_loss:.4f}")
        print(f"    Improvement: {baseline_loss:.4f} -> {new_loss:.4f} ({(1-new_loss/baseline_loss)*100:.1f}%)")
        
        # Print optimized values
        print(f"\n    Optimized parameters:")
        for pname, pval in sorted(best.items()):
            default = phase_params[pname][0]
            ratio = pval / default
            print(f"      {pname:25s}: {default:.6f} -> {pval:.6f} ({ratio:.2f}x)")
        
        # Plot after this phase
        plot_comparison(objective, current_params, f"(After Phase {phase_num})",
                       save_path=str(OUT_DIR / f'phase{phase_num}.png'))
        
        all_results[f'phase{phase_num}'] = {
            'params': best,
            'loss': best_val,
            'cumulative_loss': new_loss,
            'elapsed_s': elapsed,
        }
    
    if optimized_phase_count == 0:
        raise ValueError(f"No parameters selected for phases={phases} and param_scope='{param_scope}'")
    
    # Global refinement: joint optimization of ALL phase params together
    # This fixes the root cause of phase interference — each phase can now
    # see and compensate for other phases' effects.
    if len(phases) > 1:
        all_phase_params = {}
        for phase_num in phases:
            all_phase_params.update(get_phase_params(phase_num, param_scope=param_scope))
        
        n_global = len(all_phase_params)
        global_trials = max(n_trials // 2, 50)  # Half the per-phase trials
        
        print(f"\n{'='*60}")
        print(f"  Global Refinement Phase")
        print(f"  Joint optimization of {n_global} parameters ({global_trials} trials)...")
        
        t_start = time.time()
        
        if HAS_OPTUNA:
            best, best_val, study = optimize_optuna(
                objective, all_phase_params, current_params,
                n_trials=global_trials,
                study_name='global_refinement',
            )
        else:
            best, best_val, _ = optimize_de(
                objective, all_phase_params, current_params,
                max_iter=max(50, global_trials // 3),
            )
        
        elapsed = time.time() - t_start
        
        # Only update if global refinement improved
        candidate_params = current_params.copy()
        candidate_params.update(best)
        candidate_loss = objective(candidate_params)
        
        pre_global_loss = objective(current_params)
        if candidate_loss <= pre_global_loss:
            current_params.update(best)
            print(f"\n  Global Refinement Results:")
            print(f"    Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
            print(f"    Loss: {pre_global_loss:.4f} -> {candidate_loss:.4f} "
                  f"({(1-candidate_loss/pre_global_loss)*100:+.1f}%)")
        else:
            print(f"\n  Global refinement did not improve ({pre_global_loss:.4f} -> {candidate_loss:.4f})")
            print(f"    Keeping pre-refinement parameters.")
        
        plot_comparison(objective, current_params, "(After Global Refinement)",
                       save_path=str(OUT_DIR / 'global_refinement.png'))
    
    # Final evaluation
    print(f"\n[3/4] Final evaluation...")
    final_loss = objective(current_params)
    print(f"  Final loss (nRMSE): {final_loss:.4f}")
    print(f"  Improvement: {baseline_loss:.4f} -> {final_loss:.4f} ({(1-final_loss/baseline_loss)*100:.1f}%)")
    
    # Detailed per-metabolite report
    report = objective.detailed_report(current_params)
    print(f"\n  Per-metabolite nRMSE (top 15 worst):")
    for r in report[:15]:
        flag = " ***" if r['nrmse'] > 1.0 else ""
        print(f"    {r['name']:8s}: nRMSE={r['nrmse']:.3f}  RMSE={r['rmse']:.4f}  "
              f"sim={r['sim_final']:.4f}  exp={r['exp_final']:.4f}{flag}")
    
    # Final comparison plot
    plot_comparison(objective, current_params, "(Final Calibrated)",
                   save_path=str(OUT_DIR / 'final_calibrated.png'))
    
    # Save results (only if improved)
    print(f"\n[4/4] Saving results...")
    
    params_file = OUT_DIR / 'best_params.json'
    if final_loss <= baseline_loss:
        # Improved or equal — save new params
        with open(params_file, 'w') as f:
            json.dump(current_params, f, indent=2)
        print(f"  Parameters: {params_file}")
    else:
        # Regressed — save to a separate file, do NOT overwrite best
        regressed_file = OUT_DIR / 'last_run_params.json'
        with open(regressed_file, 'w') as f:
            json.dump(current_params, f, indent=2)
        print(f"  WARNING: Loss regressed ({baseline_loss:.4f} -> {final_loss:.4f})")
        print(f"  NOT overwriting {params_file}")
        print(f"  Regressed params saved to: {regressed_file}")
    
    # Save full report
    report_file = OUT_DIR / 'calibration_report.json'
    with open(report_file, 'w') as f:
        json.dump({
            'baseline_loss': baseline_loss,
            'final_loss': final_loss,
            'improvement_pct': (1 - final_loss / baseline_loss) * 100,
            'n_trials_per_phase': n_trials,
            'optimizer': 'optuna_TPE' if HAS_OPTUNA else 'scipy_DE',
            'target_scope': target_scope,
            'param_scope': param_scope,
            'target_metabolites': objective.target_names,
            'phases': all_results,
            'optimized_params': current_params,
            'per_metabolite': [r for r in report],
        }, f, indent=2, default=str)
    print(f"  Report: {report_file}")
    
    # Save as Python dict for easy copy-paste into equadiff_brodbar.py
    py_file = OUT_DIR / 'best_params.py'
    with open(py_file, 'w') as f:
        f.write("# Optimized Vmax parameters from ML calibration\n")
        f.write(f"# Baseline nRMSE: {baseline_loss:.4f}\n")
        f.write(f"# Final nRMSE:    {final_loss:.4f}\n")
        f.write(f"# Improvement:    {(1-final_loss/baseline_loss)*100:.1f}%\n\n")
        f.write("CALIBRATED_PARAMS = {\n")
        for pname, pval in sorted(current_params.items()):
            f.write(f"    '{pname}': {pval:.8f},\n")
        f.write("}\n")
    print(f"  Python dict: {py_file}")
    
    print(f"\n{'='*70}")
    print(f"Calibration complete!")
    print(f"Total objective evaluations: {objective.n_calls}")
    print(f"Final nRMSE: {final_loss:.4f}")
    print(f"{'='*70}")
    
    return current_params, final_loss


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ML-based Vmax recalibration')
    parser.add_argument('--phases', type=str, default='1,2,3',
                       help='Comma-separated phase numbers (default: 1,2,3)')
    parser.add_argument('--n-trials', type=int, default=150,
                       help='Number of optimization trials per phase (default: 150)')
    parser.add_argument('--load-params', type=str, default=None,
                       help='Path to JSON file with initial parameters to resume from')
    parser.add_argument('--target-scope', type=str, default='all', choices=['all', 'extracellular'],
                       help='Calibration target scope: all measured metabolites or only extracellular measured metabolites')
    parser.add_argument('--param-scope', type=str, default='all', choices=['all', 'transport_only'],
                       help='Parameter scope: all phase parameters or only extracellular transport/export Vmax parameters')
    parser.add_argument('--atp-focus', action='store_true',
                       help='Enable ATP-focused penalties (prevents ATP/ADP crash and adenylate pool collapse)')
    parser.add_argument('--atp-floor', type=float, default=0.15,
                       help='Minimum ATP floor target (mM) when --atp-focus is enabled')
    parser.add_argument('--adp-floor', type=float, default=0.05,
                       help='Minimum ADP floor target (mM) when --atp-focus is enabled')
    parser.add_argument('--adenylate-target', type=float, default=0.65,
                       help='Target final adenylate pool retention ratio when --atp-focus is enabled')
    parser.add_argument('--atp-penalty-weight', type=float, default=8.0,
                       help='Penalty weight for ATP/ADP floor violations')
    parser.add_argument('--pool-penalty-weight', type=float, default=10.0,
                       help='Penalty weight for adenylate pool retention violation')
    
    args = parser.parse_args()
    phases = [int(p) for p in args.phases.split(',')]
    
    run_calibration(
        phases=phases,
        n_trials=args.n_trials,
        load_params=args.load_params,
        target_scope=args.target_scope,
        param_scope=args.param_scope,
        atp_focus=args.atp_focus,
        atp_floor=args.atp_floor,
        adp_floor=args.adp_floor,
        adenylate_target=args.adenylate_target,
        atp_penalty_weight=args.atp_penalty_weight,
        pool_penalty_weight=args.pool_penalty_weight,
    )
