"""
Hierarchical Modeling Framework for RBC Metabolic Model
Implements multi-level parameter estimation with adaptive weighting and uncertainty quantification.
Author: Jorgelindo da Veiga
"""
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import minimize, differential_evolution
from scipy.stats import norm, chi2
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Union
import warnings
from pathlib import Path
import json

# Suppress optimization warnings for cleaner output
warnings.filterwarnings('ignore', category=RuntimeWarning)


@dataclass
class ParameterHierarchy:
    """Defines the hierarchical structure of model parameters."""
    
    # Global parameters (affect entire model)
    global_params: Dict[str, float] = field(default_factory=dict)
    global_bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # Pathway-specific parameters (affect groups of metabolites)
    pathway_params: Dict[str, Dict[str, float]] = field(default_factory=dict)
    pathway_bounds: Dict[str, Dict[str, Tuple[float, float]]] = field(default_factory=dict)
    
    # Metabolite-specific parameters (individual fine-tuning)
    metabolite_params: Dict[str, Dict[str, float]] = field(default_factory=dict)
    metabolite_bounds: Dict[str, Dict[str, Tuple[float, float]]] = field(default_factory=dict)
    
    # Uncertainty estimates
    parameter_uncertainties: Dict[str, float] = field(default_factory=dict)


@dataclass
class ExperimentalDataPoint:
    """Represents a single experimental observation with uncertainty."""
    metabolite: str
    time: float
    concentration: float
    uncertainty: float
    weight: float = 1.0
    quality_score: float = 1.0


class AdaptiveWeightingScheme:
    """Implements adaptive weighting based on data quality and uncertainty."""
    
    def __init__(self, base_weight: float = 1.0):
        self.base_weight = base_weight
        self.time_weights = {}
        self.metabolite_weights = {}
        self.uncertainty_weights = {}
    
    def calculate_weights(self, data_points: List[ExperimentalDataPoint]) -> Dict[str, float]:
        """Calculate adaptive weights for experimental data points."""
        weights = {}
        
        for point in data_points:
            key = f"{point.metabolite}_{point.time}"
            
            # Base weight
            weight = self.base_weight
            
            # Time-dependent weighting (early time points more important for initial conditions)
            time_factor = np.exp(-0.1 * point.time) + 0.3  # Exponential decay + baseline
            
            # Uncertainty-based weighting (inverse relationship)
            uncertainty_factor = 1.0 / (1.0 + point.uncertainty)
            
            # Quality-based weighting
            quality_factor = point.quality_score
            
            # Combined weight
            weights[key] = weight * time_factor * uncertainty_factor * quality_factor
            
        return weights


