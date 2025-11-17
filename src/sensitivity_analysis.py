#!/usr/bin/env python3
"""
Sensitivity Analysis for Enhanced RBC Model
Analyzes how sensitive the enhanced model is to parameter variations.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_baseline_simulation():
    """Run baseline simulation with current enhanced model."""
    try:
        print("=== Running Baseline Simulation ===")
        
        import main
        
        # Set command line arguments for main
        original_argv = sys.argv.copy()
        sys.argv = ['main.py', '--model', 'brodbar']
        
        try:
            results = main.main()
            
            # Load results from CSV since main doesn't return data
            sim_path = '../outputs/sim_states.csv'
            if os.path.exists(sim_path):
                baseline_data = pd.read_csv(sim_path)
                print(f"✓ Baseline simulation completed: {baseline_data.shape}")
                return baseline_data
            else:
                print("✗ Baseline simulation results not found")
                return None
                
        finally:
            sys.argv = original_argv
            
    except Exception as e:
        print(f"✗ Baseline simulation error: {e}")
        return None

def modify_enhancement_parameters(parameter_name, scale_factor):
    """Temporarily modify enhancement parameters in equadiff_brodbar.py."""
    try:
        # Read current enhanced model
        with open('equadiff_brodbar.py', 'r') as f:
            content = f.read()
        
        # Create temporary modified version
        modified_content = content
        
        # Modify specific enhancement parameters based on parameter_name
        if parameter_name == 'eglc_decay_rate':
            # Modify EGLC exponential decay rate (currently -0.1)
            modified_content = modified_content.replace(
                'eglc_target = 23.765 * np.exp(-0.1 * t)',
                f'eglc_target = 23.765 * np.exp({-0.1 * scale_factor} * t)'
            )
        elif parameter_name == 'elac_growth_rate':
            # Modify ELAC growth rate (currently -0.2)
            modified_content = modified_content.replace(
                'elac_target = 8.285 + 4.0 * (1 - np.exp(-0.2 * t))',
                f'elac_target = 8.285 + 4.0 * (1 - np.exp({-0.2 * scale_factor} * t))'
            )
        elif parameter_name == 'pyr_growth_rate':
            # Modify PYR growth rate (currently -0.05)
            modified_content = modified_content.replace(
                'pyr_target = 1.030 + 0.6 * (1 - np.exp(-0.05 * t))',
                f'pyr_target = 1.030 + 0.6 * (1 - np.exp({-0.05 * scale_factor} * t))'
            )
        elif parameter_name == 'lac_growth_rate':
            # Modify LAC growth rate (currently -0.08)
            modified_content = modified_content.replace(
                'lac_target = 3.614 + 25.0 * (1 - np.exp(-0.08 * t))',
                f'lac_target = 3.614 + 25.0 * (1 - np.exp({-0.08 * scale_factor} * t))'
            )
        elif parameter_name == 'feedback_strength':
            # Modify feedback coefficients (currently 5.0)
            modified_content = modified_content.replace(
                'curve_fitting_correction = 5.0 *',
                f'curve_fitting_correction = {5.0 * scale_factor} *'
            )
        
        # Write temporary modified file
        temp_file = 'equadiff_brodbar_temp.py'
        with open(temp_file, 'w') as f:
            f.write(modified_content)
        
        return temp_file
        
    except Exception as e:
        print(f"✗ Error modifying parameters: {e}")
        return None

def run_sensitivity_simulation(temp_file):
    """Run simulation with modified parameters."""
    try:
        # Backup original file and replace with modified version
        os.rename('equadiff_brodbar.py', 'equadiff_brodbar_original_temp.py')
        os.rename(temp_file, 'equadiff_brodbar.py')
        
        # Clear any cached modules
        if 'equadiff_brodbar' in sys.modules:
            del sys.modules['equadiff_brodbar']
        if 'main' in sys.modules:
            del sys.modules['main']
        
        # Run simulation
        import main
        
        original_argv = sys.argv.copy()
        sys.argv = ['main.py', '--model', 'brodbar']
        
        try:
            results = main.main()
            
            # Load results
            sim_path = '../outputs/sim_states.csv'
            if os.path.exists(sim_path):
                sensitivity_data = pd.read_csv(sim_path)
                return sensitivity_data
            else:
                return None
                
        finally:
            sys.argv = original_argv
        
    except Exception as e:
        print(f"✗ Sensitivity simulation error: {e}")
        return None
        
    finally:
        # Restore original file
        if os.path.exists('equadiff_brodbar_original_temp.py'):
            if os.path.exists('equadiff_brodbar.py'):
                os.remove('equadiff_brodbar.py')
            os.rename('equadiff_brodbar_original_temp.py', 'equadiff_brodbar.py')

def calculate_sensitivity_metrics(baseline_data, sensitivity_data, parameter_name, scale_factor):
    """Calculate sensitivity metrics comparing baseline and modified simulations."""
    try:
        # Key metabolites to analyze
        key_metabolites = {
            'EGLC': 85,
            'ELAC': 87,
            'PYR': 18,
            'LAC': 19
        }
        
        sensitivity_metrics = {
            'parameter': parameter_name,
            'scale_factor': scale_factor,
            'metabolite_sensitivity': {}
        }
        
        for name, idx in key_metabolites.items():
            col_name = f'x{idx}'
            
            if col_name in baseline_data.columns and col_name in sensitivity_data.columns:
                baseline_values = baseline_data[col_name].values
                sensitivity_values = sensitivity_data[col_name].values
                
                # Calculate metrics
                baseline_final = baseline_values[-1]
                sensitivity_final = sensitivity_values[-1]
                
                absolute_change = sensitivity_final - baseline_final
                relative_change = (absolute_change / baseline_final * 100) if baseline_final != 0 else 0
                
                # Calculate trajectory differences
                if len(baseline_values) == len(sensitivity_values):
                    trajectory_diff = np.mean(np.abs(sensitivity_values - baseline_values))
                    max_trajectory_diff = np.max(np.abs(sensitivity_values - baseline_values))
                else:
                    trajectory_diff = np.nan
                    max_trajectory_diff = np.nan
                
                sensitivity_metrics['metabolite_sensitivity'][name] = {
                    'baseline_final': float(baseline_final),
                    'sensitivity_final': float(sensitivity_final),
                    'absolute_change': float(absolute_change),
                    'relative_change': float(relative_change),
                    'trajectory_diff_mean': float(trajectory_diff),
                    'trajectory_diff_max': float(max_trajectory_diff)
                }
        
        return sensitivity_metrics
        
    except Exception as e:
        print(f"✗ Sensitivity metrics calculation error: {e}")
        return {}

def perform_comprehensive_sensitivity_analysis():
    """Perform comprehensive sensitivity analysis on key parameters."""
    try:
        print("=" * 60)
        print("ENHANCED MODEL SENSITIVITY ANALYSIS")
        print("=" * 60)
        
        # Run baseline simulation
        baseline_data = run_baseline_simulation()
        if baseline_data is None:
            print("✗ Cannot proceed without baseline simulation")
            return None
        
        # Parameters to test
        parameters_to_test = [
            ('eglc_decay_rate', [0.5, 0.8, 1.2, 1.5, 2.0]),
            ('elac_growth_rate', [0.5, 0.8, 1.2, 1.5, 2.0]),
            ('pyr_growth_rate', [0.5, 0.8, 1.2, 1.5, 2.0]),
            ('lac_growth_rate', [0.5, 0.8, 1.2, 1.5, 2.0]),
            ('feedback_strength', [0.5, 0.8, 1.2, 1.5, 2.0])
        ]
        
        all_sensitivity_results = []
        
        for param_name, scale_factors in parameters_to_test:
            print(f"\n=== Testing {param_name} ===")
            
            for scale_factor in scale_factors:
                print(f"  Testing scale factor: {scale_factor}")
                
                # Modify parameters
                temp_file = modify_enhancement_parameters(param_name, scale_factor)
                if temp_file is None:
                    continue
                
                # Run sensitivity simulation
                sensitivity_data = run_sensitivity_simulation(temp_file)
                if sensitivity_data is None:
                    continue
                
                # Calculate sensitivity metrics
                metrics = calculate_sensitivity_metrics(baseline_data, sensitivity_data, param_name, scale_factor)
                if metrics:
                    all_sensitivity_results.append(metrics)
                
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        
        return all_sensitivity_results
        
    except Exception as e:
        print(f"✗ Comprehensive sensitivity analysis error: {e}")
        return None

def analyze_sensitivity_results(sensitivity_results):
    """Analyze and summarize sensitivity results."""
    try:
        print(f"\n=== Sensitivity Analysis Results ===")
        
        if not sensitivity_results:
            print("✗ No sensitivity results to analyze")
            return {}
        
        # Group results by parameter
        parameter_groups = {}
        for result in sensitivity_results:
            param = result['parameter']
            if param not in parameter_groups:
                parameter_groups[param] = []
            parameter_groups[param].append(result)
        
        analysis_summary = {}
        
        for param_name, param_results in parameter_groups.items():
            print(f"\n{param_name.upper()}:")
            
            # Calculate sensitivity statistics
            metabolite_sensitivities = {}
            
            for metabolite in ['EGLC', 'ELAC', 'PYR', 'LAC']:
                relative_changes = []
                for result in param_results:
                    if metabolite in result['metabolite_sensitivity']:
                        rel_change = result['metabolite_sensitivity'][metabolite]['relative_change']
                        if not np.isnan(rel_change):
                            relative_changes.append(abs(rel_change))
                
                if relative_changes:
                    mean_sensitivity = np.mean(relative_changes)
                    max_sensitivity = np.max(relative_changes)
                    metabolite_sensitivities[metabolite] = {
                        'mean_sensitivity': mean_sensitivity,
                        'max_sensitivity': max_sensitivity
                    }
                    print(f"  {metabolite}: Mean={mean_sensitivity:.2f}%, Max={max_sensitivity:.2f}%")
            
            analysis_summary[param_name] = metabolite_sensitivities
        
        return analysis_summary
        
    except Exception as e:
        print(f"✗ Sensitivity analysis error: {e}")
        return {}

def create_sensitivity_plots(sensitivity_results, output_dir):
    """Create sensitivity analysis plots."""
    try:
        print(f"\n=== Creating Sensitivity Plots ===")
        os.makedirs(output_dir, exist_ok=True)
        
        if not sensitivity_results:
            print("✗ No results to plot")
            return
        
        # Group by parameter
        parameter_groups = {}
        for result in sensitivity_results:
            param = result['parameter']
            if param not in parameter_groups:
                parameter_groups[param] = []
            parameter_groups[param].append(result)
        
        # Create plots for each parameter
        for param_name, param_results in parameter_groups.items():
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()
            
            metabolites = ['EGLC', 'ELAC', 'PYR', 'LAC']
            
            for i, metabolite in enumerate(metabolites):
                if i < len(axes):
                    ax = axes[i]
                    
                    scale_factors = []
                    relative_changes = []
                    
                    for result in param_results:
                        if metabolite in result['metabolite_sensitivity']:
                            scale_factors.append(result['scale_factor'])
                            relative_changes.append(result['metabolite_sensitivity'][metabolite]['relative_change'])
                    
                    if scale_factors:
                        ax.plot(scale_factors, relative_changes, 'o-', linewidth=2, markersize=6)
                        ax.set_title(f'{metabolite} Sensitivity to {param_name}')
                        ax.set_xlabel('Parameter Scale Factor')
                        ax.set_ylabel('Relative Change (%)')
                        ax.grid(True, alpha=0.3)
                        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
                        ax.axvline(x=1, color='red', linestyle='--', alpha=0.5)
            
            plt.tight_layout()
            plot_path = os.path.join(output_dir, f'sensitivity_{param_name}.png')
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"  ✓ {param_name} plot saved: {plot_path}")
        
    except Exception as e:
        print(f"✗ Plotting error: {e}")

def save_sensitivity_results(sensitivity_results, analysis_summary, output_dir):
    """Save sensitivity analysis results."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Save detailed results
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'enhanced_model_sensitivity',
            'detailed_results': sensitivity_results,
            'analysis_summary': analysis_summary,
            'conclusions': {
                'most_sensitive_parameter': None,
                'most_robust_metabolite': None,
                'recommendations': []
            }
        }
        
        # Determine most sensitive parameter
        if analysis_summary:
            param_sensitivities = {}
            for param, metabolites in analysis_summary.items():
                total_sensitivity = sum(m['mean_sensitivity'] for m in metabolites.values())
                param_sensitivities[param] = total_sensitivity
            
            if param_sensitivities:
                most_sensitive = max(param_sensitivities, key=param_sensitivities.get)
                results_data['conclusions']['most_sensitive_parameter'] = most_sensitive
        
        # Save results
        results_path = os.path.join(output_dir, 'sensitivity_analysis_results.json')
        with open(results_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"✓ Sensitivity results saved: {results_path}")
        return results_data
        
    except Exception as e:
        print(f"✗ Error saving results: {e}")
        return None

def main_sensitivity_analysis():
    """Main sensitivity analysis function."""
    print("Starting Enhanced Model Sensitivity Analysis...")
    
    # Create output directory
    output_dir = '../outputs/sensitivity_analysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Perform comprehensive sensitivity analysis
    sensitivity_results = perform_comprehensive_sensitivity_analysis()
    
    if sensitivity_results:
        # Analyze results
        analysis_summary = analyze_sensitivity_results(sensitivity_results)
        
        # Create plots
        create_sensitivity_plots(sensitivity_results, output_dir)
        
        # Save results
        final_results = save_sensitivity_results(sensitivity_results, analysis_summary, output_dir)
        
        print(f"\n" + "=" * 60)
        print("SENSITIVITY ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"✓ Results saved to: {output_dir}")
        
        if final_results and final_results['conclusions']['most_sensitive_parameter']:
            print(f"✓ Most sensitive parameter: {final_results['conclusions']['most_sensitive_parameter']}")
        
        return True
    else:
        print("✗ Sensitivity analysis failed")
        return False

if __name__ == "__main__":
    success = main_sensitivity_analysis()
    if success:
        print("\n🎉 Sensitivity analysis completed successfully!")
    else:
        print("\n❌ Sensitivity analysis failed!")
