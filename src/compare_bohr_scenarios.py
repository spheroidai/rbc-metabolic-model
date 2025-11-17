"""
Comparative Analysis: Bohr Effect in Alkalosis vs Acidosis

Compares P50, O2 saturation, and delivery metrics between pH perturbation scenarios.

Author: Jorgelindo da Veiga
Date: 2025-11-15
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def compare_bohr_scenarios(alkalosis_csv: str, acidosis_csv: str, output_dir: str = "../Simulations/brodbar/bohr_comparison"):
    """
    Create comprehensive comparison plots between alkalosis and acidosis.
    
    Parameters:
    -----------
    alkalosis_csv : str
        Path to alkalosis bohr_metrics.csv
    acidosis_csv : str
        Path to acidosis bohr_metrics.csv
    output_dir : str
        Directory to save comparison plots
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\n" + "="*70)
    print("COMPARATIVE BOHR EFFECT ANALYSIS: ALKALOSIS vs ACIDOSIS")
    print("="*70)
    
    try:
        df_alk = pd.read_csv(alkalosis_csv)
        print(f"✓ Loaded alkalosis data: {len(df_alk)} time points")
    except FileNotFoundError:
        print(f"✗ Alkalosis file not found: {alkalosis_csv}")
        return
    
    try:
        df_aci = pd.read_csv(acidosis_csv)
        print(f"✓ Loaded acidosis data: {len(df_aci)} time points")
    except FileNotFoundError:
        print(f"✗ Acidosis file not found: {acidosis_csv}")
        return
    
    # Create comparison figure
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle('Bohr Effect Comparison: Alkalosis vs Acidosis',
                 fontsize=18, fontweight='bold', y=0.995)
    
    # Plot 1: P50 comparison
    ax1 = axes[0, 0]
    ax1.plot(df_alk['time'], df_alk['P50_mmHg'], 'b-', linewidth=2.5, label='Alkalosis', marker='o', markersize=3, markevery=max(1, len(df_alk)//20))
    ax1.plot(df_aci['time'], df_aci['P50_mmHg'], 'r-', linewidth=2.5, label='Acidosis', marker='s', markersize=3, markevery=max(1, len(df_aci)//20))
    ax1.axhline(26.8, color='gray', linestyle='--', alpha=0.5, label='Normal (26.8 mmHg)')
    ax1.fill_between([0, max(df_alk['time'].max(), df_aci['time'].max())], 25, 28.5, alpha=0.1, color='green')
    ax1.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('P50 (mmHg)', fontsize=11, fontweight='bold')
    ax1.set_title('Half-Saturation Pressure (P50)', fontsize=13, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Arterial O2 Saturation
    ax2 = axes[0, 1]
    ax2.plot(df_alk['time'], df_alk['sat_arterial']*100, 'b-', linewidth=2.5, label='Alkalosis (arterial)', alpha=0.8)
    ax2.plot(df_aci['time'], df_aci['sat_arterial']*100, 'r-', linewidth=2.5, label='Acidosis (arterial)', alpha=0.8)
    ax2.axhline(97, color='gray', linestyle='--', alpha=0.3, label='Normal (~97%)')
    ax2.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Arterial O₂ Saturation (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Arterial O₂ Saturation (pO₂=100 mmHg)', fontsize=13, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(90, 100)
    
    # Plot 3: Venous O2 Saturation
    ax3 = axes[1, 0]
    ax3.plot(df_alk['time'], df_alk['sat_venous']*100, 'b-', linewidth=2.5, label='Alkalosis (venous)', alpha=0.8)
    ax3.plot(df_aci['time'], df_aci['sat_venous']*100, 'r-', linewidth=2.5, label='Acidosis (venous)', alpha=0.8)
    ax3.axhline(75, color='gray', linestyle='--', alpha=0.3, label='Normal (~75%)')
    ax3.fill_between([0, max(df_alk['time'].max(), df_aci['time'].max())], 70, 80, alpha=0.1, color='green')
    ax3.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Venous O₂ Saturation (%)', fontsize=11, fontweight='bold')
    ax3.set_title('Venous O₂ Saturation (pO₂=40 mmHg)', fontsize=13, fontweight='bold')
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(50, 85)
    
    # Plot 4: O2 Extraction Fraction
    ax4 = axes[1, 1]
    ax4.plot(df_alk['time'], df_alk['O2_extracted_fraction']*100, 'b-', linewidth=2.5, label='Alkalosis', alpha=0.8)
    ax4.plot(df_aci['time'], df_aci['O2_extracted_fraction']*100, 'r-', linewidth=2.5, label='Acidosis', alpha=0.8)
    ax4.axhline(25, color='gray', linestyle='--', alpha=0.5, label='Normal (~25%)')
    ax4.fill_between([0, max(df_alk['time'].max(), df_aci['time'].max())], 20, 30, alpha=0.1, color='green')
    ax4.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('O₂ Extraction Fraction (%)', fontsize=11, fontweight='bold')
    ax4.set_title('O₂ Extraction from Blood to Tissues', fontsize=13, fontweight='bold')
    ax4.legend(loc='best', fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: pH Comparison
    ax5 = axes[2, 0]
    ax5.plot(df_alk['time'], df_alk['pHi'], 'b-', linewidth=2.5, label='Alkalosis pHi', marker='o', markersize=3, markevery=max(1, len(df_alk)//20))
    ax5.plot(df_aci['time'], df_aci['pHi'], 'r-', linewidth=2.5, label='Acidosis pHi', marker='s', markersize=3, markevery=max(1, len(df_aci)//20))
    ax5.axhline(7.2, color='gray', linestyle='--', alpha=0.5, label='Normal pHi (7.2)')
    ax5.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Intracellular pH (pHi)', fontsize=11, fontweight='bold')
    ax5.set_title('pH Dynamics Comparison', fontsize=13, fontweight='bold')
    ax5.legend(loc='best', fontsize=10)
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: 2,3-BPG Comparison
    ax6 = axes[2, 1]
    ax6.plot(df_alk['time'], df_alk['BPG_mM'], 'b-', linewidth=2.5, label='Alkalosis [2,3-BPG]', marker='o', markersize=3, markevery=max(1, len(df_alk)//20))
    ax6.plot(df_aci['time'], df_aci['BPG_mM'], 'r-', linewidth=2.5, label='Acidosis [2,3-BPG]', marker='s', markersize=3, markevery=max(1, len(df_aci)//20))
    ax6.axhline(5.0, color='gray', linestyle='--', alpha=0.5, label='Normal (5 mM)')
    ax6.fill_between([0, max(df_alk['time'].max(), df_aci['time'].max())], 4, 6, alpha=0.1, color='green')
    ax6.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('[2,3-BPG] (mM)', fontsize=11, fontweight='bold')
    ax6.set_title('2,3-BPG Concentration Dynamics', fontsize=13, fontweight='bold')
    ax6.legend(loc='best', fontsize=10)
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    output_path = Path(output_dir) / "bohr_comparison_alkalosis_vs_acidosis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Comparison plot saved: {output_path}")
    plt.close()
    
    # Create quantitative comparison summary
    create_comparison_summary(df_alk, df_aci, output_dir)
    
    return df_alk, df_aci


def create_comparison_summary(df_alk: pd.DataFrame, df_aci: pd.DataFrame, output_dir: str):
    """
    Create a detailed text summary comparing alkalosis and acidosis.
    """
    summary_path = Path(output_dir) / "bohr_comparison_summary.txt"
    
    with open(summary_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("BOHR EFFECT: ALKALOSIS vs ACIDOSIS COMPARISON\n")
        f.write("="*70 + "\n\n")
        
        # P50 Comparison
        f.write("─" * 70 + "\n")
        f.write("P50 (Half-Saturation Pressure)\n")
        f.write("─" * 70 + "\n\n")
        
        f.write("ALKALOSIS:\n")
        f.write(f"  Initial:  {df_alk['P50_mmHg'].iloc[0]:.2f} mmHg\n")
        f.write(f"  Final:    {df_alk['P50_mmHg'].iloc[-1]:.2f} mmHg\n")
        f.write(f"  Change:   {df_alk['P50_mmHg'].iloc[-1] - df_alk['P50_mmHg'].iloc[0]:+.2f} mmHg\n")
        f.write(f"  Mean:     {df_alk['P50_mmHg'].mean():.2f} mmHg\n\n")
        
        f.write("ACIDOSIS:\n")
        f.write(f"  Initial:  {df_aci['P50_mmHg'].iloc[0]:.2f} mmHg\n")
        f.write(f"  Final:    {df_aci['P50_mmHg'].iloc[-1]:.2f} mmHg\n")
        f.write(f"  Change:   {df_aci['P50_mmHg'].iloc[-1] - df_aci['P50_mmHg'].iloc[0]:+.2f} mmHg\n")
        f.write(f"  Mean:     {df_aci['P50_mmHg'].mean():.2f} mmHg\n\n")
        
        f.write(f"DIFFERENCE (Acidosis - Alkalosis):\n")
        f.write(f"  ΔP50 = {df_aci['P50_mmHg'].mean() - df_alk['P50_mmHg'].mean():+.2f} mmHg\n\n")
        
        # O2 Saturation Comparison
        f.write("─" * 70 + "\n")
        f.write("O₂ Saturation\n")
        f.write("─" * 70 + "\n\n")
        
        f.write("ARTERIAL (pO₂=100 mmHg):\n")
        f.write(f"  Alkalosis: {df_alk['sat_arterial'].mean()*100:.1f}%\n")
        f.write(f"  Acidosis:  {df_aci['sat_arterial'].mean()*100:.1f}%\n")
        f.write(f"  Δ = {(df_aci['sat_arterial'].mean() - df_alk['sat_arterial'].mean())*100:+.1f}%\n\n")
        
        f.write("VENOUS (pO₂=40 mmHg):\n")
        f.write(f"  Alkalosis: {df_alk['sat_venous'].mean()*100:.1f}%\n")
        f.write(f"  Acidosis:  {df_aci['sat_venous'].mean()*100:.1f}%\n")
        f.write(f"  Δ = {(df_aci['sat_venous'].mean() - df_alk['sat_venous'].mean())*100:+.1f}%\n\n")
        
        # O2 Extraction Comparison
        f.write("─" * 70 + "\n")
        f.write("O₂ Extraction Fraction\n")
        f.write("─" * 70 + "\n\n")
        
        f.write(f"  Alkalosis: {df_alk['O2_extracted_fraction'].mean()*100:.1f}%\n")
        f.write(f"  Acidosis:  {df_aci['O2_extracted_fraction'].mean()*100:.1f}%\n")
        f.write(f"  Δ = {(df_aci['O2_extracted_fraction'].mean() - df_alk['O2_extracted_fraction'].mean())*100:+.1f}%\n\n")
        
        # pH Comparison
        f.write("─" * 70 + "\n")
        f.write("pH Dynamics\n")
        f.write("─" * 70 + "\n\n")
        
        f.write(f"ALKALOSIS pHi:\n")
        f.write(f"  Initial: {df_alk['pHi'].iloc[0]:.3f}\n")
        f.write(f"  Final:   {df_alk['pHi'].iloc[-1]:.3f}\n")
        f.write(f"  Δ = {df_alk['pHi'].iloc[-1] - df_alk['pHi'].iloc[0]:+.3f}\n\n")
        
        f.write(f"ACIDOSIS pHi:\n")
        f.write(f"  Initial: {df_aci['pHi'].iloc[0]:.3f}\n")
        f.write(f"  Final:   {df_aci['pHi'].iloc[-1]:.3f}\n")
        f.write(f"  Δ = {df_aci['pHi'].iloc[-1] - df_aci['pHi'].iloc[0]:+.3f}\n\n")
        
        # 2,3-BPG Comparison
        f.write("─" * 70 + "\n")
        f.write("2,3-BPG Concentration\n")
        f.write("─" * 70 + "\n\n")
        
        f.write(f"ALKALOSIS [2,3-BPG]:\n")
        f.write(f"  Initial: {df_alk['BPG_mM'].iloc[0]:.2f} mM\n")
        f.write(f"  Final:   {df_alk['BPG_mM'].iloc[-1]:.2f} mM\n")
        f.write(f"  Δ = {df_alk['BPG_mM'].iloc[-1] - df_alk['BPG_mM'].iloc[0]:+.2f} mM\n\n")
        
        f.write(f"ACIDOSIS [2,3-BPG]:\n")
        f.write(f"  Initial: {df_aci['BPG_mM'].iloc[0]:.2f} mM\n")
        f.write(f"  Final:   {df_aci['BPG_mM'].iloc[-1]:.2f} mM\n")
        f.write(f"  Δ = {df_aci['BPG_mM'].iloc[-1] - df_aci['BPG_mM'].iloc[0]:+.2f} mM\n\n")
        
        # Physiological Interpretation
        f.write("="*70 + "\n")
        f.write("PHYSIOLOGICAL INTERPRETATION\n")
        f.write("="*70 + "\n\n")
        
        # Determine dominant effect
        P50_alk = df_alk['P50_mmHg'].mean()
        P50_aci = df_aci['P50_mmHg'].mean()
        
        if P50_aci > P50_alk:
            f.write("✓ CLASSIC BOHR EFFECT CONFIRMED:\n")
            f.write(f"  • Acidosis (↓pH) → ↑P50 ({P50_aci:.1f} mmHg) → ↓O₂ affinity\n")
            f.write(f"  • Alkalosis (↑pH) → ↓P50 ({P50_alk:.1f} mmHg) → ↑O₂ affinity\n")
            f.write(f"  • ΔP50 = {P50_aci - P50_alk:.1f} mmHg\n\n")
            
            f.write("CLINICAL SIGNIFICANCE:\n")
            f.write("  • Acidosis facilitates O₂ release to tissues (beneficial)\n")
            f.write("  • Alkalosis impairs O₂ release (tissue hypoxia risk)\n")
        else:
            f.write("⚠ INVERSE EFFECT OBSERVED (2,3-BPG dominated):\n")
            f.write(f"  • Unexpected P50 pattern suggests metabolic compensation\n")
            f.write(f"  • Check 2,3-BPG dynamics for explanation\n")
        
        f.write("\n" + "="*70 + "\n")
    
    print(f"✓ Comparison summary saved: {summary_path}")


if __name__ == "__main__":
    """Run comparison if both datasets are available."""
    
    alkalosis_path = "../Simulations/brodbar_alkalosis_severe/bohr_effect/bohr_metrics.csv"
    acidosis_path = "../Simulations/brodbar_acidosis_severe/bohr_effect/bohr_metrics.csv"
    
    # Check if files exist
    if not Path(alkalosis_path).exists():
        print(f"\n⚠ Alkalosis data not found at: {alkalosis_path}")
        print("Run: python src/main.py --curve-fit 0.0 --ph-perturbation alkalosis --ph-severity severe")
    
    if not Path(acidosis_path).exists():
        print(f"\n⚠ Acidosis data not found at: {acidosis_path}")
        print("Run: python src/main.py --curve-fit 0.0 --ph-perturbation acidosis --ph-severity severe")
    
    if Path(alkalosis_path).exists() and Path(acidosis_path).exists():
        print("\n✓ Both datasets available. Running comparison...")
        compare_bohr_scenarios(alkalosis_path, acidosis_path)
        print("\n🎉 Comparison complete!")
    else:
        print("\n📝 Waiting for simulation data...")
