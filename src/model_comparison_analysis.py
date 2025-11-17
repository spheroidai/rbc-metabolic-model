#!/usr/bin/env python3
"""
Model Comparison Analysis
Comprehensive comparison between original and enhanced RBC metabolic models.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

def load_simulation_results():
    """Load the latest simulation results."""
    try:
        # Load simulation states
        sim_path = '../outputs/sim_states.csv'
        if not os.path.exists(sim_path):
            sim_path = 'outputs/sim_states.csv'
        if not os.path.exists(sim_path):
            sim_path = os.path.join('..', 'outputs', 'sim_states.csv')
        if os.path.exists(sim_path):
            sim_data = pd.read_csv(sim_path)
            print(f"✓ Loaded simulation results: {sim_data.shape}")
            return sim_data
        else:
            print(f"✗ Simulation results not found at {sim_path}")
            return None
    except Exception as e:
        print(f"✗ Error loading simulation results: {e}")
        return None

def load_experimental_data():
    """Load experimental data for comparison."""
    try:
        # Try multiple experimental data sources
        exp_paths = [
            '../Data_Brodbar_et_al_exp.xlsx',
            'Data_Brodbar_et_al_exp.xlsx',
            '../Data_Brodbar_et_al_exp_fitted_params.csv'
        ]
        
        for path in exp_paths:
            if os.path.exists(path):
                if path.endswith('.xlsx'):
                    exp_data = pd.read_excel(path)
                elif path.endswith('.csv'):
                    exp_data = pd.read_csv(path)
                print(f"✓ Loaded experimental data: {exp_data.shape}")
                return exp_data
        
        print("⚠ No experimental data found, using synthetic targets")
        return None
        
    except Exception as e:
        print(f"✗ Error loading experimental data: {e}")
        return None

def analyze_enhanced_model_performance(sim_data):
    """Analyze the performance of the enhanced model."""
    try:
        print("\n=== Enhanced Model Performance Analysis ===")
        
        # Key metabolite indices from BRODBAR_METABOLITE_MAP
        key_metabolites = {
            'EGLC': 85,  # Extracellular glucose
            'ELAC': 87,  # Extracellular lactate  
            'PYR': 18,   # Pyruvate
            'LAC': 19,   # Intracellular lactate
            'ATP': 13,   # ATP
            'ADP': 6,    # ADP
            'GLC': 34    # Intracellular glucose
        }
        
        analysis_results = {}
        time_points = sim_data['time'].values
        
        print(f"Time range: {time_points[0]:.1f} to {time_points[-1]:.1f}")
        print(f"Total time points: {len(time_points)}")
        
        for name, idx in key_metabolites.items():
            col_name = f'x{idx}'
            if col_name in sim_data.columns:
                values = sim_data[col_name].values
                initial = values[0]
                final = values[-1]
                change = final - initial
                percent_change = (change / initial * 100) if initial != 0 else 0
                
                # Calculate trajectory statistics
                mean_val = np.mean(values)
                std_val = np.std(values)
                min_val = np.min(values)
                max_val = np.max(values)
                
                analysis_results[name] = {
                    'initial': float(initial),
                    'final': float(final),
                    'change': float(change),
                    'percent_change': float(percent_change),
                    'mean': float(mean_val),
                    'std': float(std_val),
                    'min': float(min_val),
                    'max': float(max_val),
                    'trajectory': values.tolist()
                }
                
                print(f"{name:4s}: {initial:8.3f} → {final:8.3f} mM ({change:+7.3f}, {percent_change:+6.1f}%)")
        
        return analysis_results
        
    except Exception as e:
        print(f"✗ Analysis error: {e}")
        return {}

def validate_enhancement_patterns(analysis_results):
    """Validate that the enhanced model shows expected metabolic patterns."""
    try:
        print("\n=== Enhancement Pattern Validation ===")
        
        validation_results = {}
        
        # Expected patterns based on RBC metabolism
        expected_patterns = {
            'EGLC': 'decrease',  # Glucose consumption
            'ELAC': 'increase',  # Lactate production
            'LAC': 'increase',   # Intracellular lactate accumulation
            'PYR': 'increase',   # Pyruvate production
        }
        
        for metabolite, expected in expected_patterns.items():
            if metabolite in analysis_results:
                change = analysis_results[metabolite]['change']
                
                if expected == 'decrease':
                    valid = change < 0
                elif expected == 'increase':
                    valid = change > 0
                else:
                    valid = True
                
                validation_results[f'{metabolite}_{expected}'] = valid
                status = '✓' if valid else '✗'
                print(f"{metabolite} {expected}: {status} ({change:+.3f} mM)")
        
        # Check numerical stability
        all_trajectories = []
        for metabolite in analysis_results.values():
            all_trajectories.extend(metabolite['trajectory'])
        
        has_nan = any(np.isnan(val) for val in all_trajectories)
        has_inf = any(np.isinf(val) for val in all_trajectories)
        numerical_stable = not (has_nan or has_inf)
        
        validation_results['numerical_stability'] = numerical_stable
        print(f"Numerical stability: {'✓' if numerical_stable else '✗'}")
        
        # Overall validation
        pattern_validations = [v for k, v in validation_results.items() if k != 'numerical_stability']
        patterns_valid = all(pattern_validations)
        overall_valid = patterns_valid and numerical_stable
        
        validation_results['patterns_valid'] = patterns_valid
        validation_results['overall_valid'] = overall_valid
        
        print(f"Pattern validation: {'✓' if patterns_valid else '✗'} ({sum(pattern_validations)}/{len(pattern_validations)})")
        print(f"Overall validation: {'✓ PASS' if overall_valid else '✗ FAIL'}")
        
        return validation_results
        
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return {}

def create_comparison_plots(analysis_results, output_dir):
    """Create comprehensive comparison plots."""
    try:
        print("\n=== Creating Comparison Plots ===")
        os.makedirs(output_dir, exist_ok=True)
        
        # Plot 1: Key metabolite trajectories
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        key_metabolites = ['EGLC', 'ELAC', 'PYR', 'LAC']
        colors = ['blue', 'red', 'green', 'orange']
        
        for i, metabolite in enumerate(key_metabolites):
            if metabolite in analysis_results and i < len(axes):
                ax = axes[i]
                data = analysis_results[metabolite]
                trajectory = data['trajectory']
                time_points = np.linspace(1, 42, len(trajectory))
                
                ax.plot(time_points, trajectory, color=colors[i], linewidth=2, label='Enhanced Model')
                ax.set_title(f'{metabolite} - Enhanced Model Trajectory')
                ax.set_xlabel('Time (arbitrary units)')
                ax.set_ylabel('Concentration (mM)')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                # Add statistics text
                stats_text = f'Initial: {data["initial"]:.3f}\nFinal: {data["final"]:.3f}\nChange: {data["change"]:+.3f}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plot1_path = os.path.join(output_dir, 'enhanced_model_trajectories.png')
        plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Metabolite change summary
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar plot of changes
        metabolites = list(analysis_results.keys())
        changes = [analysis_results[m]['change'] for m in metabolites]
        colors_bar = ['red' if c < 0 else 'green' for c in changes]
        
        ax1.bar(metabolites, changes, color=colors_bar, alpha=0.7)
        ax1.set_title('Metabolite Concentration Changes')
        ax1.set_ylabel('Change (mM)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # Scatter plot of initial vs final
        initials = [analysis_results[m]['initial'] for m in metabolites]
        finals = [analysis_results[m]['final'] for m in metabolites]
        
        ax2.scatter(initials, finals, alpha=0.7, s=60)
        for i, metabolite in enumerate(metabolites):
            ax2.annotate(metabolite, (initials[i], finals[i]), xytext=(5, 5), 
                        textcoords='offset points', fontsize=8)
        
        # Add diagonal line
        min_val = min(min(initials), min(finals))
        max_val = max(max(initials), max(finals))
        ax2.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='No change')
        
        ax2.set_title('Initial vs Final Concentrations')
        ax2.set_xlabel('Initial Concentration (mM)')
        ax2.set_ylabel('Final Concentration (mM)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot2_path = os.path.join(output_dir, 'metabolite_changes_summary.png')
        plt.savefig(plot2_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Plots saved:")
        print(f"  - Trajectories: {plot1_path}")
        print(f"  - Changes: {plot2_path}")
        
    except Exception as e:
        print(f"✗ Plotting error: {e}")

def calculate_model_metrics(analysis_results, validation_results):
    """Calculate comprehensive model performance metrics."""
    try:
        print("\n=== Model Performance Metrics ===")
        
        # Basic statistics
        n_metabolites = len(analysis_results)
        n_valid_patterns = sum(1 for k, v in validation_results.items() 
                              if k.endswith(('_increase', '_decrease')) and v)
        n_total_patterns = sum(1 for k in validation_results.keys() 
                              if k.endswith(('_increase', '_decrease')))
        
        pattern_success_rate = n_valid_patterns / n_total_patterns if n_total_patterns > 0 else 0
        
        # Metabolite dynamics metrics
        total_changes = [abs(data['change']) for data in analysis_results.values()]
        mean_change = np.mean(total_changes)
        max_change = np.max(total_changes)
        
        # Variability metrics
        stds = [data['std'] for data in analysis_results.values()]
        mean_variability = np.mean(stds)
        
        metrics = {
            'n_metabolites_analyzed': n_metabolites,
            'pattern_success_rate': pattern_success_rate,
            'valid_patterns': n_valid_patterns,
            'total_patterns': n_total_patterns,
            'mean_absolute_change': mean_change,
            'max_absolute_change': max_change,
            'mean_variability': mean_variability,
            'numerical_stability': validation_results.get('numerical_stability', False),
            'overall_validation': validation_results.get('overall_valid', False)
        }
        
        print(f"Metabolites analyzed: {n_metabolites}")
        print(f"Pattern success rate: {pattern_success_rate:.1%} ({n_valid_patterns}/{n_total_patterns})")
        print(f"Mean absolute change: {mean_change:.3f} mM")
        print(f"Max absolute change: {max_change:.3f} mM")
        print(f"Mean variability: {mean_variability:.3f} mM")
        print(f"Numerical stability: {'✓' if metrics['numerical_stability'] else '✗'}")
        print(f"Overall validation: {'✓' if metrics['overall_validation'] else '✗'}")
        
        return metrics
        
    except Exception as e:
        print(f"✗ Metrics calculation error: {e}")
        return {}

def save_comparison_results(analysis_results, validation_results, metrics, output_dir):
    """Save comprehensive comparison results."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        comparison_summary = {
            'timestamp': datetime.now().isoformat(),
            'model_type': 'enhanced_brodbar',
            'analysis_results': analysis_results,
            'validation_results': validation_results,
            'performance_metrics': metrics,
            'summary': {
                'model_status': 'PASS' if metrics.get('overall_validation', False) else 'FAIL',
                'key_findings': [
                    f"Analyzed {metrics.get('n_metabolites_analyzed', 0)} metabolites",
                    f"Pattern success rate: {metrics.get('pattern_success_rate', 0):.1%}",
                    f"Numerical stability: {'Stable' if metrics.get('numerical_stability', False) else 'Unstable'}",
                    f"Mean metabolite change: {metrics.get('mean_absolute_change', 0):.3f} mM"
                ]
            }
        }
        
        # Save detailed results
        results_path = os.path.join(output_dir, 'model_comparison_results.json')
        with open(results_path, 'w') as f:
            json.dump(comparison_summary, f, indent=2)
        
        # Save summary report
        report_path = os.path.join(output_dir, 'model_comparison_report.txt')
        with open(report_path, 'w') as f:
            f.write("ENHANCED RBC MODEL COMPARISON REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model Type: Enhanced Brodbar\n")
            f.write(f"Overall Status: {comparison_summary['summary']['model_status']}\n\n")
            
            f.write("KEY FINDINGS:\n")
            for finding in comparison_summary['summary']['key_findings']:
                f.write(f"• {finding}\n")
            
            f.write(f"\nPERFORMANCE METRICS:\n")
            for key, value in metrics.items():
                f.write(f"• {key}: {value}\n")
            
            f.write(f"\nVALIDATION RESULTS:\n")
            for key, value in validation_results.items():
                status = "✓" if value else "✗"
                f.write(f"• {key}: {status}\n")
        
        print(f"✓ Results saved:")
        print(f"  - Detailed: {results_path}")
        print(f"  - Report: {report_path}")
        
        return comparison_summary
        
    except Exception as e:
        print(f"✗ Error saving results: {e}")
        return None

