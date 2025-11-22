"""
Sensitivity Analysis Page - Compare impact of experimental data sources
"""
import streamlit as st
import sys
from pathlib import Path

# Add core to path
core_path = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(core_path))

from sensitivity_engine import SensitivityAnalyzer, run_comparative_simulation
from sensitivity_plotting import (
    plot_flux_difference_heatmap,
    plot_metabolite_comparison_tornado,
    plot_pathway_impact_summary,
    plot_side_by_side_comparison,
    plot_validation_metrics,
    create_comparison_summary_cards
)
from auth import init_session_state

st.set_page_config(
    page_title="Sensitivity Analysis - RBC Model",
    page_icon="🔬",
    layout="wide"
)

# Hide default Streamlit navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize auth session
init_session_state()

# Require authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in to access this page")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔑 Go to Login", width="stretch"):
            st.switch_page("pages/0_Login.py")
    st.stop()

# Custom CSS
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .comparison-card {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    /* Sidebar navigation styling */
    [data-testid="stSidebarNav"] {
        padding-top: 2rem;
    }
    
    /* Highlight main navigation pages */
    [data-testid="stSidebarNav"] ul li:first-child a,
    [data-testid="stSidebarNav"] ul li:nth-child(2) a {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white !important;
        font-weight: 700;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(255, 75, 75, 0.3);
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebarNav"] ul li:first-child a:hover,
    [data-testid="stSidebarNav"] ul li:nth-child(2) a:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
    
    /* Replace "app" with "Home" in navigation */
    [data-testid="stSidebarNav"] ul li:first-child a span {
        font-size: 0;
    }
    
    [data-testid="stSidebarNav"] ul li:first-child a span::before {
        content: "🏠 Home";
        font-size: 1rem;
        font-weight: 700;
        display: inline-block;
    }
    
    /* Add rocket emoji and style to Simulation */
    [data-testid="stSidebarNav"] ul li:nth-child(2) a span {
        font-weight: 700;
        font-size: 1rem;
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(2) a span::before {
        content: "🚀 ";
        margin-right: 0.25rem;
    }
    
    /* Style Data Upload button (5th item) in green */
    [data-testid="stSidebarNav"] ul li:nth-child(5) a {
        background: linear-gradient(90deg, #28a745 0%, #34ce57 100%);
        color: white !important;
        font-weight: 700;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(5) a:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(5) a span::before {
        content: "📤 ";
        margin-right: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🔬 Sensitivity Analysis")
st.markdown("*Analyze the impact of custom experimental data on model predictions*")

# Check if custom data is available
if 'uploaded_data_active' not in st.session_state or not st.session_state.get('uploaded_data_active'):
    st.warning("⚠️ No custom data uploaded. Please upload custom data on the **Data Upload** page first.")
    st.info("👉 Go to the **Data Upload** page to upload your experimental data.")
    st.stop()

# Info about the analysis
st.info("""
ℹ️ **How This Analysis Works**

**NEW APPROACH**: Direct experimental data comparison!

Since the RBC model is governed by fixed kinetic laws (ODEs), changing experimental data doesn't change the simulation dynamics. Instead, this analysis:

**Compares YOUR experimental measurements vs Brodbar et al. measurements:**
1. **Direct Comparison**: Shows which metabolites have different measured values
2. **Statistical Analysis**: Calculates mean, std, RMSE between the two datasets
3. **Validation Metrics**: How well the model fits each dataset (R², RMSE, MAE)

**What you'll see:**
- 📊 **Metabolite Differences**: Which metabolites show biggest measurement differences
- 📈 **Data Comparison Plots**: Side-by-side visualization of datasets
- ✅ **Validation Quality**: How well the model captures your experimental observations

**Interpretation:**
- **Large differences (>20%)**: Your measurements differ significantly from Brodbar
- **Small differences (<5%)**: Good consistency between datasets ✅
- **Validation metrics**: R² > 0.9 = excellent model fit to your data
""")

st.markdown("---")

# Sidebar: Analysis Options
st.sidebar.header("⚙️ Analysis Options")

run_analysis = st.sidebar.button("▶️ Run Comparative Analysis", type="primary", width="stretch")

if 'sensitivity_results' not in st.session_state:
    st.session_state['sensitivity_results'] = None

# Instructions
with st.expander("💡 How to Use Sensitivity Analysis", expanded=False):
    st.markdown("""
    ### What is Sensitivity Analysis?
    
    This tool compares how your **custom experimental data** affects the model predictions compared to the **original Brodbar et al. data**.
    
    ### What You'll See:
    
    1. **Data Source Comparison**
       - Overview of differences between datasets
       - Number of metabolites and timepoints
    
    2. **Flux Sensitivity**
       - How metabolic fluxes change with custom data
       - Heatmap of flux differences over time
       - Pathway-level impact summary
    
    3. **Metabolite Sensitivity**
       - Which metabolites are most affected
       - Tornado plot of top changes
       - Side-by-side comparisons
    
    4. **Validation Metrics**
       - Goodness of fit (R²)
       - Prediction errors (RMSE, MAE)
       - How well the model captures your data
    
    ### How to Use:
    
    1. Click **"Run Comparative Analysis"** in the sidebar
    2. Wait for both simulations to complete
    3. Explore the results in different sections below
    4. Use the metabolite selector to dive deeper into specific metabolites
    """)

# Run Analysis
if run_analysis:
    st.session_state['sensitivity_results'] = None  # Reset
    
    with st.spinner("🔄 Running comparative analysis..."):
        progress_container = st.empty()
        
        # Run simulation once (ODE doesn't change with different experimental data)
        progress_container.info("📊 Running simulation and loading experimental datasets...")
        results = run_comparative_simulation()
        
        if results is None:
            st.error("❌ Failed to run simulation.")
            st.stop()
        
        progress_container.success("✅ Analysis completed!")
        
        # Create analyzer (both parameters use same results since simulation is identical)
        analyzer = SensitivityAnalyzer(results, results)
        
        # Store in session state
        st.session_state['sensitivity_results'] = {
            'analyzer': analyzer,
            'results': results
        }
        
        st.success("🎉 Sensitivity analysis complete!")

# Display Results
if st.session_state['sensitivity_results'] is not None:
    results = st.session_state['sensitivity_results']
    analyzer = results['analyzer']
    
    # Section 1: Overview
    st.header("📊 Analysis Overview")
    
    met_stats, flux_stats, overall_stats = create_comparison_summary_cards(analyzer)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Metabolites Compared",
            met_stats['n_metabolites'],
            help="Total metabolites with measurements in both datasets"
        )
    
    with col2:
        st.metric(
            "Max Difference",
            f"{met_stats['max_change']:.3f} mM",
            help="Largest absolute difference in measurements"
        )
    
    with col3:
        st.metric(
            "Most Different",
            met_stats['most_sensitive'],
            help="Metabolite with biggest measurement difference"
        )
    
    st.markdown("---")
    
    # Section 2: About Fluxes
    st.header("ℹ️ Note About Metabolic Fluxes")
    
    st.info("""
    **Why aren't fluxes compared?**
    
    Metabolic fluxes are determined by the **kinetic laws** governing the RBC metabolic network, not by experimental measurements. 
    
    Both simulations (with Brodbar data or custom data) use the **same ODE system** with fixed kinetic parameters, 
    so they produce nearly identical flux distributions.
    
    **What's actually compared:**
    - ✅ Your experimental **measurements** vs Brodbar measurements
    - ✅ How well the **simulation** fits each dataset
    - ✅ Which metabolites show the biggest **measurement differences**
    
    For flux analysis, use the dedicated **Flux Analysis** page where you can explore the metabolic flux distribution 
    from your simulation.
    """)
    
    st.markdown("---")
    
    # Section 3: Metabolite Sensitivity
    st.header("📈 Metabolite Sensitivity Analysis")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Top Sensitive Metabolites")
        fig_tornado = plot_metabolite_comparison_tornado(analyzer, n=15)
        st.plotly_chart(fig_tornado, use_container_width=True)
    
    with col2:
        st.markdown("### Detailed Comparison")
        
        # Metabolite selector
        top_metabolites = analyzer.get_top_sensitive_metabolites(n=20)
        met_options = [m[0] for m in top_metabolites] if top_metabolites else analyzer.metabolites[:20]
        
        selected_metabolite = st.selectbox(
            "Select metabolite to compare:",
            met_options,
            help="Choose a metabolite to see side-by-side comparison"
        )
        
        if selected_metabolite:
            fig_comparison = plot_side_by_side_comparison(analyzer, selected_metabolite)
            st.plotly_chart(fig_comparison, use_container_width=True)
    
    st.markdown("---")
    
    # Section 4: Validation Metrics
    st.header("✅ Validation Metrics")
    st.caption("How well does the model fit your custom experimental data?")
    
    validation_metrics = analyzer.calculate_validation_metrics()
    
    if validation_metrics:
        fig_validation = plot_validation_metrics(validation_metrics)
        st.plotly_chart(fig_validation, use_container_width=True)
        
        # Metrics table
        with st.expander("📊 Detailed Validation Metrics"):
            metrics_df = []
            for met, metrics in validation_metrics.items():
                metrics_df.append({
                    'Metabolite': met,
                    'R² Score': f"{metrics['R2']:.4f}",
                    'RMSE (mM)': f"{metrics['RMSE']:.6f}",
                    'MAE (mM)': f"{metrics['MAE']:.6f}",
                    'Data Points': metrics['n_points']
                })
            st.dataframe(metrics_df, width="stretch")
            
            # Interpretation
            st.markdown("#### 📖 Interpretation Guide:")
            st.markdown("""
            - **R² > 0.9**: Excellent fit
            - **R² 0.7-0.9**: Good fit
            - **R² 0.5-0.7**: Moderate fit
            - **R² < 0.5**: Poor fit
            
            - **RMSE/MAE**: Lower is better (units: mM)
            """)
    else:
        st.info("No validation metrics available. Make sure your custom data includes metabolites present in the model.")
    
    st.markdown("---")
    
    # Section 5: Summary & Export
    st.header("📋 Analysis Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Key Findings")
        st.markdown(f"""
        - **Most Sensitive Metabolite**: {met_stats['most_sensitive']}
        - **Most Sensitive Reaction**: {flux_stats['most_sensitive']}
        - **Average Concentration Change**: {met_stats['mean_change']:.4f} mM
        - **Average Flux Change**: {flux_stats['mean_pct_change']:.2f}%
        """)
    
    with col2:
        st.markdown("### Data Sources")
        st.markdown(f"""
        - **Custom Data**: {overall_stats['n_timepoints_custom']} timepoints
        - **Brodbar Data**: {overall_stats['n_timepoints_brodbar']} timepoints
        - **Timepoint Match**: {overall_stats['simulation_match']}
        """)
    
    # Export options
    st.markdown("### 💾 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Metabolite Comparison (CSV)"):
            met_comparison = analyzer.compare_metabolite_concentrations()
            csv = met_comparison.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="metabolite_sensitivity.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📥 Export Flux Comparison (CSV)"):
            flux_comparison = analyzer.compare_flux_profiles()
            csv = flux_comparison.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="flux_sensitivity.csv",
                mime="text/csv"
            )

else:
    st.info("👆 Click **'Run Comparative Analysis'** in the sidebar to start the analysis.")
    
    # Show example/preview
    st.markdown("---")
    st.header("📚 About Sensitivity Analysis")
    
    st.markdown("""
    ### Why Run Sensitivity Analysis?
    
    Sensitivity analysis helps you understand:
    
    1. **Data Impact**: How much do your custom experimental measurements influence model predictions?
    
    2. **Model Robustness**: Are model predictions stable or highly sensitive to input data?
    
    3. **Critical Metabolites**: Which metabolites have the most influence on metabolic fluxes?
    
    4. **Validation**: How well does the model capture your experimental observations?
    
    ### When to Use:
    
    - After uploading new experimental data
    - To compare different experimental conditions
    - To identify which measurements are most critical
    - To validate model predictions against your data
    
    ### Requirements:
    
    - ✅ Custom experimental data uploaded (Data Upload page)
    - ✅ Data set to "Use for validation only" mode
    - ✅ At least one simulation run completed
    """)

# Footer
st.markdown("---")
st.caption("💡 Tip: Run simulations with different curve fitting strengths to see how it affects sensitivity!")
