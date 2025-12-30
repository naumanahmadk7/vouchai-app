import streamlit as st
import pdfplumber
import pandas as pd
import io

def extract_tables_from_pdf(file_obj, max_pages=None):
    """
    Logic: Scans the PDF for grid tables.
    max_pages: If 1, it stops after the first page (Free Tier).
    """
    all_rows = []
    
    try:
        # Re-open file buffer to start from byte 0
        file_obj.seek(0)
        
        with pdfplumber.open(file_obj) as pdf:
            # Decide how many pages to read
            pages_to_process = pdf.pages
            if max_pages:
                pages_to_process = pages_to_process[:max_pages]
                
            for i, page in enumerate(pages_to_process):
                # 'extract_tables' looks for vertical/horizontal lines
                tables = page.extract_tables()
                
                for table in tables:
                    # table is a list of lists [['Date', 'Desc'], ['1/1', 'Test']]
                    for row in table:
                        # Clean data: remove None, strip whitespace
                        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                        # Only keep rows that are not empty
                        if any(cleaned_row):
                            all_rows.append(cleaned_row)
                            
    except Exception as e:
        return None, str(e)

    if not all_rows:
        return pd.DataFrame(), "No tables found"

    # Convert to DataFrame
    # We assume the first found row is the header. 
    # (In a real pro tool, we would let the user select the header, but this is auto-mode)
    try:
        df = pd.DataFrame(all_rows[1:], columns=all_rows[0])
    except:
        # Fallback if columns don't match
        df = pd.DataFrame(all_rows)
        
    return df, "Success"

def run_statement_converter():
    st.markdown("## 🏦 PDF Bank Statement Converter")
    st.caption("Turn PDF Bank Statements into Excel/CSV automatically.")

    # ==========================================
    # 💰 THE MONETIZATION GATE (Gumroad Logic)
    # ==========================================
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔓 Pro Unlock")
        license_key = st.text_input("Enter License Key", type="password", help="Buy a key to unlock unlimited pages.")
        
        # THE PASSWORD CHECK
        is_pro = False
        if license_key == "VOUCH-2025-PRO":
            is_pro = True
            st.success("✅ Pro Mode Active: Unlimited Pages")
        else:
            st.warning("⚠️ Free Mode: Page 1 Only")
            # Replace this link with your actual Gumroad Product Link later
            st.markdown("👉 **[Buy Pro Key ($29)](https://gumroad.com)**")

    # ==========================================
    # 📤 THE UPLOADER
    # ==========================================
    uploaded_file = st.file_uploader("Upload Statement (PDF Only)", type=["pdf"])

    if uploaded_file:
        if st.button("🔄 Convert to Excel", type="primary"):
            
            with st.spinner("Scanning PDF for tables..."):
                # LOGIC: If Pro, None (All pages). If Free, 1 (First page).
                limit = None if is_pro else 1
                
                df, status = extract_tables_from_pdf(uploaded_file, max_pages=limit)
                
                if status == "Success" and not df.empty:
                    # 1. Show Success Message
                    st.success(f"✅ Conversion Complete! Extracted {len(df)} rows.")
                    
                    if not is_pro:
                        st.info("ℹ️ Free Tier: Only processed Page 1. Buy a key to convert the whole file.")

                    # 2. Preview Data
                    st.dataframe(df.head(10), use_container_width=True)

                    # 3. Download Button
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Excel (CSV)",
                        data=csv,
                        file_name="converted_statement.csv",
                        mime="text/csv"
                    )
                    
                elif "No tables" in str(status):
                    st.error("❌ No tables found.")
                    st.info("Tip: This tool works best on 'Digital PDFs' (with selectable text). If this is a scanned image, use the Audit Workbench tab.")
                else:
                    st.error(f"Error: {status}")
