"""
Extended pH Sensitivity Parameters - Additional Enzymes

Extends the original 14 pH-sensitive enzymes with additional metabolic enzymes
from amino acid metabolism, nucleotide metabolism, and other pathways.

Total enzymes: 14 (original) + 12 (new) = 26 pH-sensitive enzymes

New Enzymes Added:
------------------
Amino Acid Metabolism:
- VGLNS (Glutamine Synthetase)
- VGDH (Glutamate Dehydrogenase)
- VASAT (Aspartate Aminotransferase)
- VALAT (Alanine Aminotransferase)

Nucleotide Metabolism:
- VAPRT (Adenine Phosphoribosyltransferase)
- VADA (Adenosine Deaminase)
- VHXK (Hypoxanthine-guanine phosphoribosyltransferase)
- VGMPS (GMP Synthase)

Redox & Other:
- VGR (Glutathione Reductase)
- VGSSG (GSSG formation)
- VTKT (Transketolase)
- VTALDO (Transaldolase)

Author: Jorgelindo da Veiga
Date: 2025-11-15
"""

import numpy as np
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


# Extended enzyme pH parameters
# Format: {enzyme_name: {'pH_opt': optimal_pH, 'n_hill': Hill_coefficient, 'pathway': pathway_name}}

EXTENDED_ENZYME_PH_PARAMS = {
    # ===== AMINO ACID METABOLISM =====
    'VGLNS': {
        'pH_opt': 7.4,
        'n_hill': 2.0,
        'pathway': 'Amino Acid',
        'description': 'Glutamine Synthetase - NH3 detoxification'
    },
    'VGDH': {
        'pH_opt': 8.0,
        'n_hill': 2.5,
        'pathway': 'Amino Acid',
        'description': 'Glutamate Dehydrogenase - oxidative deamination'
    },
    'VASAT': {
        'pH_opt': 7.8,
        'n_hill': 2.2,
        'pathway': 'Amino Acid',
        'description': 'Aspartate Aminotransferase (AST/GOT)'
    },
    'VALAT': {
        'pH_opt': 7.6,
        'n_hill': 2.0,
        'pathway': 'Amino Acid',
        'description': 'Alanine Aminotransferase (ALT/GPT)'
    },
    
    # ===== NUCLEOTIDE METABOLISM =====
    'VAPRT': {
        'pH_opt': 7.2,
        'n_hill': 2.5,
        'pathway': 'Nucleotide',
        'description': 'Adenine Phosphoribosyltransferase - purine salvage'
    },
    'VADA': {
        'pH_opt': 7.0,
        'n_hill': 3.0,
        'pathway': 'Nucleotide',
        'description': 'Adenosine Deaminase - purine catabolism'
    },
    'VHXK': {
        'pH_opt': 7.4,
        'n_hill': 2.3,
        'pathway': 'Nucleotide',
        'description': 'Hypoxanthine-guanine phosphoribosyltransferase (HGPRT)'
    },
    'VGMPS': {
        'pH_opt': 7.5,
        'n_hill': 2.2,
        'pathway': 'Nucleotide',
        'description': 'GMP Synthase - guanine nucleotide biosynthesis'
    },
    
    # ===== REDOX METABOLISM =====
    'VGR': {
        'pH_opt': 7.6,
        'n_hill': 2.8,
        'pathway': 'Redox',
        'description': 'Glutathione Reductase - GSSG → GSH'
    },
    'VGSSG': {
        'pH_opt': 7.2,
        'n_hill': 2.0,
        'pathway': 'Redox',
        'description': 'GSSG formation - GSH oxidation'
    },
    
    # ===== PENTOSE PHOSPHATE PATHWAY =====
    'VTKT': {
        'pH_opt': 7.8,
        'n_hill': 2.4,
        'pathway': 'PPP',
        'description': 'Transketolase - non-oxidative PPP'
    },
    'VTALDO': {
        'pH_opt': 7.6,
        'n_hill': 2.2,
        'pathway': 'PPP',
        'description': 'Transaldolase - non-oxidative PPP'
    },
}


def get_extended_enzyme_params() -> Dict:
    """
    Get all enzyme pH parameters (original + extended).
    
    Returns:
    --------
    dict : Complete enzyme pH parameters
    """
    # Import original parameters
    try:
        from ph_sensitivity_params import ENZYME_PH_PARAMS as ORIGINAL_PARAMS
        
        # Merge original and extended
        all_params = {**ORIGINAL_PARAMS, **EXTENDED_ENZYME_PH_PARAMS}
        
        return all_params
    except ImportError:
        print("Warning: Could not import original pH parameters")
        return EXTENDED_ENZYME_PH_PARAMS


