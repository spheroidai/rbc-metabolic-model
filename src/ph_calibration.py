"""
pH Transport Parameter Calibration Module

Provides tools for calibrating and validating H+ transport parameters in RBC model:
- K_DIFF_H: Passive H+ diffusion coefficient
- K_NHE: Na+/H+ exchanger activity
- K_AE1: Cl-/HCO3- exchanger (Band 3) activity
- BETA_BUFFER: Intracellular buffering capacity

Features:
---------
1. Parameter sensitivity analysis
2. Response time validation (pHi lag vs pHe)
3. Equilibrium pH ratio validation (pHi/pHe ≈ 0.95-0.98)
4. Automated parameter optimization
5. Validation against experimental data

Author: Jorgelindo da Veiga
Date: 2025-11-15
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize, differential_evolution
from scipy.integrate import solve_ivp
from typing import Dict, Tuple, List, Optional, Callable
import warnings
warnings.filterwarnings('ignore')


# Default transport parameters (from equadiff_brodbar.py)
DEFAULT_PARAMS = {
    'K_DIFF_H': 0.03,      # Passive H+ diffusion (pH units/min)
    'K_NHE': 0.7,          # Na+/H+ exchanger
    'K_AE1': 1.5,          # Cl-/HCO3- exchanger (Band 3)
    'BETA_BUFFER': 70.0    # Buffering capacity (mM/pH unit)
}

# Physiological ranges for validation
PHYSIOLOGICAL_RANGES = {
    'pHi_rest': (7.15, 7.25),           # Normal intracellular pH
    'pHe_rest': (7.35, 7.45),           # Normal extracellular pH
    'pHi_pHe_ratio': (0.95, 0.98),      # pHi/pHe at equilibrium
    'response_time_min': 5.0,           # Min lag time (minutes)
    'response_time_max': 15.0,          # Max lag time (minutes)
    'equilibration_time': 30.0          # Time to reach 95% equilibrium (min)
}


class PhTransportCalibrator:
    """
    Calibrates pH transport parameters for realistic RBC dynamics.
    """
    
    def __init__(self, initial_params: Optional[Dict[str, float]] = None):
        """
        Initialize calibrator with transport parameters.
        
        Parameters:
        -----------
        initial_params : dict, optional
            Initial guess for transport parameters
        """
        self.params = initial_params if initial_params else DEFAULT_PARAMS.copy()
        self.calibration_history = []
        
    def simulate_pH_step_response(self, params: Dict[str, float], 
                                  pHe_initial: float = 7.4,
                                  pHe_final: float = 7.0,
                                  t_max: float = 60.0,
                                  n_points: int = 600) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Simulate pHi response to step change in pHe.
        
        Parameters:
        -----------
        params : dict
            Transport parameters to test
        pHe_initial : float
            Initial extracellular pH
        pHe_final : float
            Final extracellular pH (after step)
        t_max : float
            Simulation time (minutes)
        n_points : int
            Number of time points
            
        Returns:
        --------
        tuple : (times, pHi, pHe)
        """
        # Extract parameters
        K_DIFF = params['K_DIFF_H']
        K_NHE = params['K_NHE']
        K_AE1 = params['K_AE1']
        BETA = params['BETA_BUFFER']
        
        # Define ODE for pHi dynamics (simplified)
        def dpHi_dt(t, pHi):
            # Current pHe (step function)
            pHe = pHe_final if t > 0 else pHe_initial
            
            # H+ transport fluxes
            J_diff = K_DIFF * (pHe - pHi)                    # Passive diffusion
            J_NHE = K_NHE * (7.2 - pHi) * (pHe - 7.4)       # Na+/H+ exchanger (activated by low pHi)
            J_AE1 = K_AE1 * (pHe - pHi) * 0.5               # Cl-/HCO3- exchanger
            
            # Net H+ influx (converted to pH change)
            dpHi = (J_diff + J_NHE + J_AE1) / BETA
            
            return dpHi
        
        # Initial condition
        pHi0 = pHe_initial - 0.2  # pHi typically 0.2 units below pHe
        
        # Solve ODE
        times_min = np.linspace(0, t_max, n_points)
        solution = solve_ivp(
            dpHi_dt,
            (0, t_max),
            [pHi0],
            t_eval=times_min,
            method='LSODA',
            rtol=1e-6,
            atol=1e-8
        )
        
        if not solution.success:
            print(f"Warning: Integration failed: {solution.message}")
            return times_min, np.full_like(times_min, pHi0), np.full_like(times_min, pHe_initial)
        
        pHi = solution.y[0]
        pHe = np.where(times_min > 0, pHe_final, pHe_initial)
        
        return times_min, pHi, pHe
    
    def calculate_response_time(self, times: np.ndarray, pHi: np.ndarray, 
                               pHe: np.ndarray) -> Dict[str, float]:
        """
        Calculate characteristic response times from pH time series.
        
        Parameters:
        -----------
        times : np.ndarray
            Time points (minutes)
        pHi : np.ndarray
            Intracellular pH
        pHe : np.ndarray
            Extracellular pH
            
        Returns:
        --------
        dict : Response time metrics
        """
        # Find step time (when pHe changes)
        step_idx = np.where(np.diff(pHe) != 0)[0]
        if len(step_idx) == 0:
            step_idx = 0
        else:
            step_idx = step_idx[0]
        
        pHi_initial = pHi[step_idx]
        pHi_final = pHi[-1]
        pHe_final = pHe[-1]
        
        # Time to 50% response (t50)
        target_50 = pHi_initial + 0.5 * (pHi_final - pHi_initial)
        idx_50 = np.argmin(np.abs(pHi - target_50))
        t50 = times[idx_50] - times[step_idx]
        
        # Time to 90% response (t90)
        target_90 = pHi_initial + 0.9 * (pHi_final - pHi_initial)
        idx_90 = np.argmin(np.abs(pHi - target_90))
        t90 = times[idx_90] - times[step_idx]
        
        # Time to 95% response (t95)
        target_95 = pHi_initial + 0.95 * (pHi_final - pHi_initial)
        idx_95 = np.argmin(np.abs(pHi - target_95))
        t95 = times[idx_95] - times[step_idx]
        
        # Equilibrium pHi/pHe ratio
        pHi_pHe_ratio = pHi_final / pHe_final
        
        return {
            't50_min': t50,
            't90_min': t90,
            't95_min': t95,
            'pHi_final': pHi_final,
            'pHe_final': pHe_final,
            'pHi_pHe_ratio': pHi_pHe_ratio
        }
    
    def validate_parameters(self, params: Dict[str, float], 
                          verbose: bool = True) -> Dict[str, bool]:
        """
        Validate transport parameters against physiological criteria.
        
        Parameters:
        -----------
        params : dict
            Transport parameters to validate
        verbose : bool
            Print validation results
            
        Returns:
        --------
        dict : Validation results (True/False for each criterion)
        """
        # Simulate step response
        times, pHi, pHe = self.simulate_pH_step_response(params)
        
        # Calculate metrics
        metrics = self.calculate_response_time(times, pHi, pHe)
        
        # Validation criteria
        validation = {
            'response_time_ok': (
                PHYSIOLOGICAL_RANGES['response_time_min'] <= metrics['t50_min'] <= 
                PHYSIOLOGICAL_RANGES['response_time_max']
            ),
            'equilibration_time_ok': (
                metrics['t95_min'] <= PHYSIOLOGICAL_RANGES['equilibration_time']
            ),
            'pHi_pHe_ratio_ok': (
                PHYSIOLOGICAL_RANGES['pHi_pHe_ratio'][0] <= metrics['pHi_pHe_ratio'] <= 
                PHYSIOLOGICAL_RANGES['pHi_pHe_ratio'][1]
            ),
            'pHi_range_ok': (
                PHYSIOLOGICAL_RANGES['pHi_rest'][0] <= metrics['pHi_final'] <= 
                PHYSIOLOGICAL_RANGES['pHi_rest'][1]
            )
        }
        
        validation['all_ok'] = all(validation.values())
        
        if verbose:
            print("\n" + "="*60)
            print("PARAMETER VALIDATION RESULTS")
            print("="*60)
            print(f"\nTransport Parameters:")
            for key, val in params.items():
                print(f"  {key}: {val:.4f}")
            
            print(f"\nResponse Metrics:")
            print(f"  t50 (50% response): {metrics['t50_min']:.2f} min")
            print(f"  t90 (90% response): {metrics['t90_min']:.2f} min")
            print(f"  t95 (95% response): {metrics['t95_min']:.2f} min")
            print(f"  pHi/pHe ratio: {metrics['pHi_pHe_ratio']:.4f}")
            print(f"  Final pHi: {metrics['pHi_final']:.3f}")
            
            print(f"\nValidation Criteria:")
            status_icon = lambda x: "✓" if x else "✗"
            print(f"  {status_icon(validation['response_time_ok'])} Response time (5-15 min): "
                  f"{metrics['t50_min']:.2f} min")
            print(f"  {status_icon(validation['equilibration_time_ok'])} Equilibration time (<30 min): "
                  f"{metrics['t95_min']:.2f} min")
            print(f"  {status_icon(validation['pHi_pHe_ratio_ok'])} pHi/pHe ratio (0.95-0.98): "
                  f"{metrics['pHi_pHe_ratio']:.4f}")
            print(f"  {status_icon(validation['pHi_range_ok'])} pHi in physiological range: "
                  f"{metrics['pHi_final']:.3f}")
            
            print(f"\n{'='*60}")
            if validation['all_ok']:
                print("✓ ALL VALIDATION CRITERIA PASSED")
            else:
                print("✗ SOME VALIDATION CRITERIA FAILED")
            print(f"{'='*60}\n")
        
        return validation
    
    def sensitivity_analysis(self, param_name: str, 
                           param_range: Tuple[float, float],
                           n_points: int = 20) -> pd.DataFrame:
        """
        Perform sensitivity analysis for a single parameter.
        
        Parameters:
        -----------
        param_name : str
            Name of parameter to vary
        param_range : tuple
            (min, max) range for parameter
        n_points : int
            Number of points to test
            
        Returns:
        --------
        pd.DataFrame : Sensitivity analysis results
        """
        param_values = np.linspace(param_range[0], param_range[1], n_points)
        
        results = []
        for val in param_values:
            params = self.params.copy()
            params[param_name] = val
            
            # Simulate
            times, pHi, pHe = self.simulate_pH_step_response(params)
            metrics = self.calculate_response_time(times, pHi, pHe)
            
            results.append({
                param_name: val,
                't50_min': metrics['t50_min'],
                't90_min': metrics['t90_min'],
                't95_min': metrics['t95_min'],
                'pHi_pHe_ratio': metrics['pHi_pHe_ratio'],
                'pHi_final': metrics['pHi_final']
            })
        
        return pd.DataFrame(results)
    
    def optimize_parameters(self, target_t50: float = 10.0,
                          target_ratio: float = 0.97,
                          method: str = 'differential_evolution') -> Dict[str, float]:
        """
        Optimize transport parameters to match target metrics.
        
        Parameters:
        -----------
        target_t50 : float
            Target response time at 50% (minutes)
        target_ratio : float
            Target pHi/pHe equilibrium ratio
        method : str
            Optimization method ('minimize' or 'differential_evolution')
            
        Returns:
        --------
        dict : Optimized parameters
        """
        print(f"\n{'='*60}")
        print("PARAMETER OPTIMIZATION")
        print(f"{'='*60}")
        print(f"Target t50: {target_t50:.1f} min")
        print(f"Target pHi/pHe ratio: {target_ratio:.3f}")
        print(f"Method: {method}\n")
        
        def objective(x):
            """Objective function to minimize."""
            params = {
                'K_DIFF_H': x[0],
                'K_NHE': x[1],
                'K_AE1': x[2],
                'BETA_BUFFER': x[3]
            }
            
            # Simulate
            times, pHi, pHe = self.simulate_pH_step_response(params)
            metrics = self.calculate_response_time(times, pHi, pHe)
            
            # Penalize deviations from targets
            error_t50 = (metrics['t50_min'] - target_t50)**2
            error_ratio = (metrics['pHi_pHe_ratio'] - target_ratio)**2 * 100
            
            # Penalize out-of-range values
            penalty = 0
            if metrics['t50_min'] < 5 or metrics['t50_min'] > 15:
                penalty += 100
            if metrics['pHi_pHe_ratio'] < 0.95 or metrics['pHi_pHe_ratio'] > 0.98:
                penalty += 100
            
            return error_t50 + error_ratio + penalty
        
        # Parameter bounds
        bounds = [
            (0.01, 0.1),   # K_DIFF_H
            (0.1, 2.0),    # K_NHE
            (0.5, 3.0),    # K_AE1
            (30.0, 150.0)  # BETA_BUFFER
        ]
        
        # Initial guess
        x0 = [self.params['K_DIFF_H'], self.params['K_NHE'], 
              self.params['K_AE1'], self.params['BETA_BUFFER']]
        
        # Optimize
        if method == 'differential_evolution':
            result = differential_evolution(objective, bounds, seed=42, 
                                          maxiter=100, disp=True)
        else:
            result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
        
        # Extract optimized parameters
        optimized = {
            'K_DIFF_H': result.x[0],
            'K_NHE': result.x[1],
            'K_AE1': result.x[2],
            'BETA_BUFFER': result.x[3]
        }
        
        print(f"\nOptimization {'converged' if result.success else 'did not converge'}")
        print(f"Final objective value: {result.fun:.4f}\n")
        
        # Validate optimized parameters
        self.validate_parameters(optimized, verbose=True)
        
        return optimized
    
    def plot_sensitivity_results(self, sensitivity_data: Dict[str, pd.DataFrame],
                                output_path: str = "sensitivity_analysis.png"):
        """
        Plot sensitivity analysis results for all parameters.
        
        Parameters:
        -----------
        sensitivity_data : dict
            Dictionary of DataFrames from sensitivity_analysis()
        output_path : str
            Path to save plot
        """
        n_params = len(sensitivity_data)
        fig, axes = plt.subplots(2, n_params, figsize=(4*n_params, 8))
        
        if n_params == 1:
            axes = axes.reshape(-1, 1)
        
        for idx, (param_name, df) in enumerate(sensitivity_data.items()):
            # Plot 1: Response times
            ax1 = axes[0, idx]
            ax1.plot(df[param_name], df['t50_min'], 'b-', linewidth=2, label='t50', marker='o')
            ax1.plot(df[param_name], df['t90_min'], 'r-', linewidth=2, label='t90', marker='s')
            ax1.axhspan(5, 15, alpha=0.2, color='green', label='Target range (t50)')
            ax1.set_xlabel(param_name, fontsize=12)
            ax1.set_ylabel('Response Time (min)', fontsize=12)
            ax1.set_title(f'Sensitivity: {param_name}', fontsize=13, fontweight='bold')
            ax1.legend(loc='best', fontsize=10)
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: pHi/pHe ratio
            ax2 = axes[1, idx]
            ax2.plot(df[param_name], df['pHi_pHe_ratio'], 'g-', linewidth=2, marker='d')
            ax2.axhspan(0.95, 0.98, alpha=0.2, color='green', label='Target range')
            ax2.set_xlabel(param_name, fontsize=12)
            ax2.set_ylabel('pHi/pHe Ratio', fontsize=12)
            ax2.set_title(f'Equilibrium Ratio vs {param_name}', fontsize=13, fontweight='bold')
            ax2.legend(loc='best', fontsize=10)
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Sensitivity analysis plot saved: {output_path}")


