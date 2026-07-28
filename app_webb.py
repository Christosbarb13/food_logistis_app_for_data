import streamlit as st
import pandas as pd
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract as ps
import dokimi_app

# Ρύθμιση Tesseract CMD
ps.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ρύθμιση τίτλου και σελίδας
st.set_page_config(page_title="Εφαρμογή Μισθοτροφοδοσίας & OCR", page_icon="📊", layout="wide")
st.title("📊 Εφαρμογή Μισθοτροφοδοσίας & Αναγνώριση Παραστατικών (OCR)")

tabs = st.tabs(["📁 Επεξεργασία Excel", "📷 Αναγνώριση Παραστατικών (timologia)"])

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

# === TAB 2: OCR Παραστατικών ===
with tabs[1]:
    st.header("Αναγνώριση Παραστατικού & Εξαγωγή σε Μορφή 'timologia'")
    st.write("Ανεβάστε μια εικόνα (JPG/PNG) παραστατικού για να εξαχθούν αυτόματα οι 6 στήλες (`ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ`, `ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ`, `ΜΟΝ. ΜΕΤΡ.`, `ΠΟΣΟΤ.`, `ΤΙΜΗ ΜΟΝΑΔΑΣ`, `ΣΥΝΟΛΟ ΑΞΙΑΣ`).")
    
    img_file = st.file_uploader("Ανεβάστε εικόνα παραστατικού", type=["jpg", "jpeg", "png"], key="img_uploader")
    
    if img_file is not None:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(img_file, caption="Προεπισκόπηση Εικόνας", use_container_width=True)
            
        with col2:
            if st.button("🚀 Εκτέλεση OCR & Ανάλυσης"):
                with st.spinner("Γίνεται επεξεργασία εικόνας και αναγνώριση κειμένου..."):
                    # Μετατροπή uploaded file σε OpenCV BGR image
                    image_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
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
