"""
ML-based MM recalibration for the RBC metabolic model.

Supports:
- legacy calibration
- vmax_only
- km_only
- vmax_then_km
- km_then_vmax
- joint_vmax_km
- staged_full
- explicit stage_plan execution
"""

import sys
import os
import json
import time
import argparse
import csv
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from equadiff_brodbar import equadiff_brodbar, BRODBAR_METABOLITE_MAP, NUM_BASE_METABOLITES
from parse_initial_conditions import parse_initial_conditions

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False
    from scipy.optimize import differential_evolution

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# =============================================================================
# CONFIG
# =============================================================================

DATA_DIR = Path(__file__).parent
OUT_DIR = Path(__file__).parent.parent / "Simulations" / "brodbar" / "calibration"

LEGACY_RESULTS_TSV_FIELDS = [
    "timestamp",
    "stage",
    "target_scope",
    "param_scope",
    "baseline_target_loss",
    "candidate_target_loss",
    "joint_loss",
    "extracellular_loss",
    "glycolysis_loss",
    "endpoint_nrmse",
    "status",
    "description",
]

RESULTS_TSV_FIELDS = [
    "timestamp",
    "stage",
    "target_scope",
    "param_scope",
    "baseline_target_loss",
    "candidate_target_loss",
    "joint_loss",
    "glycolysis_energy_loss",
    "nucleotide_purine_loss",
    "amino_redox_side_loss",
    "extracellular_loss",
    "glycolysis_loss",
    "endpoint_nrmse",
    "status",
    "description",
]

EXP_TO_MODEL = {
    "GLC": 0, "G6P": 1, "F6P": 2, "GO6P": 4,
    "F16BP": 11, "P3G": 14, "B23PG": 15,
    "P2G": 16, "PEP": 17, "PYR": 18, "LAC": 19, "MAL": 20,
    "CIT": 22, "ADE": 25, "INO": 27, "HYPX": 28, "XAN": 29, "URT": 30,
    "ATP": 35, "ADP": 36, "AMP": 37, "GMP": 40, "IMP": 42,
    "SAH": 51, "ARG": 53, "CITR": 55, "ASP": 56, "SER": 57,
    "ALA": 58, "GLU": 60, "GLN": 61, "OXOP": 65,
    "GSH": 70, "GSSG": 71,
    "EGLC": 85, "ELAC": 87, "EADE": 89, "EINO": 90,
    "EGLN": 91, "EGLU": 92, "ECYS": 93,
    "EURT": 97, "EXAN": 99, "EHYPX": 100, "EMAL": 101,
    "EFUM": 102, "ECIT": 103,
    "ASN": 106, "EOXOP": 107, "ESER": 108, "EARG": 109,
    "EGSSG": 110, "EGSH": 111, "EASN": 112,
}

EXTRACELLULAR_TARGET_METABOLITES = {name for name in EXP_TO_MODEL if name.startswith("E")}
ENERGETICS_TARGET_METABOLITES = {"ATP", "ADP", "AMP"}
GLYCOLYSIS_TARGET_METABOLITES = {
    "EGLC", "GLC", "G6P", "F6P", "F16BP",
    "P3G", "B23PG", "P2G", "PEP", "PYR", "LAC", "ELAC",
}
GLYCOLYSIS_TERMINAL_TARGET_METABOLITES = {"EGLC", "GLC", "P2G", "PEP", "PYR", "LAC", "ELAC"}
GLYCOLYSIS_EXTRACELLULAR_TARGET_METABOLITES = (
    GLYCOLYSIS_TARGET_METABOLITES | EXTRACELLULAR_TARGET_METABOLITES | ENERGETICS_TARGET_METABOLITES
)
CORE_GLYCOLYSIS_ENERGY_TARGET_METABOLITES = {
    "EGLC", "GLC", "G6P", "F6P", "F16BP", "P3G", "B23PG",
    "P2G", "PEP", "PYR", "LAC", "ELAC", "ATP", "ADP", "AMP",
}
NUCLEOTIDE_PURINE_TARGET_METABOLITES = {
    "ADE", "INO", "HYPX", "XAN", "URT", "GMP", "IMP",
    "EADE", "EINO", "EURT", "EXAN", "EHYPX",
}
AMINO_REDOX_SIDE_TARGET_METABOLITES = {
    "GO6P", "MAL", "CIT", "SAH", "ARG", "CITR", "ASP", "SER", "ALA", "GLU", "GLN", "OXOP",
    "GSH", "GSSG", "ASN",
    "EGLN", "EGLU", "ECYS", "EMAL", "EFUM", "ECIT", "EOXOP", "ESER", "EARG",
    "EGSSG", "EGSH", "EASN",
}
ALL_SUPPORTED_TARGET_METABOLITES = set(EXP_TO_MODEL)

PATHWAY_TARGET_GROUPS = {
    "glycolysis_energy": GLYCOLYSIS_EXTRACELLULAR_TARGET_METABOLITES,
    "core_glycolysis_energy": CORE_GLYCOLYSIS_ENERGY_TARGET_METABOLITES,
    "nucleotide_purine": NUCLEOTIDE_PURINE_TARGET_METABOLITES,
    "amino_redox_side": AMINO_REDOX_SIDE_TARGET_METABOLITES,
}
PATHWAY_PHASE_OBJECTIVE_NAMES = {
    1: "glycolysis_energy",
    2: "nucleotide_purine",
    3: "amino_redox_side",
}
PATHWAY_MONITOR_REGRESSION_LIMITS = {
    "glycolysis_energy": 0.25,
    "nucleotide_purine": 0.35,
    "amino_redox_side": 0.35,
    "extracellular": 0.25,
    "glycolysis": 0.25,
}

HIGH_WEIGHT_METABOLITES = {"GLC", "G6P", "LAC", "PYR", "EGLC", "ELAC"}

CRITICAL_WEIGHT_METABOLITES = {
    "ATP": 15.0,
    "ADP": 15.0,
    "AMP": 10.0,
    "B23PG": 8.0,
    "GSH": 5.0,
    "GSSG": 5.0,
    "PEP": 5.0,
    "GLC": 3.0,
    "LAC": 3.0,
    "P2G": 3.0,
}

TARGET_SCOPE_WEIGHT_OVERRIDES = {
    "glycolysis_terminal": {
        "EGLC": 8.0,
        "ELAC": 8.0,
        "GLC": 4.0,
        "LAC": 4.0,
        "PYR": 3.0,
        "PEP": 3.0,
        "P2G": 3.0,
    },
    "glycolysis_extracellular": {
        "EGLC": 8.0,
        "ELAC": 8.0,
        "GLC": 6.0,
        "G6P": 6.0,
        "LAC": 5.0,
        "F6P": 4.0,
        "F16BP": 4.0,
        "PYR": 4.0,
        "PEP": 3.0,
        "P2G": 3.0,
        "EURT": 4.0,
        "EFUM": 3.0,
        "EGLN": 2.5,
        "EOXOP": 2.5,
        "EADE": 2.5,
        "EARG": 2.5,
    },
    "glycolysis_energy": {
        "EGLC": 8.0,
        "ELAC": 8.0,
        "GLC": 6.0,
        "G6P": 6.0,
        "ATP": 15.0,
        "ADP": 15.0,
        "AMP": 10.0,
        "LAC": 5.0,
        "F6P": 4.0,
        "F16BP": 4.0,
        "PYR": 4.0,
        "PEP": 3.0,
        "P2G": 3.0,
    },
    "core_glycolysis_energy": {
        "EGLC": 8.0,
        "ELAC": 8.0,
        "GLC": 6.0,
        "G6P": 6.0,
        "ATP": 15.0,
        "ADP": 15.0,
        "AMP": 10.0,
        "B23PG": 8.0,
        "LAC": 5.0,
        "F6P": 4.0,
        "F16BP": 4.0,
        "P3G": 4.0,
        "PYR": 4.0,
        "PEP": 3.0,
        "P2G": 3.0,
    },
    "nucleotide_purine": {
        "IMP": 5.0,
        "GMP": 5.0,
        "AMP": 6.0,
        "EADE": 4.0,
        "EURT": 4.0,
        "EXAN": 3.0,
        "HYPX": 3.0,
        "ADE": 3.0,
        "INO": 2.5,
        "URT": 3.0,
    },
    "amino_redox_side": {
        "GSH": 6.0,
        "GSSG": 6.0,
        "GLU": 4.0,
        "GLN": 3.0,
        "EOXOP": 3.0,
        "EGLN": 3.0,
        "ECIT": 3.0,
        "EFUM": 3.0,
    },
    "all_supported": {
        "EGLC": 8.0,
        "ELAC": 8.0,
        "GLC": 6.0,
        "G6P": 6.0,
        "ATP": 15.0,
        "ADP": 15.0,
        "AMP": 10.0,
        "IMP": 5.0,
        "GMP": 5.0,
        "GSH": 6.0,
        "GSSG": 6.0,
        "GLU": 4.0,
        "EURT": 4.0,
        "EADE": 4.0,
        "EOXOP": 3.0,
    },
}

TARGET_SCOPE_ENDPOINT_METABOLITES = {
    "glycolysis_terminal": {"EGLC", "ELAC"},
    "glycolysis_extracellular": {"EGLC", "ELAC", "GLC", "LAC", "ATP", "ADP", "AMP"},
    "glycolysis_energy": {"EGLC", "ELAC", "GLC", "LAC", "ATP", "ADP", "AMP"},
    "core_glycolysis_energy": {"EGLC", "ELAC", "GLC", "LAC", "ATP", "ADP", "AMP", "B23PG"},
    "all_supported": {"EGLC", "ELAC", "GLC", "LAC", "ATP", "ADP", "AMP"},
}
TARGET_SCOPE_ENDPOINT_WEIGHTS = {
    "glycolysis_terminal": 3.0,
    "glycolysis_extracellular": 2.0,
    "glycolysis_energy": 2.0,
    "core_glycolysis_energy": 2.0,
    "all_supported": 2.0,
}

NRMSE_CAP = 50.0
SOLVE_CACHE_SIZE = 16


def resolve_target_scope_metabolites(target_scope):
    if target_scope == "all":
        return ALL_SUPPORTED_TARGET_METABOLITES
    if target_scope == "extracellular":
        return EXTRACELLULAR_TARGET_METABOLITES
    if target_scope == "glycolysis":
        return GLYCOLYSIS_TARGET_METABOLITES
    if target_scope == "glycolysis_terminal":
        return GLYCOLYSIS_TERMINAL_TARGET_METABOLITES
    if target_scope == "glycolysis_extracellular":
        return GLYCOLYSIS_EXTRACELLULAR_TARGET_METABOLITES
    if target_scope == "core_glycolysis_energy":
        return CORE_GLYCOLYSIS_ENERGY_TARGET_METABOLITES
    raise ValueError(f"Unsupported target_scope: {target_scope}")


def use_pathway_phase_objectives(target_scope):
    return target_scope == "glycolysis_extracellular"


# =============================================================================
# PARAMETER PHASES
# =============================================================================

PHASE1_PARAMS = {
    "vmax_VHK": (0.267472, 0.2, 5.0),
    "vmax_VPFK": (0.391893, 0.8, 5.0),
    "vmax_VFDPA": (1.156751, 0.5, 10.0),
    "vmax_VPK": (0.936322, 0.1, 50.0),
    "vmax_VPGK": (4.690379, 0.5, 50.0),
    "vmax_VPGM": (1.170854, 0.1, 50.0),
    "vmax_VLDH": (0.284952, 0.5, 50.0),
    "vmax_VEGLC": (1.077000, 0.5, 3.5),
    "vmax_VELAC": (0.580000, 0.05, 10.0),
    "vmax_VENOPGM": (5.515612, 2.0, 50.0),
    "vmax_VDPGM": (2.5, 0.1, 5.0),
    "vmax_V23DPGP": (3.0, 0.5, 30.0),
    "ka_F16BP_PK": (0.005, 0.0005, 0.1),
    "alpha_F16BP_PK": (10.0, 1.0, 100.0),
    "vmax_VPEP_PASE": (0.1, 0.01, 10.0),
    "km_GLC_HK": (0.05, 0.005, 5.0),
    "km_G6P": (0.146, 0.01, 5.0),
    "km_F6P": (0.207, 0.01, 5.0),
    "km_F16BP": (0.094, 0.005, 5.0),
    "km_B13PG": (1.013, 0.001, 5.0),
    "km_P3G": (0.134, 0.01, 5.0),
    "km_P2G": (0.134, 0.01, 5.0),
    "km_PEP": (0.175, 0.01, 5.0),
    "km_ADP_ATP": (1.0, 0.05, 10.0),
    "km_PYR": (0.697, 0.01, 5.0),
    "km_LAC": (49.862494, 1.0, 100.0),
    "km_NAD_NADH": (1.0, 0.05, 20.0),
    "km_NADH_NAD": (1.0, 0.05, 20.0),
    "km_ATP_HK": (0.5, 0.05, 2.0),
    "km_ATP_PFK": (0.1, 0.01, 1.0),
    "km_GLC_transport": (5.0, 1.0, 20.0),
    "km_EGLC": (49.5, 5.0, 60.0),
    "ki_ATP_PK": (2.5, 0.5, 10.0),
    "ki_PYR_PK": (1.0, 0.1, 5.0),
}