def run_calibration_workflow(output_dir: str = "html/brodbar/ph_calibration"):
    """
    Run complete calibration workflow with default parameters.
    
    Parameters:
    -----------
    output_dir : str
        Directory for saving calibration results
    """
    from pathlib import Path
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("pH TRANSPORT PARAMETER CALIBRATION WORKFLOW")
    print("="*70 + "\n")
    
    # Initialize calibrator
    calibrator = PhTransportCalibrator()
    
    # Step 1: Validate default parameters
    print("STEP 1: Validating default parameters...")
    validation = calibrator.validate_parameters(DEFAULT_PARAMS)
    
    # Step 2: Sensitivity analysis
    print("\nSTEP 2: Performing sensitivity analysis...")
    sensitivity_data = {}
    
    param_ranges = {
        'K_DIFF_H': (0.01, 0.1),
        'K_NHE': (0.1, 2.0),
        'K_AE1': (0.5, 3.0),
        'BETA_BUFFER': (30.0, 150.0)
    }
    
    for param_name, param_range in param_ranges.items():
        print(f"  Analyzing {param_name}...")
        df = calibrator.sensitivity_analysis(param_name, param_range, n_points=15)
        sensitivity_data[param_name] = df
    
    # Plot sensitivity results
    calibrator.plot_sensitivity_results(
        sensitivity_data,
        output_path=str(output_dir / "sensitivity_analysis.png")
    )
    
    # Step 3: Parameter optimization (if validation failed)
    if not validation['all_ok']:
        print("\nSTEP 3: Optimizing parameters...")
        optimized_params = calibrator.optimize_parameters(
            target_t50=10.0,
            target_ratio=0.97,
            method='differential_evolution'
        )
        
        # Save optimized parameters
        with open(output_dir / "optimized_parameters.txt", 'w') as f:
            f.write("# Optimized pH Transport Parameters\n")
            f.write("# Generated by ph_calibration.py\n\n")
            for key, val in optimized_params.items():
                f.write(f"{key} = {val:.6f}\n")
        
        print(f"\n✓ Optimized parameters saved to: {output_dir / 'optimized_parameters.txt'}")
    else:
        print("\n✓ Default parameters are valid - no optimization needed")
    
    print("\n" + "="*70)
    print("CALIBRATION WORKFLOW COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    """
    Run calibration workflow.
    """
    run_calibration_workflow()
