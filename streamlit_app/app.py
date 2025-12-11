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

# Modern CSS with fade red gradient theme
st.markdown("""
<style>
    /* Hide default Streamlit navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Root variables for consistent theming */
    :root {
        --red-50: #FEF2F2;
        --red-100: #FEE2E2;
        --red-200: #FECACA;
        --red-300: #FCA5A5;
        --red-400: #F87171;
        --red-500: #EF4444;
        --red-600: #DC2626;
        --red-700: #B91C1C;
        --red-800: #991B1B;
        --red-900: #7F1D1D;
        --gray-50: #F9FAFB;
        --gray-100: #F3F4F6;
        --gray-600: #4B5563;
        --gray-800: #1F2937;
    }
    
    /* Hero header with gradient text */
    .hero-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #DC2626 0%, #B91C1C 50%, #7F1D1D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-size: 1.25rem;
        color: var(--gray-600);
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Modern feature cards */
    .feature-card {
        background: linear-gradient(145deg, #FFFFFF 0%, var(--red-50) 100%);
        padding: 1.75rem;
        border-radius: 16px;
        border: 1px solid var(--red-100);
        box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.1), 0 2px 4px -1px rgba(220, 38, 38, 0.06);
        height: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(220, 38, 38, 0.15), 0 10px 10px -5px rgba(220, 38, 38, 0.08);
        border-color: var(--red-200);
    }
    
    .feature-card h4 {
        color: var(--red-700);
        font-weight: 700;
        margin-bottom: 0.75rem;
    }
    
    /* Metric cards with gradient */
    .metric-card {
        background: linear-gradient(135deg, var(--red-500) 0%, var(--red-700) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(220, 38, 38, 0.3);
    }
    
    .metric-card .value {
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1;
    }
    
    .metric-card .label {
        font-size: 0.875rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Glass morphism welcome card */
    .welcome-card {
        background: linear-gradient(135deg, rgba(254, 242, 242, 0.9) 0%, rgba(254, 226, 226, 0.7) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(220, 38, 38, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--gray-50) 0%, var(--red-50) 100%);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.25);
    }
    
    /* Divider with gradient */
    .gradient-divider {
        height: 3px;
        background: linear-gradient(90deg, transparent 0%, var(--red-300) 50%, transparent 100%);
        border: none;
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--gray-800);
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, var(--red-50) 0%, white 100%);
        border-left: 4px solid var(--red-500);
        padding: 1rem 1.25rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 2rem;
        color: var(--gray-600);
        background: linear-gradient(180deg, transparent 0%, var(--red-50) 100%);
        border-radius: 20px 20px 0 0;
        margin-top: 2rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, var(--red-50) 0%, white 100%);
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize auth session
init_session_state()

# Main header with gradient text
st.markdown('<h1 class="hero-header">🩸 RBC Metabolic Model</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Interactive Red Blood Cell Metabolism Simulation Platform</p>', unsafe_allow_html=True)

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

# Hero section with gradient divider
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div class="welcome-card">
        <h3 style="color: #B91C1C; margin-top: 0;">Welcome to the RBC Metabolic Model</h3>
        <p style="color: #4B5563; line-height: 1.7;">
            This platform provides an interactive interface to simulate and analyze <strong>red blood cell metabolism</strong> 
            based on the comprehensive model by <strong>Bordbar et al. (2015)</strong>.
        </p>
        <p style="color: #4B5563; margin-bottom: 0;"><strong>Explore complex metabolic dynamics with:</strong></p>
        <ul style="color: #4B5563; margin-top: 0.5rem;">
            <li>108 metabolites across multiple pathways</li>
            <li>Real-time simulation with adjustable parameters</li>
            <li>Interactive visualizations and data export</li>
            <li>Bohr effect and pH perturbation analysis</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# Features section with modern cards
st.markdown('<p class="section-header">🚀 Key Features</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""
    <div class="feature-card">
        <h4>🧪 Metabolic Simulations</h4>
        <p style="color: #4B5563; font-size: 0.95rem; line-height: 1.6;">
            Run comprehensive RBC metabolism simulations with customizable time duration, 
            adjustable curve fitting strength, multiple initial condition sources, 
            and advanced solver options.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h4>📊 Interactive Analysis</h4>
        <p style="color: #4B5563; font-size: 0.95rem; line-height: 1.6;">
            Visualize and analyze results with dynamic metabolite concentration plots, 
            flux distribution heatmaps, experimental data comparison, 
            and export to CSV, PDF, or ZIP.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h4>🔬 Advanced Studies</h4>
        <p style="color: #4B5563; font-size: 0.95rem; line-height: 1.6;">
            Explore physiological phenomena including Bohr effect simulation, 
            pH perturbation scenarios, oxygen binding dynamics, 
            and BPG (2,3-bisphosphoglycerate) analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# Model statistics with custom metric cards
st.markdown('<p class="section-header">📈 Model Statistics</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.markdown("""
    <div class="metric-card">
        <div class="value">108</div>
        <div class="label">Metabolites</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <div class="value">~200</div>
        <div class="label">Reactions</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <div class="value">8</div>
        <div class="label">Pathways</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <div class="value">14</div>
        <div class="label">Data Points</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# Quick start guide
st.markdown('<p class="section-header">🎯 Quick Start Guide</p>', unsafe_allow_html=True)

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
    st.markdown("""
    <div class="info-box">
        <strong style="color: #B91C1C;">RBC Metabolic Model v2.0</strong><br><br>
        Based on the comprehensive red blood cell 
        metabolic reconstruction by Bordbar et al. (2015).<br><br>
        <strong>Features:</strong>
        <ul style="margin: 0.5rem 0 0 0; padding-left: 1.2rem;">
            <li>Multi-pathway metabolism</li>
            <li>Experimental data integration</li>
            <li>pH and Bohr effect modeling</li>
            <li>Interactive web interface</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
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

# Footer with gradient
st.markdown("""
<div class="footer">
    <p style="font-size: 1.1rem; font-weight: 600; color: #B91C1C; margin-bottom: 0.5rem;">Ready to explore RBC metabolism?</p>
    <p style="margin: 0;">👈 Select a page from the sidebar to get started!</p>
</div>
""", unsafe_allow_html=True)
