"""
Analyze 2,3-BPG Dynamics and Impact on Bohr Effect

Investigates why 2,3-BPG concentration changes during pH perturbations
and how this affects P50 and oxygen delivery.

Author: Jorgelindo da Veiga
Date: 2025-11-15
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def analyze_bpg_dynamics(scenario: str = "alkalosis"):
    """
    Analyze 2,3-BPG metabolism and its impact on Bohr effect.
    
    Parameters:
    -----------
    scenario : str
        pH perturbation scenario ('alkalosis' or 'acidosis')
    """
    print("\n" + "="*70)
    print(f"ANALYSE DYNAMIQUE 2,3-BPG - {scenario.upper()}")
    print("="*70)
    
    # Load Bohr data
    bohr_path = f"../Simulations/brodbar_{scenario}_severe/bohr_effect/bohr_metrics.csv"
    if not Path(bohr_path).exists():
        print(f"✗ Bohr data not found: {bohr_path}")
        return
    
    df_bohr = pd.read_csv(bohr_path)
    print(f"✓ Loaded Bohr metrics: {len(df_bohr)} time points")
    
    # Load flux data for BPG-related enzymes
    flux_path = f"../Simulations/brodbar_{scenario}_severe/fluxes/reaction_fluxes.csv"
    if not Path(flux_path).exists():
        print(f"✗ Flux data not found: {flux_path}")
        return
    
    df_flux = pd.read_csv(flux_path, index_col=0)
    print(f"✓ Loaded flux data: {len(df_flux)} time points")
    
    # Extract BPG-related fluxes
    bpg_enzymes = {
        'VDPGM': '2,3-BPG Mutase (production)',
        'V23DPGP': '2,3-BPG Phosphatase (degradation)',
        'VGAPDH': 'GAPDH (competes with DPGM)',
        'VPGK': 'PGK (downstream of BPG shunt)'
    }
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'2,3-BPG Dynamics and P50 Correlation - {scenario.capitalize()}',
                 fontsize=16, fontweight='bold')
    
    # Plot 1: BPG concentration over time
    ax1 = axes[0, 0]
    ax1.plot(df_bohr['time'], df_bohr['BPG_mM'], 'orange', linewidth=3, marker='o', markersize=4, markevery=max(1, len(df_bohr)//20))
    ax1.axhline(5.0, color='gray', linestyle='--', alpha=0.5, label='Normal (5.0 mM)')
    ax1.fill_between([0, df_bohr['time'].max()], 4, 6, alpha=0.1, color='green', label='Physiological range')
    ax1.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('[2,3-BPG] (mM)', fontsize=11, fontweight='bold')
    ax1.set_title('2,3-BPG Concentration', fontsize=13, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Add statistics text
    bpg_initial = df_bohr['BPG_mM'].iloc[0]
    bpg_final = df_bohr['BPG_mM'].iloc[-1]
    bpg_change = ((bpg_final - bpg_initial) / bpg_initial) * 100
    stats_text = f"Initial: {bpg_initial:.2f} mM\nFinal: {bpg_final:.2f} mM\nChange: {bpg_change:+.1f}%"
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             fontsize=10, fontweight='bold')
    
    # Plot 2: BPG metabolic fluxes
    ax2 = axes[0, 1]
    time_flux = df_flux.index.values
    
    for enzyme, label in bpg_enzymes.items():
        if enzyme in df_flux.columns:
            ax2.plot(time_flux, df_flux[enzyme], linewidth=2, label=label, alpha=0.8)
    
    ax2.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Flux (mM/h)', fontsize=11, fontweight='bold')
    ax2.set_title('BPG Metabolic Fluxes', fontsize=13, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    
    # Plot 3: P50 vs BPG correlation
    ax3 = axes[1, 0]
    scatter = ax3.scatter(df_bohr['BPG_mM'], df_bohr['P50_mmHg'], 
                         c=df_bohr['time'], cmap='plasma', s=60, alpha=0.7,
                         edgecolors='black', linewidth=0.5)
    
    # Add regression line
    if len(df_bohr) > 2:
        z = np.polyfit(df_bohr['BPG_mM'], df_bohr['P50_mmHg'], 1)
        p = np.poly1d(z)
        bpg_range = np.linspace(df_bohr['BPG_mM'].min(), df_bohr['BPG_mM'].max(), 100)
        ax3.plot(bpg_range, p(bpg_range), "r--", linewidth=2.5, alpha=0.8, 
                label=f'P50 = {z[0]:.2f}·[BPG] + {z[1]:.1f}')
        
        # Calculate correlation
        corr = np.corrcoef(df_bohr['BPG_mM'], df_bohr['P50_mmHg'])[0,1]
        ax3.text(0.05, 0.95, f'R = {corr:.3f}', transform=ax3.transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
                fontsize=11, fontweight='bold')
    
    ax3.axvline(5.0, color='gray', linestyle='--', alpha=0.3)
    ax3.axhline(26.8, color='gray', linestyle='--', alpha=0.3)
    ax3.set_xlabel('[2,3-BPG] (mM)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('P50 (mmHg)', fontsize=11, fontweight='bold')
    ax3.set_title('P50 vs [2,3-BPG] Correlation', fontsize=13, fontweight='bold')
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    
    cbar = plt.colorbar(scatter, ax=ax3)
    cbar.set_label('Time (hours)', fontsize=10, fontweight='bold')
    
    # Plot 4: pH and BPG together with dual axis
    ax4 = axes[1, 1]
    ax4_twin = ax4.twinx()
    
    line1 = ax4.plot(df_bohr['time'], df_bohr['pHi'], 'purple', linewidth=2.5, 
                     label='pHi', marker='o', markersize=3, markevery=max(1, len(df_bohr)//20))
    ax4.axhline(7.2, color='purple', linestyle='--', alpha=0.3)
    ax4.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('pHi', fontsize=11, fontweight='bold', color='purple')
    ax4.tick_params(axis='y', labelcolor='purple')
    
    line2 = ax4_twin.plot(df_bohr['time'], df_bohr['BPG_mM'], 'orange', linewidth=2.5,
                          label='[2,3-BPG]', marker='s', markersize=3, markevery=max(1, len(df_bohr)//20))
    ax4_twin.axhline(5.0, color='orange', linestyle='--', alpha=0.3)
    ax4_twin.set_ylabel('[2,3-BPG] (mM)', fontsize=11, fontweight='bold', color='orange')
    ax4_twin.tick_params(axis='y', labelcolor='orange')
    
    # Combine legends
    lines = line1 + line2
    labs = [l.get_label() for l in lines]
    ax4.legend(lines, labs, loc='best')
    ax4.set_title('pH-BPG Coupling', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    output_dir = f"../Simulations/brodbar_{scenario}_severe/bohr_effect"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "BPG_dynamics_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ BPG dynamics plot saved: {output_path}")
    plt.close()
    
    # Create detailed analysis report
    create_bpg_report(df_bohr, df_flux, scenario, output_dir)


def create_bpg_report(df_bohr: pd.DataFrame, df_flux: pd.DataFrame, scenario: str, output_dir: str):
    """
    Create detailed text report on BPG dynamics.
    """
    report_path = Path(output_dir) / "BPG_dynamics_report.txt"
    
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write(f"2,3-BPG DYNAMICS ANALYSIS - {scenario.upper()}\n")
        f.write("="*70 + "\n\n")
        
        # BPG concentration statistics
        f.write("─" * 70 + "\n")
        f.write("2,3-BPG Concentration\n")
        f.write("─" * 70 + "\n")
        bpg_initial = df_bohr['BPG_mM'].iloc[0]
        bpg_final = df_bohr['BPG_mM'].iloc[-1]
        bpg_min = df_bohr['BPG_mM'].min()
        bpg_max = df_bohr['BPG_mM'].max()
        bpg_mean = df_bohr['BPG_mM'].mean()
        
        f.write(f"Initial:  {bpg_initial:.3f} mM\n")
        f.write(f"Final:    {bpg_final:.3f} mM\n")
        f.write(f"Change:   {bpg_final - bpg_initial:+.3f} mM ({((bpg_final-bpg_initial)/bpg_initial*100):+.1f}%)\n")
        f.write(f"Mean:     {bpg_mean:.3f} mM\n")
        f.write(f"Range:    {bpg_min:.3f} - {bpg_max:.3f} mM\n")
        f.write(f"Normal:   5.0 mM\n\n")
        
        # P50 correlation with BPG
        f.write("─" * 70 + "\n")
        f.write("P50 vs [2,3-BPG] Correlation\n")
        f.write("─" * 70 + "\n")
        corr = np.corrcoef(df_bohr['BPG_mM'], df_bohr['P50_mmHg'])[0,1]
        z = np.polyfit(df_bohr['BPG_mM'], df_bohr['P50_mmHg'], 1)
        
        f.write(f"Correlation coefficient: {corr:.3f}\n")
        f.write(f"Linear fit: P50 = {z[0]:.2f}·[BPG] + {z[1]:.1f}\n")
        f.write(f"Slope: {z[0]:.2f} mmHg/mM\n\n")
        
        # Expected vs observed P50 from Bohr coefficient
        f.write("─" * 70 + "\n")
        f.write("Bohr Coefficient Analysis\n")
        f.write("─" * 70 + "\n")
        
        # Theoretical Bohr coefficient: -0.48
        pH_initial = df_bohr['pHi'].iloc[0]
        pH_final = df_bohr['pHi'].iloc[-1]
        delta_pH = pH_final - pH_initial
        
        # Expected P50 change from pH alone (Bohr effect)
        P50_normal = 26.8
        bohr_coef = -0.48
        expected_P50_from_pH = P50_normal * (1 + bohr_coef * delta_pH)
        
        # Expected P50 change from BPG alone
        bpg_coef = 0.3  # mmHg/mM from bohr_effect.py
        expected_P50_from_BPG = P50_normal + bpg_coef * (bpg_final - 5.0)
        
        # Observed P50
        P50_initial = df_bohr['P50_mmHg'].iloc[0]
        P50_final = df_bohr['P50_mmHg'].iloc[-1]
        
        f.write(f"pH change: {pH_initial:.3f} → {pH_final:.3f} (Δ = {delta_pH:+.3f})\n")
        f.write(f"Expected ΔP50 from pH alone: {expected_P50_from_pH - P50_normal:+.2f} mmHg\n")
        f.write(f"Expected ΔP50 from BPG alone: {expected_P50_from_BPG - P50_normal:+.2f} mmHg\n")
        f.write(f"Observed ΔP50: {P50_final - P50_initial:+.2f} mmHg\n\n")
        
        # Flux analysis
        f.write("─" * 70 + "\n")
        f.write("BPG Metabolic Fluxes\n")
        f.write("─" * 70 + "\n\n")
        
        time_early = 1.0
        time_late = 8.0
        
        # Find closest time indices
        idx_early = (df_flux.index - time_early).abs().argmin()
        idx_late = (df_flux.index - time_late).abs().argmin()
        
        for enzyme in ['VDPGM', 'V23DPGP']:
            if enzyme in df_flux.columns:
                flux_early = df_flux[enzyme].iloc[idx_early]
                flux_late = df_flux[enzyme].iloc[idx_late]
                change_pct = ((flux_late - flux_early) / (flux_early + 1e-9)) * 100
                
                enzyme_name = "2,3-BPG Mutase" if enzyme == "VDPGM" else "2,3-BPG Phosphatase"
                f.write(f"{enzyme_name}:\n")
                f.write(f"  t={time_early}h: {flux_early:.4f} mM/h\n")
                f.write(f"  t={time_late}h: {flux_late:.4f} mM/h\n")
                f.write(f"  Change: {change_pct:+.1f}%\n\n")
        
        # Interpretation
        f.write("="*70 + "\n")
        f.write("PHYSIOLOGICAL INTERPRETATION\n")
        f.write("="*70 + "\n\n")
        
        if scenario == "alkalosis":
            if bpg_final < bpg_initial * 0.5:
                f.write("⚠ SEVERE BPG DEPLETION DETECTED\n\n")
                f.write("Mechanism:\n")
                f.write("1. Extracellular alkalosis (pHe↑) applied\n")
                f.write("2. Intracellular pH buffering maintains low pHi\n")
                f.write("3. Low pHi inhibits 2,3-BPG Mutase (DPGM)\n")
                f.write("4. BPG production ↓↓↓\n")
                f.write("5. BPG depletion → P50↑ (counterintuitive!)\n\n")
                f.write("Result:\n")
                f.write("• BPG effect DOMINATES over pH direct effect\n")
                f.write("• P50 increases despite alkalosis\n")
                f.write("• O₂ affinity decreases (opposite of expected)\n")
        elif scenario == "acidosis":
            if bpg_final > bpg_initial * 1.2:
                f.write("✓ BPG PRODUCTION ENHANCED\n\n")
                f.write("Mechanism:\n")
                f.write("1. Extracellular acidosis (pHe↓) applied\n")
                f.write("2. Intracellular pH may increase (compensation)\n")
                f.write("3. Favorable pH for DPGM activity\n")
                f.write("4. BPG production ↑\n")
                f.write("5. BPG accumulation → P50↑\n\n")
                f.write("Result:\n")
                f.write("• Both pH and BPG effects synergize\n")
                f.write("• P50 increases (expected for acidosis)\n")
                f.write("• Enhanced O₂ release to tissues\n")
        
        f.write("\n" + "="*70 + "\n")
    
    print(f"✓ BPG dynamics report saved: {report_path}")


if __name__ == "__main__":
    import sys
    
    scenario = sys.argv[1] if len(sys.argv) > 1 else "alkalosis"
    analyze_bpg_dynamics(scenario)
