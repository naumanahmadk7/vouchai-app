import streamlit as st

# ==========================================
# 0. CONFIG (Must be the first command)
# ==========================================
st.set_page_config(
    page_title="VouchAI | Audit Workbench", 
    layout="wide", 
    page_icon="🛡️"
)

# IMPORT TOOLS (The Modular Connections)
import audit_tool       # Kitchen #1 (Audit)
import statement_tool   # Kitchen #2 (Statement Converter)

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
    # Run the function from statement_tool.py
    statement_tool.run_statement_converter()
