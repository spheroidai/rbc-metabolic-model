"""
Data Loader - Load experimental data with Streamlit caching
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "src"))

@st.cache_data(ttl=3600)
def load_experimental_data():
    """
    Load experimental data from Brodbar et al.
    Returns DataFrame with metabolite time series
    """
    try:
        data_path = project_root / "Data_Brodbar_et_al_exp.xlsx"
        df = pd.read_excel(data_path, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Error loading experimental data: {e}")
        return None

@st.cache_data(ttl=3600)
def load_fitted_parameters():
    """
    Load polynomial-logarithmic fitted parameters for curve fitting
    Returns DataFrame with coefficients (a, b, c, d, e) for each metabolite
    """
    try:
        data_path = project_root / "Data_Brodbar_et_al_exp_fitted_params.csv"
        df = pd.read_csv(data_path)
        return df
    except Exception as e:
        st.error(f"Error loading fitted parameters: {e}")
        return None

@st.cache_data(ttl=3600)
def load_initial_conditions(source="JA Final"):
    """
    Load initial conditions for metabolites
    
    Parameters:
    -----------
    source : str
        "JA Final" - from Initial_conditions_JA_Final.xls
        "Brodbar" - from Data_Brodbar_et_al_exp.xlsx first timepoint
    
    Returns:
    --------
    dict : metabolite_name -> concentration (mM)
    """
    try:
        if source == "JA Final":
            ic_path = project_root / "Initial_conditions_JA_Final.xls"
            df = pd.read_excel(ic_path, engine='xlrd')
            # Assuming columns: Metabolite, Concentration
            if 'Metabolite' in df.columns and 'Concentration' in df.columns:
                return dict(zip(df['Metabolite'], df['Concentration']))
            else:
                # Try first two columns
                return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
        
        elif source == "Brodbar":
            exp_data = load_experimental_data()
            if exp_data is not None:
                # Get first timepoint for each metabolite
                ic_dict = {}
                for col in exp_data.columns:
                    if col != 'Time':
                        ic_dict[col] = exp_data[col].iloc[0]
                return ic_dict
    
    except Exception as e:
        st.error(f"Error loading initial conditions: {e}")
        return {}

@st.cache_data
def get_metabolite_list():
    """
    Get list of all metabolites in the model
    Returns list of metabolite names
    """
    try:
        from equadiff_brodbar import BRODBAR_METABOLITE_MAP
        return list(BRODBAR_METABOLITE_MAP.keys())
    except Exception as e:
        st.warning(f"Could not load metabolite list: {e}")
        return []

@st.cache_data
def get_data_summary():
    """
    Get summary statistics of experimental data
    Returns dict with summary info
    """
    exp_data = load_experimental_data()
    if exp_data is None:
        return {}
    
    summary = {
        'n_metabolites': len(exp_data.columns) - 1,  # excluding Time
        'n_timepoints': len(exp_data),
        'time_range': (exp_data['Time'].min(), exp_data['Time'].max()) if 'Time' in exp_data.columns else (0, 0),
        'metabolites': list(exp_data.columns[exp_data.columns != 'Time'])
    }
    
    return summary

def validate_data_files():
    """
    Check if all required data files exist
    Returns dict with file availability status
    """
    required_files = {
        'experimental_data': project_root / "Data_Brodbar_et_al_exp.xlsx",
        'fitted_params': project_root / "Data_Brodbar_et_al_exp_fitted_params.csv",
        'initial_conditions': project_root / "Initial_conditions_JA_Final.xls"
    }
    
    status = {}
    for name, path in required_files.items():
        status[name] = path.exists()
    
    return status
