"""
pH Perturbation Visualization Module

Creates specialized plots and PDF reports for pH perturbation effects on RBC metabolism.

Features:
---------
1. pHe/pHi temporal dynamics with lag analysis
2. pH-dependent enzyme activity modulation
3. Key metabolite responses (2,3-BPG, ATP, Lactate)
4. Before/After perturbation comparison
5. Comprehensive PDF report

Author: Jorgelindo da Veiga
Date: 2025-11-15
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import pH sensitivity parameters
import sys
import os
# Ensure src directory is in path
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

try:
    from ph_sensitivity_params import (pH_ENZYME_PARAMS, compute_pH_modulation,
                                        list_pH_sensitive_enzymes)
    ENZYME_PH_PARAMS = pH_ENZYME_PARAMS  # Alias for compatibility
    get_all_enzyme_names = list_pH_sensitive_enzymes  # Alias for compatibility
    PH_PARAMS_AVAILABLE = True
    print(f"✓ Loaded pH sensitivity parameters for {len(ENZYME_PH_PARAMS)} enzymes")
except ImportError as e:
    PH_PARAMS_AVAILABLE = False
    ENZYME_PH_PARAMS = {}
    print(f"⚠ Warning: pH sensitivity parameters not available ({e})")
    
    # Define dummy functions for compatibility
    def compute_pH_modulation(pH, enzyme_name):
        return 1.0
    def get_all_enzyme_names():
        return []


class PhVisualization:
    """
    Handles visualization of pH perturbation effects on RBC metabolism.
    """
    
    def __init__(self, flux_csv_path: str, output_dir: str = "html/brodbar/ph_analysis"):
        """
        Initialize pH visualization with flux data.
        
        Parameters:
        -----------
        flux_csv_path : str
            Path to reaction_fluxes.csv file
        output_dir : str
            Directory for saving pH-specific plots
        """
        self.flux_csv_path = flux_csv_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load flux data
        print(f"Loading flux data from: {flux_csv_path}")
        self.df_flux = pd.read_csv(flux_csv_path, index_col=0)
        self.times = self.df_flux.index.values
        
        print(f"  ✓ Loaded {len(self.df_flux)} time points")
        print(f"  ✓ Tracking {len(self.df_flux.columns)} reactions")
        
    def plot_pH_dynamics(self, pHi_data: Optional[np.ndarray] = None, 
                         pHe_data: Optional[np.ndarray] = None,
                         perturbation_start: float = 2.0) -> str:
        """
        Plot pHe and pHi temporal dynamics showing lag response.
        
        Parameters:
        -----------
        pHi_data : np.ndarray, optional
            Intracellular pH time series (if None, uses constant 7.2)
        pHe_data : np.ndarray, optional
            Extracellular pH time series (if None, uses constant 7.4)
        perturbation_start : float
            Time when perturbation starts (hours)
            
        Returns:
        --------
        str : Path to saved plot
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Use provided data or defaults
        if pHi_data is None:
            pHi_data = np.full_like(self.times, 7.2)
        if pHe_data is None:
            pHe_data = np.full_like(self.times, 7.4)
        
        # Plot 1: pH time series
        ax1.plot(self.times, pHe_data, 'b-', linewidth=2, label='pHe (extracellular)', marker='o', markersize=4)
        ax1.plot(self.times, pHi_data, 'r-', linewidth=2, label='pHi (intracellular)', marker='s', markersize=4)
        ax1.axvline(perturbation_start, color='gray', linestyle='--', alpha=0.5, label=f'Perturbation start (t={perturbation_start}h)')
        ax1.axhline(7.2, color='red', linestyle=':', alpha=0.3, label='Normal pHi')
        ax1.axhline(7.4, color='blue', linestyle=':', alpha=0.3, label='Normal pHe')
        ax1.set_xlabel('Time (hours)', fontsize=12)
        ax1.set_ylabel('pH', fontsize=12)
        ax1.set_title('Extracellular and Intracellular pH Dynamics', fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([min(pHi_data.min(), pHe_data.min()) - 0.1, 
                      max(pHi_data.max(), pHe_data.max()) + 0.1])
        
        # Plot 2: pH gradient (pHe - pHi)
        pH_gradient = pHe_data - pHi_data
        ax2.plot(self.times, pH_gradient, 'g-', linewidth=2, marker='d', markersize=4)
        ax2.axhline(0, color='black', linestyle='-', alpha=0.3)
        ax2.axvline(perturbation_start, color='gray', linestyle='--', alpha=0.5)
        ax2.fill_between(self.times, 0, pH_gradient, where=(pH_gradient >= 0), 
                         alpha=0.3, color='green', label='pHe > pHi (H+ influx)')
        ax2.fill_between(self.times, 0, pH_gradient, where=(pH_gradient < 0), 
                         alpha=0.3, color='red', label='pHe < pHi (H+ efflux)')
        ax2.set_xlabel('Time (hours)', fontsize=12)
        ax2.set_ylabel('pH Gradient (pHe - pHi)', fontsize=12)
        ax2.set_title('Transmembrane pH Gradient', fontsize=14, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / "pH_dynamics.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ pH dynamics plot saved: {output_path}")
        return str(output_path)
    
    def plot_enzyme_activities(self, pHi_data: np.ndarray) -> str:
        """
        Plot pH-dependent enzyme activity modulation over time.
        
        Parameters:
        -----------
        pHi_data : np.ndarray
            Intracellular pH time series
            
        Returns:
        --------
        str : Path to saved plot
        """
        if not PH_PARAMS_AVAILABLE:
            print("  ⚠ pH sensitivity parameters not available, skipping enzyme activity plot")
            return ""
        
        # Key pH-sensitive enzymes to plot
        key_enzymes = ['VHK', 'VPFK', 'VPK', 'VDPGM', 'VLDH', 'VG6PDH']
        
        fig, axes = plt.subplots(3, 2, figsize=(14, 12))
        axes = axes.flatten()
        
        for idx, enzyme in enumerate(key_enzymes):
            if enzyme in ENZYME_PH_PARAMS:
                # Compute activity modulation over time
                activities = []
                for pH in pHi_data:
                    f_pH = compute_pH_modulation(enzyme, pH)
                    activities.append(f_pH * 100)  # Convert to percentage
                
                activities = np.array(activities)
                
                # Plot
                ax = axes[idx]
                ax.plot(self.times, activities, linewidth=2, color='navy', marker='o', markersize=3)
                ax.axhline(100, color='black', linestyle='--', alpha=0.5, label='100% (normal)')
                ax.fill_between(self.times, 100, activities, where=(activities >= 100), 
                               alpha=0.3, color='green', label='Activation')
                ax.fill_between(self.times, 100, activities, where=(activities < 100), 
                               alpha=0.3, color='red', label='Inhibition')
                
                # Get pH optimum for annotation
                pH_opt = ENZYME_PH_PARAMS[enzyme]['pH_opt']
                
                ax.set_xlabel('Time (hours)', fontsize=10)
                ax.set_ylabel('Activity (%)', fontsize=10)
                ax.set_title(f'{enzyme} (pH opt: {pH_opt:.2f})', fontsize=11, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.legend(loc='best', fontsize=8)
                
                # Add min/max annotations
                min_activity = activities.min()
                max_activity = activities.max()
                ax.text(0.02, 0.98, f'Max: {max_activity:.1f}%\nMin: {min_activity:.1f}%', 
                       transform=ax.transAxes, fontsize=9, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = self.output_dir / "enzyme_activities_pH.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Enzyme activities plot saved: {output_path}")
        return str(output_path)
    
    def plot_key_metabolites(self, metabolite_data: Dict[str, np.ndarray],
                            perturbation_start: float = 2.0) -> str:
        """
        Plot key pH-sensitive metabolites (2,3-BPG, ATP, Lactate).
        
        Parameters:
        -----------
        metabolite_data : dict
            Dictionary with keys: 'BPG', 'ATP', 'ADP', 'LAC' and numpy arrays as values
        perturbation_start : float
            Time when perturbation starts
            
        Returns:
        --------
        str : Path to saved plot
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: 2,3-BPG
        if 'BPG' in metabolite_data:
            ax = axes[0, 0]
            bpg = metabolite_data['BPG']
            ax.plot(self.times, bpg, 'purple', linewidth=2, marker='o', markersize=4)
            ax.axvline(perturbation_start, color='gray', linestyle='--', alpha=0.5)
            ax.set_xlabel('Time (hours)', fontsize=11)
            ax.set_ylabel('Concentration (mM)', fontsize=11)
            ax.set_title('2,3-BPG (Oxygen Affinity Modulator)', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add change annotation
            bpg_initial = bpg[0]
            bpg_final = bpg[-1]
            change_pct = ((bpg_final - bpg_initial) / bpg_initial) * 100
            ax.text(0.02, 0.98, f'Δ = {change_pct:+.1f}%\nInitial: {bpg_initial:.3f} mM\nFinal: {bpg_final:.3f} mM', 
                   transform=ax.transAxes, fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
        
        # Plot 2: ATP
        if 'ATP' in metabolite_data:
            ax = axes[0, 1]
            atp = metabolite_data['ATP']
            ax.plot(self.times, atp, 'red', linewidth=2, marker='s', markersize=4, label='ATP')
            if 'ADP' in metabolite_data:
                adp = metabolite_data['ADP']
                ax.plot(self.times, adp, 'orange', linewidth=2, marker='^', markersize=4, label='ADP')
            ax.axvline(perturbation_start, color='gray', linestyle='--', alpha=0.5)
            ax.set_xlabel('Time (hours)', fontsize=11)
            ax.set_ylabel('Concentration (mM)', fontsize=11)
            ax.set_title('Energy Metabolism (ATP/ADP)', fontsize=12, fontweight='bold')
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            # Energy charge
            if 'ADP' in metabolite_data and 'AMP' in metabolite_data:
                amp = metabolite_data.get('AMP', np.zeros_like(atp))
                energy_charge = (atp + 0.5 * adp) / (atp + adp + amp + 1e-6)
                ax_twin = ax.twinx()
                ax_twin.plot(self.times, energy_charge, 'green', linewidth=1.5, 
                           linestyle='--', alpha=0.7, label='Energy Charge')
                ax_twin.set_ylabel('Energy Charge', fontsize=10, color='green')
                ax_twin.tick_params(axis='y', labelcolor='green')
                ax_twin.legend(loc='lower right', fontsize=9)
        
        # Plot 3: Lactate (intra + extra)
        if 'LAC' in metabolite_data:
            ax = axes[1, 0]
            lac = metabolite_data['LAC']
            ax.plot(self.times, lac, 'brown', linewidth=2, marker='d', markersize=4, label='Intracellular LAC')
            if 'ELAC' in metabolite_data:
                elac = metabolite_data['ELAC']
                ax.plot(self.times, elac, 'orange', linewidth=2, marker='o', markersize=4, label='Extracellular ELAC')
            ax.axvline(perturbation_start, color='gray', linestyle='--', alpha=0.5)
            ax.set_xlabel('Time (hours)', fontsize=11)
            ax.set_ylabel('Concentration (mM)', fontsize=11)
            ax.set_title('Lactate Production and Transport', fontsize=12, fontweight='bold')
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
        
        # Plot 4: Glycolytic flux summary
        ax = axes[1, 1]
        if all(flux in self.df_flux.columns for flux in ['VHK', 'VPFK', 'VPK']):
            ax.plot(self.times, self.df_flux['VHK'], linewidth=2, label='VHK (Hexokinase)', marker='o', markersize=3)
            ax.plot(self.times, self.df_flux['VPFK'], linewidth=2, label='VPFK (PFK - most pH-sensitive)', marker='s', markersize=3)
            ax.plot(self.times, self.df_flux['VPK'], linewidth=2, label='VPK (Pyruvate Kinase)', marker='^', markersize=3)
            ax.axvline(perturbation_start, color='gray', linestyle='--', alpha=0.5)
            ax.set_xlabel('Time (hours)', fontsize=11)
            ax.set_ylabel('Flux (mM/h)', fontsize=11)
            ax.set_title('Glycolytic Flux (pH-Sensitive Enzymes)', fontsize=12, fontweight='bold')
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = self.output_dir / "key_metabolites_pH.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Key metabolites plot saved: {output_path}")
        return str(output_path)
    
    def compare_scenarios(self, control_flux_csv: str, perturbed_flux_csv: str,
                         scenario_name: str = "Acidosis") -> str:
        """
        Compare control vs pH-perturbed scenarios side-by-side.
        
        Parameters:
        -----------
        control_flux_csv : str
            Path to control simulation flux CSV
        perturbed_flux_csv : str
            Path to perturbed simulation flux CSV
        scenario_name : str
            Name of perturbation scenario
            
        Returns:
        --------
        str : Path to saved plot
        """
        # Load both datasets
        df_control = pd.read_csv(control_flux_csv, index_col=0)
        df_perturbed = pd.read_csv(perturbed_flux_csv, index_col=0)
        
        # Key enzymes for comparison
        key_enzymes = ['VHK', 'VPFK', 'VPK', 'VDPGM']
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        for idx, enzyme in enumerate(key_enzymes):
            if enzyme in df_control.columns and enzyme in df_perturbed.columns:
                ax = axes[idx]
                
                times_control = df_control.index.values
                times_perturbed = df_perturbed.index.values
                
                ax.plot(times_control, df_control[enzyme], 'b-', linewidth=2, 
                       label='Control (pH 7.4)', marker='o', markersize=3)
                ax.plot(times_perturbed, df_perturbed[enzyme], 'r-', linewidth=2, 
                       label=f'{scenario_name}', marker='s', markersize=3)
                
                ax.set_xlabel('Time (hours)', fontsize=11)
                ax.set_ylabel('Flux (mM/h)', fontsize=11)
                ax.set_title(f'{enzyme}', fontsize=12, fontweight='bold')
                ax.legend(loc='best', fontsize=10)
                ax.grid(True, alpha=0.3)
                
                # Calculate average flux reduction
                avg_control = df_control[enzyme].mean()
                avg_perturbed = df_perturbed[enzyme].mean()
                reduction_pct = ((avg_perturbed - avg_control) / avg_control) * 100
                
                ax.text(0.02, 0.98, f'Avg change: {reduction_pct:+.1f}%', 
                       transform=ax.transAxes, fontsize=9, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        plt.suptitle(f'Flux Comparison: Control vs {scenario_name}', 
                    fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        output_path = self.output_dir / f"comparison_control_vs_{scenario_name.lower()}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Comparison plot saved: {output_path}")
        return str(output_path)
    
    def create_pH_report(self, plots: List[str], scenario_name: str = "pH Perturbation",
                        notes: str = "") -> str:
        """
        Create comprehensive PDF report with all pH-related plots.
        
        Parameters:
        -----------
        plots : list of str
            List of plot file paths to include
        scenario_name : str
            Name of the perturbation scenario
        notes : str
            Additional notes to include in report
            
        Returns:
        --------
        str : Path to saved PDF
        """
        output_path = self.output_dir / f"pH_Analysis_Report_{scenario_name.replace(' ', '_')}.pdf"
        
        with PdfPages(output_path) as pdf:
            # Title page
            fig = plt.figure(figsize=(11, 8.5))
            fig.text(0.5, 0.7, 'RBC Metabolic Model', ha='center', fontsize=24, fontweight='bold')
            fig.text(0.5, 0.6, f'{scenario_name} Analysis', ha='center', fontsize=20)
            fig.text(0.5, 0.5, f'pH Perturbation Effects', ha='center', fontsize=16, style='italic')
            fig.text(0.5, 0.3, f'Generated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}', 
                    ha='center', fontsize=12)
            fig.text(0.5, 0.2, f'Total plots: {len(plots)}', ha='center', fontsize=12)
            if notes:
                fig.text(0.5, 0.1, notes, ha='center', fontsize=10, style='italic', wrap=True)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Add all plots
            for plot_path in plots:
                if Path(plot_path).exists():
                    img = plt.imread(plot_path)
                    fig = plt.figure(figsize=(11, 8.5))
                    plt.imshow(img)
                    plt.axis('off')
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close()
        
        print(f"  ✓ PDF report saved: {output_path}")
        return str(output_path)


def generate_pH_analysis(flux_csv_path: str, output_dir: str = "html/brodbar/ph_analysis",
                        scenario_name: str = "Acidosis", 
                        pHi_data: Optional[np.ndarray] = None,
                        pHe_data: Optional[np.ndarray] = None,
                        metabolite_data: Optional[Dict[str, np.ndarray]] = None,
                        control_flux_csv: Optional[str] = None) -> str:
    """
    Generate complete pH analysis with all plots and PDF report.
    
    Parameters:
    -----------
    flux_csv_path : str
        Path to reaction_fluxes.csv
    output_dir : str
        Output directory for plots
    scenario_name : str
        Name of perturbation scenario
    pHi_data : np.ndarray, optional
        Intracellular pH time series
    pHe_data : np.ndarray, optional
        Extracellular pH time series
    metabolite_data : dict, optional
        Dictionary of key metabolite time series
    control_flux_csv : str, optional
        Path to control simulation flux CSV for comparison
        
    Returns:
    --------
    str : Path to PDF report
    """
    print(f"\n{'='*60}")
    print(f"GENERATING pH ANALYSIS: {scenario_name}")
    print(f"{'='*60}")
    
    viz = PhVisualization(flux_csv_path, output_dir)
    
    # Interpolate pH data to match flux timepoints if necessary
    if pHi_data is not None and len(pHi_data) != len(viz.times):
        print(f"⚠ pH data has {len(pHi_data)} points but flux has {len(viz.times)} points")
        print(f"  Interpolating pH data to match flux timepoints...")
        from scipy.interpolate import interp1d
        
        # Get original pH timepoints from metabolite CSV
        metabolite_csv_path = flux_csv_path.replace('fluxes/reaction_fluxes.csv', 
                                                     'metabolites/pH_metabolites.csv')
        try:
            df_metabolites = pd.read_csv(metabolite_csv_path)
            t_pH = df_metabolites['Time (hours)'].values
            
            # Interpolate pHi and pHe
            f_pHi = interp1d(t_pH, pHi_data, kind='linear', fill_value='extrapolate')
            f_pHe = interp1d(t_pH, pHe_data, kind='linear', fill_value='extrapolate')
            
            pHi_data = f_pHi(viz.times)
            pHe_data = f_pHe(viz.times)
            print(f"  ✓ Interpolated pH data to {len(pHi_data)} points")
        except Exception as e:
            print(f"  ✗ Interpolation failed: {e}")
            print(f"  Using original pH data (plots may fail)")
    
    plots = []
    
    # 1. pH dynamics
    print("\n📊 Generating pH dynamics plot...")
    plot_path = viz.plot_pH_dynamics(pHi_data, pHe_data)
    if plot_path:
        plots.append(plot_path)
    
    # 2. Enzyme activities
    if pHi_data is not None:
        print("\n📊 Generating enzyme activity plots...")
        plot_path = viz.plot_enzyme_activities(pHi_data)
        if plot_path:
            plots.append(plot_path)
    
    # 3. Key metabolites
    if metabolite_data:
        print("\n📊 Generating key metabolite plots...")
        plot_path = viz.plot_key_metabolites(metabolite_data)
        if plot_path:
            plots.append(plot_path)
    
    # 4. Comparison with control
    if control_flux_csv and Path(control_flux_csv).exists():
        print(f"\n📊 Generating comparison with control...")
        plot_path = viz.compare_scenarios(control_flux_csv, flux_csv_path, scenario_name)
        if plot_path:
            plots.append(plot_path)
    
    # 5. Create PDF report
    print("\n📄 Creating pH analysis PDF report...")
    notes = f"pH perturbation scenario: {scenario_name}\nTotal time points: {len(viz.times)}"
    pdf_path = viz.create_pH_report(plots, scenario_name, notes)
    
    print(f"\n{'='*60}")
    print(f"✓ pH ANALYSIS COMPLETE")
    print(f"  Output directory: {output_dir}")
    print(f"  Total plots: {len(plots)}")
    print(f"  PDF report: {pdf_path}")
    print(f"{'='*60}\n")
    
    return pdf_path


if __name__ == "__main__":
    """
    Test pH visualization module with example data.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ph_visualization.py <flux_csv_path> [scenario_name]")
        print("\nExample:")
        print("  python ph_visualization.py html/brodbar/fluxes/reaction_fluxes.csv Acidosis")
        sys.exit(1)
    
    flux_csv = sys.argv[1]
    scenario = sys.argv[2] if len(sys.argv) > 2 else "pH Perturbation"
    
    if not Path(flux_csv).exists():
        print(f"Error: Flux CSV file not found: {flux_csv}")
        sys.exit(1)
    
    # Generate analysis with default data
    pdf_report = generate_pH_analysis(
        flux_csv_path=flux_csv,
        scenario_name=scenario
    )
    
    print(f"\n✓ Analysis complete! PDF report: {pdf_report}")