PHASE2_PARAMS = {
    "vmax_VAMPD1": (0.538065, 0.001, 0.1),
    "vmax_VADSS": (0.3, 0.01, 5.0),
    "vmax_VIMPH": (0.2, 0.01, 5.0),
    "vmax_VRKa": (0.4, 0.01, 3.0),
    "vmax_VPRPPASe": (0.5, 0.05, 3.0),
    "vmax_VAK": (0.8, 0.05, 8.0),
    "vmax_VAK2": (0.5, 0.01, 5.0),
    "vmax_VHGPRT1": (0.645581, 0.01, 6.0),
    "vmax_VHGPRT2": (0.25, 0.001, 1.0),
    "vmax_Vnucleo2": (0.15, 0.005, 2.0),
    "vmax_VGMPS": (0.379205, 0.01, 4.0),
    "vmax_VPNPase1": (0.25, 0.1, 1.0),
    "vmax_VXAO": (0.2, 0.1, 1.0),
    "vmax_VXAO2": (0.15, 0.05, 3.0),
    "vmax_VEXAN": (0.15, 0.001, 0.5),
    "vmax_VEURT": (0.15, 0.001, 1.0),
    "vmax_VEINO": (0.0001, 0.0001, 0.003),
    "vmax_VADA": (0.3, 0.01, 1.0),
    "vmax_VGMPK": (0.15, 0.01, 5.0),
    "vmax_VAPRT": (1.088, 0.1, 10.0),
    "vmax_VADSL": (0.4, 0.01, 5.0),
    "vmax_VNDPK": (1.0, 0.01, 10.0),
    "vmax_VNDPK_rev": (1.0, 0.01, 10.0),
    "vmax_VAK_rev": (0.5, 0.01, 5.0),
    "vmax_Vnucleo_GMP": (0.15, 0.01, 0.5),
    "vmax_VGDA": (0.15, 0.01, 0.5),
    "km_ATP": (0.569, 0.05, 5.0),
    "km_AMP": (0.283, 0.05, 3.0),
}

PHASE3_PARAMS = {
    "vmax_VGDH": (0.5, 0.01, 2.0),
    "vmax_VGDH_rev": (0.1, 0.01, 5.0),
    "vmax_VALATA": (0.35, 0.01, 2.0),
    "vmax_VASPTA": (0.4, 0.01, 4.0),
    "vmax_VGLNS": (0.4, 0.01, 4.0),
    "vmax_VEGLN": (0.001, 0.01, 2.0),
    "vmax_VEGLU": (0.001, 0.0001, 2.0),
    "vmax_VGSR": (1.0, 0.05, 10.0),
    "vmax_VGPX": (1.079815, 0.05, 10.0),
    "vmax_VME": (0.3, 0.01, 3.0),
    "vmax_VFUM": (0.5, 0.01, 5.0),
    "vmax_VMLD": (0.4, 0.01, 4.0),
    "vmax_VECIT": (0.25, 0.005, 2.5),
    "vmax_VASPTA_rev": (0.2, 0.01, 5.0),
    "vmax_VALATA_rev": (0.15, 0.05, 0.5),
    "vmax_VSHMT": (0.1, 0.01, 1.0),
    "vmax_VPHGDH": (0.1, 0.05, 0.5),
    "vmax_VOPLAH": (0.15, 0.01, 5.0),
    "km_GSSG": (1.0, 0.01, 5.0),
    "km_GLU": (0.289, 0.01, 3.0),
    "vmax_VEADE_fwd": (0.01, 0.0001, 0.001),
    "vmax_VEADE_rev": (0.01, 0.001, 1.0),
    "vmax_VEHYPX": (0.002, 0.01, 3.0),
    "vmax_VEFUM": (0.2, 0.001, 5.0),
    "vmax_VEMAL": (0.001, 0.0001, 1.0),
    "vmax_VGSS": (0.4, 0.01, 3.0),
    "vmax_VGGT": (0.3, 0.01, 3.0),
    "vmax_VGGCT": (0.25, 0.01, 3.0),
    "vmax_VEOXOP": (0.15, 0.01, 3.0),
    "vmax_VESER": (0.15, 0.01, 2.0),
    "vmax_VEARG": (0.05, 0.001, 1.0),
    "vmax_VEGSSG": (0.01, 0.001, 0.5),
    "vmax_VEGSH": (0.01, 0.001, 0.5),
    "vmax_VASNG": (0.15, 0.01, 2.0),
    "vmax_VEASN": (0.05, 0.001, 1.0),
    "vmax_VECYS": (0.0005, 0.0001, 0.5),
    "k_EGSH_deg": (0.1, 0.01, 1.0),
    "k_EGSSG_deg": (0.05, 0.01, 1.0),
}

PHASE_MAP = {1: PHASE1_PARAMS, 2: PHASE2_PARAMS, 3: PHASE3_PARAMS}
PHASE_NAMES = {
    1: "Core Glycolysis & Transport",
    2: "Nucleotide Metabolism",
    3: "Amino Acids, Redox & Transport",
}

DEFAULT_PARAM_VALUES = {
    pname: default
    for phase_params in PHASE_MAP.values()
    for pname, (default, _, _) in phase_params.items()
}

TRANSPORT_ONLY_PARAM_NAMES = {
    "vmax_VEGLC",
    "vmax_VELAC",
    "vmax_VEXAN",
    "vmax_VEURT",
    "vmax_VEINO",
    "vmax_VEADE_fwd",
    "vmax_VEADE_rev",
    "vmax_VEHYPX",
    "vmax_VEMAL",
    "vmax_VEFUM",
    "vmax_VECIT",
    "vmax_VEGLN",
    "vmax_VEGLU",
    "vmax_VEOXOP",
    "vmax_VESER",
    "vmax_VEARG",
    "vmax_VEGSSG",
    "vmax_VEGSH",
    "vmax_VEASN",
    "vmax_VECYS",
}
EADE_FOCUS_PARAM_NAMES = {"vmax_VAPRT", "vmax_VEADE_fwd", "vmax_VEADE_rev"}
GLYCOLYSIS_FOCUS_PARAM_NAMES = set(PHASE1_PARAMS)
CORE_KM_ANCHOR_PARAM_NAMES = {
    "km_F6P",
    "km_F16BP",
    "km_PEP",
    "km_PYR",
    "km_LAC",
    "km_EGLC",
}
CORE_KM_SHAPE_PARAM_NAMES = {
    "km_G6P",
    "km_P3G",
    "km_P2G",
    "km_GLC_transport",
    "km_ADP_ATP",
    "km_ATP_HK",
    "km_ATP_PFK",
    "km_NAD_NADH",
    "km_NADH_NAD",
}
CORE_KM_PARAM_NAMES = CORE_KM_ANCHOR_PARAM_NAMES | CORE_KM_SHAPE_PARAM_NAMES
CORE_LOWER_GLYCOLYSIS_PROBE_PARAM_NAMES = {
    "km_P3G",
    "km_P2G",
    "km_PEP",
    "km_PYR",
    "km_ADP_ATP",
    "vmax_VPGK",
    "vmax_VPGM",
    "vmax_VENOPGM",
    "vmax_VPK",
}
PURINE_TRANSPORT_NARROW_PARAM_NAMES = {
    "vmax_VPNPase1",
    "vmax_VXAO",
    "vmax_VXAO2",
    "vmax_VEXAN",
    "vmax_VEURT",
    "vmax_VAPRT",
}

GLYCOLYSIS_TERMINAL_PARAM_NAMES = {
    "vmax_VEGLC",
    "vmax_VELAC",
    "vmax_VHK",
    "vmax_VPGK",
    "vmax_VPK",
    "vmax_VLDH",
    "vmax_VENOPGM",
    "vmax_VPEP_PASE",
    "km_GLC_HK",
    "km_P2G",
    "km_PEP",
    "km_ADP_ATP",
    "km_PYR",
    "km_LAC",
    "km_NADH_NAD",
    "km_GLC_transport",
    "km_EGLC",
    "ki_ATP_PK",
    "ki_PYR_PK",
}
GLYCOLYSIS_TERMINAL_PARAMS = {name: PHASE1_PARAMS[name] for name in GLYCOLYSIS_TERMINAL_PARAM_NAMES}
GLYCOLYSIS_TERMINAL_PARAMS["vmax_VELAC"] = (0.580000, 0.2, 10.0)
GLYCOLYSIS_TERMINAL_PARAMS["vmax_VPEP_PASE"] = (0.1, 0.01, 2.0)

EXTRACELLULAR_COUPLED_PARAM_NAMES = {
    "vmax_VEGLC",
    "vmax_VELAC",
    "vmax_VXAO",
    "vmax_VXAO2",
    "vmax_VEXAN",
    "vmax_VEURT",
    "vmax_VAPRT",
    "vmax_VEADE_fwd",
    "vmax_VEADE_rev",
    "vmax_VADSL",
    "vmax_VGLNS",
    "vmax_VEGLN",
    "vmax_VOPLAH",
    "vmax_VGGCT",
    "vmax_VEOXOP",
    "vmax_VFUM",
    "vmax_VEFUM",
    "vmax_VEARG",
}
GLYCOLYSIS_EXTRACELLULAR_PARAM_NAMES = GLYCOLYSIS_FOCUS_PARAM_NAMES | EXTRACELLULAR_COUPLED_PARAM_NAMES


# =============================================================================
# TAXONOMY
# =============================================================================

PARAM_CLASS_VMAX = "vmax"
PARAM_CLASS_KM = "km"
PARAM_CLASS_REGULATION = "regulation"
PARAM_CLASS_TRANSPORT = "transport"
PARAM_CLASS_DEGRADATION = "degradation"
PARAM_CLASS_EFFECTIVE_MISC = "effective_misc"

IDENTIFIABLE_CORE = "core"
IDENTIFIABLE_CAUTION = "caution"
STRUCTURAL_COMPENSATION_RISK = "compensation_risk"

TRANSPORT_PARAM_NAMES = {
    "vmax_VEGLC",
    "vmax_VELAC",
    "vmax_VEXAN",
    "vmax_VEURT",
    "vmax_VEINO",
    "vmax_VEADE_fwd",
    "vmax_VEADE_rev",
    "vmax_VEHYPX",
    "vmax_VEMAL",
    "vmax_VEFUM",
    "vmax_VECIT",
    "vmax_VEGLN",
    "vmax_VEGLU",
    "vmax_VEOXOP",
    "vmax_VESER",
    "vmax_VEARG",
    "vmax_VEGSSG",
    "vmax_VEGSH",
    "vmax_VEASN",
    "vmax_VECYS",
    "km_EGLC",
    "km_LAC",
    "km_GLC_transport",
}

DEGRADATION_PARAM_NAMES = {"k_EGSH_deg", "k_EGSSG_deg"}

REGULATION_PARAM_NAMES = {
    "ki_ATP_PK",
    "ki_PYR_PK",
    "ka_F16BP_PK",
    "alpha_F16BP_PK",
    "n_F16BP_PK",
    "km_ADP_ATP",
    "km_NAD_NADH",
    "km_NADH_NAD",
    "km_NADP_NADPH",
    "km_NADPH_NADP",
}

EFFECTIVE_MISC_PARAM_NAMES = {
    "vmax_V23DPGP",
    "vmax_VPEP_PASE",
    "vmax_VNDPK_rev",
    "vmax_VAK_rev",
    "vmax_Vnucleo_GMP",
}

IDENTIFIABLE_CORE_PARAM_NAMES = {
    "vmax_VHK",
    "vmax_VPFK",
    "vmax_VPGK",
    "vmax_VPK",
    "vmax_VLDH",
    "vmax_VEGLC",
    "vmax_VELAC",
    "km_GLC_HK",
    "km_F6P",
    "km_F16BP",
    "km_B13PG",
    "km_PEP",
    "km_PYR",
    "km_EGLC",
    "km_LAC",
}

IDENTIFIABLE_CAUTION_PARAM_NAMES = {
    "km_ADP_ATP",
    "km_NAD_NADH",
    "km_NADH_NAD",
    "ki_ATP_PK",
    "ki_PYR_PK",
    "ka_F16BP_PK",
    "alpha_F16BP_PK",
    "vmax_VEXAN",
    "vmax_VEURT",
    "vmax_VEINO",
    "vmax_VEADE_fwd",
    "vmax_VEADE_rev",
    "vmax_VEGLN",
    "vmax_VEGLU",
    "vmax_VEOXOP",
    "vmax_VEARG",
    "vmax_VEFUM",
}

