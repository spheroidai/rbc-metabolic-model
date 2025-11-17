"""
Refactored RBC ODE system with mechanistic transport and intracellular pH.
- Keeps 108 states (indices match your existing model layout).
- Introduces principled GLUT1 (glucose) and MCT1 (lactate/H+) transport.
- Includes adenylate and redox pools, GPX detox, and buffered pH dynamics.
Author: ChatGPT (refactor for stability + interpretability)
"""

from dataclasses import dataclass
import numpy as np
from typing import Dict, Any, Tuple
from math import log10
from scipy.integrate import solve_ivp

# ------------------------- Utilities -------------------------

def mm(s, km, h=1.0):
    s = max(float(s), 0.0)
    km = max(float(km), 1e-12)
    if h != 1.0:
        return (s**h)/(km**h + s**h)
    return s/(km + s)

def safe_ratio(a, b, eps=1e-9):
    return float(a)/max(float(b), eps)

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# ------------------------- Parameters -------------------------

@dataclass
class CoreParams:
    # GLUT1 bidirectional transport (EGLC <-> GLC)
    Vglut_in: float = 0.08     # mM/day
    Vglut_out: float = 0.003   # mM/day
    Km_glc_e: float = 5.0
    Km_glc_i: float = 1.0

    # Hexokinase
    Vhk: float = 0.25
    Km_hk: float = 0.2

    # PFK (lumped control of upper glycolysis)
    Vpfk: float = 0.20
    Km_pfk: float = 0.15

    # PK
    Vpk: float = 0.25
    Km_pk: float = 0.15

    # LDH
    Vldh_f: float = 0.30
    Vldh_r: float = 0.05
    Km_pyr: float = 0.15
    Km_lac: float = 0.5

    # MCT1 bidirectional transport (ELAC <-> LAC), pH-coupled
    Vmct_in: float = 0.02
    Vmct_out: float = 0.09
    Km_lac_e: float = 5.0
    Km_lac_i: float = 1.0

    # GPX (GSH + H2O2 -> GSSG)
    Vgpx: float = 0.15
    Km_gsh: float = 0.2
    Km_h2o2: float = 0.05

    # Buffer capacity for pH (beta, mM per pH unit)
    beta: float = 35.0

    # Homeostatic pull for pHi
    pH_set: float = 7.20
    pH_tau: float = 0.8  # 1/day

# ------------------------- ODE System -------------------------