def compute_pH_modulation_extended(enzyme_name: str, pH: float, 
                                   pH_ref: float = 7.2) -> float:
    """
    Compute pH-dependent activity modulation for any enzyme (original or extended).
    
    Uses modified Hill equation normalized at pH_ref.
    
    Parameters:
    -----------
    enzyme_name : str
        Name of enzyme (e.g., 'VGLNS', 'VGDH')
    pH : float
        Current pH value
    pH_ref : float
        Reference pH for normalization (default: 7.2)
        
    Returns:
    --------
    float : Activity modulation factor (0.0-2.0, typically capped at 2.0)
    """
    all_params = get_extended_enzyme_params()
    
    if enzyme_name not in all_params:
        # Enzyme not pH-sensitive, return 1.0 (no modulation)
        return 1.0
    
    params = all_params[enzyme_name]
    pH_opt = params['pH_opt']
    n = params['n_hill']
    
    # Convert pH to [H+] concentration
    H_current = 10**(-pH)
    H_opt = 10**(-pH_opt)
    H_ref = 10**(-pH_ref)
    
    # Modified Hill equation
    f_pH = (H_opt**n + H_ref**n) / (H_opt**n + H_current**n)
    
    # Cap at 2.0 (200% activity)
    f_pH = min(f_pH, 2.0)
    
    return f_pH


def get_enzyme_by_pathway(pathway: str) -> List[str]:
    """
    Get list of enzymes in a specific pathway.
    
    Parameters:
    -----------
    pathway : str
        Pathway name (e.g., 'Glycolysis', 'Amino Acid', 'Nucleotide')
        
    Returns:
    --------
    list : Enzyme names in pathway
    """
    all_params = get_extended_enzyme_params()
    
    return [
        enzyme for enzyme, params in all_params.items()
        if params.get('pathway', '') == pathway
    ]


def print_extended_enzyme_summary():
    """
    Print summary of all pH-sensitive enzymes (original + extended).
    """
    all_params = get_extended_enzyme_params()
    
    # Group by pathway
    pathways = {}
    for enzyme, params in all_params.items():
        pathway = params.get('pathway', 'Unknown')
        if pathway not in pathways:
            pathways[pathway] = []
        pathways[pathway].append((enzyme, params))
    
    print("\n" + "="*80)
    print("EXTENDED pH-SENSITIVE ENZYMES SUMMARY")
    print("="*80 + "\n")
    
    print(f"Total enzymes: {len(all_params)}\n")
    
    for pathway, enzymes in sorted(pathways.items()):
        print(f"\n{'='*80}")
        print(f"PATHWAY: {pathway} ({len(enzymes)} enzymes)")
        print(f"{'='*80}")
        
        print(f"{'Enzyme':<15} {'pH opt':<10} {'n_Hill':<10} {'Description':<45}")
        print("-" * 80)
        
        for enzyme, params in sorted(enzymes):
            pH_opt = params['pH_opt']
            n_hill = params['n_hill']
            desc = params.get('description', 'No description')
            
            print(f"{enzyme:<15} {pH_opt:<10.2f} {n_hill:<10.2f} {desc:<45}")
    
    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    
    # Find most pH-sensitive (highest Hill coefficient)
    most_sensitive = max(all_params.items(), key=lambda x: x[1]['n_hill'])
    print(f"Most pH-sensitive: {most_sensitive[0]} (n={most_sensitive[1]['n_hill']:.2f})")
    
    # Find optimal pH ranges
    pH_opts = [params['pH_opt'] for params in all_params.values()]
    print(f"pH optimum range: {min(pH_opts):.2f} - {max(pH_opts):.2f}")
    print(f"Mean pH optimum: {np.mean(pH_opts):.2f}")
    
    # Acidosis/alkalosis effects
    print(f"\nPredicted Effects:")
    print(f"  Acidosis (pH 7.0):")
    n_inhibited = sum(1 for p in all_params.values() if p['pH_opt'] > 7.2)
    print(f"    - {n_inhibited}/{len(all_params)} enzymes inhibited")
    
    print(f"  Alkalosis (pH 7.6):")
    n_activated = sum(1 for p in all_params.values() if p['pH_opt'] > 7.4)
    print(f"    - {n_activated}/{len(all_params)} enzymes activated")
    
    print("\n" + "="*80 + "\n")