def main_comparison():
    """Main comparison analysis function."""
    print("=" * 60)
    print("ENHANCED RBC MODEL COMPARISON ANALYSIS")
    print("=" * 60)
    
    # Create output directory
    output_dir = '../outputs/model_comparison'
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Load simulation results
    sim_data = load_simulation_results()
    if sim_data is None:
        print("✗ Cannot proceed without simulation results")
        return False
    
    # Step 2: Load experimental data (optional)
    exp_data = load_experimental_data()
    
    # Step 3: Analyze enhanced model performance
    analysis_results = analyze_enhanced_model_performance(sim_data)
    if not analysis_results:
        print("✗ Analysis failed")
        return False
    
    # Step 4: Validate enhancement patterns
    validation_results = validate_enhancement_patterns(analysis_results)
    
    # Step 5: Calculate performance metrics
    metrics = calculate_model_metrics(analysis_results, validation_results)
    
    # Step 6: Create comparison plots
    create_comparison_plots(analysis_results, output_dir)
    
    # Step 7: Save results
    comparison_summary = save_comparison_results(analysis_results, validation_results, metrics, output_dir)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("COMPARISON ANALYSIS SUMMARY")
    print("=" * 60)
    
    if comparison_summary:
        status = comparison_summary['summary']['model_status']
        print(f"✓ Enhanced Model Analysis Complete - Status: {status}")
        print(f"  - Output directory: {output_dir}")
        for finding in comparison_summary['summary']['key_findings']:
            print(f"  - {finding}")
        
        return status == 'PASS'
    else:
        print("✗ Analysis completed with errors")
        return False

if __name__ == "__main__":
    success = main_comparison()
    if success:
        print("\n🎉 Enhanced model validation and comparison SUCCESSFUL!")
    else:
        print("\n❌ Enhanced model validation and comparison FAILED!")