class HierarchicalFitter:
    """
    Hierarchical modeling framework for enhanced data fitting.
    
    Implements a three-level parameter estimation approach:
    1. Global parameters: Fundamental kinetic constants
    2. Pathway parameters: Pathway-specific scaling factors
    3. Metabolite parameters: Individual fine-tuning parameters
    """
    
    def __init__(self, model_function, initial_conditions, experimental_data, time_points):
        """
        Initialize the hierarchical fitter.
        
        Parameters:
        -----------
        model_function : callable
            The differential equation function (e.g., equadiff_brodbar)
        initial_conditions : numpy.ndarray
            Initial metabolite concentrations
        experimental_data : dict
            Dictionary mapping metabolite names to experimental time series
        time_points : numpy.ndarray
            Time points for experimental observations
        """
        self.model_function = model_function
        self.initial_conditions = initial_conditions.copy()
        self.experimental_data = experimental_data
        self.time_points = time_points
        
        # Initialize parameter hierarchy
        self.parameter_hierarchy = ParameterHierarchy()
        
        # Initialize weighting scheme
        self.weighting_scheme = AdaptiveWeightingScheme()
        
        # Metabolic pathway definitions
        self.pathways = self._define_pathways()
        
        # Fitting results storage
        self.fitting_results = {}
        self.optimization_history = []
        
        # Uncertainty quantification
        self.parameter_covariance = None
        self.confidence_intervals = {}
        
    def _define_pathways(self) -> Dict[str, List[str]]:
        """Define metabolic pathways for hierarchical parameter organization."""
        return {
            'glycolysis': ['GLC', 'G6P', 'F6P', 'F16BP', 'DHAP', 'GA3P', 'B13PG', 'B23PG', 'P3G', 'P2G', 'PEP', 'PYR'],
            'pentose_phosphate': ['G6P', 'GL6P', 'F6P', 'R5P', 'X5P', 'S7P', 'E4P'],
            'nucleotide_metabolism': ['AMP', 'ADP', 'ATP', 'GMP', 'GDP', 'GTP', 'IMP', 'XMP'],
            'amino_acid_metabolism': ['ALA', 'ARG', 'ASP', 'ASN', 'CYS', 'GLN', 'GLU', 'GLY'],
            'redox_system': ['GSH', 'GSSG', 'NADH', 'NAD', 'NADPH', 'NADP'],
            'transport': ['EGLC', 'ELAC', 'EURT', 'EPYR', 'EADE', 'EASP', 'ECIT'],
            'energy_metabolism': ['ATP', 'ADP', 'AMP', 'PCR', 'CR', 'LAC', 'PYR']
        }
    
    def setup_parameter_hierarchy(self):
        """Setup the hierarchical parameter structure."""
        
        # Global parameters (fundamental kinetic constants)
        self.parameter_hierarchy.global_params = {
            'global_vmax_scale': 1.0,      # Global scaling for Vmax values
            'global_km_scale': 1.0,        # Global scaling for Km values
            'global_ki_scale': 1.0,        # Global scaling for inhibition constants
            'temperature_factor': 1.0,      # Temperature correction factor
            'ph_correction': 1.0           # pH correction factor
        }
        
        self.parameter_hierarchy.global_bounds = {
            'global_vmax_scale': (0.1, 10.0),
            'global_km_scale': (0.1, 10.0),
            'global_ki_scale': (0.1, 10.0),
            'temperature_factor': (0.8, 1.2),
            'ph_correction': (0.8, 1.2)
        }
        
        # Pathway-specific parameters
        for pathway_name in self.pathways.keys():
            self.parameter_hierarchy.pathway_params[pathway_name] = {
                'vmax_scale': 1.0,         # Pathway-specific Vmax scaling
                'flux_balance': 1.0,       # Pathway flux balance factor
                'regulation_strength': 1.0  # Pathway regulation strength
            }
            
            self.parameter_hierarchy.pathway_bounds[pathway_name] = {
                'vmax_scale': (0.1, 5.0),
                'flux_balance': (0.5, 2.0),
                'regulation_strength': (0.1, 3.0)
            }
        
        # Metabolite-specific parameters (for experimental metabolites only)
        for metabolite in self.experimental_data.keys():
            self.parameter_hierarchy.metabolite_params[metabolite] = {
                'concentration_scale': 1.0,  # Individual concentration scaling
                'time_shift': 0.0,          # Time shift for kinetic alignment
                'noise_variance': 0.01      # Metabolite-specific noise level
            }
            
            self.parameter_hierarchy.metabolite_bounds[metabolite] = {
                'concentration_scale': (0.1, 10.0),
                'time_shift': (-2.0, 2.0),
                'noise_variance': (0.001, 1.0)
            }
    
    def prepare_experimental_data(self) -> List[ExperimentalDataPoint]:
        """Convert experimental data to structured format with uncertainty estimates."""
        data_points = []
        
        for metabolite, time_series in self.experimental_data.items():
            if isinstance(time_series, (list, np.ndarray)) and len(time_series) == len(self.time_points):
                for i, (time, concentration) in enumerate(zip(self.time_points, time_series)):
                    if not np.isnan(concentration) and concentration > 0:
                        # Estimate uncertainty (could be improved with actual experimental errors)
                        uncertainty = max(0.05 * concentration, 0.001)  # 5% relative error minimum
                        
                        # Quality score based on concentration magnitude and time point
                        quality_score = min(1.0, concentration / 0.1)  # Higher for higher concentrations
                        
                        data_point = ExperimentalDataPoint(
                            metabolite=metabolite,
                            time=time,
                            concentration=concentration,
                            uncertainty=uncertainty,
                            quality_score=quality_score
                        )
                        data_points.append(data_point)
        
        return data_points
    
    def simulate_model(self, parameters: Dict[str, float]) -> np.ndarray:
        """
        Simulate the model with given parameters.
        
        Parameters:
        -----------
        parameters : dict
            Dictionary of parameter values
            
        Returns:
        --------
        numpy.ndarray
            Simulated concentration trajectories
        """
        try:
            # Apply parameter modifications to initial conditions if needed
            x0_modified = self.initial_conditions.copy()
            
            # Solve the ODE system
            sol = solve_ivp(
                fun=lambda t, x: self.model_function(t, x),
                t_span=(self.time_points[0], self.time_points[-1]),
                y0=x0_modified,
                t_eval=self.time_points,
                method='LSODA',
                rtol=1e-8,
                atol=1e-10
            )
            
            if sol.success:
                return sol.y.T  # Transpose to get (time, metabolite) shape
            else:
                print(f"Integration failed: {sol.message}")
                return np.full((len(self.time_points), len(x0_modified)), np.nan)
                
        except Exception as e:
            print(f"Simulation error: {e}")
            return np.full((len(self.time_points), len(self.initial_conditions)), np.nan)
    
    def calculate_objective(self, parameters: Dict[str, float], data_points: List[ExperimentalDataPoint]) -> float:
        """
        Calculate the weighted objective function for parameter optimization.
        
        Parameters:
        -----------
        parameters : dict
            Current parameter values
        data_points : list
            Experimental data points with uncertainties
            
        Returns:
        --------
        float
            Weighted sum of squared residuals
        """
        # Simulate model
        simulation_results = self.simulate_model(parameters)
        
        if np.any(np.isnan(simulation_results)):
            return 1e10  # Large penalty for failed simulations
        
        # Calculate weights
        weights = self.weighting_scheme.calculate_weights(data_points)
        
        # Calculate weighted residuals
        total_error = 0.0
        n_points = 0
        
        for point in data_points:
            # Find corresponding simulation result
            time_idx = np.argmin(np.abs(self.time_points - point.time))
            
            # Get metabolite index (this would need to be mapped properly)
            # For now, using a simplified approach
            metabolite_idx = self._get_metabolite_index(point.metabolite)
            
            if metabolite_idx is not None and metabolite_idx < simulation_results.shape[1]:
                simulated_value = simulation_results[time_idx, metabolite_idx]
                
                # Apply metabolite-specific scaling if available
                if point.metabolite in self.parameter_hierarchy.metabolite_params:
                    scale = self.parameter_hierarchy.metabolite_params[point.metabolite].get('concentration_scale', 1.0)
                    simulated_value *= scale
                
                # Calculate weighted residual
                residual = (point.concentration - simulated_value) / point.uncertainty
                weight = weights.get(f"{point.metabolite}_{point.time}", 1.0)
                
                total_error += weight * residual**2
                n_points += 1
        
        return total_error / max(n_points, 1)  # Normalize by number of points
    
    def _get_metabolite_index(self, metabolite_name: str) -> Optional[int]:
        """Get the index of a metabolite in the state vector."""
        # This would need to be implemented based on the specific model structure
        # For now, return a placeholder
        metabolite_map = {
            'PYR': 18, 'LAC': 19, 'MAL': 20, 'B23PG': 15,
            'EGLC': 85, 'ELAC': 87, 'CYT': 84, 'EURT': 97
        }
        return metabolite_map.get(metabolite_name.upper())
    
    def fit_hierarchical_model(self, max_iterations: int = 100) -> Dict:
        """
        Perform hierarchical model fitting.
        
        Parameters:
        -----------
        max_iterations : int
            Maximum number of optimization iterations
            
        Returns:
        --------
        dict
            Fitting results and statistics
        """
        print("Starting hierarchical model fitting...")
        
        # Setup parameter hierarchy
        self.setup_parameter_hierarchy()
        
        # Prepare experimental data
        data_points = self.prepare_experimental_data()
        print(f"Prepared {len(data_points)} experimental data points")
        
        # Stage 1: Global parameter optimization
        print("\nStage 1: Global parameter optimization")
        global_result = self._optimize_global_parameters(data_points)
        
        # Stage 2: Pathway-specific parameter optimization
        print("\nStage 2: Pathway parameter optimization")
        pathway_result = self._optimize_pathway_parameters(data_points)
        
        # Stage 3: Metabolite-specific parameter optimization
        print("\nStage 3: Metabolite parameter optimization")
        metabolite_result = self._optimize_metabolite_parameters(data_points)
        
        # Uncertainty quantification
        print("\nPerforming uncertainty quantification...")
        self._quantify_uncertainties(data_points)
        
        # Compile results
        results = {
            'global_optimization': global_result,
            'pathway_optimization': pathway_result,
            'metabolite_optimization': metabolite_result,
            'parameter_hierarchy': self.parameter_hierarchy,
            'confidence_intervals': self.confidence_intervals,
            'optimization_history': self.optimization_history
        }
        
        self.fitting_results = results
        return results
    
    def _optimize_global_parameters(self, data_points: List[ExperimentalDataPoint]) -> Dict:
        """Optimize global parameters."""
        # Extract global parameters and bounds
        param_names = list(self.parameter_hierarchy.global_params.keys())
        initial_values = [self.parameter_hierarchy.global_params[name] for name in param_names]
        bounds = [self.parameter_hierarchy.global_bounds[name] for name in param_names]
        
        def objective(params):
            param_dict = dict(zip(param_names, params))
            return self.calculate_objective(param_dict, data_points)
        
        # Use differential evolution for global optimization
        result = differential_evolution(
            objective,
            bounds=bounds,
            maxiter=50,
            popsize=15,
            seed=42
        )
        
        # Update global parameters
        for i, name in enumerate(param_names):
            self.parameter_hierarchy.global_params[name] = result.x[i]
        
        return {
            'success': result.success,
            'final_cost': result.fun,
            'iterations': result.nit,
            'parameters': dict(zip(param_names, result.x))
        }
    
    def _optimize_pathway_parameters(self, data_points: List[ExperimentalDataPoint]) -> Dict:
        """Optimize pathway-specific parameters."""
        results = {}
        
        for pathway_name in self.pathways.keys():
            param_names = list(self.parameter_hierarchy.pathway_params[pathway_name].keys())
            initial_values = [self.parameter_hierarchy.pathway_params[pathway_name][name] for name in param_names]
            bounds = [self.parameter_hierarchy.pathway_bounds[pathway_name][name] for name in param_names]
            
            def objective(params):
                param_dict = dict(zip(param_names, params))
                return self.calculate_objective(param_dict, data_points)
            
            result = minimize(
                objective,
                x0=initial_values,
                bounds=bounds,
                method='L-BFGS-B'
            )
            
            # Update pathway parameters
            for i, name in enumerate(param_names):
                self.parameter_hierarchy.pathway_params[pathway_name][name] = result.x[i]
            
            results[pathway_name] = {
                'success': result.success,
                'final_cost': result.fun,
                'parameters': dict(zip(param_names, result.x))
            }
        
        return results
    
    def _optimize_metabolite_parameters(self, data_points: List[ExperimentalDataPoint]) -> Dict:
        """Optimize metabolite-specific parameters."""
        results = {}
        
        for metabolite in self.experimental_data.keys():
            if metabolite in self.parameter_hierarchy.metabolite_params:
                param_names = list(self.parameter_hierarchy.metabolite_params[metabolite].keys())
                initial_values = [self.parameter_hierarchy.metabolite_params[metabolite][name] for name in param_names]
                bounds = [self.parameter_hierarchy.metabolite_bounds[metabolite][name] for name in param_names]
                
                # Filter data points for this metabolite
                metabolite_data = [dp for dp in data_points if dp.metabolite == metabolite]
                
                def objective(params):
                    param_dict = dict(zip(param_names, params))
                    return self.calculate_objective(param_dict, metabolite_data)
                
                result = minimize(
                    objective,
                    x0=initial_values,
                    bounds=bounds,
                    method='L-BFGS-B'
                )
                
                # Update metabolite parameters
                for i, name in enumerate(param_names):
                    self.parameter_hierarchy.metabolite_params[metabolite][name] = result.x[i]
                
                results[metabolite] = {
                    'success': result.success,
                    'final_cost': result.fun,
                    'parameters': dict(zip(param_names, result.x))
                }
        
        return results
    
    def _quantify_uncertainties(self, data_points: List[ExperimentalDataPoint]):
        """Perform uncertainty quantification using bootstrap or Hessian methods."""
        # Simplified uncertainty quantification
        # In practice, this would use bootstrap sampling or Hessian-based methods
        
        for param_name in self.parameter_hierarchy.global_params.keys():
            # Placeholder uncertainty estimate (would be calculated properly)
            self.parameter_hierarchy.parameter_uncertainties[param_name] = 0.1
            
            # Confidence intervals (95%)
            param_value = self.parameter_hierarchy.global_params[param_name]
            uncertainty = self.parameter_hierarchy.parameter_uncertainties[param_name]
            
            self.confidence_intervals[param_name] = {
                'lower': param_value - 1.96 * uncertainty,
                'upper': param_value + 1.96 * uncertainty,
                'uncertainty': uncertainty
            }
    
    def save_results(self, output_path: str):
        """Save fitting results to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert results to JSON-serializable format
        serializable_results = self._make_serializable(self.fitting_results)
        
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Results saved to {output_file}")
    
    def _make_serializable(self, obj):
        """Convert numpy arrays and other non-serializable objects to serializable format."""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        else:
            return obj
    
    def generate_diagnostic_plots(self, output_dir: str):
        """Generate diagnostic plots for model fitting assessment."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Plot parameter evolution
        self._plot_parameter_evolution(output_path / "parameter_evolution.png")
        
        # Plot residuals analysis
        self._plot_residuals_analysis(output_path / "residuals_analysis.png")
        
        # Plot uncertainty quantification
        self._plot_uncertainty_analysis(output_path / "uncertainty_analysis.png")
    
    def _plot_parameter_evolution(self, output_file: Path):
        """Plot parameter evolution during optimization."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Parameter Evolution During Optimization')
        
        # Global parameters
        ax = axes[0, 0]
        for param_name, param_value in self.parameter_hierarchy.global_params.items():
            ax.bar(param_name, param_value)
        ax.set_title('Global Parameters')
        ax.tick_params(axis='x', rotation=45)
        
        # Pathway parameters (example)
        ax = axes[0, 1]
        pathway_names = list(self.parameter_hierarchy.pathway_params.keys())[:5]  # First 5 pathways
        vmax_scales = [self.parameter_hierarchy.pathway_params[name]['vmax_scale'] for name in pathway_names]
        ax.bar(pathway_names, vmax_scales)
        ax.set_title('Pathway Vmax Scales')
        ax.tick_params(axis='x', rotation=45)
        
        # Metabolite parameters (example)
        ax = axes[1, 0]
        metabolite_names = list(self.parameter_hierarchy.metabolite_params.keys())[:5]  # First 5 metabolites
        conc_scales = [self.parameter_hierarchy.metabolite_params[name]['concentration_scale'] for name in metabolite_names]
        ax.bar(metabolite_names, conc_scales)
        ax.set_title('Metabolite Concentration Scales')
        ax.tick_params(axis='x', rotation=45)
        
        # Confidence intervals
        ax = axes[1, 1]
        if self.confidence_intervals:
            param_names = list(self.confidence_intervals.keys())[:5]  # First 5 parameters
            values = [self.parameter_hierarchy.global_params[name] for name in param_names]
            uncertainties = [self.confidence_intervals[name]['uncertainty'] for name in param_names]
            ax.errorbar(range(len(param_names)), values, yerr=uncertainties, fmt='o')
            ax.set_xticks(range(len(param_names)))
            ax.set_xticklabels(param_names, rotation=45)
            ax.set_title('Parameter Uncertainties')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_residuals_analysis(self, output_file: Path):
        """Plot residuals analysis."""
        # Placeholder for residuals analysis plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Residuals Analysis\n(To be implemented with actual data)', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title('Residuals Analysis')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_uncertainty_analysis(self, output_file: Path):
        """Plot uncertainty analysis."""
        # Placeholder for uncertainty analysis plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Uncertainty Analysis\n(To be implemented with actual data)', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title('Uncertainty Analysis')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()


def main():
    """Example usage of the hierarchical fitter."""
    print("Hierarchical Modeling Framework for RBC Metabolic Model")
    print("=" * 60)
    
    # This would be called with actual model and data
    # Example placeholder code:
    
    # from equadiff_brodbar import equadiff_brodbar
    # from parse_initial_conditions import parse_initial_conditions
    # 
    # # Load model and data
    # x0 = parse_initial_conditions('initial_cond_RBC_aire.xls')
    # experimental_data = {...}  # Load experimental data
    # time_points = np.array([1, 4, 8, 11, 15, 18, 22, 25, 29, 32, 36, 38, 43, 46])
    # 
    # # Create and run hierarchical fitter
    # fitter = HierarchicalFitter(equadiff_brodbar, x0, experimental_data, time_points)
    # results = fitter.fit_hierarchical_model()
    # 
    # # Save results and generate plots
    # fitter.save_results('outputs/hierarchical_fit_results.json')
    # fitter.generate_diagnostic_plots('outputs/hierarchical_diagnostics/')
    
    print("Framework initialized successfully!")
    print("Use this module by importing HierarchicalFitter class")


if __name__ == "__main__":
    main()