def test_extended_modulation():
    """
    Test pH modulation for extended enzymes at different pH values.
    """
    print("\n" + "="*80)
    print("TESTING EXTENDED ENZYME pH MODULATION")
    print("="*80 + "\n")
    
    # Test enzymes
    test_enzymes = ['VGLNS', 'VGDH', 'VAPRT', 'VADA', 'VGR', 'VTKT']
    test_pHs = [6.8, 7.0, 7.2, 7.4, 7.6, 7.8]
    
    print(f"{'Enzyme':<12} ", end='')
    for pH in test_pHs:
        print(f"pH {pH:.1f}  ", end='')
    print()
    print("-" * 80)
    
    for enzyme in test_enzymes:
        print(f"{enzyme:<12} ", end='')
        for pH in test_pHs:
            f_pH = compute_pH_modulation_extended(enzyme, pH)
            print(f"{f_pH:>6.2f}  ", end='')
        print()
    
    print("\n" + "="*80)
    print("Interpretation:")
    print("  > 1.00 : Enzyme activated")
    print("  = 1.00 : Normal activity (pH 7.2)")
    print("  < 1.00 : Enzyme inhibited")
    print("="*80 + "\n")


def compare_enzyme_sensitivities():
    """
    Compare pH sensitivities across all enzymes.
    """
    import matplotlib.pyplot as plt
    
    all_params = get_extended_enzyme_params()
    
    # Calculate activity at acidosis (pH 7.0) and alkalosis (pH 7.6)
    pH_acidosis = 7.0
    pH_alkalosis = 7.6
    
    results = []
    for enzyme, params in all_params.items():
        f_acidosis = compute_pH_modulation_extended(enzyme, pH_acidosis)
        f_alkalosis = compute_pH_modulation_extended(enzyme, pH_alkalosis)
        
        results.append({
            'enzyme': enzyme,
            'pathway': params.get('pathway', 'Unknown'),
            'pH_opt': params['pH_opt'],
            'n_hill': params['n_hill'],
            'acidosis': f_acidosis,
            'alkalosis': f_alkalosis
        })
    
    # Sort by pH optimum
    results.sort(key=lambda x: x['pH_opt'])
    
    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    enzymes = [r['enzyme'] for r in results]
    acidosis_vals = [r['acidosis'] for r in results]
    alkalosis_vals = [r['alkalosis'] for r in results]
    colors = ['red' if v < 1.0 else 'green' for v in acidosis_vals]
    
    # Plot 1: Acidosis effects
    x_pos = np.arange(len(enzymes))
    bars1 = ax1.barh(x_pos, acidosis_vals, color=colors, alpha=0.7, edgecolor='black')
    ax1.axvline(1.0, color='black', linestyle='--', linewidth=2, alpha=0.5, label='Normal (100%)')
    ax1.set_yticks(x_pos)
    ax1.set_yticklabels(enzymes, fontsize=8)
    ax1.set_xlabel('Activity at pH 7.0 (Acidosis)', fontsize=12, fontweight='bold')
    ax1.set_title('Enzyme Activity in Acidosis', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Plot 2: Alkalosis effects
    colors2 = ['red' if v < 1.0 else 'green' for v in alkalosis_vals]
    bars2 = ax2.barh(x_pos, alkalosis_vals, color=colors2, alpha=0.7, edgecolor='black')
    ax2.axvline(1.0, color='black', linestyle='--', linewidth=2, alpha=0.5, label='Normal (100%)')
    ax2.set_yticks(x_pos)
    ax2.set_yticklabels(enzymes, fontsize=8)
    ax2.set_xlabel('Activity at pH 7.6 (Alkalosis)', fontsize=12, fontweight='bold')
    ax2.set_title('Enzyme Activity in Alkalosis', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    from pathlib import Path
    output_dir = Path("html/brodbar/ph_extended")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "extended_enzyme_sensitivities.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Extended enzyme sensitivity plot saved: {output_path}")


if __name__ == "__main__":
    """
    Test extended pH sensitivity module.
    """
    print_extended_enzyme_summary()
    test_extended_modulation()
    compare_enzyme_sensitivities()