OPTIMIZATION_STRATEGY_CHOICES = {
    "legacy",
    "vmax_only",
    "km_only",
    "core_km_then_purine_transport",
    "vmax_then_km",
    "km_then_vmax",
    "joint_vmax_km",
    "staged_full",
}

OPTIMIZATION_STRATEGY_TEMPLATES = {
    "vmax_only": [
        {"name": "vmax_only", "parameter_classes": [PARAM_CLASS_VMAX]},
    ],
    "km_only": [
        {"name": "km_only", "parameter_classes": [PARAM_CLASS_KM]},
    ],
    "core_km_then_purine_transport": [
        {
            "name": "core_km_anchor",
            "phases": [1],
            "target_scope": "core_glycolysis_energy",
            "param_scope": "core_km",
            "parameter_classes": [PARAM_CLASS_KM],
            "include_params": sorted(CORE_KM_ANCHOR_PARAM_NAMES),
        },
        {
            "name": "core_km_shape_energy",
            "phases": [1],
            "target_scope": "core_glycolysis_energy",
            "param_scope": "core_km",
            "parameter_classes": [PARAM_CLASS_KM],
            "include_params": sorted(CORE_KM_SHAPE_PARAM_NAMES),
        },
        {
            "name": "purine_transport_refine",
            "phases": [2],
            "target_scope": "glycolysis_extracellular",
            "param_scope": "purine_transport_narrow",
            "parameter_classes": [PARAM_CLASS_VMAX],
            "include_params": sorted(PURINE_TRANSPORT_NARROW_PARAM_NAMES),
        },
    ],
    "vmax_then_km": [
        {"name": "vmax_stage", "parameter_classes": [PARAM_CLASS_VMAX]},
        {"name": "km_stage", "parameter_classes": [PARAM_CLASS_KM]},
    ],
    "km_then_vmax": [
        {"name": "km_stage", "parameter_classes": [PARAM_CLASS_KM]},
        {"name": "vmax_stage", "parameter_classes": [PARAM_CLASS_VMAX]},
    ],
    "joint_vmax_km": [
        {"name": "joint_vmax_km", "parameter_classes": [PARAM_CLASS_VMAX, PARAM_CLASS_KM]},
    ],
    "staged_full": [
        {
            "name": "stage_a_vmax_core",
            "parameter_classes": [PARAM_CLASS_VMAX],
            "identifiability_levels": [IDENTIFIABLE_CORE],
        },
        {
            "name": "stage_b_km_core",
            "parameter_classes": [PARAM_CLASS_KM],
            "identifiability_levels": [IDENTIFIABLE_CORE],
        },
        {
            "name": "stage_c_joint_core",
            "parameter_classes": [PARAM_CLASS_VMAX, PARAM_CLASS_KM],
            "identifiability_levels": [IDENTIFIABLE_CORE, IDENTIFIABLE_CAUTION],
        },
        {
            "name": "stage_d_regulation_fine",
            "parameter_classes": [PARAM_CLASS_REGULATION],
            "identifiability_levels": [IDENTIFIABLE_CAUTION],
        },
    ],
}


def normalize_name_list(values):
    if values is None:
        return None
    if isinstance(values, str):
        values = [v.strip() for v in values.split(",") if v.strip()]
    return [str(v) for v in values]


def get_parameter_classes(param_name):
    classes = set()
    if param_name.startswith("vmax_"):
        classes.add(PARAM_CLASS_VMAX)
    if param_name.startswith("km_"):
        classes.add(PARAM_CLASS_KM)
    if param_name.startswith(("ki_", "ka_", "alpha_", "n_")) or param_name in REGULATION_PARAM_NAMES:
        classes.add(PARAM_CLASS_REGULATION)
    if (
        param_name in TRANSPORT_PARAM_NAMES
        or "transport" in param_name
        or param_name.startswith("vmax_VE")
    ):
        classes.add(PARAM_CLASS_TRANSPORT)
    if param_name in DEGRADATION_PARAM_NAMES:
        classes.add(PARAM_CLASS_DEGRADATION)
    if param_name in EFFECTIVE_MISC_PARAM_NAMES or not classes:
        classes.add(PARAM_CLASS_EFFECTIVE_MISC)
    return classes


def get_parameter_identifiability(param_name):
    if param_name in IDENTIFIABLE_CORE_PARAM_NAMES:
        return IDENTIFIABLE_CORE
    if param_name in IDENTIFIABLE_CAUTION_PARAM_NAMES:
        return IDENTIFIABLE_CAUTION
    return STRUCTURAL_COMPENSATION_RISK


def build_parameter_taxonomy():
    all_names = sorted(DEFAULT_PARAM_VALUES)
    taxonomy = {
        "classes": {
            PARAM_CLASS_VMAX: [],
            PARAM_CLASS_KM: [],
            PARAM_CLASS_REGULATION: [],
            PARAM_CLASS_TRANSPORT: [],
            PARAM_CLASS_DEGRADATION: [],
            PARAM_CLASS_EFFECTIVE_MISC: [],
        },
        "identifiability": {
            IDENTIFIABLE_CORE: [],
            IDENTIFIABLE_CAUTION: [],
            STRUCTURAL_COMPENSATION_RISK: [],
        },
    }
    for name in all_names:
        for cls in get_parameter_classes(name):
            taxonomy["classes"][cls].append(name)
        taxonomy["identifiability"][get_parameter_identifiability(name)].append(name)
    return taxonomy


def filter_param_dict(
    param_dict,
    parameter_classes=None,
    identifiability_levels=None,
    include_params=None,
    exclude_params=None,
):
    allowed_classes = set(normalize_name_list(parameter_classes) or [])
    allowed_ident = set(normalize_name_list(identifiability_levels) or [])
    include_names = set(normalize_name_list(include_params) or [])
    exclude_names = set(normalize_name_list(exclude_params) or [])

    filtered = {}
    for name, bounds in param_dict.items():
        if include_names and name not in include_names:
            continue
        if name in exclude_names:
            continue
        if allowed_classes and get_parameter_classes(name).isdisjoint(allowed_classes):
            continue
        if allowed_ident and get_parameter_identifiability(name) not in allowed_ident:
            continue
        filtered[name] = bounds
    return filtered


# =============================================================================
# DATA
# =============================================================================

def load_experimental_data():
    df = pd.read_excel(DATA_DIR / "Data_Bordbar_et_al_exp.xlsx")
    exp_names = [str(n).strip().upper() for n in df.iloc[:, 0].tolist()]
    exp_values = df.iloc[:, 1:].values.astype(float)
    time_exp = np.array([float(c) for c in df.columns[1:]])
    name_to_row = {n: i for i, n in enumerate(exp_names)}
    return time_exp, exp_values, name_to_row


def load_initial_conditions():
    n_with_phi = NUM_BASE_METABOLITES + 1
    metabolite_list = [""] * n_with_phi
    for name, idx in BRODBAR_METABOLITE_MAP.items():
        if idx < n_with_phi:
            metabolite_list[idx] = name
    model = {"metab": metabolite_list}
    x0, _ = parse_initial_conditions(model, str(DATA_DIR / "Initial_conditions_JA_Final.xls"))
    return x0


# =============================================================================
# PARAMETER SELECTION
# =============================================================================

def get_phase_params(phase_num, param_scope="all"):
    phase_params = PHASE_MAP[phase_num]
    if param_scope == "all":
        return phase_params
    if param_scope == "transport_only":
        return {name: bounds for name, bounds in phase_params.items() if name in TRANSPORT_ONLY_PARAM_NAMES}
    if param_scope == "eade_focus":
        return {name: bounds for name, bounds in phase_params.items() if name in EADE_FOCUS_PARAM_NAMES}
    if param_scope == "glycolysis_mm":
        return {name: bounds for name, bounds in phase_params.items() if name in GLYCOLYSIS_FOCUS_PARAM_NAMES}
    if param_scope == "core_km":
        if phase_num != 1:
            return {}
        return {name: bounds for name, bounds in phase_params.items() if name in CORE_KM_PARAM_NAMES}
    if param_scope == "core_lower_glycolysis_probe":
        if phase_num != 1:
            return {}
        return {name: bounds for name, bounds in phase_params.items() if name in CORE_LOWER_GLYCOLYSIS_PROBE_PARAM_NAMES}
    if param_scope == "glycolysis_terminal":
        if phase_num != 1:
            return {}
        return GLYCOLYSIS_TERMINAL_PARAMS
    if param_scope == "glycolysis_extracellular":
        return {name: bounds for name, bounds in phase_params.items() if name in GLYCOLYSIS_EXTRACELLULAR_PARAM_NAMES}
    if param_scope == "extracellular_coupled":
        return {name: bounds for name, bounds in phase_params.items() if name in EXTRACELLULAR_COUPLED_PARAM_NAMES}
    if param_scope == "purine_transport_narrow":
        return {name: bounds for name, bounds in phase_params.items() if name in PURINE_TRANSPORT_NARROW_PARAM_NAMES}
    raise ValueError(f"Unsupported param_scope: {param_scope}")


def get_phase_params_filtered(
    phase_num,
    param_scope="all",
    parameter_classes=None,
    identifiability_levels=None,
    include_params=None,
    exclude_params=None,
):
    base = get_phase_params(phase_num, param_scope=param_scope)
    return filter_param_dict(
        base,
        parameter_classes=parameter_classes,
        identifiability_levels=identifiability_levels,
        include_params=include_params,
        exclude_params=exclude_params,
    )


def adjust_bounds_for_strategy(param_name, bounds, parameter_classes=None):
    default, lo, hi = bounds
    classes = get_parameter_classes(param_name)
    requested = set(normalize_name_list(parameter_classes) or [])

    if not requested:
        return (default, lo, hi)

    if PARAM_CLASS_KM in classes and PARAM_CLASS_KM in requested:
        center = max(default, 1e-8)
        return (default, max(lo, center / 10.0), min(hi, center * 10.0))

    if PARAM_CLASS_REGULATION in classes and PARAM_CLASS_REGULATION in requested:
        center = max(default, 1e-8)
        return (default, max(lo, center / 5.0), min(hi, center * 5.0))

    if PARAM_CLASS_DEGRADATION in classes and PARAM_CLASS_DEGRADATION in requested:
        center = max(default, 1e-8)
        return (default, max(lo, center / 3.0), min(hi, center * 3.0))

    return (default, lo, hi)


def build_stage_phase_params(stage_config, default_param_scope):
    stage_phase_map = {}
    param_scope = stage_config.get("param_scope", default_param_scope)
    parameter_classes = stage_config.get("parameter_classes")
    identifiability_levels = stage_config.get("identifiability_levels")
    include_params = stage_config.get("include_params")
    exclude_params = stage_config.get("exclude_params")

    for phase_num in stage_config["phases"]:
        filtered = get_phase_params_filtered(
            phase_num,
            param_scope=param_scope,
            parameter_classes=parameter_classes,
            identifiability_levels=identifiability_levels,
            include_params=include_params,
            exclude_params=exclude_params,
        )
        filtered = {
            name: adjust_bounds_for_strategy(name, bounds, parameter_classes=parameter_classes)
            for name, bounds in filtered.items()
        }
        stage_phase_map[phase_num] = filtered
    return stage_phase_map


def normalize_stage_config(stage, default_cfg):
    stage = dict(stage)

    if "phases" not in stage and "phase_order" in stage:
        stage["phases"] = stage["phase_order"]
    if "identifiability_levels" not in stage and "identifiability_filter" in stage:
        stage["identifiability_levels"] = stage["identifiability_filter"]

    stage.setdefault("name", f"stage_{default_cfg['index']}")
    stage.setdefault("phases", list(default_cfg["phases"]))
    stage.setdefault("param_scope", default_cfg["param_scope"])
    stage.setdefault("target_scope", default_cfg["target_scope"])
    stage.setdefault("parameter_classes", default_cfg["parameter_classes"])
    stage.setdefault("identifiability_levels", None)
    stage.setdefault("include_params", None)
    stage.setdefault("exclude_params", None)
    stage.setdefault("n_trials", default_cfg["n_trials"])
    stage.setdefault("global_trials", default_cfg["global_trials"])
    stage.setdefault("atp_focus", default_cfg["atp_focus"])
    stage.setdefault("atp_floor", default_cfg["atp_floor"])
    stage.setdefault("adp_floor", default_cfg["adp_floor"])
    stage.setdefault("adenylate_target", default_cfg["adenylate_target"])
    stage.setdefault("atp_penalty_weight", default_cfg["atp_penalty_weight"])
    stage.setdefault("pool_penalty_weight", default_cfg["pool_penalty_weight"])
    stage.setdefault("curve_fit_strength", default_cfg["curve_fit_strength"])
    stage.setdefault("seed", default_cfg["seed"])

    stage["phases"] = [int(p) for p in stage["phases"]]
    stage["parameter_classes"] = normalize_name_list(stage.get("parameter_classes"))
    stage["identifiability_levels"] = normalize_name_list(stage.get("identifiability_levels"))
    stage["include_params"] = normalize_name_list(stage.get("include_params"))
    stage["exclude_params"] = normalize_name_list(stage.get("exclude_params"))

    return stage


