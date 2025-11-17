#!/usr/bin/env python3
"""
Module to load initial conditions from Initial_conditions_JA_Final.xls
and map them to the Brodbar metabolic model.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

# Import the metabolite mapping from the Brodbar model
try:
    from equadiff_brodbar import BRODBAR_METABOLITE_MAP
except ImportError:
    BRODBAR_METABOLITE_MAP = {}

def load_ja_initial_conditions(file_path="Initial_conditions_JA_Final.xls"):
    """
    Load initial conditions from Initial_conditions_JA_Final.xls file
    and map them to the Brodbar model metabolites.
    
    Parameters:
    -----------
    file_path : str
        Path to the Initial_conditions_JA_Final.xls file
        
    Returns:
    --------
    x0 : numpy.ndarray
        Vector of initial conditions for all 108 metabolites (including H2O2 and pHi)
    x0_names : list
        List of metabolite names corresponding to x0 values
    """
    
    # Read the JA Final initial conditions file
    try:
        df = pd.read_excel(file_path)
        print(f"Loading initial conditions from: {file_path}")
        
        # Extract metabolite names and concentrations
        metabolites = df.iloc[:, 0].dropna()  # First column: metabolite names
        concentrations = df.iloc[:, 1].dropna()  # Second column: concentrations
        
        # Ensure same length
        min_len = min(len(metabolites), len(concentrations))
        metabolites = metabolites.iloc[:min_len]
        concentrations = concentrations.iloc[:min_len]
        
        print(f"Found {min_len} metabolite-concentration pairs in JA Final file")
        
        # Create a dictionary for easy lookup
        ja_conditions = {}
        for i in range(min_len):
            metab = str(metabolites.iloc[i]).strip()
            conc = concentrations.iloc[i]
            if pd.notna(metab) and pd.notna(conc):
                try:
                    ja_conditions[metab] = float(conc)
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert concentration for {metab}: {conc}")
                    ja_conditions[metab] = 1.0  # Default value
        
        print(f"Successfully parsed {len(ja_conditions)} metabolite concentrations")
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        print("Using default initial conditions")
        ja_conditions = {}
    
    # Initialize x0 vector for 108 metabolites (106 + H2O2 + pHi)
    x0 = np.ones(108)  # Default to 1.0 mM
    
    # Create metabolite names list based on BRODBAR_METABOLITE_MAP
    if BRODBAR_METABOLITE_MAP:
        # Use the metabolite mapping from the Brodbar model
        x0_names = [''] * 108
        
        # Fill in the metabolite names based on the mapping
        for metab_name, index in BRODBAR_METABOLITE_MAP.items():
            if 0 <= index < 108:
                x0_names[index] = metab_name
        
        # Set specific values for known metabolites
        matched_count = 0
        for metab_name, index in BRODBAR_METABOLITE_MAP.items():
            if 0 <= index < 108:
                # Try exact match first
                if metab_name in ja_conditions:
                    x0[index] = ja_conditions[metab_name]
                    matched_count += 1
                # Try without 'E' prefix for extracellular metabolites
                elif metab_name.startswith('E') and metab_name[1:] in ja_conditions:
                    x0[index] = ja_conditions[metab_name[1:]]
                    matched_count += 1
                # Try common variations
                elif metab_name == 'GLC' and 'EGLC' in ja_conditions:
                    x0[index] = ja_conditions['EGLC']
                    matched_count += 1
                elif metab_name == 'LAC' and 'ELAC' in ja_conditions:
                    x0[index] = ja_conditions['ELAC']
                    matched_count += 1
        
        print(f"Matched {matched_count} metabolites from JA Final conditions to Brodbar model")
        
    else:
        # Fallback: create a basic metabolite names list
        x0_names = [f'Metabolite_{i}' for i in range(108)]
        print("Warning: BRODBAR_METABOLITE_MAP not available, using generic names")
    
    # Set specific initial conditions for key metabolites
    special_metabolites = {
        'H2O2': (106, 0.0001),  # H2O2 at index 106
        'pHi': (107, 7.2),      # Intracellular pH at index 107
    }
    
    for metab_name, (index, default_value) in special_metabolites.items():
        if index < len(x0):
            x0[index] = ja_conditions.get(metab_name, default_value)
            if index < len(x0_names):
                x0_names[index] = metab_name
    
    # Apply some key metabolite values from JA conditions if available
    key_metabolites = {
        'ATP': 0.933,
        'ADP': 1.169,
        'AMP': 0.739,
        'GLC': 25.34,  # Glucose
        'LAC': 4.826,  # Lactate
        'PYR': 0.076,  # Pyruvate
        'NADH': 0.003,
        'NADPH': 0.002,
        'GSH': 2.5,
        'GSSG': 0.1,
    }
    
    for metab_name, default_conc in key_metabolites.items():
        if metab_name in ja_conditions:
            # Find the metabolite in the mapping and set its value
            for mapped_name, index in BRODBAR_METABOLITE_MAP.items():
                if (mapped_name == metab_name or 
                    mapped_name.replace('E', '') == metab_name or
                    mapped_name.endswith(metab_name)):
                    if 0 <= index < len(x0):
                        x0[index] = ja_conditions[metab_name]
                        break
    
    # Ensure no negative or zero concentrations (use small positive values)
    x0 = np.maximum(x0, 1e-6)
    
    print(f"Initial conditions vector created with {len(x0)} metabolites")
    print(f"Concentration range: {x0.min():.6f} - {x0.max():.6f} mM")
    
    return x0, x0_names


def get_ja_metabolite_summary():
    """
    Get a summary of metabolites and their concentrations from the JA Final file.
    """
    try:
        x0, x0_names = load_ja_initial_conditions()
        
        print("\n=== JA Initial Conditions Summary ===")
        print(f"Total metabolites: {len(x0)}")
        
        # Show top 20 metabolites by concentration
        sorted_indices = np.argsort(x0)[::-1]  # Sort in descending order
        
        print("\nTop 20 metabolites by concentration:")
        for i, idx in enumerate(sorted_indices[:20]):
            if idx < len(x0_names) and x0_names[idx]:
                print(f"{i+1:2d}. {x0_names[idx]:<15} = {x0[idx]:.6f} mM")
        
        return x0, x0_names
        
    except Exception as e:
        print(f"Error getting JA metabolite summary: {e}")
        return None, None


if __name__ == "__main__":
    # Test the function
    x0, x0_names = load_ja_initial_conditions()
    if x0 is not None:
        get_ja_metabolite_summary()
