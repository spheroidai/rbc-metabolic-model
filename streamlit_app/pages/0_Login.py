"""
Login and Signup Page
Allows users to authenticate or create new accounts.

Author: RBC Metabolic Model Team
Date: 2025-11-22
"""
import streamlit as st
import sys
from pathlib import Path

# Add core directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.auth import AuthManager, init_session_state

st.set_page_config(
    page_title="Login - RBC Metabolic Model",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
init_session_state()

# Initialize auth manager
auth = AuthManager()

# Custom CSS for login page
st.markdown("""
    <style>
    /* Hide default Streamlit navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding-left: 24px;
        padding-right: 24px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# Check if already authenticated
if st.session_state.authenticated:
    st.success(f"✅ Already logged in as **{st.session_state.user.email}**")
    
    st.markdown("### Where would you like to go?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Home", use_container_width=True, type="primary"):
            st.switch_page("app.py")
    
    with col2:
        if st.button("🧪 Simulation", use_container_width=True):
            st.switch_page("pages/1_Simulation.py")
    
    st.markdown("---")
    
    if st.button("🚪 Logout", use_container_width=True):
        auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.user_profile = None
        st.session_state.is_admin = False
        st.success("✅ Logged out successfully!")
        st.rerun()
    
    st.stop()

# Check if auth is configured
if not auth.is_configured():
    st.error("🔧 Authentication system not configured")
    st.info("""
    **Setup Required:**
    1. Create a Supabase account at https://supabase.com
    2. Create a new project
    3. Add the following to `.streamlit/secrets.toml`:
    
    ```toml
    [supabase]
    url = "your-project-url"
    anon_key = "your-anon-key"
    ```
    
    4. Run the SQL schema from `SUPABASE_SETUP.sql`
    """)
    st.stop()

# Header
st.title("🧬 RBC Metabolic Model")
st.markdown("### Welcome!")
st.caption("Red Blood Cell metabolism simulation and analysis platform")

st.markdown("---")

# Tabs for Login and Signup
tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

# ============================================================================
# LOGIN TAB
# ============================================================================
with tab1:
    st.subheader("Login to Your Account")
    
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email",
            placeholder="your.email@example.com",
            key="login_email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submit = st.form_submit_button(
                "🔓 Login",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            st.form_submit_button(
                "Clear",
                use_container_width=True
            )
        
        if submit:
            if not email or not password:
                st.error("❌ Please fill in all fields")
            else:
                with st.spinner("🔐 Authenticating..."):
                    result = auth.sign_in(email, password)
                    
                    if result["success"]:
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.user = result["user"]
                        
                        # Get user profile
                        profile = auth.get_user_profile(result["user"].id)
                        st.session_state.user_profile = profile
                        
                        # Check if admin
                        st.session_state.is_admin = profile.get("role") == "admin" if profile else False
                        st.session_state.is_active = profile.get("is_active", True) if profile else True
                        
                        st.success("✅ Login successful!")
                        st.balloons()
                        
                        # Redirect after a short delay
                        import time
                        time.sleep(1)
                        st.switch_page("app.py")
                    else:
                        st.error(f"❌ {result.get('error', 'Login failed')}")
                        st.info("💡 Tip: Check your email and password, or create a new account.")

# ============================================================================
# SIGNUP TAB
# ============================================================================
with tab2:
    st.subheader("Create New Account")
    
    with st.form("signup_form", clear_on_submit=False):
        new_email = st.text_input(
            "Email *",
            placeholder="your.email@example.com",
            key="signup_email",
            help="We'll send a verification email to this address"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input(
                "Full Name *",
                placeholder="John Doe",
                key="signup_name"
            )
        
        with col2:
            new_org = st.text_input(
                "Organization",
                placeholder="University/Company",
                key="signup_org",
                help="Optional"
            )
        
        new_password = st.text_input(
            "Password *",
            type="password",
            key="signup_pwd",
            help="Minimum 8 characters"
        )
        
        new_password2 = st.text_input(
            "Confirm Password *",
            type="password",
            key="signup_pwd2"
        )
        
        st.markdown("##### Terms & Conditions")
        accept_terms = st.checkbox(
            "I agree to the terms of service and privacy policy",
            key="accept_terms"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submit_signup = st.form_submit_button(
                "✨ Create Account",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            st.form_submit_button(
                "Clear",
                use_container_width=True
            )
        
        if submit_signup:
            # Validation
            errors = []
            
            if not all([new_email, new_name, new_password, new_password2]):
                errors.append("Please fill in all required fields (*)")
            
            if not accept_terms:
                errors.append("You must accept the terms and conditions")
            
            if new_password != new_password2:
                errors.append("Passwords don't match")
            
            if len(new_password) < 8:
                errors.append("Password must be at least 8 characters")
            
            if "@" not in new_email:
                errors.append("Please enter a valid email address")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                with st.spinner("📝 Creating your account..."):
                    result = auth.sign_up(
                        email=new_email,
                        password=new_password,
                        full_name=new_name,
                        organization=new_org
                    )
                    
                    if result["success"]:
                        st.success("✅ Account created successfully!")
                        st.info("""
                        📧 **Next Steps:**
                        1. Check your email inbox
                        2. Click the verification link
                        3. Return here and login
                        
                        *You can close this tab after verification.*
                        """)
                        st.balloons()
                    else:
                        st.error(f"❌ {result.get('error', 'Signup failed')}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: rgba(255,255,255,0.7);'>
    <p>🧬 RBC Metabolic Model v2.0</p>
    <p>Need help? Contact <a href='mailto:support@example.com' style='color: rgba(255,255,255,0.9);'>support@example.com</a></p>
</div>
""", unsafe_allow_html=True)