class RBCEq:
    """
    Compact, interpretable RBC core with 108 states.
    We evolve only the key connected pieces; all other states are carried through (dx=0).
    Index map (subset):
      13 ATP, 6 ADP, 9 AMP (derived, no ODE); total adenylate A_tot set in ic().
      34 GLC (intracellular), 85 EGLC (extracellular)
      30 G6P, 28 F6P
      67 PEP, 69 PYR, 51 LAC
      87 ELAC (extracellular lactate)
      42 GSH, 43 GSSG (derived by mass), 106 H2O2
      107 pHi
    """
    def __init__(self, core: CoreParams):
        self.p = core
        # Fixed pools (reasonable defaults, editable in ic())
        self.A_tot = 1.5     # mM (ATP+ADP+AMP)
        self.NAD_tot = 0.5   # mM (NAD + NADH)
        self.NADP_tot = 0.2  # mM (NADP + NADPH)
        self.GSH_tot = 2.0   # mM (GSH + 2 GSSG)

    # ------- helper to enforce array length and pull named species
    def _extract(self, x: np.ndarray) -> Dict[str, float]:
        z = np.zeros(108, dtype=float)
        z[:min(len(x),108)] = x[:min(len(x),108)]
        # Pools
        ATP = max(z[13], 1e-9)
        ADP = max(z[6], 1e-9)
        AMP = max(self.A_tot - ATP - ADP, 0.0)
        NAD = max(z[56] if len(z)>56 else 0.25, 1e-9)
        NADH = max(self.NAD_tot - NAD, 0.0)
        NADP = max(z[58] if len(z)>58 else 0.05, 1e-9)
        NADPH = max(self.NADP_tot - NADP, 0.0)
        GSH = max(z[42] if len(z)>42 else 1.8, 1e-9)
        GSSG = max( (self.GSH_tot - GSH)/2.0, 0.0)

        return dict(
            z=z, ATP=ATP, ADP=ADP, AMP=AMP,
            NAD=NAD, NADH=NADH, NADP=NADP, NADPH=NADPH,
            GSH=GSH, GSSG=GSSG
        )

    # ------- main RHS
    def rhs(self, t: float, x: np.ndarray) -> np.ndarray:
        p = self.p
        S = self._extract(x)
        z = S["z"]

        # Named species (local aliases)
        ATP, ADP = S["ATP"], S["ADP"]
        NAD, NADH = S["NAD"], S["NADH"]
        GSH, GSSG = S["GSH"], S["GSSG"]

        GLC  = max(z[34], 0.0)
        EGLC = max(z[85], 0.0)
        G6P  = max(z[30], 0.0)
        F6P  = max(z[28], 0.0)
        PEP  = max(z[67], 0.0)
        PYR  = max(z[69], 0.0)
        LAC  = max(z[51], 0.0)
        ELAC = max(z[87], 0.0)
        H2O2 = max(z[106], 0.0)
        pHi  = clamp(z[107], 6.2, 7.8)  # keep in sane bounds during math

        # -------- Transport
        # GLUT1 (EGLC -> GLC) - allow small backflux; weak pH modulation
        pH_fac_in  = 1.0 + 0.3*(pHi - 7.0)
        pH_fac_out = 1.0 + 0.3*(7.40 - 7.0)  # ext pH ~ 7.4

        v_glut_in  = p.Vglut_in  * mm(EGLC, p.Km_glc_e) * pH_fac_in
        v_glut_out = p.Vglut_out * mm(GLC,  p.Km_glc_i) * pH_fac_out
        V_GLUT = v_glut_in - v_glut_out  # positive: net influx

        # MCT1 (ELAC <-> LAC) with H+ symport – lower pHi favors efflux
        mct_fac_out = 1.0 + 0.6*max(0.0, 7.2 - pHi)  # acid promotes efflux
        mct_fac_in  = 1.0 + 0.2*max(0.0, pHi - 7.2)  # base slightly favors uptake
        v_mct_in  = p.Vmct_in  * mm(ELAC, p.Km_lac_e) * mct_fac_in
        v_mct_out = p.Vmct_out * mm(LAC,  p.Km_lac_i) * mct_fac_out
        V_MCT = v_mct_in - v_mct_out  # positive: net ELAC->LAC

        # -------- Core glycolysis
        # HK: GLC + ATP -> G6P + ADP (+ H+)
        v_hk = p.Vhk * mm(GLC, p.Km_hk) * mm(ATP, 0.2)

        # PFK: F6P + ATP -> ... (+ H+)
        # Use F6P generated by PGI from G6P (simple equilibration)
        v_pgi = 0.8*(G6P - F6P)  # fast isomerase surrogate
        F6P_eff = max(F6P + v_pgi*0.1, 0.0)
        v_pfk = p.Vpfk * mm(F6P_eff, p.Km_pfk) * mm(ATP, 0.2)

        # PK: PEP + ADP -> PYR + ATP
        # Build PEP from upper glycolysis; keep a simple funnel: F6P -> ... -> PEP
        v_upper = 0.6*v_pfk
        v_pep_form = v_upper
        v_pk = p.Vpk * mm(PEP + v_pep_form*0.1, p.Km_pk) * mm(ADP, 0.2)

        # LDH: PYR + NADH <-> LAC + NAD+
        v_ldh_f = p.Vldh_f * mm(PYR, p.Km_pyr) * mm(NADH, 0.05)
        v_ldh_r = p.Vldh_r * mm(LAC, p.Km_lac) * mm(NAD,  0.05)
        v_ldh = v_ldh_f - v_ldh_r

        # -------- GPX (detox)
        v_gpx = p.Vgpx * mm(GSH, p.Km_gsh) * mm(H2O2, p.Km_h2o2)

        # -------- Differential equations (only for touched states)
        dx = np.zeros_like(z)

        # Glucose compartments
        dx[85] += -V_GLUT                 # EGLC
        dx[34] += +V_GLUT - v_hk          # GLC(i)

        # Upper glycolysis
        dx[30] += +v_hk - v_pgi           # G6P
        dx[28] += +v_pgi - v_pfk          # F6P

        # PEP/PYR/ATP/ADP/Lactate
        dx[67] += +v_pep_form - v_pk      # PEP
        dx[69] += +v_pk - v_ldh           # PYR
        dx[51] += +v_ldh + V_MCT          # LAC(i)
        dx[87] += -V_MCT                  # ELAC

        # Adenylates: explicit ATP/ADP; AMP from pool (no ODE)
        # ATP produced by PK, consumed by HK/PFK; ADP opposite
        dx[13] += +v_pk - v_hk - v_pfk
        dx[6]  += -dx[13]                 # conserve A_tot in ODE sense

        # Redox: simple NAD/NADH couple via LDH
        dx[56] += +v_ldh                  # NAD increases when LDH forward (NADH->NAD)
        # NADH is pool-derived => no dx[57]

        # GSH decreases with GPX; GSSG comes from pool
        dx[42] += -2.0*v_gpx              # 2 GSH per H2O2
        dx[106]+= -v_gpx + 1e-4           # small basal ROS production minus GPX

        # -------- Intracellular pH
        # Sources of H+ (acid): HK, PFK, LDH forward; GPX neutral-ish (ignore)
        acid = 0.7*v_hk + 0.7*v_pfk + 0.9*max(v_ldh, 0.0)
        # Sinks: ATP synthesis (PK), LDH reverse, lactate/H+ efflux via MCT (v_mct_out)
        base = 0.8*v_pk + 0.9*max(-v_ldh, 0.0) + 0.6*max(v_mct_out, 0.0)

        net_H = acid - base  # mM/day of "H+" equivalent
        dpH = -(net_H / max(p.beta,1e-6)) + (p.pH_set - pHi)/max(p.pH_tau,1e-3)

        # Soft bounds
        if pHi < 6.8:   dpH += 3.0*(6.8 - pHi)
        if pHi > 7.6:   dpH += 3.0*(7.6 - pHi)

        dx[107] = dpH

        return dx

    # ------------- Public integrate API -------------
    def integrate(self, t_span: Tuple[float,float], x0: np.ndarray, t_eval: np.ndarray, rtol=1e-6, atol=1e-9):
        # Ensure 108-length x0
        x_init = np.zeros(108, dtype=float)
        x_init[:min(len(x0),108)] = x0[:min(len(x0),108)]
        sol = solve_ivp(self.rhs, t_span, x_init, method="BDF", t_eval=t_eval, rtol=rtol, atol=atol, vectorized=False)
        return sol

