"""
Enzyme Flux Tracking and Analysis Module

Track all Michaelis-Menten reaction fluxes during RBC model simulation
while maintaining original MM kinetics.

Features:
- Record all enzyme fluxes at each time point
- Compute pathway-level flux distributions
- Identify rate-limiting steps
- Visualize flux patterns
- Export flux data for analysis

Author: Jorgelindo da Veiga
Date: October 2025
"""

import numpy as np
from numpy.typing import NDArray
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
from scipy.integrate import solve_ivp
from dataclasses import dataclass, field


@dataclass
class FluxRecord:
    """Store flux data for one enzyme reaction."""
    name: str
    pathway: str
    times: List[float] = field(default_factory=list)
    fluxes: List[float] = field(default_factory=list)
    vmax: float = 0.0
    km: float = 0.0
    
    def add_timepoint(self, t: float, flux: float):
        """Record flux at a time point."""
        self.times.append(t)
        self.fluxes.append(flux)
    
    def get_mean_flux(self) -> float:
        """Get time-averaged flux."""
        return np.mean(self.fluxes) if self.fluxes else 0.0
    
    def get_max_flux(self) -> float:
        """Get maximum flux."""
        return np.max(self.fluxes) if self.fluxes else 0.0


class FluxTracker:
    """
    Track all enzyme fluxes during ODE integration.
    
    This wraps the equadiff_brodbar function to record all
    Michaelis-Menten reaction rates at each time point.
    """
    
    def __init__(self):
        """Initialize flux tracker."""
        self.flux_records: Dict[str, FluxRecord] = {}
        self.time_points: List[float] = []
        self.current_fluxes: Dict[str, float] = {}
        
        # Define pathway groupings
        self.pathway_groups = {
            'Transport': ['VELAC', 'VEADE', 'VEINO', 'VEHYPX', 'VEMAL', 'VEGLC', 
                         'VEADO', 'VEPYR', 'VEGLN', 'VEGLU', 'VECYS'],
            'Glycolysis': ['VHK', 'VPGI', 'VPFK', 'VFDPA', 'VTPI', 'VGAPDH', 
                          'VPGK', 'VPGM', 'VENOPGM', 'VPK', 'VLDH'],
            'Pentose_Phosphate': ['VG6PDH', 'VPGLS', 'V6PGD', 'VR5PI', 'VR5PE', 
                                  'VTKL1', 'VTKL2', 'VTAL'],
            'Nucleotide': ['VAK', 'VAK2', 'VAPRT', 'VADA', 'VAMPD1', 'VHGPRT1', 
                          'VHGPRT2', 'VGMPS', 'VADSS', 'VIMPH', 'VPNPase1', 'VPRPPASE'],
            'Amino_Acid': ['VGLNS', 'VGDH', 'VASPTA', 'VALATA'],
            'Redox': ['VGSR', 'VGPX', 'VGLUCYS', 'VGSS'],
            'Other': ['V23DPGP', 'VDPGM', 'VME', 'VPC', 'VFUM', 'VMLD']
        }
        
        # Initialize flux records
        for pathway, reactions in self.pathway_groups.items():
            for rxn in reactions:
                self.flux_records[rxn] = FluxRecord(name=rxn, pathway=pathway)
    
    def record_flux(self, reaction_name: str, flux: float, t: float):
        """
        Record a flux value at a time point.
        
        Parameters:
        -----------
        reaction_name : str
            Name of the enzyme/reaction (e.g., 'VELAC', 'VHK')
        flux : float
            Reaction rate (mM/h)
        t : float
            Time point (hours)
        """
        if reaction_name not in self.flux_records:
            # Auto-detect pathway or assign to 'Other'
            pathway = 'Other'
            for pw, rxns in self.pathway_groups.items():
                if reaction_name in rxns:
                    pathway = pw
                    break
            self.flux_records[reaction_name] = FluxRecord(name=reaction_name, pathway=pathway)
        
        self.flux_records[reaction_name].add_timepoint(t, flux)
        self.current_fluxes[reaction_name] = flux
    
    def get_pathway_flux(self, pathway: str, t_index: int = -1) -> float:
        """
        Get total flux through a pathway at a time point.
        
        Parameters:
        -----------
        pathway : str
            Pathway name ('Glycolysis', 'Pentose_Phosphate', etc.)
        t_index : int
            Time index (-1 for last time point)
            
        Returns:
        --------
        float
            Sum of absolute fluxes in the pathway
        """
        total_flux = 0.0
        if pathway in self.pathway_groups:
            for rxn in self.pathway_groups[pathway]:
                if rxn in self.flux_records and self.flux_records[rxn].fluxes:
                    total_flux += abs(self.flux_records[rxn].fluxes[t_index])
        return total_flux
    
    def get_rate_limiting_steps(self, pathway: str, n_top: int = 5) -> List[Tuple[str, float]]:
        """
        Identify rate-limiting steps (lowest fluxes) in a pathway.
        
        Parameters:
        -----------
        pathway : str
            Pathway name
        n_top : int
            Number of top rate-limiting reactions to return
            
        Returns:
        --------
        List[Tuple[str, float]]
            List of (reaction_name, mean_flux) tuples, sorted by flux (ascending)
        """
        pathway_fluxes = []
        if pathway in self.pathway_groups:
            for rxn in self.pathway_groups[pathway]:
                if rxn in self.flux_records:
                    mean_flux = self.flux_records[rxn].get_mean_flux()
                    pathway_fluxes.append((rxn, abs(mean_flux)))
        
        # Sort by flux (ascending) - lowest fluxes are rate-limiting
        pathway_fluxes.sort(key=lambda x: x[1])
        return pathway_fluxes[:n_top]
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """
        Export all flux data to pandas DataFrame.
        
        Returns:
        --------
        pd.DataFrame
            DataFrame with columns: time, reaction, pathway, flux
        """
        data = []
        for rxn_name, record in self.flux_records.items():
            for t, flux in zip(record.times, record.fluxes):
                data.append({
                    'time': t,
                    'reaction': rxn_name,
                    'pathway': record.pathway,
                    'flux': flux
                })
        return pd.DataFrame(data)
    
    def plot_pathway_fluxes(self, pathway: str, save_path: Optional[str] = None):
        """
        Plot all fluxes in a pathway over time.
        
        Parameters:
        -----------
        pathway : str
            Pathway name
        save_path : Optional[str]
            Path to save plot (if None, displays plot)
        """
        if pathway not in self.pathway_groups:
            print(f"Unknown pathway: {pathway}")
            return
        
        plt.figure(figsize=(12, 6))
        
        for rxn in self.pathway_groups[pathway]:
            if rxn in self.flux_records and self.flux_records[rxn].fluxes:
                record = self.flux_records[rxn]
                plt.plot(record.times, record.fluxes, label=rxn, linewidth=2, alpha=0.7)
        
        plt.xlabel('Time (hours)', fontsize=12, fontweight='bold')
        plt.ylabel('Flux (mM/h)', fontsize=12, fontweight='bold')
        plt.title(f'{pathway} Pathway - Enzyme Fluxes', fontsize=14, fontweight='bold')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        else:
            plt.show()
        plt.close()
    
    def plot_pathway_distribution(self, t_index: int = -1, save_path: Optional[str] = None):
        """
        Plot flux distribution across all pathways at a time point.
        
        Parameters:
        -----------
        t_index : int
            Time index (-1 for last time point)
        save_path : Optional[str]
            Path to save plot
        """
        pathway_fluxes = {}
        for pathway in self.pathway_groups.keys():
            pathway_fluxes[pathway] = self.get_pathway_flux(pathway, t_index)
        
        # Sort by flux
        sorted_pathways = sorted(pathway_fluxes.items(), key=lambda x: x[1], reverse=True)
        pathways = [p[0] for p in sorted_pathways]
        fluxes = [p[1] for p in sorted_pathways]
        
        plt.figure(figsize=(10, 6))
        colors = plt.cm.Set3(np.linspace(0, 1, len(pathways)))
        bars = plt.bar(pathways, fluxes, color=colors, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar, flux in zip(bars, fluxes):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{flux:.2f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.xlabel('Metabolic Pathway', fontsize=12, fontweight='bold')
        plt.ylabel('Total Flux (mM/h)', fontsize=12, fontweight='bold')
        plt.title('Metabolic Flux Distribution Across Pathways', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        else:
            plt.show()
        plt.close()
    
    def generate_report(self, output_path: str = 'html/flux_analysis_report.txt'):
        """
        Generate comprehensive flux analysis report.
        
        Parameters:
        -----------
        output_path : str
            Path for output report file
        """
        with open(output_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("ENZYME FLUX ANALYSIS REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write("PATHWAY FLUX SUMMARY\n")
            f.write("-"*70 + "\n")
            for pathway in self.pathway_groups.keys():
                total_flux = self.get_pathway_flux(pathway)
                f.write(f"{pathway:20s}: {total_flux:10.4f} mM/h\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("RATE-LIMITING STEPS BY PATHWAY\n")
            f.write("="*70 + "\n\n")
            
            for pathway in self.pathway_groups.keys():
                f.write(f"\n{pathway}:\n")
                f.write("-"*50 + "\n")
                rate_limiting = self.get_rate_limiting_steps(pathway, n_top=3)
                for i, (rxn, flux) in enumerate(rate_limiting, 1):
                    f.write(f"  {i}. {rxn:15s}: {flux:10.6f} mM/h\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("TOP 10 HIGHEST FLUX REACTIONS (TIME-AVERAGED)\n")
            f.write("="*70 + "\n")
            
            all_fluxes = [(name, record.get_mean_flux(), record.pathway) 
                         for name, record in self.flux_records.items()]
            all_fluxes.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for i, (name, flux, pathway) in enumerate(all_fluxes[:10], 1):
                f.write(f"{i:2d}. {name:15s} ({pathway:20s}): {flux:10.6f} mM/h\n")
        
        print(f"Flux analysis report saved to: {output_path}")


def create_flux_tracking_wrapper(tracker: FluxTracker, custom_params: Optional[Dict] = None):
    """
    Create a wrapper function that tracks fluxes during simulation.
    
    This function wraps equadiff_brodbar to intercept and record all
    enzyme reaction rates while maintaining original MM kinetics.
    
    Parameters:
    -----------
    tracker : FluxTracker
        FluxTracker instance to record fluxes
    custom_params : Optional[Dict]
        Custom parameters for optimization
        
    Returns:
    --------
    function
        Wrapped ODE function that records fluxes
    """
    from equadiff_brodbar import equadiff_brodbar
    
    def wrapped_ode(t: float, x: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        ODE function with flux tracking.
        
        NOTE: This currently calls equadiff_brodbar which computes fluxes internally.
        To track individual fluxes, you would need to modify equadiff_brodbar to
        return flux values, or duplicate the flux calculations here.
        
        For now, this is a placeholder structure.
        """
        # Call original ODE function
        dxdt = equadiff_brodbar(t, x, thermo_constraints=None, custom_params=custom_params)
        
        # TODO: Extract individual fluxes from reactions
        # This requires accessing intermediate flux values from equadiff_brodbar
        # For demonstration, we'll track a few key reactions
        
        # Example flux tracking (you'll need to compute these from x vector)
        # tracker.record_flux('VELAC', flux_value, t)
        # tracker.record_flux('VHK', flux_value, t)
        # etc.
        
        return dxdt
    
    return wrapped_ode


# Example usage
if __name__ == "__main__":
    print("Flux Analyzer Module")
    print("="*70)
    print("\nThis module provides tools for tracking enzyme fluxes during")
    print("RBC metabolic model simulation while maintaining MM kinetics.")
    print("\nKey features:")
    print("  - Track all enzyme reaction rates")
    print("  - Analyze pathway-level flux distributions")
    print("  - Identify rate-limiting steps")
    print("  - Visualize flux patterns")
    print("  - Export data for further analysis")
