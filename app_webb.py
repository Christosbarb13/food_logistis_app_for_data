import streamlit as st
import pandas as pd
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract as ps
import dokimi_app
import fitz  # PyMuPDF για PDF επεξεργασία
import re
# Ρύθμιση Tesseract CMD
ps.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ρύθμιση τίτλου και σελίδας
st.set_page_config(page_title="Εφαρμογή Μισθοτροφοδοσίας & OCR", layout="wide")
st.title("Εφαρμογή Μισθοτροφοδοσίας & Αναγνώριση Παραστατικών (OCR & PDF)")

# --- Ρυθμίσεις Sidebar ---
with st.sidebar:
    st.header("⚙️ Ρυθμίσεις Εξαγωγής")
    use_ai = st.toggle("Χρήση Τεχνητής Νοημοσύνης (Gemini AI)", value=False)
    
    if use_ai:
        api_key = st.text_input("Google Gemini API Key", type="password", help="Εισάγετε το API Key σας από το Google AI Studio.")
        st.markdown("[Δημιουργία δωρεάν API Key](https://aistudio.google.com/app/apikey)")
        custom_prompt = st.text_area(
            "Οδηγίες Εξαγωγής (Προδιαγραφές)",
            value="Εξήγαγε τις εξής στήλες: 'ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ', 'ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ', 'ΜΟΝ. ΜΕΤΡ.', 'ΠΟΣΟΤ.', 'ΤΙΜΗ ΜΟΝΑΔΑΣ', 'ΣΥΝΟΛΟ ΑΞΙΑΣ'."
        )
    else:
        api_key = ""
        custom_prompt = ""

tabs = st.tabs(["Επεξεργασία Excel", "Αναγνώριση Παραστατικών (Εικόνες & PDF)"])

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
    st.header("Αναγνώριση Παραστατικού (JPG, PNG, WEBP, PDF)")
    st.write("Ανεβάστε μια εικόνα (JPG/PNG/WEBP) ή αρχείο **PDF** παραστατικού για να εξαχθούν αυτόματα οι 6 στήλες (`ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ`, `ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ`, `ΜΟΝ. ΜΕΤΡ.`, `ΠΟΣΟΤ.`, `ΤΙΜΗ ΜΟΝΑΔΑΣ`, `ΣΥΝΟΛΟ ΑΞΙΑΣ`).")
    st.info("💡 **Tip για καλύτερα αποτελέσματα:** Τα αρχεία από κανονικό σκάνερ/εκτυπωτή ή από εφαρμογές σκαναρίσματος κινητού (π.χ. Microsoft Lens, Adobe Scan) που εξάγουν PDF διαβάζονται με σχεδόν 100% ακρίβεια. Αντίθετα, απλές φωτογραφίες από κάμερα κινητού ενδέχεται να έχουν σκιές, γωνίες και θολούρα που δυσκολεύουν το OCR.")
    
    uploaded_doc = st.file_uploader("Ανεβάστε αρχείο (JPG, PNG, WEBP, PDF)", type=["jpg", "jpeg", "png", "webp", "pdf"], key="doc_uploader")
    
    if uploaded_doc is not None:
        col1, col2 = st.columns([1, 2])
        is_pdf = uploaded_doc.name.lower().endswith(".pdf")
        
        with col1:
            if is_pdf:
                st.info("Επιλέχθηκε αρχείο PDF. Γίνεται προεπισκόπηση της 1ης σελίδας...")
                pdf_bytes = uploaded_doc.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=150)
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                st.image(img_pil, caption="Προεπισκόπηση PDF (1η Σελίδα)", use_container_width=True)
            else:
                st.image(uploaded_doc, caption="Προεπισκόπηση Εικόνας", use_container_width=True)
            
        with col2:
            if st.button("Εκτέλεση OCR & Ανάλυσης"):
                with st.spinner("Γίνεται επεξεργασία αρχείου και αναγνώριση κειμένου..."):
                    text = ""
                    if is_pdf:
                        # 1. Δοκιμή άμεσης εξαγωγής κειμένου αν είναι ψηφιακό PDF
                        uploaded_doc.seek(0)
                        pdf_bytes = uploaded_doc.read()
                        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                        extracted_text = ""
                        for page in doc:
                            extracted_text += page.get_text() + "\n"
                        
                        # 2. Έλεγχος αν περιέχει πραγματικά δεδομένα (τουλάχιστον 3 αριθμούς)
                        has_real_text = len(re.findall(r'\d+', extracted_text)) >= 3
                        
                        if has_real_text:
                            text = extracted_text
                        else:
                            # 3. Αν είναι σκαναρισμένο PDF, μετατροπή σε εικόνα υψηλής ανάλυσης & πλήρες OpenCV Pipeline
                            text_pages = []
                            for page_num in range(len(doc)):
                                page = doc.load_page(page_num)
                                pix = page.get_pixmap(dpi=300)
                                img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))
                                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                                if gray.shape[1] < 1500:
                                    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                                blur = cv2.GaussianBlur(gray, (3, 3), 0)
                                _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                                page_text = ps.image_to_string(thresh, lang='ell', config='--psm 4')
                                text_pages.append(page_text)
                            text = "\n".join(text_pages)
                    else:
                        # Επεξεργασία εικόνας (JPG/PNG/WEBP με PIL)
                        uploaded_doc.seek(0)
                        img_pil = Image.open(uploaded_doc).convert("RGB")
                        img_np = np.array(img_pil)
                        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                        if gray.shape[1] < 1500:
                            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                        blur = cv2.GaussianBlur(gray, (3, 3), 0)
                        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        text = ps.image_to_string(thresh, lang='ell', config='--psm 4')
                    
                    if use_ai:
                        if not api_key:
                            st.error("Παρακαλώ εισάγετε ένα έγκυρο API Key στις Ρυθμίσεις (Sidebar) αριστερά για να χρησιμοποιήσετε το AI.")
                            st.stop()
                        try:
                            df_out = dokimi_app.parse_with_llm(text, api_key, custom_prompt)
                        except Exception as e:
                            st.error(f"Σφάλμα κατά την επικοινωνία με το AI: {e}")
                            st.stop()
                    else:
                        df_out = dokimi_app.parse_to_timologia_df(text)
                    
                    st.subheader("Εξαγόμενα Δεδομένα (Μορφή 'timologia')")
                    st.dataframe(df_out, use_container_width=True)
                    
                    # Προετοιμασία λήψης Excel
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_out.to_excel(writer, sheet_name='timologia', index=False)
                    
                    st.download_button(
                        label="Λήψη σε Αρχείο Excel",
                        data=buffer.getvalue(),
                        file_name="timologia_extracted.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
