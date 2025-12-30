import streamlit as st

# ==========================================
# 0. CONFIG (Must be the first command)
# ==========================================
st.set_page_config(
    page_title="VouchAI | Audit Workbench", 
    layout="wide", 
    page_icon="🛡️"
)

# IMPORT TOOLS (Modular Structure)
# Note: We import 'audit_tool' which contains the logic we just moved
import audit_tool 

# ==========================================
# 1. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h1>🛡️ VouchAI</h1>", unsafe_allow_html=True)
    st.caption("Enterprise Audit Automation")
    st.markdown("---")
    
    # Navigation Menu
    menu_choice = st.radio(
        "Select Module:", 
        ["1. Audit Workbench (Free)", "2. Statement Converter (Pro)"]
    )
    
    st.markdown("---")
    st.info("🔒 Secure Cloud Environment")

# ==========================================
# 2. ROUTING LOGIC
# ==========================================
if menu_choice == "1. Audit Workbench (Free)":
    # Run the function from audit_tool.py
    audit_tool.run_audit_tool()

elif menu_choice == "2. Statement Converter (Pro)":
    st.title("🏦 PDF Statement Converter")
    st.warning("🚧 This module is under construction.")
    st.markdown("""
    ### Coming Soon
    This feature will allow you to:
    - Upload PDF Bank Statements (Chase, Wells Fargo, etc.)
    - Automatically extract tables into Excel.
    - Reconcile balances automatically.
    
    **Status:** Development Phase.
    """)
