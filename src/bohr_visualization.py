"""
Bohr Effect Visualization Module

Creates comprehensive plots showing:
- P50 dynamics over time
- O2 saturation (arterial vs venous)
- O2 delivery metrics
- Correlation with pH and 2,3-BPG

Author: Jorgelindo da Veiga
Date: 2025-11-15
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Optional


def create_bohr_plots(bohr_csv_path: str, output_dir: str, scenario: Optional[str] = None):
    """
    Create comprehensive Bohr effect visualization plots.
    
    Parameters:
    -----------
    bohr_csv_path : str
        Path to bohr_metrics.csv file
    output_dir : str
        Directory to save plots
    scenario : str, optional
        pH perturbation scenario name (e.g., 'alkalosis', 'acidosis')
    """
    # Load Bohr data
    df = pd.read_csv(bohr_csv_path)
    
    # Create figure with 3x2 subplots
    fig = plt.subplots(3, 2, figsize=(16, 14))
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    
    scenario_title = f" - {scenario.capitalize()}" if scenario else ""
    fig.suptitle(f'Bohr Effect: O₂ Delivery Dynamics{scenario_title}',
                 fontsize=18, fontweight='bold', y=0.995)
    
    time = df['time'].values
    
    # Plot 1: P50 over time
    ax1 = axes[0, 0]
    ax1.plot(time, df['P50_mmHg'], 'b-', linewidth=2.5, label='P50')
    ax1.axhline(26.8, color='gray', linestyle='--', alpha=0.5, label='Normal P50 (26.8 mmHg)')
    ax1.fill_between(time, 25, 28.5, alpha=0.1, color='green', label='Physiological range')
    ax1.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('P50 (mmHg)', fontsize=11, fontweight='bold')
    ax1.set_title('Half-Saturation Pressure (P50)', fontsize=13, fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: O2 Saturations
    ax2 = axes[0, 1]
    ax2.plot(time, df['sat_arterial'] * 100, 'r-', linewidth=2.5, label='Arterial (pO₂=100 mmHg)', marker='o', markersize=3, markevery=max(1, len(time)//20))
    ax2.plot(time, df['sat_venous'] * 100, 'b-', linewidth=2.5, label='Venous (pO₂=40 mmHg)', marker='s', markersize=3, markevery=max(1, len(time)//20))
    ax2.axhline(97, color='red', linestyle=':', alpha=0.3, label='Normal arterial (~97%)')
    ax2.axhline(75, color='blue', linestyle=':', alpha=0.3, label='Normal venous (~75%)')
    ax2.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('O₂ Saturation (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Hemoglobin O₂ Saturation', fontsize=13, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(50, 100)
    
    # Plot 3: O2 Content
    ax3 = axes[1, 0]
    ax3.plot(time, df['O2_arterial_mL_per_dL'], 'r-', linewidth=2.5, label='Arterial O₂ content')
    ax3.plot(time, df['O2_venous_mL_per_dL'], 'b-', linewidth=2.5, label='Venous O₂ content')
    ax3.fill_between(time, df['O2_venous_mL_per_dL'], df['O2_arterial_mL_per_dL'],
                     alpha=0.3, color='green', label='O₂ extracted')
    ax3.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('O₂ Content (mL O₂/dL blood)', fontsize=11, fontweight='bold')
    ax3.set_title('Blood O₂ Content', fontsize=13, fontweight='bold')
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: O2 Extraction Fraction
    ax4 = axes[1, 1]
    ax4.plot(time, df['O2_extracted_fraction'] * 100, 'g-', linewidth=3, label='Extraction fraction')
    ax4.axhline(25, color='gray', linestyle='--', alpha=0.5, label='Normal (~25%)')
    ax4.fill_between(time, 20, 30, alpha=0.1, color='green', label='Normal range')
    ax4.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('O₂ Extraction Fraction (%)', fontsize=11, fontweight='bold')
    ax4.set_title('O₂ Extraction from Blood to Tissues', fontsize=13, fontweight='bold')
    ax4.legend(loc='best', fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(15, 35)
    
    # Plot 5: pH and 2,3-BPG
    ax5 = axes[2, 0]
    ax5_twin = ax5.twinx()
    
    line1 = ax5.plot(time, df['pHi'], 'purple', linewidth=2.5, label='pHi', marker='o', markersize=3, markevery=max(1, len(time)//20))
    ax5.axhline(7.2, color='purple', linestyle='--', alpha=0.3, label='Normal pHi (7.2)')
    ax5.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Intracellular pH (pHi)', fontsize=11, fontweight='bold', color='purple')
    ax5.tick_params(axis='y', labelcolor='purple')
    
    line2 = ax5_twin.plot(time, df['BPG_mM'], 'orange', linewidth=2.5, label='[2,3-BPG]', marker='s', markersize=3, markevery=max(1, len(time)//20))
    ax5_twin.axhline(5.0, color='orange', linestyle='--', alpha=0.3, label='Normal [2,3-BPG] (5 mM)')
    ax5_twin.set_ylabel('[2,3-BPG] (mM)', fontsize=11, fontweight='bold', color='orange')
    ax5_twin.tick_params(axis='y', labelcolor='orange')
    
    # Combine legends
    lines = line1 + line2
    labs = [l.get_label() for l in lines]
    ax5.legend(lines, labs, loc='best', fontsize=9)
    ax5.set_title('pH and 2,3-BPG Dynamics', fontsize=13, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: P50 vs pHi correlation
    ax6 = axes[2, 1]
    scatter = ax6.scatter(df['pHi'], df['P50_mmHg'], c=time, cmap='viridis',
                         s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
    
    # Add trend line
    if len(df) > 2:
        z = np.polyfit(df['pHi'], df['P50_mmHg'], 1)
        p = np.poly1d(z)
        pH_range = np.linspace(df['pHi'].min(), df['pHi'].max(), 100)
        ax6.plot(pH_range, p(pH_range), "r--", linewidth=2, alpha=0.8, label=f'Trend: P50 = {z[0]:.1f}·pH + {z[1]:.1f}')
    
    ax6.axvline(7.2, color='gray', linestyle='--', alpha=0.3, label='Normal pHi')
    ax6.axhline(26.8, color='gray', linestyle='--', alpha=0.3, label='Normal P50')
    ax6.set_xlabel('Intracellular pH (pHi)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('P50 (mmHg)', fontsize=11, fontweight='bold')
    ax6.set_title('Bohr Effect: P50 vs pH Correlation', fontsize=13, fontweight='bold')
    ax6.legend(loc='best', fontsize=9)
    ax6.grid(True, alpha=0.3)
    
    # Add colorbar for time
    cbar = plt.colorbar(scatter, ax=ax6, label='Time (hours)')
    cbar.set_label('Time (hours)', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot
    output_path = Path(output_dir) / "bohr_effect_dynamics.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✓ Bohr dynamics plot saved: {output_path}")
    plt.close()
    
    # Create summary statistics
    create_bohr_summary(df, output_dir, scenario)


def create_bohr_summary(df: pd.DataFrame, output_dir: str, scenario: Optional[str] = None):
    """
    Create a summary text file with key Bohr effect statistics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Bohr metrics dataframe
    output_dir : str
        Directory to save summary
    scenario : str, optional
        pH perturbation scenario name
    """
    summary_path = Path(output_dir) / "bohr_summary.txt"
    
    with open(summary_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write(f"BOHR EFFECT ANALYSIS SUMMARY{' - ' + scenario.upper() if scenario else ''}\n")
        f.write("="*70 + "\n\n")
        
        # Time range
        f.write(f"Time Range: {df['time'].min():.2f} - {df['time'].max():.2f} hours\n")
        f.write(f"Data Points: {len(df)}\n\n")
        
        # P50 statistics
        f.write("─" * 70 + "\n")
        f.write("P50 (Half-Saturation Pressure)\n")
        f.write("─" * 70 + "\n")
        f.write(f"Initial:  {df['P50_mmHg'].iloc[0]:.2f} mmHg\n")
        f.write(f"Final:    {df['P50_mmHg'].iloc[-1]:.2f} mmHg\n")
        f.write(f"Change:   {df['P50_mmHg'].iloc[-1] - df['P50_mmHg'].iloc[0]:+.2f} mmHg\n")
        f.write(f"Mean:     {df['P50_mmHg'].mean():.2f} ± {df['P50_mmHg'].std():.2f} mmHg\n")
        f.write(f"Range:    {df['P50_mmHg'].min():.2f} - {df['P50_mmHg'].max():.2f} mmHg\n")
        f.write(f"Normal:   26.8 mmHg\n\n")
        
        # O2 saturation statistics
        f.write("─" * 70 + "\n")
        f.write("O₂ Saturation\n")
        f.write("─" * 70 + "\n")
        f.write(f"Arterial (pO₂=100 mmHg):\n")
        f.write(f"  Initial:  {df['sat_arterial'].iloc[0]*100:.1f}%\n")
        f.write(f"  Final:    {df['sat_arterial'].iloc[-1]*100:.1f}%\n")
        f.write(f"  Mean:     {df['sat_arterial'].mean()*100:.1f}%\n\n")
        
        f.write(f"Venous (pO₂=40 mmHg):\n")
        f.write(f"  Initial:  {df['sat_venous'].iloc[0]*100:.1f}%\n")
        f.write(f"  Final:    {df['sat_venous'].iloc[-1]*100:.1f}%\n")
        f.write(f"  Mean:     {df['sat_venous'].mean()*100:.1f}%\n\n")
        
        # O2 extraction statistics
        f.write("─" * 70 + "\n")
        f.write("O₂ Extraction\n")
        f.write("─" * 70 + "\n")
        f.write(f"Extraction Fraction:\n")
        f.write(f"  Initial:  {df['O2_extracted_fraction'].iloc[0]*100:.1f}%\n")
        f.write(f"  Final:    {df['O2_extracted_fraction'].iloc[-1]*100:.1f}%\n")
        f.write(f"  Mean:     {df['O2_extracted_fraction'].mean()*100:.1f}%\n")
        f.write(f"  Normal:   ~25%\n\n")
        
        # pH and 2,3-BPG statistics
        f.write("─" * 70 + "\n")
        f.write("pH and 2,3-BPG\n")
        f.write("─" * 70 + "\n")
        f.write(f"pHi:\n")
        f.write(f"  Initial:  {df['pHi'].iloc[0]:.3f}\n")
        f.write(f"  Final:    {df['pHi'].iloc[-1]:.3f}\n")
        f.write(f"  Change:   {df['pHi'].iloc[-1] - df['pHi'].iloc[0]:+.3f}\n")
        f.write(f"  Normal:   7.2\n\n")
        
        f.write(f"[2,3-BPG]:\n")
        f.write(f"  Initial:  {df['BPG_mM'].iloc[0]:.2f} mM\n")
        f.write(f"  Final:    {df['BPG_mM'].iloc[-1]:.2f} mM\n")
        f.write(f"  Change:   {df['BPG_mM'].iloc[-1] - df['BPG_mM'].iloc[0]:+.2f} mM\n")
        f.write(f"  Normal:   5.0 mM\n\n")
        
        # Physiological interpretation
        f.write("="*70 + "\n")
        f.write("PHYSIOLOGICAL INTERPRETATION\n")
        f.write("="*70 + "\n\n")
        
        # Determine if alkalosis or acidosis
        pH_change = df['pHi'].iloc[-1] - df['pHi'].iloc[0]
        P50_change = df['P50_mmHg'].iloc[-1] - df['P50_mmHg'].iloc[0]
        
        if pH_change > 0.01:
            f.write("✓ ALKALOSIS DETECTED (pH increase)\n")
            f.write("  • ↑ pH → ↓ P50 → ↑ O₂ affinity\n")
            f.write("  • Hemoglobin holds O₂ more tightly\n")
            f.write("  • ↓ O₂ release to tissues\n")
            f.write("  • Potential tissue hypoxia risk\n\n")
        elif pH_change < -0.01:
            f.write("✓ ACIDOSIS DETECTED (pH decrease)\n")
            f.write("  • ↓ pH → ↑ P50 → ↓ O₂ affinity\n")
            f.write("  • Hemoglobin releases O₂ more easily\n")
            f.write("  • ↑ O₂ delivery to tissues\n")
            f.write("  • Beneficial Bohr effect for tissue O₂ supply\n\n")
        else:
            f.write("✓ pH STABLE (minimal change)\n")
            f.write("  • Maintained O₂ binding characteristics\n")
            f.write("  • Normal O₂ delivery capacity\n\n")
        
        f.write("="*70 + "\n")
    
    print(f"  ✓ Bohr summary saved: {summary_path}")


if __name__ == "__main__":
    """Test visualization with sample data."""
    print("This module is meant to be imported, not run directly.")
    print("Use: from bohr_visualization import create_bohr_plots")
