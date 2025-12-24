import os
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
import easyocr
import numpy as np
from PIL import Image
import streamlit as st
import shutil  # <--- CRITICAL FOR CLOUD

# --- CONFIGURATION: CLOUD vs LOCAL ---
# This tells the app: "If on Cloud, find Tesseract automatically. If on Windows, look in C drive."
if shutil.which('tesseract'): 
    pytesseract.pytesseract.tesseract_cmd = shutil.which('tesseract')
else:
    # Windows Fallback
    possible_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(possible_path):
        pytesseract.pytesseract.tesseract_cmd = possible_path

# Load EasyOCR once (Cache it)
@st.cache_resource
def get_easyocr_reader():
    # gpu=False is required for Free Cloud Hosting
    return easyocr.Reader(['en'], gpu=False)

def extract_text_ensemble(file_path):
    """
    Ensemble OCR:
    - PDF: Runs Digital Read + Tesseract + EasyOCR
    - Image: Runs Tesseract + EasyOCR directly
    """
    combined_text = ""
    separator = "\n" + "="*20 + "\n"
    
    # Check file type
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # === CASE A: IMAGE FILES (JPG, PNG) ===
        if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]:
            try:
                img = Image.open(file_path)
                
                # Engine 1: Tesseract
                combined_text += f"{separator}--- TESSERACT OCR ---{separator}"
                try:
                    combined_text += pytesseract.image_to_string(img) + "\n"
                except Exception as e:
                    combined_text += f"[Tesseract Error: {e}]\n"
                
                # Engine 2: EasyOCR
                try:
                    reader = get_easyocr_reader()
                    img_np = np.array(img)
                    results = reader.readtext(img_np, detail=0)
                    combined_text += f"{separator}--- EASYOCR AI ---{separator}"
                    combined_text += " ".join(results) + "\n"
                except Exception as e:
                    combined_text += f"[EasyOCR Error: {e}]\n"
                
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
        try:
            doc = fitz.open(file_path)
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom=2
                
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                
                try:
                    combined_text += pytesseract.image_to_string(img_pil) + "\n"
                except: pass
                
                try:
                    reader = get_easyocr_reader()
                    results = reader.readtext(img_np, detail=0)
                    combined_text += " ".join(results) + "\n"
                except: pass
                
            doc.close()
        except Exception as e:
            return f"[PDF Image Scan Error: {e}]"
            
        return combined_text

    except Exception as e:
        return f"[Ensemble Error: {e}]"