def resolve_stage_plan(
    optimization_strategy,
    phases,
    param_scope,
    target_scope,
    n_trials,
    global_trials,
    seed,
    parameter_classes=None,
    atp_focus=False,
    atp_floor=0.15,
    adp_floor=0.05,
    adenylate_target=0.65,
    atp_penalty_weight=8.0,
    pool_penalty_weight=10.0,
    curve_fit_strength=0.0,
    stage_plan=None,
):
    default_cfg = {
        "index": 1,
        "phases": list(phases),
        "param_scope": param_scope,
        "target_scope": target_scope,
        "parameter_classes": parameter_classes,
        "n_trials": n_trials,
        "global_trials": global_trials,
        "seed": seed,
        "atp_focus": atp_focus,
        "atp_floor": atp_floor,
        "adp_floor": adp_floor,
        "adenylate_target": adenylate_target,
        "atp_penalty_weight": atp_penalty_weight,
        "pool_penalty_weight": pool_penalty_weight,
        "curve_fit_strength": curve_fit_strength,
    }

    if stage_plan is None:
        if optimization_strategy == "legacy" and parameter_classes is None:
            raw_plan = [{"name": "legacy"}]
        else:
            raw_plan = OPTIMIZATION_STRATEGY_TEMPLATES.get(optimization_strategy)
            if raw_plan is None:
                raise ValueError(f"Unsupported optimization_strategy: {optimization_strategy}")
    else:
        raw_plan = stage_plan

    resolved = []
    for idx, raw_stage in enumerate(raw_plan, start=1):
        cfg = dict(default_cfg)
        cfg["index"] = idx
        stage = normalize_stage_config(raw_stage, cfg)
        stage["phase_params"] = build_stage_phase_params(stage, stage["param_scope"])
        stage["selected_param_names"] = sorted({p for d in stage["phase_params"].values() for p in d})
        resolved.append(stage)
    return resolved


# =============================================================================
# OBJECTIVE
# =============================================================================

class ObjectiveFunction:
    def __init__(
        self,
        x0,
        time_exp,
        exp_values,
        name_to_row,
        t_max=46,
        target_scope="all",
        target_names=None,
        objective_name=None,
        endpoint_target_names=None,
        endpoint_weight=None,
        atp_focus=False,
        atp_floor=0.15,
        adp_floor=0.05,
        adenylate_target=0.65,
        atp_penalty_weight=8.0,
        pool_penalty_weight=10.0,
        curve_fit_strength=0.0,
    ):
        self.x0 = x0
        self.time_exp = time_exp
        self.exp_values = exp_values
        self.name_to_row = name_to_row
        self.t_max = t_max
        self.target_scope = target_scope
        self.objective_name = objective_name or target_scope
        self.atp_focus = atp_focus
        self.atp_floor = atp_floor
        self.adp_floor = adp_floor
        self.adenylate_target = adenylate_target
        self.atp_penalty_weight = atp_penalty_weight
        self.pool_penalty_weight = pool_penalty_weight
        self.curve_fit_strength = curve_fit_strength
        self.dynamic_eps = 1e-6
        self.level_weight = 1.0
        self.slope_weight = 0.35
        self.curve_endpoint_weight = 0.50
        self.fold_weight = 0.30

        if target_scope not in {"all", "extracellular", "glycolysis", "glycolysis_terminal", "glycolysis_extracellular", "core_glycolysis_energy"}:
            raise ValueError(f"Unsupported target_scope: {target_scope}")

        self.active_exp_mask = np.asarray(time_exp) <= (self.t_max + 1e-9)
        self.active_time_exp = np.asarray(time_exp)[self.active_exp_mask]
        if self.active_time_exp.size == 0:
            raise ValueError(f"No experimental time points available within t_max={self.t_max}")

        self.t_eval_dense = np.linspace(1, t_max, 200)
        self.t_eval_fast = np.sort(np.unique(np.concatenate(([1], self.active_time_exp))))

        self.target_names = []
        self.target_indices = []
        self.target_exp = []
        self.target_weights = []

        selected_target_names = set(target_names) if target_names is not None else resolve_target_scope_metabolites(target_scope)
        scope_weight_overrides = TARGET_SCOPE_WEIGHT_OVERRIDES.get(
            self.objective_name,
            TARGET_SCOPE_WEIGHT_OVERRIDES.get(self.target_scope, {}),
        )

        for ename, midx in EXP_TO_MODEL.items():
            if ename not in selected_target_names:
                continue
            if ename not in name_to_row:
                continue

            row = name_to_row[ename]
            self.target_names.append(ename)
            self.target_indices.append(midx)
            self.target_exp.append(exp_values[row, self.active_exp_mask])

            if ename in CRITICAL_WEIGHT_METABOLITES:
                w = CRITICAL_WEIGHT_METABOLITES[ename]
            elif ename in HIGH_WEIGHT_METABOLITES:
                w = 2.0
            else:
                w = 1.0
            if ename in scope_weight_overrides:
                w = max(w, scope_weight_overrides[ename])
            self.target_weights.append(w)

        if not self.target_names:
            raise ValueError(f"No experimental targets found for target_scope='{self.target_scope}'")

        self.target_exp = np.array(self.target_exp)
        self.target_weights = np.array(self.target_weights)
        self.n_targets = len(self.target_names)

        self.screen_exp_positions = np.unique(
            np.linspace(0, self.target_exp.shape[1] - 1, min(5, self.target_exp.shape[1]), dtype=int)
        )
        self.screen_time_exp = self.active_time_exp[self.screen_exp_positions]
        self.target_exp_screen = self.target_exp[:, self.screen_exp_positions]

        resolved_endpoint_target_names = (
            set(endpoint_target_names)
            if endpoint_target_names is not None
            else TARGET_SCOPE_ENDPOINT_METABOLITES.get(
                self.objective_name,
                TARGET_SCOPE_ENDPOINT_METABOLITES.get(self.target_scope, set()),
            )
        )

        self.endpoint_weight = (
            endpoint_weight
            if endpoint_weight is not None
            else TARGET_SCOPE_ENDPOINT_WEIGHTS.get(
                self.objective_name,
                TARGET_SCOPE_ENDPOINT_WEIGHTS.get(self.target_scope, 0.0),
            )
        )

        self.endpoint_mask = np.array(
            [name in resolved_endpoint_target_names for name in self.target_names],
            dtype=bool,
        )

        self.norm_factors = np.maximum(np.mean(np.abs(self.target_exp), axis=1), 0.01)

        self.atp_idx = 35
        self.adp_idx = 36
        self.amp_idx = 37
        self.init_adenylate_pool = float(max(x0[self.atp_idx] + x0[self.adp_idx] + x0[self.amp_idx], 1e-8))

        self.exp_pool_trajectory = None
        if "ATP" in name_to_row and "ADP" in name_to_row and "AMP" in name_to_row:
            atp_exp = exp_values[name_to_row["ATP"], self.active_exp_mask]
            adp_exp = exp_values[name_to_row["ADP"], self.active_exp_mask]
            amp_exp = exp_values[name_to_row["AMP"], self.active_exp_mask]
            self.exp_pool_trajectory = atp_exp + adp_exp + amp_exp

        self.screen_pool_trajectory = None
        if self.exp_pool_trajectory is not None:
            self.screen_pool_trajectory = self.exp_pool_trajectory[self.screen_exp_positions]

        self.nad_idx = 75
        self.nadh_idx = 76
        self.nadp_idx = 77
        self.nadph_idx = 78
        self.init_nad_pool = float(x0[self.nad_idx] + x0[self.nadh_idx])
        self.init_nadp_pool = float(x0[self.nadp_idx] + x0[self.nadph_idx])

        self.target_caps = np.full(self.n_targets, NRMSE_CAP, dtype=float)
        if self.atp_focus:
            atp_like_mask = np.isin(self.target_names, ["ATP", "ADP", "AMP"])
            self.target_caps[atp_like_mask] = 50.0

        self.default_param_values = DEFAULT_PARAM_VALUES

        self.t_eval_screen = np.sort(np.unique(np.concatenate(([1], self.active_time_exp[self.screen_exp_positions]))))
        self.t_eval_report = np.sort(np.unique(np.concatenate((self.t_eval_fast, [t_max]))))
        self.exp_eval_indices = np.searchsorted(self.t_eval_fast, self.active_time_exp)
        self.screen_eval_indices = np.searchsorted(self.t_eval_screen, self.active_time_exp[self.screen_exp_positions])
        self.report_exp_indices = np.searchsorted(self.t_eval_report, self.active_time_exp)
        self.report_final_index = int(np.searchsorted(self.t_eval_report, self.t_max))

        self._solve_cache = {}
        self.n_calls = 0
        self.best_loss = float("inf")
        self.best_params = None
        self.best_loss_breakdown = None

    @staticmethod
    def _params_cache_key(custom_params):
        if not custom_params:
            return ()
        return tuple(sorted((pname, float(pval)) for pname, pval in custom_params.items()))

    def _cached_solve(self, custom_params, mode="fast"):
        cache_key = (mode, self._params_cache_key(custom_params))
        cached = self._solve_cache.get(cache_key)
        if cached is not None:
            return cached

        if mode == "fast":
            t_eval = self.t_eval_fast
            rtol, atol = 1e-4, 1e-6
        elif mode == "screen":
            t_eval = self.t_eval_screen
            rtol, atol = 5e-4, 5e-6
        elif mode == "report":
            t_eval = self.t_eval_report
            rtol, atol = 1e-5, 1e-7
        elif mode == "dense":
            t_eval = self.t_eval_dense
            rtol, atol = 1e-5, 1e-7
        else:
            raise ValueError(f"Unsupported solve mode: {mode}")

        sol = solve_ivp(
            lambda t, y: equadiff_brodbar(t, y, custom_params=custom_params, curve_fit_strength=self.curve_fit_strength),
            (1, self.t_max),
            self.x0,
            method="LSODA",
            t_eval=t_eval,
            rtol=rtol,
            atol=atol,
        )

        self._solve_cache[cache_key] = sol
        if len(self._solve_cache) > SOLVE_CACHE_SIZE:
            oldest_key = next(iter(self._solve_cache))
            self._solve_cache.pop(oldest_key, None)

        return sol

    def _level_loss(self, sim_targets, target_exp):
        rmse = np.sqrt(np.mean((sim_targets - target_exp) ** 2, axis=1))
        nrmses = np.minimum(rmse / self.norm_factors, self.target_caps)
        loss = np.average(nrmses, weights=self.target_weights)
        return float(self.level_weight * loss)

    def _target_loss(self, sim_targets, target_exp):
        return self._level_loss(sim_targets, target_exp)

    def _slope_loss(self, sim_targets, target_exp, timepoints):
        if sim_targets.shape[1] < 2 or len(timepoints) < 2:
            return 0.0

        dt = np.diff(timepoints)
        if dt.size == 0:
            return 0.0

        sim_slopes = np.diff(sim_targets, axis=1) / dt[None, :]
        exp_slopes = np.diff(target_exp, axis=1) / dt[None, :]
        rmse = np.sqrt(np.mean((sim_slopes - exp_slopes) ** 2, axis=1))
        nrmses = np.minimum(rmse / self.norm_factors, self.target_caps)
        loss = np.average(nrmses, weights=self.target_weights)
        return float(self.slope_weight * loss)

    def _endpoint_loss(self, sim_targets, target_exp):
        endpoint_errors = np.abs(sim_targets[:, -1] - target_exp[:, -1]) / self.norm_factors
        loss = self.curve_endpoint_weight * np.average(endpoint_errors, weights=self.target_weights)

        if self.endpoint_weight > 0.0 and np.any(self.endpoint_mask):
            loss += self.endpoint_weight * np.average(
                endpoint_errors[self.endpoint_mask],
                weights=self.target_weights[self.endpoint_mask],
            )

        return float(loss)

    def _fold_change_loss(self, sim_targets, target_exp):
        sim_start = sim_targets[:, 0]
        sim_end = sim_targets[:, -1]
        exp_start = target_exp[:, 0]
        exp_end = target_exp[:, -1]

        sim_log_fold = np.log((sim_end + self.dynamic_eps) / (sim_start + self.dynamic_eps))
        exp_log_fold = np.log((exp_end + self.dynamic_eps) / (exp_start + self.dynamic_eps))
        fold_errors = np.minimum(np.abs(sim_log_fold - exp_log_fold), self.target_caps)
        loss = np.average(fold_errors, weights=self.target_weights)
        return float(self.fold_weight * loss)

    def _composite_loss(self, sim_targets, target_exp, timepoints):
        level_loss = self._level_loss(sim_targets, target_exp)
        slope_loss = self._slope_loss(sim_targets, target_exp, timepoints)
        endpoint_loss = self._endpoint_loss(sim_targets, target_exp)
        fold_loss = self._fold_change_loss(sim_targets, target_exp)

        total_loss = level_loss + slope_loss + endpoint_loss + fold_loss
        breakdown = {
            "level_loss": float(level_loss),
            "slope_loss": float(slope_loss),
            "endpoint_loss": float(endpoint_loss),
            "fold_loss": float(fold_loss),
        }
        return float(total_loss), breakdown

    def _loss_inputs_for_mode(self, y, mode):
        if mode == "screen":
            return y[self.target_indices][:, self.screen_eval_indices], self.target_exp_screen, self.screen_time_exp, self.screen_eval_indices, self.screen_pool_trajectory
        if mode == "fast":
            return y[self.target_indices][:, self.exp_eval_indices], self.target_exp, self.active_time_exp, self.exp_eval_indices, self.exp_pool_trajectory
        if mode == "report":
            return y[self.target_indices][:, self.report_exp_indices], self.target_exp, self.active_time_exp, self.report_exp_indices, self.exp_pool_trajectory
        raise ValueError(f"Unsupported loss mode: {mode}")

    def _evaluate_total_loss(self, custom_params, mode):
        sol = self._cached_solve(custom_params, mode=mode)
        if not sol.success:
            return None, None, None

        y = np.maximum(sol.y, 0.0)
        sim_targets, target_exp, timepoints, exp_eval_indices, exp_pool_trajectory = self._loss_inputs_for_mode(y, mode)
        composite_loss, breakdown = self._composite_loss(sim_targets, target_exp, timepoints)
        regularization_loss = self._regularization_loss(custom_params)
        physiological_penalty_loss = self._penalty_loss(y, exp_eval_indices, exp_pool_trajectory)
        total_loss = composite_loss + regularization_loss + physiological_penalty_loss
        breakdown = {
            **breakdown,
            "regularization_loss": float(regularization_loss),
            "physiological_penalty_loss": float(physiological_penalty_loss),
            "total_loss": float(total_loss),
        }
        return float(total_loss), breakdown, y

    def objective_weights(self):
        return {
            "level_weight": float(self.level_weight),
            "slope_weight": float(self.slope_weight),
            "curve_endpoint_weight": float(self.curve_endpoint_weight),
            "fold_weight": float(self.fold_weight),
            "scope_endpoint_weight": float(self.endpoint_weight),
        }

    def loss_breakdown(self, custom_params, mode="fast"):
        total_loss, breakdown, _ = self._evaluate_total_loss(custom_params, mode=mode)
        if breakdown is None:
            return None
        return breakdown

    def _regularization_loss(self, custom_params):
        if not custom_params:
            return 0.0

        class_base_weights = {
            PARAM_CLASS_VMAX: 0.005,
            PARAM_CLASS_KM: 0.010,
            PARAM_CLASS_REGULATION: 0.020,
            PARAM_CLASS_TRANSPORT: 0.010,
            PARAM_CLASS_DEGRADATION: 0.030,
            PARAM_CLASS_EFFECTIVE_MISC: 0.020,
        }
        ident_mult = {
            IDENTIFIABLE_CORE: 1.0,
            IDENTIFIABLE_CAUTION: 1.5,
            STRUCTURAL_COMPENSATION_RISK: 2.0,
        }

        reg = 0.0
        for pname, pval in custom_params.items():
            default = self.default_param_values.get(pname)
            if default is None or pval <= 0 or default <= 0:
                continue
            log_ratio = np.log10(pval / default)
            classes = get_parameter_classes(pname)
            base_weight = max(class_base_weights.get(cls, 0.005) for cls in classes)
            mult = ident_mult.get(get_parameter_identifiability(pname), 1.0)
            reg += base_weight * mult * (log_ratio ** 2)

        return float(reg)

    def _penalty_loss(self, y, exp_eval_indices, exp_pool_trajectory):
        total_penalty = 0.0

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

            total_penalty += self.atp_penalty_weight * (atp_floor_pen + 0.5 * adp_floor_pen)
            total_penalty += self.pool_penalty_weight * pool_pen

            if exp_pool_trajectory is not None:
                sim_pool = (atp + adp + amp)[exp_eval_indices]
                pool_norm = max(np.mean(exp_pool_trajectory), 0.1)
                pool_traj_rmse = np.sqrt(np.mean((sim_pool - exp_pool_trajectory) ** 2))
                total_penalty += 5.0 * (pool_traj_rmse / pool_norm)

        if self.init_nad_pool > 0.01:
            nad_pool_final = float(y[self.nad_idx, -1] + y[self.nadh_idx, -1])
            total_penalty += 3.0 * (abs(nad_pool_final - self.init_nad_pool) / self.init_nad_pool)

        if self.init_nadp_pool > 0.01:
            nadp_pool_final = float(y[self.nadp_idx, -1] + y[self.nadph_idx, -1])
            total_penalty += 3.0 * (abs(nadp_pool_final - self.init_nadp_pool) / self.init_nadp_pool)

        return float(total_penalty)

    def screen(self, custom_params):
        try:
            total_loss, _, _ = self._evaluate_total_loss(custom_params, mode="screen")
            if total_loss is None:
                return 100.0
            return total_loss
        except Exception:
            return 100.0

    def endpoint_nrmse(self, custom_params):
        sol = self._cached_solve(custom_params, mode="report")
        if not np.any(self.endpoint_mask):
            return 0.0
        if not sol.success:
            return float("inf")
        y = np.maximum(sol.y, 0.0)
        endpoint_values = y[self.target_indices, self.report_final_index]
        endpoint_errors = np.abs(endpoint_values - self.target_exp[:, -1]) / self.norm_factors
        return float(np.average(endpoint_errors[self.endpoint_mask], weights=self.target_weights[self.endpoint_mask]))

    def __call__(self, custom_params):
        self.n_calls += 1
        try:
            total_loss, breakdown, _ = self._evaluate_total_loss(custom_params, mode="fast")
            if total_loss is None:
                return 100.0

            if total_loss < self.best_loss:
                self.best_loss = total_loss
                self.best_params = {} if not custom_params else custom_params.copy()
                self.best_loss_breakdown = dict(breakdown)

            return total_loss
        except Exception:
            return 100.0

    def detailed_report(self, custom_params):
        sol = self._cached_solve(custom_params, mode="report")
        if not sol.success:
            return []
        y = np.maximum(sol.y, 0.0)

        report = []
        for i, (ename, midx) in enumerate(zip(self.target_names, self.target_indices)):
            sim_at_exp = y[midx, self.report_exp_indices]
            rmse = np.sqrt(np.mean((sim_at_exp - self.target_exp[i]) ** 2))
            nrmse = rmse / self.norm_factors[i]
            report.append({
                "name": ename,
                "idx": midx,
                "rmse": rmse,
                "nrmse": nrmse,
                "exp_mean_abs": float(np.mean(np.abs(self.target_exp[i]))),
                "norm_factor": float(self.norm_factors[i]),
                "sim_final": y[midx, self.report_final_index],
                "exp_final": self.target_exp[i, -1],
            })
        return sorted(report, key=lambda r: r["nrmse"], reverse=True)


