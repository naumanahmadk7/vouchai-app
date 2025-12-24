import os
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
import easyocr
import numpy as np
from PIL import Image
import streamlit as st

# --- CONFIGURATION ---
# POINT THIS TO YOUR TESSERACT EXE
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load EasyOCR once (Cache it to speed up app)
@st.cache_resource
def get_easyocr_reader():
    return easyocr.Reader(['en'], gpu=False)

def extract_text_ensemble(file_path):
    """
    Ensemble OCR:
    - PDF: Runs Digital Read + Tesseract + EasyOCR
    - Image: Runs Tesseract + EasyOCR directly (bypasses PDF engine)
    """
    combined_text = ""
    separator = "\n" + "="*20 + "\n"
    
    # Check file type
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # === CASE A: IMAGE FILES (JPG, PNG) ===
        if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            try:
                img = Image.open(file_path)
                
                # Engine 1: Tesseract
                combined_text += f"{separator}--- TESSERACT OCR ---{separator}"
                combined_text += pytesseract.image_to_string(img) + "\n"
                
                # Engine 2: EasyOCR
                reader = get_easyocr_reader()
                # Convert PIL Image to Numpy for EasyOCR
                img_np = np.array(img)
                results = reader.readtext(img_np, detail=0)
                combined_text += f"{separator}--- EASYOCR AI ---{separator}"
                combined_text += " ".join(results) + "\n"
                
                return combined_text
            except Exception as e:
                return f"[Image Processing Error: {e}]"

        # === CASE B: PDF FILES ===
        # 1. Digital Read (Fastest)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: combined_text += text + "\n"
        except: pass

        # 2. Image-based OCR (Tesseract + EasyOCR)
        doc = fitz.open(file_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom=2
            
            # Create generic image objects
            img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # Tesseract
            combined_text += pytesseract.image_to_string(img_pil) + "\n"
            
            # EasyOCR
            reader = get_easyocr_reader()
            results = reader.readtext(img_np, detail=0)
            combined_text += " ".join(results) + "\n"
            
        doc.close()
        return combined_text

    except Exception as e:
        return f"[Ensemble Error: {e}]"