# ------------------------- IC helper -------------------------

def default_ic() -> np.ndarray:
    """Reasonable 108-length initial condition with extracellular pools populated."""
    x = np.zeros(108, dtype=float)
    # Key intracellular
    x[13] = 1.1   # ATP
    x[6]  = 0.35  # ADP
    x[34] = 1.5   # GLC(i)
    x[30] = 0.3   # G6P
    x[28] = 0.2   # F6P
    x[67] = 0.2   # PEP
    x[69] = 0.6   # PYR
    x[51] = 1.0   # LAC(i)
    x[42] = 1.6   # GSH
    x[56] = 0.30  # NAD
    x[58] = 0.08  # NADP
    x[106]= 0.02  # H2O2
    x[107]= 7.20  # pHi
    # Extracellular
    x[85] = 24.0  # EGLC (mM)
    x[87] = 6.0   # ELAC (mM)
    return x

# ------------------------- Export convenience -------------------------

def simulate_core(params: Dict[str, float], t_eval: np.ndarray, x0: np.ndarray=None):
    core = CoreParams(**params)
    model = RBCEq(core)
    if x0 is None:
        x0 = default_ic()
    t_span = (float(t_eval[0]), float(t_eval[-1]))
    sol = model.integrate(t_span, x0, t_eval)
    return sol

def test_refactored_model():
    """Test the refactored RBC model."""
    print("Testing Refactored RBC Model")
    print("=" * 30)
    
    # Test simulation
    t_eval = np.linspace(0, 5, 20)
    x0 = default_ic()
    
    # Create model with default parameters
    core = CoreParams()
    model = RBCEq(core)
    
    sol = model.integrate((0.0, 5.0), x0, t_eval)
    
    if sol.success:
        print(f"✓ Refactored model test successful!")
        print(f"  Solution shape: {sol.y.shape}")
        print(f"  Time points: {len(sol.t)}")
        
        # Show key metabolite trajectories
        print("\nKey metabolite concentrations:")
        print(f"  GLC: {sol.y[34, 0]:.3f} → {sol.y[34, -1]:.3f}")
        print(f"  LAC: {sol.y[51, 0]:.3f} → {sol.y[51, -1]:.3f}")
        print(f"  ATP: {sol.y[13, 0]:.3f} → {sol.y[13, -1]:.3f}")
        print(f"  pHi: {sol.y[107, 0]:.3f} → {sol.y[107, -1]:.3f}")
        print(f"  EGLC: {sol.y[85, 0]:.3f} → {sol.y[85, -1]:.3f}")
        print(f"  ELAC: {sol.y[87, 0]:.3f} → {sol.y[87, -1]:.3f}")
        
        return sol
    else:
        print("✗ Refactored model test failed")
        return None

if __name__ == "__main__":
    test_refactored_model()
