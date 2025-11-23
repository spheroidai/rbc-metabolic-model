"""
RBC Metabolic Model - Streamlit Web Application
Main Entry Point

Author: Jorgelindo da Veiga
Based on: Bordbar et al. (2015) RBC metabolic model
"""

import streamlit as st
from pathlib import Path
import sys

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))
from auth import init_session_state, get_user_name, get_user_email, AuthManager

# Page configuration
st.set_page_config(
    page_title="RBC Metabolic Model",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "RBC Metabolic Model - Interactive simulation platform for red blood cell metabolism"
    }
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Hide default Streamlit navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Main content styling */
    .main-header {
        font-size: 3.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: 100%;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
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

# Initialize auth session
init_session_state()

# Main header
st.markdown('<h1 class="main-header">🩸 RBC Metabolic Model</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Interactive Red Blood Cell Metabolism Simulation Platform</p>', unsafe_allow_html=True)

# Authentication status widget
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    if st.session_state.get("authenticated", False):
        # User is logged in
        user_name = get_user_name() or "User"
        user_email = get_user_email() or ""
        
        st.success(f"✅ Logged in as **{user_name}**")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("🧪 Simulation", width="stretch", type="primary"):
                st.switch_page("pages/1_Simulation.py")
        
        with col_b:
            if st.session_state.get("is_admin", False):
                if st.button("⚙️ Admin", width="stretch"):
                    st.switch_page("pages/6_Admin.py")
            else:
                st.button("⚙️ Admin", width="stretch", disabled=True, 
                         help="Admin access only")
        
        with col_c:
            if st.button("🚪 Logout", width="stretch"):
                auth = AuthManager()
                auth.sign_out()
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.user_profile = None
                st.session_state.is_admin = False
                st.rerun()
    else:
        # User is not logged in
        st.info("👋 Please log in to access simulations and analysis tools")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🔑 Login", width="stretch", type="primary"):
                st.switch_page("pages/0_Login.py")
        
        with col_b:
            if st.button("📝 Sign Up", width="stretch"):
                st.switch_page("pages/0_Login.py")

# Hero section
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    ### Welcome to the RBC Metabolic Model Web Application
    
    This platform provides an interactive interface to simulate and analyze **red blood cell metabolism** 
    based on the comprehensive model by **Bordbar et al. (2015)**.
    
    **Explore complex metabolic dynamics with:**
    - 107 metabolites across multiple pathways
    - Real-time simulation with adjustable parameters
    - Interactive visualizations and data export
    - Bohr effect and pH perturbation analysis
    """)

st.markdown("---")

# Features section
st.markdown("### 🚀 Key Features")
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.markdown("#### 🧪 **Metabolic Simulations**")
        st.write("""
        Run comprehensive RBC metabolism simulations with:
        - Customizable time duration
        - Adjustable curve fitting strength
        - Multiple initial condition sources
        - Advanced solver options
        """)
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.markdown("#### 📊 **Interactive Analysis**")
        st.write("""
        Visualize and analyze results with:
        - Dynamic metabolite concentration plots
        - Flux distribution heatmaps
        - Experimental data comparison
        - Export to CSV, PDF, or ZIP
        """)
        st.markdown('</div>', unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.markdown("#### 🔬 **Advanced Studies**")
        st.write("""
        Explore physiological phenomena:
        - Bohr effect simulation
        - pH perturbation scenarios
        - Oxygen binding dynamics
        - BPG (2,3-bisphosphoglycerate) analysis
        """)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Model statistics
st.markdown("### 📈 Model Statistics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Metabolites",
        value="107",
        help="Total number of metabolites tracked in the model"
    )

with col2:
    st.metric(
        label="Reactions",
        value="~200",
        help="Approximate number of biochemical reactions"
    )

with col3:
    st.metric(
        label="Pathways",
        value="8",
        help="Major metabolic pathways (Glycolysis, PPP, Nucleotide, etc.)"
    )

with col4:
    st.metric(
        label="Data Points",
        value="14",
        help="Experimental time points from Brodbar et al."
    )

st.markdown("---")

# Quick start guide
st.markdown("### 🎯 Quick Start Guide")

with st.expander("**1️⃣ Run Your First Simulation**", expanded=False):
    st.markdown("""
    1. Navigate to the **🚀 Simulation** page from the sidebar
    2. Choose your simulation parameters (default settings work great!)
    3. Click the **"▶️ Start Simulation"** button
    4. Wait for the simulation to complete (~30-60 seconds)
    5. View results and download outputs
    """)

with st.expander("**2️⃣ Analyze Results**", expanded=False):
    st.markdown("""
    1. Go to the **📊 Results** page after running a simulation
    2. Select metabolites of interest from the dropdown
    3. Explore interactive plots with zoom and pan
    4. Compare with experimental data
    5. Export visualizations for your research
    """)

with st.expander("**3️⃣ Explore Advanced Features**", expanded=False):
    st.markdown("""
    - **🔬 Bohr Effect**: Study oxygen binding cooperativity and BPG influence
    - **⚗️ pH Analysis**: Simulate acidosis/alkalosis scenarios
    - **📈 Advanced**: Compare multiple simulations and sensitivity analysis
    """)

st.markdown("---")

# Sidebar navigation
with st.sidebar:
    st.markdown("---")
    
    # Login button - Gray, first when not authenticated
    if not st.session_state.get("authenticated", False):
        if st.button("🔑 Login", width="stretch", key="sidebar_login"):
            st.switch_page("pages/0_Login.py")
    
    # Home button - always visible
    if st.button("🏠 Home", width="stretch", key="sidebar_home"):
        st.switch_page("app.py")
    
    # Main pages - only when authenticated
    if st.session_state.get("authenticated", False):
        if st.button("🧪 Simulation", width="stretch", key="sidebar_simulation"):
            st.switch_page("pages/1_Simulation.py")
        
        if st.button("🔬 Flux Analysis", width="stretch", key="sidebar_flux"):
            st.switch_page("pages/2_Flux_Analysis.py")
        
        if st.button("📊 Sensitivity Analysis", width="stretch", key="sidebar_sensitivity"):
            st.switch_page("pages/3_Sensitivity_Analysis.py")
        
        if st.button("🎯 Parameter Calibration", width="stretch", key="sidebar_calibration"):
            st.switch_page("pages/5_Parameter_Calibration.py")
        
        if st.button("🗺️ Pathway Visualization", width="stretch", key="sidebar_visualization"):
            st.switch_page("pages/7_Pathway_Visualization.py")
        
        # Data Upload button - Green (primary)
        if st.button("📤 Data Upload", width="stretch", type="primary", key="sidebar_upload"):
            st.switch_page("pages/4_Data_Upload.py")
    
    st.markdown("---")
    
    # Admin access
    if st.session_state.get("authenticated", False):
        if st.session_state.get("is_admin", False):
            if st.button("⚙️ Admin", width="stretch", key="sidebar_admin"):
                st.switch_page("pages/6_Admin.py")
        else:
            st.caption("⚙️ Admin (admins only)")
    
    st.markdown("---")
    
    st.markdown("### 📚 About")
    st.info("""
    **RBC Metabolic Model v2.0**
    
    Based on the comprehensive red blood cell 
    metabolic reconstruction by Bordbar et al. (2015).
    
    **Features:**
    - Multi-pathway metabolism
    - Experimental data integration
    - pH and Bohr effect modeling
    - Interactive web interface
    """)
    
    st.markdown("### 🔗 Resources")
    st.markdown("""
    - [Documentation](../Documentation/)
    - [GitHub Repository](#)
    - [Original Article](https://www.cell.com/action/showPdf?pii=S2405-4712%2815%2900149-0)
    """)
    
    st.markdown("### 💡 Tips")
    st.success("""
    **New to metabolic modeling?**
    
    Start with the default parameters in the 
    Simulation page. The model is pre-configured 
    with physiologically relevant values!
    """)
    
    st.markdown("---")
    st.caption("Developed by Jorgelindo da Veiga • 2025")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Ready to explore RBC metabolism?</strong></p>
    <p>👈 Select a page from the sidebar to get started!</p>
</div>
""", unsafe_allow_html=True)
