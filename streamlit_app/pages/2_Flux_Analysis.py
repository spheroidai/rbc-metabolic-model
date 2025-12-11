"""
Metabolic Flux Analysis Page
============================

Interactive visualization of metabolic fluxes with heatmap and detailed views.

Features:
- Flux distribution at initial, midpoint, and final timepoints
- Interactive heatmap (click to view flux details)
- Detailed flux analysis with substrate/product concentrations
- CSV export of flux data

Author: Jorgelindo da Veiga
Date: 2025-11-17
"""

import streamlit as st
import sys
from pathlib import Path

# Add core modules to path
core_path = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(core_path))

from flux_plotting import (
    create_flux_heatmap,
    create_flux_distribution_combined,
    create_flux_detail_view,
    export_flux_data_csv
)
from auth import init_session_state, check_page_auth
from styles import apply_global_styles

# Page configuration
st.set_page_config(
    page_title="Flux Analysis - RBC Model",
    page_icon="🔬",
    layout="wide"
)

# Apply global styles
apply_global_styles()

# Initialize and check authentication
init_session_state()
if not check_page_auth():
    st.stop()

# Title
st.title("🔬 Metabolic Flux Analysis")
st.markdown("*Interactive exploration of reaction fluxes through metabolic pathways*")

# Check if simulation results exist
if 'simulation_results' not in st.session_state or st.session_state.simulation_results is None:
    st.warning("⚠️ No simulation results found. Please run a simulation first on the **Simulation** page.")
    st.info("👉 Go to the Simulation page to run your first simulation.")
    st.stop()

results = st.session_state.simulation_results

# Check if flux data is available
if 'flux_data' not in results or results['flux_data'] is None:
    st.error("❌ Flux data not available in simulation results.")
    st.info("This might be an issue with the simulation. Please try running a new simulation.")
    st.stop()

flux_data = results['flux_data']

# Check flux data validity
if 'times' not in flux_data or 'fluxes' not in flux_data:
    st.error("❌ Invalid flux data format.")
    st.stop()

if len(flux_data['times']) == 0 or len(flux_data['fluxes']) == 0:
    st.error("❌ No flux data captured during simulation.")
    st.stop()

# Display simulation info
st.success(f"✅ Loaded flux data: {len(flux_data['times'])} time points, {len(flux_data['fluxes'])} reactions")

# Instructions at the top
st.markdown("---")
with st.expander("💡 How to Use This Page", expanded=False):
    st.markdown("""
    1. **Flux Distributions**: Compare pathway activities and top 20 reactions at initial, midpoint, and final timepoints
    2. **Flux Balance Analysis**: 
       - Use the sidebar to select a specific reaction
       - View detailed flux dynamics over time
       - Analyze substrate and product concentrations
       - Access statistical summaries
    3. **Flux Heatmap**: 
       - Overview of all fluxes over time grouped by metabolic pathway
       - Colors indicate normalized flux intensity (red = high, blue = low)
       - Quick visual identification of metabolic patterns
    4. **Export**: Download flux data as CSV for further analysis (sidebar or individual flux)
    
    **Pathways Tracked:**
    - 🔹 Glycolysis
    - 🔹 Pentose Phosphate Pathway
    - 🔹 Transport
    - 🔹 Nucleotide Metabolism
    - 🔹 Amino Acid Metabolism
    - 🔹 Redox Reactions
    - 🔹 2,3-BPG Shunt
    - 🔹 Other Reactions
    """)

# Sidebar: Flux selection for detail view
st.sidebar.title("🎯 Flux Selection")
st.sidebar.markdown("Select a reaction to view detailed analysis")

# Get all reaction names sorted
all_reactions = sorted(flux_data['fluxes'].keys())

# Reaction selector
selected_reaction = st.sidebar.selectbox(
    "Select Reaction:",
    options=["None"] + all_reactions,
    help="Choose a reaction to view detailed time course and substrate/product dynamics"
)

# Export button in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Export Data")
if st.sidebar.button("📥 Download Flux Data (CSV)", width="stretch"):
    csv_data = export_flux_data_csv(flux_data)
    st.sidebar.download_button(
        label="💾 Save CSV File",
        data=csv_data,
        file_name="metabolic_fluxes.csv",
        mime="text/csv",
        width="stretch"
    )
    st.sidebar.success("✓ CSV ready for download!")

# Main content
st.markdown("---")

# Section 1: Flux Distributions at Key Timepoints
st.header("📊 Flux Distribution Analysis")
st.caption("Compare pathway activities and top reactions at different timepoints")

tab1, tab2, tab3 = st.tabs(["📌 Initial", "⏱️ Midpoint", "🏁 Final"])

with tab1:
    with st.spinner("Generating initial timepoint distribution..."):
        fig_initial = create_flux_distribution_combined(flux_data, 'initial')
        st.plotly_chart(fig_initial, use_container_width=True)

with tab2:
    with st.spinner("Generating midpoint distribution..."):
        fig_midpoint = create_flux_distribution_combined(flux_data, 'midpoint')
        st.plotly_chart(fig_midpoint, use_container_width=True)

with tab3:
    with st.spinner("Generating final timepoint distribution..."):
        fig_final = create_flux_distribution_combined(flux_data, 'final')
        st.plotly_chart(fig_final, use_container_width=True)

# Section 2: Detailed Flux Analysis (when reaction selected)
if selected_reaction != "None":
    st.markdown("---")
    st.header(f"📈 Flux Balance Analysis: {selected_reaction}")
    st.caption(f"Comprehensive view of {selected_reaction} flux dynamics")
    
    with st.spinner(f"Analyzing {selected_reaction}..."):
        # Prepare metabolite results with simulation times
        metabolite_results = {
            'metabolite_names': results.get('metabolite_names', []),
            'concentrations': results.get('x', None),
            'sim_times': results.get('t', flux_data['times'])  # Use full simulation times
        }
        
        detail_fig = create_flux_detail_view(selected_reaction, flux_data, metabolite_results)
        st.plotly_chart(detail_fig, use_container_width=True)
    
    # Export button for this specific flux
    st.markdown("### 💾 Export This Flux")
    col1, col2 = st.columns([1, 3])
    with col1:
        import pandas as pd
        df_single = pd.DataFrame({
            'Time_days': flux_data['times'],
            f'{selected_reaction}_flux': flux_data['fluxes'][selected_reaction]
        })
        csv_single = df_single.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {selected_reaction} Data",
            data=csv_single,
            file_name=f"flux_{selected_reaction}.csv",
            mime="text/csv"
        )

# Section 3: Flux Heatmap
st.markdown("---")
st.header("🔥 Flux Heatmap Overview")
st.caption("Normalized flux intensities for top reactions by variance, grouped by metabolic pathway (optimized for display)")

with st.spinner("Generating flux heatmap..."):
    # Prepare metabolite results for detail view
    metabolite_results = {
        'metabolite_names': results.get('metabolite_names', []),
        'concentrations': results.get('x', None)
    }
    
    heatmap_fig = create_flux_heatmap(flux_data, metabolite_results)
    
    # Display heatmap
    st.plotly_chart(heatmap_fig, use_container_width=True)

# Debug info (only in development)
if st.sidebar.checkbox("Show Debug Info", value=False):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🐛 Debug Information")
    st.sidebar.write(f"Time points: {len(flux_data['times'])}")
    st.sidebar.write(f"Reactions tracked: {len(flux_data['fluxes'])}")
    st.sidebar.write(f"Simulation duration: {flux_data['times'][-1]:.1f} days")
    st.sidebar.write(f"Total metabolites: {results.get('n_metabolites', 'N/A')}")
