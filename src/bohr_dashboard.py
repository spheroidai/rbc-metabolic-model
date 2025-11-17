"""
Interactive Dashboard Summary for Bohr Effect Analysis

Displays all key results from pH perturbation simulations with Bohr effect.

Author: Jorgelindo da Veiga
Date: 2025-11-15
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys


def create_dashboard_summary():
    """
    Create a comprehensive dashboard summarizing all Bohr effect analyses.
    """
    print("\n" + "="*70)
    print("BOHR EFFECT DASHBOARD - COMPLETE SUMMARY")
    print("="*70 + "\n")
    
    scenarios = {
        'alkalosis_severe': 'Severe Alkalosis (pH 7.4→7.8)',
        'acidosis_severe': 'Severe Acidosis (pH 7.4→7.0)'
    }
    
    results = {}
    
    # Load data for each scenario
    for scenario_key, scenario_name in scenarios.items():
        bohr_path = f"../Simulations/brodbar_{scenario_key}/bohr_effect/bohr_metrics.csv"
        
        if Path(bohr_path).exists():
            df = pd.read_csv(bohr_path)
            results[scenario_key] = {
                'name': scenario_name,
                'data': df,
                'exists': True
            }
            print(f"✓ Loaded {scenario_name}: {len(df)} time points")
        else:
            results[scenario_key] = {
                'name': scenario_name,
                'exists': False
            }
            print(f"✗ {scenario_name}: Data not found")
    
    if not any(r['exists'] for r in results.values()):
        print("\n⚠ No simulation data found. Run simulations first:")
        print("  python src/main.py --curve-fit 0.0 --ph-perturbation alkalosis --ph-severity severe")
        print("  python src/main.py --curve-fit 0.0 --ph-perturbation acidosis --ph-severity severe")
        return
    
    # Create comprehensive summary table
    print("\n" + "="*70)
    print("QUANTITATIVE SUMMARY")
    print("="*70 + "\n")
    
    print(f"{'Metric':<30} {'Alkalosis':<20} {'Acidosis':<20}")
    print("─"*70)
    
    metrics = [
        ('P50 Initial (mmHg)', 'P50_mmHg', 0),
        ('P50 Final (mmHg)', 'P50_mmHg', -1),
        ('P50 Mean (mmHg)', 'P50_mmHg', 'mean'),
        ('',) * 3,  # Separator
        ('Sat Arterial (%)', 'sat_arterial', 'mean', 100),
        ('Sat Venous (%)', 'sat_venous', 'mean', 100),
        ('O₂ Extraction (%)', 'O2_extracted_fraction', 'mean', 100),
        ('',) * 3,  # Separator
        ('pHi Initial', 'pHi', 0),
        ('pHi Final', 'pHi', -1),
        ('ΔpHi', 'pHi', 'delta'),
        ('',) * 3,  # Separator
        ('[BPG] Initial (mM)', 'BPG_mM', 0),
        ('[BPG] Final (mM)', 'BPG_mM', -1),
        ('Δ[BPG] (mM)', 'BPG_mM', 'delta'),
    ]
    
    for metric_info in metrics:
        if len(metric_info) < 2:
            print()  # Empty line
            continue
        
        metric_name = metric_info[0]
        col_name = metric_info[1]
        stat_type = metric_info[2]
        multiplier = metric_info[3] if len(metric_info) > 3 else 1
        
        values = {}
        for scenario_key in ['alkalosis_severe', 'acidosis_severe']:
            if results[scenario_key]['exists']:
                df = results[scenario_key]['data']
                
                if stat_type == 'mean':
                    val = df[col_name].mean() * multiplier
                elif stat_type == 'delta':
                    val = (df[col_name].iloc[-1] - df[col_name].iloc[0]) * multiplier
                elif isinstance(stat_type, int):
                    val = df[col_name].iloc[stat_type] * multiplier
                
                values[scenario_key] = val
            else:
                values[scenario_key] = None
        
        alk_str = f"{values['alkalosis_severe']:.2f}" if values['alkalosis_severe'] is not None else "N/A"
        aci_str = f"{values['acidosis_severe']:.2f}" if values['acidosis_severe'] is not None else "N/A"
        
        print(f"{metric_name:<30} {alk_str:<20} {aci_str:<20}")
    
    print("\n" + "="*70)
    print("PHYSIOLOGICAL INSIGHTS")
    print("="*70 + "\n")
    
    if results['alkalosis_severe']['exists']:
        df_alk = results['alkalosis_severe']['data']
        print("ALKALOSIS:")
        print(f"  • P50 dynamics: {df_alk['P50_mmHg'].iloc[0]:.1f} → {df_alk['P50_mmHg'].iloc[-1]:.1f} mmHg")
        print(f"  • 2,3-BPG: {df_alk['BPG_mM'].iloc[0]:.2f} → {df_alk['BPG_mM'].iloc[-1]:.2f} mM")
        
        if df_alk['BPG_mM'].iloc[-1] < 1.0:
            print("  ⚠ Severe BPG depletion → P50 increase despite alkalosis")
            print("  ⚠ BPG effect DOMINATES over pH direct effect")
        print()
    
    if results['acidosis_severe']['exists']:
        df_aci = results['acidosis_severe']['data']
        print("ACIDOSIS:")
        print(f"  • P50 dynamics: {df_aci['P50_mmHg'].iloc[0]:.1f} → {df_aci['P50_mmHg'].iloc[-1]:.1f} mmHg")
        print(f"  • 2,3-BPG: {df_aci['BPG_mM'].iloc[0]:.2f} → {df_aci['BPG_mM'].iloc[-1]:.2f} mM")
        
        if df_aci['P50_mmHg'].mean() > 27.0:
            print("  ✓ Enhanced O₂ release (P50↑)")
            print("  ✓ Beneficial for tissue oxygenation")
        print()
    
    # Create mini comparison plot if both exist
    if results['alkalosis_severe']['exists'] and results['acidosis_severe']['exists']:
        print("="*70)
        print("Creating comparison plot...")
        create_mini_comparison(results)
        print("✓ Comparison plot created")
    
    print("\n" + "="*70)
    print("AVAILABLE ANALYSES")
    print("="*70)
    print("\n📊 Detailed Plots Available:")
    
    for scenario_key, result in results.items():
        if result['exists']:
            base_dir = f"../Simulations/brodbar_{scenario_key}/bohr_effect"
            print(f"\n{result['name']}:")
            print(f"  • Bohr dynamics: {base_dir}/bohr_effect_dynamics.png")
            print(f"  • Summary text: {base_dir}/bohr_summary.txt")
            print(f"  • BPG analysis: {base_dir}/BPG_dynamics_analysis.png")
    
    print("\n🔬 Analysis Scripts:")
    print("  • Compare scenarios: python compare_bohr_scenarios.py")
    print("  • BPG dynamics: python analyze_BPG_dynamics.py [alkalosis|acidosis]")
    print("  • pH flux effects: python analyze_pH_flux_effects_early.py")
    
    print("\n" + "="*70 + "\n")


def create_mini_comparison(results):
    """Create a compact 2-panel comparison plot."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Bohr Effect: Alkalosis vs Acidosis - Key Metrics', 
                 fontsize=14, fontweight='bold')
    
    df_alk = results['alkalosis_severe']['data']
    df_aci = results['acidosis_severe']['data']
    
    # Plot 1: P50 comparison
    ax1 = axes[0]
    ax1.plot(df_alk['time'], df_alk['P50_mmHg'], 'b-', linewidth=2.5, label='Alkalosis', marker='o', markersize=2, alpha=0.8)
    ax1.plot(df_aci['time'], df_aci['P50_mmHg'], 'r-', linewidth=2.5, label='Acidosis', marker='s', markersize=2, alpha=0.8)
    ax1.axhline(26.8, color='gray', linestyle='--', alpha=0.5, label='Normal')
    ax1.set_xlabel('Time (hours)', fontweight='bold')
    ax1.set_ylabel('P50 (mmHg)', fontweight='bold')
    ax1.set_title('Half-Saturation Pressure', fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: O2 Extraction comparison
    ax2 = axes[1]
    ax2.plot(df_alk['time'], df_alk['O2_extracted_fraction']*100, 'b-', linewidth=2.5, label='Alkalosis', marker='o', markersize=2, alpha=0.8)
    ax2.plot(df_aci['time'], df_aci['O2_extracted_fraction']*100, 'r-', linewidth=2.5, label='Acidosis', marker='s', markersize=2, alpha=0.8)
    ax2.axhline(25, color='gray', linestyle='--', alpha=0.5, label='Normal (~25%)')
    ax2.set_xlabel('Time (hours)', fontweight='bold')
    ax2.set_ylabel('O₂ Extraction Fraction (%)', fontweight='bold')
    ax2.set_title('Oxygen Extraction', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = "../Simulations/brodbar/bohr_comparison/mini_comparison.png"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    create_dashboard_summary()