# =============================================================================
# OPTIMIZERS
# =============================================================================

def optimize_optuna(objective, phase_params, fixed_params, n_trials=200, study_name=None, seed=42):
    def optuna_objective(trial):
        custom_params = fixed_params.copy()
        for pname, (_, lo, hi) in phase_params.items():
            val = trial.suggest_float(pname, lo, hi, log=True)
            custom_params[pname] = val
        screen_loss = objective.screen(custom_params)
        trial.report(screen_loss, 0)
        if screen_loss >= 100.0 or trial.should_prune():
            raise optuna.TrialPruned()
        final_loss = objective(custom_params)
        trial.report(final_loss, 1)
        if trial.should_prune():
            raise optuna.TrialPruned()
        return final_loss

    sampler = optuna.samplers.TPESampler(
        seed=seed,
        n_startup_trials=min(30, max(1, n_trials // 4)),
        multivariate=True,
    )
    pruner = optuna.pruners.MedianPruner(
        n_startup_trials=min(10, max(1, n_trials // 5)),
        n_warmup_steps=0,
        interval_steps=1,
    )

    study = optuna.create_study(
        direction="minimize",
        sampler=sampler,
        pruner=pruner,
        study_name=study_name or "mm_calibration",
    )

    seed_trial = {}
    for pname, (default, lo, hi) in phase_params.items():
        loaded_val = fixed_params.get(pname, default)
        seed_trial[pname] = float(np.clip(loaded_val, lo, hi))
    study.enqueue_trial(seed_trial)

    study.optimize(optuna_objective, n_trials=n_trials, show_progress_bar=True)
    return study.best_params, study.best_value, study


def optimize_de(objective, phase_params, fixed_params, max_iter=150):
    param_names = list(phase_params.keys())
    bounds = [(lo, hi) for _, (_, lo, hi) in phase_params.items()]

    def de_objective(x):
        custom_params = fixed_params.copy()
        for i, pname in enumerate(param_names):
            custom_params[pname] = x[i]
        return objective(custom_params)

    result = differential_evolution(
        de_objective,
        bounds,
        maxiter=max_iter,
        popsize=20,
        strategy="best1bin",
        mutation=(0.5, 1.5),
        recombination=0.8,
        seed=42,
        tol=1e-6,
        polish=True,
        workers=1,
    )

    best = {pname: result.x[i] for i, pname in enumerate(param_names)}
    return best, result.fun, result


# =============================================================================
# OBJECTIVE BUILDERS
# =============================================================================

def build_objective(
    x0,
    time_exp,
    exp_values,
    name_to_row,
    t_max=46,
    target_scope="all",
    target_names=None,
    objective_name=None,
    endpoint_target_names=None,
    endpoint_weight=None,
    atp_focus=False,
    atp_floor=0.15,
    adp_floor=0.05,
    adenylate_target=0.65,
    atp_penalty_weight=8.0,
    pool_penalty_weight=10.0,
    curve_fit_strength=0.0,
):
    return ObjectiveFunction(
        x0,
        time_exp,
        exp_values,
        name_to_row,
        t_max=t_max,
        target_scope=target_scope,
        target_names=target_names,
        objective_name=objective_name,
        endpoint_target_names=endpoint_target_names,
        endpoint_weight=endpoint_weight,
        atp_focus=atp_focus,
        atp_floor=atp_floor,
        adp_floor=adp_floor,
        adenylate_target=adenylate_target,
        atp_penalty_weight=atp_penalty_weight,
        pool_penalty_weight=pool_penalty_weight,
        curve_fit_strength=curve_fit_strength,
    )


def build_primary_objective(
    x0,
    time_exp,
    exp_values,
    name_to_row,
    target_scope,
    t_max=46,
    atp_focus=False,
    atp_floor=0.15,
    adp_floor=0.05,
    adenylate_target=0.65,
    atp_penalty_weight=8.0,
    pool_penalty_weight=10.0,
    curve_fit_strength=0.0,
):
    if use_pathway_phase_objectives(target_scope):
        return build_objective(
            x0,
            time_exp,
            exp_values,
            name_to_row,
            t_max=t_max,
            target_scope="all",
            objective_name="all_supported",
            atp_focus=atp_focus,
            atp_floor=atp_floor,
            adp_floor=adp_floor,
            adenylate_target=adenylate_target,
            atp_penalty_weight=atp_penalty_weight,
            pool_penalty_weight=pool_penalty_weight,
            curve_fit_strength=curve_fit_strength,
        )
    return build_objective(
        x0,
        time_exp,
        exp_values,
        name_to_row,
        t_max=t_max,
        target_scope=target_scope,
        atp_focus=atp_focus,
        atp_floor=atp_floor,
        adp_floor=adp_floor,
        adenylate_target=adenylate_target,
        atp_penalty_weight=atp_penalty_weight,
        pool_penalty_weight=pool_penalty_weight,
        curve_fit_strength=curve_fit_strength,
    )


def build_phase_objectives(
    x0,
    time_exp,
    exp_values,
    name_to_row,
    target_scope,
    t_max=46,
    atp_focus=False,
    atp_floor=0.15,
    adp_floor=0.05,
    adenylate_target=0.65,
    atp_penalty_weight=8.0,
    pool_penalty_weight=10.0,
    curve_fit_strength=0.0,
):
    phase_objectives = {}
    if use_pathway_phase_objectives(target_scope):
        for phase_num, objective_name in PATHWAY_PHASE_OBJECTIVE_NAMES.items():
            phase_objectives[phase_num] = build_objective(
                x0,
                time_exp,
                exp_values,
                name_to_row,
                t_max=t_max,
                target_scope="all",
                target_names=PATHWAY_TARGET_GROUPS[objective_name],
                objective_name=objective_name,
                atp_focus=atp_focus,
                atp_floor=atp_floor,
                adp_floor=adp_floor,
                adenylate_target=adenylate_target,
                atp_penalty_weight=atp_penalty_weight,
                pool_penalty_weight=pool_penalty_weight,
                curve_fit_strength=curve_fit_strength,
            )
    return phase_objectives


def build_monitor_objectives(
    x0,
    time_exp,
    exp_values,
    name_to_row,
    target_scope,
    t_max=46,
    curve_fit_strength=0.0,
):
    monitor_objectives = {}
    if target_scope in {"glycolysis_extracellular", "all", "core_glycolysis_energy"}:
        for scope_name in ("glycolysis_energy", "nucleotide_purine", "amino_redox_side"):
            monitor_objectives[scope_name] = build_objective(
                x0,
                time_exp,
                exp_values,
                name_to_row,
                t_max=t_max,
                target_scope="all",
                target_names=PATHWAY_TARGET_GROUPS[scope_name],
                objective_name=scope_name,
                curve_fit_strength=curve_fit_strength,
            )
        monitor_objectives["extracellular"] = ObjectiveFunction(
            x0, time_exp, exp_values, name_to_row,
            t_max=t_max, target_scope="extracellular", curve_fit_strength=curve_fit_strength
        )
        monitor_objectives["glycolysis"] = ObjectiveFunction(
            x0, time_exp, exp_values, name_to_row,
            t_max=t_max, target_scope="glycolysis", curve_fit_strength=curve_fit_strength
        )
    return monitor_objectives


def build_objective_bundle(
    x0,
    time_exp,
    exp_values,
    name_to_row,
    target_scope,
    t_max=46,
    atp_focus=False,
    atp_floor=0.15,
    adp_floor=0.05,
    adenylate_target=0.65,
    atp_penalty_weight=8.0,
    pool_penalty_weight=10.0,
    curve_fit_strength=0.0,
):
    primary = build_primary_objective(
        x0, time_exp, exp_values, name_to_row,
        target_scope=target_scope,
        t_max=t_max,
        atp_focus=atp_focus,
        atp_floor=atp_floor,
        adp_floor=adp_floor,
        adenylate_target=adenylate_target,
        atp_penalty_weight=atp_penalty_weight,
        pool_penalty_weight=pool_penalty_weight,
        curve_fit_strength=curve_fit_strength,
    )
    phase_objectives = build_phase_objectives(
        x0, time_exp, exp_values, name_to_row,
        target_scope=target_scope,
        t_max=t_max,
        atp_focus=atp_focus,
        atp_floor=atp_floor,
        adp_floor=adp_floor,
        adenylate_target=adenylate_target,
        atp_penalty_weight=atp_penalty_weight,
        pool_penalty_weight=pool_penalty_weight,
        curve_fit_strength=curve_fit_strength,
    )
    monitor_objectives = build_monitor_objectives(
        x0, time_exp, exp_values, name_to_row,
        target_scope=target_scope,
        t_max=t_max,
        curve_fit_strength=curve_fit_strength,
    )
    monitor_regression_limits = get_monitor_regression_limits(target_scope)

    return {
        "primary": primary,
        "phase_objectives": phase_objectives,
        "monitor_objectives": monitor_objectives,
        "monitor_regression_limits": monitor_regression_limits,
    }


def evaluate_monitor_metrics(primary_objective, monitor_objectives, params):
    metrics = {
        "target": float(primary_objective(params)),
        "endpoint_nrmse": float(primary_objective.endpoint_nrmse(params)),
    }
    metrics["joint"] = metrics["target"]
    for scope_name, scope_objective in monitor_objectives.items():
        metrics[scope_name] = float(scope_objective(params))
    return metrics


def accept_monitor_metrics(
    incumbent_metrics,
    candidate_metrics,
    monitor_regression_limits=None,
    max_endpoint_regression=0.15,
):
    reasons = []
    if candidate_metrics["target"] > incumbent_metrics["target"]:
        reasons.append(f"target {incumbent_metrics['target']:.4f}->{candidate_metrics['target']:.4f}")

    for metric_name, max_regression in (monitor_regression_limits or {}).items():
        if metric_name in incumbent_metrics and metric_name in candidate_metrics:
            if candidate_metrics[metric_name] > incumbent_metrics[metric_name] + max_regression:
                reasons.append(
                    f"{metric_name} {incumbent_metrics[metric_name]:.4f}->{candidate_metrics[metric_name]:.4f}"
                )

    if "endpoint_nrmse" in incumbent_metrics and "endpoint_nrmse" in candidate_metrics:
        if candidate_metrics["endpoint_nrmse"] > incumbent_metrics["endpoint_nrmse"] + max_endpoint_regression:
            reasons.append(
                f"endpoint {incumbent_metrics['endpoint_nrmse']:.4f}->{candidate_metrics['endpoint_nrmse']:.4f}"
            )

    if reasons:
        return False, "; ".join(reasons)
    return True, "accepted"


def get_monitor_regression_limits(target_scope):
    if target_scope in {"glycolysis_extracellular", "all"}:
        return PATHWAY_MONITOR_REGRESSION_LIMITS.copy()
    if target_scope == "core_glycolysis_energy":
        return {
            "glycolysis_energy": PATHWAY_MONITOR_REGRESSION_LIMITS["glycolysis_energy"],
            "glycolysis": PATHWAY_MONITOR_REGRESSION_LIMITS["glycolysis"],
            "extracellular": PATHWAY_MONITOR_REGRESSION_LIMITS["extracellular"],
        }
    return {}


def format_metric_summary(metrics, metric_keys):
    parts = []
    for metric_name in metric_keys:
        if metric_name in metrics:
            parts.append(f"{metric_name}={metrics[metric_name]:.4f}")
    return ", ".join(parts)


def format_metric_changes(before_metrics, after_metrics, metric_keys):
    parts = []
    for metric_name in metric_keys:
        if metric_name in before_metrics and metric_name in after_metrics:
            parts.append(f"{metric_name} {before_metrics[metric_name]:.4f} -> {after_metrics[metric_name]:.4f}")
    return ", ".join(parts)


def total_objective_calls(*objective_groups):
    total = 0
    seen_ids = set()
    pending = list(objective_groups)

    while pending:
        group = pending.pop()

        if group is None:
            continue

        if isinstance(group, dict):
            pending.extend(group.values())
            continue

        if isinstance(group, (list, tuple, set)):
            pending.extend(group)
            continue

        n_calls = getattr(group, "n_calls", None)
        if isinstance(n_calls, (int, float)):
            obj_id = id(group)
            if obj_id not in seen_ids:
                seen_ids.add(obj_id)
                total += int(n_calls)

    return total


# =============================================================================
# TSV HELPERS
# =============================================================================

def ensure_results_tsv_schema(results_file):
    if not results_file.exists():
        return
    with open(results_file, newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    if not rows:
        return

    header = rows[0]
    if header == RESULTS_TSV_FIELDS:
        return

    migrated_rows = []
    for raw in rows[1:]:
        if not raw:
            continue
        if len(raw) == len(RESULTS_TSV_FIELDS):
            row_map = {field: raw[i] for i, field in enumerate(RESULTS_TSV_FIELDS)}
        elif header == LEGACY_RESULTS_TSV_FIELDS and len(raw) == len(LEGACY_RESULTS_TSV_FIELDS):
            legacy_map = {field: raw[i] for i, field in enumerate(LEGACY_RESULTS_TSV_FIELDS)}
            row_map = {field: "" for field in RESULTS_TSV_FIELDS}
            for field in LEGACY_RESULTS_TSV_FIELDS:
                row_map[field] = legacy_map.get(field, "")
        else:
            row_map = {field: raw[i] if i < len(raw) else "" for i, field in enumerate(header)}
            row_map = {field: row_map.get(field, "") for field in RESULTS_TSV_FIELDS}
        migrated_rows.append(row_map)

    with open(results_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_TSV_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(migrated_rows)


def append_results_row(out_dir, row):
    results_file = out_dir / "results.tsv"
    ensure_results_tsv_schema(results_file)
    file_exists = results_file.exists()
    with open(results_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_TSV_FIELDS, delimiter="\t")
        if not file_exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RESULTS_TSV_FIELDS})
    return results_file


# =============================================================================
# VISUALS
# =============================================================================

def plot_comparison(objective, params, title_suffix="", save_path=None):
    sol = objective._cached_solve(params, mode="dense")
    if not sol.success:
        print(f"  Skipping plot {title_suffix}: calibrated solve failed ({sol.message})")
        return
    y = np.maximum(sol.y, 0.0)

    sol_def = objective._cached_solve(None, mode="dense")
    if not sol_def.success:
        print(f"  Skipping plot {title_suffix}: default solve failed ({sol_def.message})")
        return
    y_def = np.maximum(sol_def.y, 0.0)

    plot_mets = [
        ("GLC", 0), ("LAC", 19), ("ATP", 35), ("ADP", 36),
        ("B23PG", 15), ("EGLC", 85), ("ELAC", 87), ("GSH", 70),
        ("GSSG", 71), ("GLU", 60), ("HYPX", 28), ("IMP", 42),
        ("MAL", 20), ("ADE", 25), ("PYR", 18), ("ALA", 58),
    ]

    fig, axes = plt.subplots(4, 4, figsize=(20, 16))
    fig.suptitle(f"MM Calibration Results {title_suffix}", fontsize=14, fontweight="bold")
    axes = axes.flatten()

    for i, (mname, midx) in enumerate(plot_mets):
        ax = axes[i]
        exp_key = mname.upper()
        if exp_key in objective.name_to_row:
            row = objective.name_to_row[exp_key]
            ax.scatter(
                objective.time_exp,
                objective.exp_values[row, :],
                color="black",
                s=40,
                zorder=5,
                label="Experimental",
                marker="o",
            )
        ax.plot(sol_def.t, y_def[midx], color="red", linewidth=1, alpha=0.5, linestyle="--", label="Default")
        ax.plot(sol.t, y[midx], color="blue", linewidth=2, label="Calibrated")
        ax.set_title(f"{mname} (idx {midx})", fontsize=10)
        ax.set_xlabel("Time (days)", fontsize=8)
        ax.set_ylabel("mM", fontsize=8)
        ax.legend(fontsize=6, loc="best")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  Plot saved: {save_path}")
    plt.close(fig)


# =============================================================================
# MAIN
# =============================================================================

def run_calibration(
    phases=None,
    n_trials=200,
    load_params=None,
    target_scope="all",
    param_scope="all",
    generate_plots=True,
    atp_focus=False,
    atp_floor=0.15,
    adp_floor=0.05,
    adenylate_target=0.65,
    atp_penalty_weight=8.0,
    pool_penalty_weight=10.0,
    global_trials=None,
    seed=42,
    t_max=46,
    curve_fit_strength=0.0,
    out_dir=None,
    optimization_strategy="legacy",
    parameter_classes=None,
    stage_plan=None,
):
    if phases is None:
        phases = [1, 2, 3]
    if global_trials is not None and global_trials < 0:
        raise ValueError("global_trials must be >= 0")
    if t_max <= 1:
        raise ValueError("t_max must be > 1")
    if stage_plan is None and optimization_strategy not in OPTIMIZATION_STRATEGY_CHOICES:
        raise ValueError(f"Unsupported optimization_strategy: {optimization_strategy}")

    resolved_global_trials = max(1, n_trials // 2) if global_trials is None else global_trials
    resolved_out_dir = Path(out_dir) if out_dir is not None else OUT_DIR

    resolved_stage_plan = resolve_stage_plan(
        optimization_strategy=optimization_strategy,
        phases=phases,
        param_scope=param_scope,
        target_scope=target_scope,
        n_trials=n_trials,
        global_trials=resolved_global_trials,
        seed=seed,
        parameter_classes=parameter_classes,
        atp_focus=atp_focus,
        atp_floor=atp_floor,
        adp_floor=adp_floor,
        adenylate_target=adenylate_target,
        atp_penalty_weight=atp_penalty_weight,
        pool_penalty_weight=pool_penalty_weight,
        curve_fit_strength=curve_fit_strength,
        stage_plan=stage_plan,
    )

    print("=" * 70)
    print("RBC Metabolic Model — ML-based MM Recalibration")
    print(f"Optimizer: {'optuna TPE (Bayesian)' if HAS_OPTUNA else 'scipy DE (fallback)'}")
    print(f"Phases: {phases}")
    print(f"Trials per phase: {n_trials}")
    if len(phases) > 1:
        print(f"Global refinement trials: {resolved_global_trials}")
    print(f"Target scope: {target_scope}")
    print(f"Parameter scope: {param_scope}")
    print(f"Optimization strategy: {optimization_strategy}")
    if parameter_classes is not None:
        print(f"Requested parameter classes: {normalize_name_list(parameter_classes)}")
    print(f"Resolved stages: {[stage['name'] for stage in resolved_stage_plan]}")
    print(f"Seed: {seed}")
    print(f"Calibration horizon: 1-{t_max} days")
    if curve_fit_strength > 0.0:
        print(f"Curve-fit curriculum strength: {curve_fit_strength}")
    print(f"Plots: {'enabled' if generate_plots else 'skipped'}")
    if atp_focus:
        print(
            "ATP focus: ON "
            f"(ATP floor={atp_floor}, ADP floor={adp_floor}, adenylate target={adenylate_target})"
        )
    print("=" * 70)

    print("\n[1/4] Loading data...")
    time_exp, exp_values, name_to_row = load_experimental_data()
    x0 = load_initial_conditions()
    print(f"  Experimental: {len(name_to_row)} metabolites, {len(time_exp)} timepoints")
    print(f"  Time range: {time_exp[0]}-{time_exp[-1]} days")

    resolved_out_dir.mkdir(parents=True, exist_ok=True)

    global_bundle = build_objective_bundle(
        x0, time_exp, exp_values, name_to_row,
        target_scope=target_scope,
        t_max=t_max,
        atp_focus=atp_focus,
        atp_floor=atp_floor,
        adp_floor=adp_floor,
        adenylate_target=adenylate_target,
        atp_penalty_weight=atp_penalty_weight,
        pool_penalty_weight=pool_penalty_weight,
        curve_fit_strength=curve_fit_strength,
    )
    global_primary = global_bundle["primary"]
    global_phase_objectives = global_bundle["phase_objectives"]
    global_monitor_objectives = global_bundle["monitor_objectives"]
    global_monitor_regression_limits = global_bundle["monitor_regression_limits"]
    protected_metric_keys = list(global_monitor_objectives.keys()) + ["endpoint_nrmse"]

    current_params = {}
    if load_params:
        with open(load_params, "r") as f:
            current_params = json.load(f)
        if "vmax_VEADE" in current_params:
            legacy_vmax_veade = current_params.pop("vmax_VEADE")
            current_params.setdefault("vmax_VEADE_fwd", legacy_vmax_veade)
            current_params.setdefault("vmax_VEADE_rev", legacy_vmax_veade)
        print(f"  Loaded {len(current_params)} params from {load_params}")

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

    current_metrics = evaluate_monitor_metrics(global_primary, global_monitor_objectives, current_params if current_params else {})
    baseline_loss = current_metrics["target"]
    print(f"\n  Baseline loss (nRMSE): {baseline_loss:.4f}")
    if protected_metric_keys:
        print(f"  Baseline protected metrics: {format_metric_summary(current_metrics, protected_metric_keys)}")

    results_tsv = append_results_row(
        resolved_out_dir,
        {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stage": "baseline",
            "target_scope": target_scope,
            "param_scope": param_scope,
            "baseline_target_loss": baseline_loss,
            "candidate_target_loss": baseline_loss,
            "joint_loss": current_metrics.get("joint", ""),
            "glycolysis_energy_loss": current_metrics.get("glycolysis_energy", ""),
            "nucleotide_purine_loss": current_metrics.get("nucleotide_purine", ""),
            "amino_redox_side_loss": current_metrics.get("amino_redox_side", ""),
            "extracellular_loss": current_metrics.get("extracellular", ""),
            "glycolysis_loss": current_metrics.get("glycolysis", ""),
            "endpoint_nrmse": current_metrics.get("endpoint_nrmse", ""),
            "status": "baseline",
            "description": load_params or "default",
        },
    )

    if generate_plots:
        plot_comparison(global_primary, current_params, "(Baseline)", save_path=str(resolved_out_dir / "baseline.png"))

    print("\n[2/4] Running optimization phases...")
    all_results = {}
    global_refinement_results = {}
    stage_reports = []
    stage_bundles = []
    optimized_phase_count = 0

    for stage_index, stage in enumerate(resolved_stage_plan, start=1):
        stage_name = stage["name"]
        stage_param_scope = stage["param_scope"]
        stage_parameter_classes = stage.get("parameter_classes")
        stage_identifiability = stage.get("identifiability_levels")
        stage_n_trials = int(stage.get("n_trials", n_trials))
        stage_global_trials = int(stage.get("global_trials", resolved_global_trials))
        stage_seed = int(stage.get("seed", seed))
        stage_start_loss = current_metrics["target"]

        stage_bundle = build_objective_bundle(
            x0, time_exp, exp_values, name_to_row,
            target_scope=stage["target_scope"],
            t_max=t_max,
            atp_focus=bool(stage["atp_focus"]),
            atp_floor=float(stage["atp_floor"]),
            adp_floor=float(stage["adp_floor"]),
            adenylate_target=float(stage["adenylate_target"]),
            atp_penalty_weight=float(stage["atp_penalty_weight"]),
            pool_penalty_weight=float(stage["pool_penalty_weight"]),
            curve_fit_strength=float(stage["curve_fit_strength"]),
        )
        stage_bundles.append(stage_bundle)

        stage_primary = stage_bundle["primary"]
        stage_phase_objectives = stage_bundle["phase_objectives"]

        stage_phase_labels = []
        stage_global_label = None

        print(f"\n{'#' * 70}")
        print(f"Stage {stage_index}: {stage_name}")
        print(f"  Stage target scope: {stage['target_scope']}")
        print(f"  Param scope: {stage_param_scope}")
        print(f"  Parameter classes: {stage_parameter_classes or 'all'}")
        print(f"  Identifiability: {stage_identifiability or 'all'}")
        print(f"  Trials per phase: {stage_n_trials}")
        print(f"  Global refinement trials: {stage_global_trials}")
        print(f"{'#' * 70}")

        for phase_num in stage["phases"]:
            phase_params = stage["phase_params"].get(phase_num, {})
            phase_name = PHASE_NAMES[phase_num]
            phase_objective = stage_phase_objectives.get(phase_num, stage_primary)

            phase_label = f"phase{phase_num}" if stage_name == "legacy" else f"{stage_name}.phase{phase_num}"
            phase_plot_name = f"phase{phase_num}.png" if stage_name == "legacy" else f"{stage_name}_phase{phase_num}.png"

            if not phase_params:
                print(f"\n{'=' * 60}")
                print(f"  Phase {phase_num}: {phase_name}")
                print(f"  Skipping (no parameters selected for stage '{stage_name}')")
                continue

            print(f"\n{'=' * 60}")
            print(f"  Phase {phase_num}: {phase_name}")
            print(f"  Objective: {phase_objective.objective_name} ({phase_objective.n_targets} targets)")
            print(f"  Optimizing {len(phase_params)} parameters...")
            print(f"  Parameters: {list(phase_params.keys())}")
            optimized_phase_count += 1

            t_start = time.time()
            pre_phase_params = current_params.copy()
            pre_phase_metrics = current_metrics.copy()

            if HAS_OPTUNA:
                best, best_val, _ = optimize_optuna(
                    phase_objective,
                    phase_params,
                    current_params,
                    n_trials=stage_n_trials,
                    study_name=f"{stage_name}_phase{phase_num}_{phase_objective.objective_name}",
                    seed=stage_seed,
                )
            else:
                best, best_val, _ = optimize_de(
                    phase_objective,
                    phase_params,
                    current_params,
                    max_iter=max(100, stage_n_trials // 3),
                )

            elapsed = time.time() - t_start

            candidate_params = pre_phase_params.copy()
            candidate_params.update(best)
            candidate_metrics = evaluate_monitor_metrics(global_primary, global_monitor_objectives, candidate_params)

            accepted, acceptance_reason = accept_monitor_metrics(
                pre_phase_metrics,
                candidate_metrics,
                monitor_regression_limits=global_monitor_regression_limits,
            )

            if accepted:
                current_params = candidate_params
                current_metrics = candidate_metrics

            new_loss = current_metrics["target"]

            print(f"\n  Phase {phase_num} Results:")
            print(f"    Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
            print(f"    Best phase-objective loss: {best_val:.4f}")
            print(f"    Cumulative loss: {new_loss:.4f}")
            print(f"    Improvement: {baseline_loss:.4f} -> {new_loss:.4f} ({(1-new_loss/baseline_loss)*100:.1f}%)")
            print(f"    Status: {'accepted' if accepted else 'discarded'}")
            print(f"    Decision: {acceptance_reason}")
            if protected_metric_keys:
                print(f"    Protected metrics: {format_metric_changes(pre_phase_metrics, candidate_metrics, protected_metric_keys)}")

            print("\n    Optimized parameters:")
            for pname, pval in sorted(best.items()):
                default = phase_params[pname][0]
                ratio = pval / default
                print(f"      {pname:25s}: {default:.6f} -> {pval:.6f} ({ratio:.2f}x)")

            if generate_plots:
                plot_comparison(global_primary, current_params, f"(After {phase_label})", save_path=str(resolved_out_dir / phase_plot_name))

            append_results_row(
                resolved_out_dir,
                {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "stage": phase_label,
                    "target_scope": stage["target_scope"],
                    "param_scope": stage_param_scope,
                    "baseline_target_loss": pre_phase_metrics["target"],
                    "candidate_target_loss": candidate_metrics["target"],
                    "joint_loss": candidate_metrics.get("joint", ""),
                    "glycolysis_energy_loss": candidate_metrics.get("glycolysis_energy", ""),
                    "nucleotide_purine_loss": candidate_metrics.get("nucleotide_purine", ""),
                    "amino_redox_side_loss": candidate_metrics.get("amino_redox_side", ""),
                    "extracellular_loss": candidate_metrics.get("extracellular", ""),
                    "glycolysis_loss": candidate_metrics.get("glycolysis", ""),
                    "endpoint_nrmse": candidate_metrics.get("endpoint_nrmse", ""),
                    "status": "keep" if accepted else "discard",
                    "description": acceptance_reason,
                },
            )

            all_results[phase_label] = {
                "stage_name": stage_name,
                "phase_num": phase_num,
                "phase_name": phase_name,
                "target_scope": stage["target_scope"],
                "param_scope": stage_param_scope,
                "parameter_classes": stage_parameter_classes,
                "identifiability_levels": stage_identifiability,
                "params": best,
                "loss": best_val,
                "candidate_loss": candidate_metrics["target"],
                "cumulative_loss": new_loss,
                "elapsed_s": elapsed,
                "accepted": accepted,
                "acceptance_reason": acceptance_reason,
                "candidate_metrics": candidate_metrics,
                "retained_metrics": current_metrics,
            }
            stage_phase_labels.append(phase_label)

        all_stage_params = {}
        for phase_num in stage["phases"]:
            all_stage_params.update(stage["phase_params"].get(phase_num, {}))

        if stage_global_trials > 0 and all_stage_params:
            stage_global_label = "global_refinement" if stage_name == "legacy" else f"{stage_name}.global_refinement"
            global_plot_name = "global_refinement.png" if stage_name == "legacy" else f"{stage_name}_global_refinement.png"

            print(f"\n{'=' * 60}")
            print("  Global Refinement Phase")
            print(f"  Joint optimization of {len(all_stage_params)} parameters ({stage_global_trials} trials)...")

            t_start = time.time()
            pre_global_params = current_params.copy()
            pre_global_metrics = current_metrics.copy()

            if HAS_OPTUNA:
                best, best_val, _ = optimize_optuna(
                    stage_primary,
                    all_stage_params,
                    current_params,
                    n_trials=stage_global_trials,
                    study_name=f"{stage_name}_global_refinement",
                    seed=stage_seed,
                )
            else:
                best, best_val, _ = optimize_de(
                    stage_primary,
                    all_stage_params,
                    current_params,
                    max_iter=max(1, stage_global_trials // 3),
                )

            elapsed = time.time() - t_start

            candidate_params = pre_global_params.copy()
            candidate_params.update(best)
            candidate_metrics = evaluate_monitor_metrics(global_primary, global_monitor_objectives, candidate_params)

            accepted, acceptance_reason = accept_monitor_metrics(
                pre_global_metrics,
                candidate_metrics,
                monitor_regression_limits=global_monitor_regression_limits,
            )

            if accepted:
                current_params.update(best)
                current_metrics = candidate_metrics
                print(f"\n  Global Refinement Results:")
                print(f"    Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
                print(
                    f"    Loss: {pre_global_metrics['target']:.4f} -> {candidate_metrics['target']:.4f} "
                    f"({(1-candidate_metrics['target']/pre_global_metrics['target'])*100:+.1f}%)"
                )
                print(f"    Decision: {acceptance_reason}")
            else:
                print(f"\n  Global refinement discarded ({pre_global_metrics['target']:.4f} -> {candidate_metrics['target']:.4f})")
                print(f"    Decision: {acceptance_reason}")
                print("    Keeping pre-refinement parameters.")

            if protected_metric_keys:
                print(f"    Protected metrics: {format_metric_changes(pre_global_metrics, candidate_metrics, protected_metric_keys)}")

            if generate_plots:
                plot_comparison(global_primary, current_params, f"(After {stage_global_label})", save_path=str(resolved_out_dir / global_plot_name))

            append_results_row(
                resolved_out_dir,
                {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "stage": stage_global_label,
                    "target_scope": stage["target_scope"],
                    "param_scope": stage_param_scope,
                    "baseline_target_loss": pre_global_metrics["target"],
                    "candidate_target_loss": candidate_metrics["target"],
                    "joint_loss": candidate_metrics.get("joint", ""),
                    "glycolysis_energy_loss": candidate_metrics.get("glycolysis_energy", ""),
                    "nucleotide_purine_loss": candidate_metrics.get("nucleotide_purine", ""),
                    "amino_redox_side_loss": candidate_metrics.get("amino_redox_side", ""),
                    "extracellular_loss": candidate_metrics.get("extracellular", ""),
                    "glycolysis_loss": candidate_metrics.get("glycolysis", ""),
                    "endpoint_nrmse": candidate_metrics.get("endpoint_nrmse", ""),
                    "status": "keep" if accepted else "discard",
                    "description": acceptance_reason,
                },
            )

            global_refinement_results[stage_global_label] = {
                "stage_name": stage_name,
                "target_scope": stage["target_scope"],
                "param_scope": stage_param_scope,
                "parameter_classes": stage_parameter_classes,
                "identifiability_levels": stage_identifiability,
                "params": best,
                "loss": best_val,
                "candidate_loss": candidate_metrics["target"],
                "cumulative_loss": current_metrics["target"],
                "elapsed_s": elapsed,
                "accepted": accepted,
                "acceptance_reason": acceptance_reason,
                "candidate_metrics": candidate_metrics,
                "retained_metrics": current_metrics,
            }

        stage_end_loss = current_metrics["target"]
        stage_reports.append(
            {
                "name": stage_name,
                "target_scope": stage["target_scope"],
                "param_scope": stage_param_scope,
                "parameter_classes": stage_parameter_classes,
                "identifiability_levels": stage_identifiability,
                "include_params": stage.get("include_params"),
                "exclude_params": stage.get("exclude_params"),
                "selected_params": stage["selected_param_names"],
                "phase_labels": stage_phase_labels,
                "global_refinement_label": stage_global_label,
                "n_trials": stage_n_trials,
                "global_trials": stage_global_trials,
                "atp_focus": stage["atp_focus"],
                "curve_fit_strength": stage["curve_fit_strength"],
                "start_loss": stage_start_loss,
                "end_loss": stage_end_loss,
                "accepted": bool(stage["selected_param_names"]) and stage_end_loss <= stage_start_loss + 1e-12,
            }
        )

    if optimized_phase_count == 0:
        raise ValueError(
            f"No parameters selected for phases={phases}, param_scope='{param_scope}', "
            f"and optimization_strategy='{optimization_strategy}'"
        )

    print("\n[3/4] Final evaluation...")
    current_metrics = evaluate_monitor_metrics(global_primary, global_monitor_objectives, current_params)
    final_loss = current_metrics["target"]
    print(f"  Final loss (nRMSE): {final_loss:.4f}")
    print(f"  Improvement: {baseline_loss:.4f} -> {final_loss:.4f} ({(1-final_loss/baseline_loss)*100:.1f}%)")
    if protected_metric_keys:
        print(f"  Final protected metrics: {format_metric_summary(current_metrics, protected_metric_keys)}")

    report = global_primary.detailed_report(current_params)
    print("\n  Per-metabolite nRMSE (top 15 worst):")
    for r in report[:15]:
        flag = " ***" if r["nrmse"] > 1.0 else ""
        print(
            f"    {r['name']:8s}: nRMSE={r['nrmse']:.3f}  RMSE={r['rmse']:.4f}  "
            f"sim={r['sim_final']:.4f}  exp={r['exp_final']:.4f}{flag}"
        )

    if generate_plots:
        plot_comparison(global_primary, current_params, "(Final Calibrated)", save_path=str(resolved_out_dir / "final_calibrated.png"))

    print("\n[4/4] Saving results...")

    params_file = resolved_out_dir / "best_params.json"
    if final_loss <= baseline_loss:
        with open(params_file, "w") as f:
            json.dump(current_params, f, indent=2)
        print(f"  Parameters: {params_file}")
    else:
        regressed_file = resolved_out_dir / "last_run_params.json"
        with open(regressed_file, "w") as f:
            json.dump(current_params, f, indent=2)
        print(f"  WARNING: Loss regressed ({baseline_loss:.4f} -> {final_loss:.4f})")
        print(f"  NOT overwriting {params_file}")
        print(f"  Regressed params saved to: {regressed_file}")

    append_results_row(
        resolved_out_dir,
        {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stage": "final",
            "target_scope": target_scope,
            "param_scope": param_scope,
            "baseline_target_loss": baseline_loss,
            "candidate_target_loss": final_loss,
            "joint_loss": current_metrics.get("joint", ""),
            "glycolysis_energy_loss": current_metrics.get("glycolysis_energy", ""),
            "nucleotide_purine_loss": current_metrics.get("nucleotide_purine", ""),
            "amino_redox_side_loss": current_metrics.get("amino_redox_side", ""),
            "extracellular_loss": current_metrics.get("extracellular", ""),
            "glycolysis_loss": current_metrics.get("glycolysis", ""),
            "endpoint_nrmse": current_metrics.get("endpoint_nrmse", ""),
            "status": "keep" if final_loss <= baseline_loss else "discard",
            "description": str(results_tsv),
        },
    )

    final_loss_breakdown = global_primary.loss_breakdown(current_params, mode="fast")

    report_file = resolved_out_dir / "calibration_report.json"
    with open(report_file, "w") as f:
        json.dump(
            {
                "baseline_loss": baseline_loss,
                "final_loss": final_loss,
                "improvement_pct": (1 - final_loss / baseline_loss) * 100,
                "n_trials_per_phase": n_trials,
                "optimizer": "optuna_TPE" if HAS_OPTUNA else "scipy_DE",
                "seed": seed,
                "t_max": t_max,
                "time_unit_assumption": "days",
                "curve_fit_strength": curve_fit_strength,
                "target_scope": target_scope,
                "param_scope": param_scope,
                "optimization_strategy": optimization_strategy,
                "parameter_classes": normalize_name_list(parameter_classes),
                "objective_weights": global_primary.objective_weights(),
                "best_loss_breakdown": global_primary.best_loss_breakdown,
                "final_loss_breakdown": final_loss_breakdown,
                "resolved_stage_plan": resolved_stage_plan,
                "target_metabolites": global_primary.target_names,
                "monitor_metrics": current_metrics,
                "results_tsv": str(results_tsv),
                "phases": all_results,
                "global_refinements": global_refinement_results,
                "stage_reports": stage_reports,
                "stages": stage_reports,
                "parameter_taxonomy": build_parameter_taxonomy(),
                "optimized_params": current_params,
                "per_metabolite": [r for r in report],
            },
            f,
            indent=2,
            default=str,
        )
    print(f"  Report: {report_file}")

    py_file = resolved_out_dir / "best_params.py"
    with open(py_file, "w") as f:
        f.write("# Optimized MM parameters from ML calibration\n")
        f.write(f"# Baseline nRMSE: {baseline_loss:.4f}\n")
        f.write(f"# Final nRMSE:    {final_loss:.4f}\n")
        f.write(f"# Improvement:    {(1-final_loss/baseline_loss)*100:.1f}%\n\n")
        f.write("CALIBRATED_PARAMS = {\n")
        for pname, pval in sorted(current_params.items()):
            f.write(f"    '{pname}': {pval:.8f},\n")
        f.write("}\n")
    print(f"  Python dict: {py_file}")

    print(f"\n{'=' * 70}")
    print("Calibration complete!")
    print(
        "Total objective evaluations: "
        f"{total_objective_calls(global_primary, global_phase_objectives, global_monitor_objectives, stage_bundles)}"
    )
    print(f"Final nRMSE: {final_loss:.4f}")
    print(f"{'=' * 70}")

    return current_params, final_loss


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ML-based MM recalibration")
    parser.add_argument("--phases", type=str, default="1,2,3", help="Comma-separated phase numbers")
    parser.add_argument("--n-trials", type=int, default=150, help="Optimization trials per phase")
    parser.add_argument(
        "--global-trials",
        type=int,
        default=None,
        help="Global refinement trials after stage phases (default: n_trials // 2; set 0 to skip)",
    )
    parser.add_argument("--load-params", type=str, default=None, help="Path to JSON file with initial parameters")
    parser.add_argument(
        "--target-scope",
        type=str,
        default="all",
        choices=["all", "extracellular", "glycolysis", "glycolysis_terminal", "glycolysis_extracellular", "core_glycolysis_energy"],
        help="Calibration target scope",
    )
    parser.add_argument(
        "--param-scope",
        type=str,
        default="all",
        choices=["all", "transport_only", "eade_focus", "glycolysis_mm", "core_km", "core_lower_glycolysis_probe", "glycolysis_terminal", "extracellular_coupled", "glycolysis_extracellular", "purine_transport_narrow"],
        help="Parameter scope",
    )
    parser.add_argument("--skip-plots", action="store_true", help="Skip comparison plots")
    parser.add_argument("--atp-focus", action="store_true", help="Enable ATP-focused penalties")
    parser.add_argument("--atp-floor", type=float, default=0.15, help="Minimum ATP floor target")
    parser.add_argument("--adp-floor", type=float, default=0.05, help="Minimum ADP floor target")
    parser.add_argument("--adenylate-target", type=float, default=0.65, help="Target final adenylate pool retention ratio")
    parser.add_argument("--atp-penalty-weight", type=float, default=8.0, help="Penalty weight for ATP/ADP floor violations")
    parser.add_argument("--pool-penalty-weight", type=float, default=10.0, help="Penalty weight for adenylate pool retention violation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--t-max", type=float, default=46.0, help="Calibration horizon in days")
    parser.add_argument("--curve-fit-strength", type=float, default=0.0, help="Curve-fit curriculum strength")
    parser.add_argument("--out-dir", type=str, default=None, help="Optional output directory")
    parser.add_argument(
        "--optimization-strategy",
        type=str,
        default="legacy",
        choices=sorted(OPTIMIZATION_STRATEGY_CHOICES),
        help="Explicit optimization strategy",
    )
    parser.add_argument(
        "--parameter-classes",
        type=str,
        default=None,
        help="Optional comma-separated parameter classes to restrict optimization, e.g. vmax,km,transport",
    )
    parser.add_argument(
        "--stage-plan-file",
        type=str,
        default=None,
        help="Optional JSON file containing an explicit stage_plan array",
    )

    args = parser.parse_args()
    phases = [int(p) for p in args.phases.split(",") if p.strip()]

    stage_plan = None
    if args.stage_plan_file:
        with open(args.stage_plan_file, "r") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict) and "stage_plan" in loaded:
            stage_plan = loaded["stage_plan"]
        elif isinstance(loaded, list):
            stage_plan = loaded
        else:
            raise ValueError("stage_plan file must be a JSON array or a JSON object with a 'stage_plan' field")

    run_calibration(
        phases=phases,
        n_trials=args.n_trials,
        global_trials=args.global_trials,
        load_params=args.load_params,
        target_scope=args.target_scope,
        param_scope=args.param_scope,
        generate_plots=not args.skip_plots,
        atp_focus=args.atp_focus,
        atp_floor=args.atp_floor,
        adp_floor=args.adp_floor,
        adenylate_target=args.adenylate_target,
        atp_penalty_weight=args.atp_penalty_weight,
        pool_penalty_weight=args.pool_penalty_weight,
        seed=args.seed,
        t_max=args.t_max,
        curve_fit_strength=args.curve_fit_strength,
        out_dir=args.out_dir,
        optimization_strategy=args.optimization_strategy,
        parameter_classes=args.parameter_classes,
        stage_plan=stage_plan,
    )