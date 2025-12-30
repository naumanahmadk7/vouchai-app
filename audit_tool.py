import streamlit as st
import pandas as pd
import re
import tempfile
import os
from utils import extract_text_ensemble

# ==========================================
# 1. HELPER FUNCTIONS (The "Engine")
# ==========================================
def parse_invoice_text(text: str, filename: str) -> dict:
    data = {
        "File": filename,
        "Vendor": "Unknown Vendor",
        "Date": None,
        "Amount": 0.0,
        "Invoice_No": None,
        "Raw_Text": text
    }

    clean_lines = []
    noise_patterns = [
        r"===", r"---", r"OCR", r"DIGITIZATION", 
        r"TESSERACT", r"EASYOCR", r"PDFPLUMBER",
        r"Billed", r"Ship", r"Invoice", r"Page", r"Phone", r"Fax", 
        r"Email", r"Web", r"Tax", r"GST", r"VAT", r"Payment"
    ]
    
    for line in text.split('\n'):
        if len(line.strip()) < 3: continue
        is_noise = False
        for p in noise_patterns:
            if re.search(p, line, re.IGNORECASE): 
                is_noise = True
                break
        if not is_noise:
            clean_lines.append(line.strip())

    for line in clean_lines[:8]: 
        if not re.search(r'\d', line) and re.match(r'^[A-Za-z]', line):
            data["Vendor"] = line
            break

    greedy_amount = re.search(r'(?:Total|Balance|Due|Amount).*?([\d,]+\.\d{2})', text, re.IGNORECASE)
    if greedy_amount:
        try:
            val = float(greedy_amount.group(1).replace(',', '').replace(' ', ''))
            data["Amount"] = val
        except: pass
    else:
        all_money = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2})', text)
        valid_amounts = []
        for m in all_money:
            try:
                v = float(m.replace(',', ''))
                valid_amounts.append(v)
            except: pass
        if valid_amounts:
            data["Amount"] = max(valid_amounts)

    months = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    text_date = re.search(f"({months}" + r"\s+\d{1,2},?\s*\d{4})", text, re.IGNORECASE)
    numeric_date = re.search(r'(\d{4}-\d{2}-\d{2})|(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)

    if text_date:
        data["Date"] = text_date.group(1)
    elif numeric_date:
        data["Date"] = numeric_date.group(0)

    return data

def run_audit_match(ledger_df, processed_invoices):
    results = ledger_df.copy()
    results['Match Status'] = '❌ Missing'
    results['Linked File'] = ''

    for idx, row in results.iterrows():
        try: ledger_amt = float(row.get('Amount', 0))
        except: ledger_amt = 0.0
        
        ledger_date = str(row.get('Date', '')).lower()
        
        for inv in processed_invoices:
            amt_match = abs(ledger_amt - inv['Amount']) < 1.00
            
            inv_date = str(inv['Date']).lower()
            date_match = False
            if len(inv_date) > 3 and len(ledger_date) > 3:
                if inv_date in ledger_date or ledger_date in inv_date:
                    date_match = True
                if '2019' in inv_date and '2019' in ledger_date:
                    date_match = True 

            if amt_match: 
                results.at[idx, 'Match Status'] = '✅ Matched'
                results.at[idx, 'Linked File'] = inv['File']
                break 
                
    return results

# ==========================================
# 2. THE MAIN UI FUNCTION
# ==========================================
def run_audit_tool():
    st.markdown("""
    <style>
        .main-header { font-size: 2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0px; }
        .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 20px; }
        div[data-testid="stDataFrame"] { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<p class="main-header">🛡️ VouchAI Workbench</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Automated Reconciliation System (Community Edition)</p>', unsafe_allow_html=True)

    # --- SIDEBAR SETTINGS ---
    with st.sidebar:
        st.header("⚙️ Settings")
        mode = st.radio("Select Mode:", ["1. Bookkeeping (Create Excel)", "2. Audit (Verify Excel)"])
        st.info("Running Cloud Optimized Extraction")

    # --- SAFE FILE UPLOADER (Security Upgrade) ---
    uploaded_invoices = st.file_uploader(
        "1️⃣ Upload Invoices (Max 10MB per file)", 
        type=['pdf', 'png', 'jpg', 'jpeg'], 
        accept_multiple_files=True
    )
    
    # Security Check
    if uploaded_invoices:
        if len(uploaded_invoices) > 10:
             st.error("⚠️ Free Tier Limit Reached: Max 10 files allowed. Contact Sales for Enterprise Access.")
             st.stop()
        for f in uploaded_invoices:
             if f.size > 10 * 1024 * 1024:
                  st.error(f"⚠️ File too large: {f.name} (Limit: 10MB)")
                  st.stop()

    ledger_file = None
    if mode == "2. Audit (Verify Excel)":
        ledger_file = st.file_uploader("2️⃣ Upload Ledger (Excel/CSV)", type=['xlsx', 'csv'])

    if 'audit_results' not in st.session_state:
        st.session_state.audit_results = None

    if uploaded_invoices:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            
            processed_data = []
            progress_bar = st.progress(0)
            
            with st.spinner("Extracting Data (Cloud Engine)..."):
                for i, file in enumerate(uploaded_invoices):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.name.split('.')[-1]}") as tmp:
                        tmp.write(file.getvalue())
                        tmp_path = tmp.name
                    
                    # CALL ENGINE (From utils.py)
                    raw_text = extract_text_ensemble(tmp_path)
                    
                    # PARSE TEXT
                    parsed = parse_invoice_text(raw_text, file.name)
                    processed_data.append(parsed)
                    
                    try: os.unlink(tmp_path)
                    except: pass
                    progress_bar.progress((i + 1) / len(uploaded_invoices))

            # MODES
            if mode == "1. Bookkeeping (Create Excel)":
                df = pd.DataFrame(processed_data)
                df['Match Status'] = '✨ Auto-Created'
                st.session_state.audit_results = df
                
            elif mode == "2. Audit (Verify Excel)" and ledger_file:
                if ledger_file.name.endswith('.csv'):
                    ledger_df = pd.read_csv(ledger_file)
                else:
                    ledger_df = pd.read_excel(ledger_file)
                
                result_df = run_audit_match(ledger_df, processed_data)
                st.session_state.audit_results = result_df
                
            elif mode == "2. Audit (Verify Excel)" and not ledger_file:
                st.error("Please upload an Excel file to verify against.")

    # RESULTS UI
    if st.session_state.audit_results is not None:
        st.markdown("---")
        left_col, right_col = st.columns([1, 1])
        
        with right_col:
            st.subheader("📊 Data Grid")
            selection = st.dataframe(
                st.session_state.audit_results, 
                use_container_width=True,
                selection_mode="single-row",
                on_select="rerun"
            )
            csv = st.session_state.audit_results.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report", csv, "vouchai_report.csv", "text/csv")

        with left_col:
            st.subheader("📄 Evidence Viewer")
            selected_file_name = None
            if hasattr(selection, "selection") and selection.selection.rows:
                 row_idx = selection.selection.rows[0]
                 row_data = st.session_state.audit_results.iloc[row_idx]
                 selected_file_name = row_data.get('Linked File') or row_data.get('File')

            file_to_show = None
            if selected_file_name:
                for f in uploaded_invoices:
                    if f.name == selected_file_name:
                        file_to_show = f
                        break
            
            if file_to_show:
                st.info(f"Viewing: {file_to_show.name}")
                
                # --- SAFE DOWNLOAD BUTTON (Fixes Chrome Block) ---
                st.download_button(
                    label=f"💾 Download {file_to_show.name} to View",
                    data=file_to_show.getvalue(),
                    file_name=file_to_show.name,
                    mime=file_to_show.type
                )
                
                # --- SAFE PREVIEW (With Fallback) ---
                if "pdf" in file_to_show.type:
                    import base64
                    base64_pdf = base64.b64encode(file_to_show.getvalue()).decode('utf-8')
                    pdf_display = f'<object data="data:application/pdf;base64,{base64_pdf}" type="application/pdf" width="100%" height="500"><p>Preview blocked by browser. Use Download button!</p></object>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.image(file_to_show, use_column_width=True)
            else:
                st.warning("Select a row on the right to view the proof.")
