import pandas as pd
import numpy as np

def load_experimental_initial_conditions():
    """
    Load initial conditions from the first experimental values in Data_Brodbar_et_al_exp.xlsx
    Returns a dictionary mapping metabolite names to their initial concentrations
    """
    try:
        # Read the experimental data file
        df = pd.read_excel('Data_Brodbar_et_al_exp.xlsx', engine='openpyxl')
        
        # Extract metabolite names from first column and initial values from second column (index 1)
        metabolite_names = df.iloc[:, 0].tolist()  # First column contains metabolite names
        initial_values = df.iloc[:, 1].tolist()    # Second column contains initial experimental values
        
        # Create dictionary mapping metabolite names to initial values
        experimental_initial_conditions = {}
        for name, value in zip(metabolite_names, initial_values):
            if pd.notna(name) and pd.notna(value):
                experimental_initial_conditions[str(name).strip()] = float(value)
        
        print(f"Loaded {len(experimental_initial_conditions)} experimental initial conditions")
        
        return experimental_initial_conditions
        
    except Exception as e:
        print(f"Error loading experimental initial conditions: {e}")
        return {}

def get_brodbar_metabolite_mapping():
    """
    Use the correct metabolite mapping from equadiff_brodbar.py
    """
    # Import the correct mapping from equadiff_brodbar.py
    from equadiff_brodbar import BRODBAR_METABOLITE_MAP
    return BRODBAR_METABOLITE_MAP

def create_experimental_initial_vector():
    """
    Create the initial conditions vector for the Brodbar model using experimental data
    """
    # Load experimental initial conditions
    exp_conditions = load_experimental_initial_conditions()
    metabolite_mapping = get_brodbar_metabolite_mapping()
    
    # Initialize vector with default values (small positive values to avoid numerical issues)
    x0 = np.full(108, 0.001)  # 108 metabolites in Brodbar model
    
    # Map experimental values to the correct positions
    mapped_count = 0
    for exp_name, exp_value in exp_conditions.items():
        if exp_name in metabolite_mapping:
            index = metabolite_mapping[exp_name]
            if 0 <= index < 108:
                x0[index] = max(exp_value, 1e-6)  # Ensure positive values
                mapped_count += 1
                print(f"Mapped {exp_name} -> index {index}: {exp_value}")
    
    print(f"Successfully mapped {mapped_count} experimental values to model positions")
    
    # Set some default values for unmapped metabolites based on typical physiological ranges
    default_values = {
        51: 0.5,    # NAD
        52: 0.1,    # NADH  
        53: 0.01,   # NADP
        54: 0.05,   # NADPH
        55: 2.0,    # GSH
        56: 0.1,    # GSSG
        107: 7.2,   # pHi (physiological pH)
    }
    
    for index, value in default_values.items():
        if index < 108:
            x0[index] = value
    
    # Clean the vector to ensure no NaN/Inf values
    x0 = np.nan_to_num(x0, nan=0.001, posinf=1.0, neginf=0.001)
    x0 = np.maximum(x0, 1e-6)  # Ensure all values are positive
    
    return x0

if __name__ == "__main__":
    # Test the function
    x0 = create_experimental_initial_vector()
    print(f"\nCreated initial conditions vector with shape: {x0.shape}")
    print(f"Min value: {np.min(x0)}")
    print(f"Max value: {np.max(x0)}")
    print(f"Any NaN/Inf: {np.any(~np.isfinite(x0))}")
