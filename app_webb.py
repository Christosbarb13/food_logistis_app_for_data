import streamlit as st
import pandas as pd
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract as ps
import dokimi_app
import fitz  # PyMuPDF για PDF επεξεργασία

# Ρύθμιση Tesseract CMD
ps.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ρύθμιση τίτλου και σελίδας
st.set_page_config(page_title="Εφαρμογή Μισθοτροφοδοσίας & OCR", page_icon="📊", layout="wide")
st.title("📊 Εφαρμογή Μισθοτροφοδοσίας & Αναγνώριση Παραστατικών (OCR & PDF)")

tabs = st.tabs(["📁 Επεξεργασία Excel", "📷 Αναγνώριση Παραστατικών (Εικόνες & PDF)"])

# === TAB 1: Επεξεργασία Excel ===
with tabs[0]:
    st.header("Επεξεργασία Αρχείων Excel")
    uploaded_file = st.file_uploader("Επιλέξτε ένα αρχείο Excel", type=["xlsx", "xls"], key="excel_uploader")

    if uploaded_file is not None:
        st.success("Το αρχείο Excel φορτώθηκε επιτυχώς!")
        xl = pd.ExcelFile(uploaded_file)
        sheet_choice = st.selectbox("Επιλέξτε φύλλο (sheet):", xl.sheet_names)
        
        if sheet_choice:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_choice)
            st.subheader(f"Δεδομένα φύλλου: {sheet_choice}")
            st.dataframe(df.head(20), use_container_width=True)

# === TAB 2: OCR & PDF Παραστατικών ===
with tabs[1]:
    st.header("Αναγνώριση Παραστατικού (JPG, PNG, PDF)")
    st.write("Ανεβάστε μια εικόνα (JPG/PNG) ή αρχείο **PDF** παραστατικού για να εξαχθούν αυτόματα οι 6 στήλες (`ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ`, `ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ`, `ΜΟΝ. ΜΕΤΡ.`, `ΠΟΣΟΤ.`, `ΤΙΜΗ ΜΟΝΑΔΑΣ`, `ΣΥΝΟΛΟ ΑΞΙΑΣ`).")
    
    uploaded_doc = st.file_uploader("Ανεβάστε αρχείο (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"], key="doc_uploader")
    
    if uploaded_doc is not None:
        col1, col2 = st.columns([1, 2])
        is_pdf = uploaded_doc.name.lower().endswith(".pdf")
        
        with col1:
            if is_pdf:
                st.info("📄 Επιλέχθηκε αρχείο PDF. Γίνεται προεπισκόπηση της 1ης σελίδας...")
                pdf_bytes = uploaded_doc.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=150)
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                st.image(img_pil, caption="Προεπισκόπηση PDF (1η Σελίδα)", use_container_width=True)
            else:
                st.image(uploaded_doc, caption="Προεπισκόπηση Εικόνας", use_container_width=True)
            
        with col2:
            if st.button("🚀 Εκτέλεση OCR & Ανάλυσης"):
                with st.spinner("Γίνεται επεξεργασία αρχείου και αναγνώριση κειμένου..."):
                    text = ""
                    if is_pdf:
                        # 1. Δοκιμή άμεσης εξαγωγής κειμένου αν είναι ψηφιακό PDF
                        uploaded_doc.seek(0)
                        pdf_bytes = uploaded_doc.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        for page in doc:
                            text += page.get_text() + "\n"
                        
                        # 2. Αν είναι σκαναρισμένο PDF (χωρίς ψηφιακό κείμενο), κάνουμε OCR στη σελίδα
                        if len(text.strip()) < 20:
                            page = doc.load_page(0)
                            pix = page.get_pixmap(dpi=300)
                            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))
                            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                            blur = cv2.GaussianBlur(gray, (3, 3), 0)
                            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                            text = ps.image_to_string(thresh, lang='ell', config='--psm 6')
                    else:
                        # Επεξεργασία εικόνας (JPG/PNG)
                        image_bytes = np.asarray(bytearray(uploaded_doc.read()), dtype=np.uint8)
                        img = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                        blur = cv2.GaussianBlur(resized, (3, 3), 0)
                        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        text = ps.image_to_string(thresh, lang='ell', config='--psm 6')
                    
                    df_out = dokimi_app.parse_to_timologia_df(text)
                    
                    st.subheader("📋 Εξαγόμενα Δεδομένα (Μορφή 'timologia')")
                    st.dataframe(df_out, use_container_width=True)
                    
                    # Προετοιμασία λήψης Excel
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_out.to_excel(writer, sheet_name='timologia', index=False)
                    
                    st.download_button(
                        label="📥 Λήψη σε Αρχείο Excel",
                        data=buffer.getvalue(),
                        file_name="timologia_extracted.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
