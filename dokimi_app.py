import sys
import re
import cv2
import pytesseract as ps
import pandas as pd
import json
from google import genai

# 1. Ρύθμιση εκτύπωσης Ελληνικών στην κονσόλα
sys.stdout.reconfigure(encoding='utf-8')

# 2. Διαδρομή Tesseract OCR
ps.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_and_ocr(image_path):
    """
    Προεπεξεργασία εικόνας (2x Resize + Gaussian Blur + Otsu Thresholding)
    και εκτέλεση OCR με Tesseract.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Το αρχείο {image_path} δεν βρέθηκε.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Αποφυγή μεγέθυνσης αν η εικόνα είναι ήδη υψηλής ανάλυσης
    if gray.shape[1] < 1500:
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Εκτέλεση OCR με PSM 4 (Columnar text)
    text = ps.image_to_string(thresh, lang='ell', config='--psm 4')
    return text

def parse_to_timologia_df(ocr_text):
    """
    Αναλύει το κείμενο OCR με δυναμικό List Slicing και το μετατρέπει σε DataFrame 
    με τις 6 στήλες:
    ['ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ', 'ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ', 'ΜΟΝ. ΜΕΤΡ.', 'ΠΟΣΟΤ.', 'ΤΙΜΗ ΜΟΝΑΔΑΣ', 'ΣΥΝΟΛΟ ΑΞΙΑΣ']
    """
    all_lines = ocr_text.split('\n')
    records = []

    def format_decimal(val_str):
        if val_str == '-':
            return '-'
        val_clean = val_str.replace(',', '.')
        parts = val_clean.split('.')
        if len(parts) > 2:
            val_clean = "".join(parts[:-1]) + "." + parts[-1]
        try:
            num = float(val_clean)
            return f"{num:.2f}"
        except ValueError:
            return val_clean

    # === 1. ΔΥΝΑΜΙΚΟΣ ΕΝΤΟΠΙΣΜΟΣ ΑΡΧΗΣ ΠΙΝΑΚΑ (Header Detection) ===
    header_keywords = ["ΠΕΡΙΓΡΑΦΗ", "ΚΩΔΙΚΟΣ", "ΠΟΣΟΤ", "ΕΜΠΟΡΕΥΜΑΤΟΣ", "ΧΟΡΗΓΗΣΑΤΕ"]
    start_idx = 0
    for i, line in enumerate(all_lines):
        line_upper = line.upper()
        if any(keyword in line_upper for keyword in header_keywords):
            start_idx = i + 1  # Ο πίνακας ξεκινάει αμέσως μετά την επικεφαλίδα
            break

    # === 2. ΔΥΝΑΜΙΚΟΣ ΕΝΤΟΠΙΣΜΟΣ ΤΕΛΟΥΣ ΠΙΝΑΚΑ (Footer Detection) ===
    footer_keywords = ["ΣΥΝΟΛΟ", "ΦΠΑ", "ΕΘΕΩΡΗΘΗ", "ΥΠΟΓΡΑΦΗ", "ΣΦΡΑΓΙΔΑ", "ΠΛΗΡΩΤΕΟ", "ΓΕΝΙΚΟ", "ΕΙΣΠΡΑΧΘΗΚΕ", "ΠΑΡΑΛΑΜΒΑΝΩΝ"]
    end_idx = len(all_lines)
    for i in range(start_idx, len(all_lines)):
        line_upper = all_lines[i].upper()
        
        # Αποφυγή false positive αν η γραμμή περιέχει 'ΣΥΝΟΛΟ' αλλά είναι η επικεφαλίδα του πίνακα
        if "ΣΥΝΟΛΟ ΑΞΙΑΣ" in line_upper or "ΤΙΜΗ ΜΟΝΑΔΑΣ" in line_upper:
            continue
            
        if any(keyword in line_upper for keyword in footer_keywords):
            end_idx = i  # Ο πίνακας τελειώνει πριν από το άθροισμα/υπογραφή
            break

    # Λέξεις κλειδιά επικεφαλίδων στοιχείων πελάτη/αποστολής που πρέπει να παραλείπονται
    customer_info_keywords = [
        "ΑΦΜ", "ΤΗΛΕΦΩΝΟ", "ΔΟΥ", "Δ.Ο.Υ", "ΔΙΕΥΘΥΝΣΗ", "ΕΠΑΓΓΕΛΜΑ", "ΓΕΜΗ",
        "ΠΑΡΑΣΤΑΤΙΚΟΥ", "ΗΜΕΡΟΜΗΝΙΑ", "ΑΠΟΣΤΟΛΗΣ", "ΦΟΡΤΩΣΗΣ", "ΠΡΟΟΡΙΣΜΟΥ",
        "ΠΛΗΡΩΜΗΣ", "ΕΠΩΝΥΜΙΑ", "ΣΕΙΡΑ", "ΤΟΠΟΣ", "ΤΡΟΠΟΣ"
    ]

    # === 3. LIST SLICING: Απομόνωση ΜΟΝΟ των γραμμών του πίνακα ===
    table_lines = all_lines[start_idx:end_idx]

    # === 4. ΕΠΕΞΕΡΓΑΣΙΑ ΚΑΘΕ ΓΡΑΜΜΗΣ ΤΟΥ ΠΙΝΑΚΑ ===
    for line in table_lines:
        line_str = line.strip()
        if not line_str:
            continue

        line_upper = line_str.upper()
        # Παράλειψη γραμμών που περιέχουν στοιχεία επικεφαλίδας παραστατικού/πελάτη
        if any(k in line_upper for k in customer_info_keywords):
            continue

        # Καθαρισμός θορύβου χαρακτήρων
        line_clean = re.sub(r'[\[\]\{\}\|”"«»\~]', '', line_str)

        # Εξαγωγή Κωδικού Είδους (αν υπάρχει στο ξεκίνημα)
        code_match = re.match(r'^([0-9]{2,4}[\.,\s]+[0-9]{3,6}|[0-9]{5,6})', line_clean)
        if code_match:
            raw_code = code_match.group(0)
            code = re.sub(r'[^\d]', '', raw_code)[:6]
            line_clean = line_clean[len(raw_code):].strip()
        else:
            code = '-'

        # Εξαγωγή Μονάδας Μέτρησης (τεμά, τεμαχ, Κιλά, Κιβώ)
        u_match = re.search(r'\b(τεμά|τεμαχ|τεμ|κιλά|κιβώ|κτν|κιλ|kg|gr)\b', line_clean, re.IGNORECASE)
        if u_match:
            unit_str = u_match.group(0)
            u_lower = unit_str.lower()
            if 'τεμ' in u_lower:
                unit = 'τεμά'
            elif 'κιλ' in u_lower or 'kg' in u_lower:
                unit = 'Κιλά'
            elif 'κιβ' in u_lower:
                unit = 'Κιβώ'
            else:
                unit = unit_str
        else:
            unit = 'τεμά'

        # Εντοπισμός αριθμών για Ποσότητα, Τιμή Μονάδας, Σύνολο Αξίας
        clean_nums = re.findall(r'\b\d+[\.,]\d+\b|\b\d+\b', line_clean)

        if len(clean_nums) >= 3:
            posot = format_decimal(clean_nums[-3])
            timi_mon = format_decimal(clean_nums[-2])
            synolo = format_decimal(clean_nums[-1])
            nums_to_remove = clean_nums[-3:]
        elif len(clean_nums) == 2:
            posot = '-'
            timi_mon = format_decimal(clean_nums[-2])
            synolo = format_decimal(clean_nums[-1])
            nums_to_remove = clean_nums[-2:]
        elif len(clean_nums) == 1:
            posot = '-'
            timi_mon = '-'
            synolo = format_decimal(clean_nums[-1])
            nums_to_remove = clean_nums[-1:]
        else:
            posot, timi_mon, synolo = '-', '-', '-'
            nums_to_remove = []

        # Εξαγωγή Περιγραφής Εμπορεύματος
        desc = line_clean
        if u_match:
            desc = desc.replace(u_match.group(0), '')
        for num in nums_to_remove:
            desc = desc.replace(num, '')

        desc = re.sub(r'[^a-zA-Zα-ωΑ-Ω0-9\s\.\-\/\(\)]', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Προσθήκη εγγραφής αν περιέχει έγκυρη περιγραφή και τουλάχιστον μία τιμή
        if len(desc) > 2 and (synolo != '-' or timi_mon != '-'):
            records.append({
                'ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ': code,
                'ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ': desc,
                'ΜΟΝ. ΜΕΤΡ.': unit,
                'ΠΟΣΟΤ.': posot,
                'ΤΙΜΗ ΜΟΝΑΔΑΣ': timi_mon,
                'ΣΥΝΟΛΟ ΑΞΙΑΣ': synolo
            })

    columns = ['ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ', 'ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ', 'ΜΟΝ. ΜΕΤΡ.', 'ΠΟΣΟΤ.', 'ΤΙΜΗ ΜΟΝΑΔΑΣ', 'ΣΥΝΟΛΟ ΑΞΙΑΣ']
    df = pd.DataFrame(records, columns=columns)
    return df

# === ΚΥΡΙΩΣ ΠΡΟΓΡΑΜΜΑ ===
if __name__ == '__main__':
    image_file = "dokimi.jpg"
    excel_output = "dokimi_timologia_output.xlsx"
    
    print(f"--- 1. Επεξεργασία εικόνας & OCR: {image_file} ---")
    try:
        raw_text = preprocess_and_ocr(image_file)
        
        print("--- 2. Μετατροπή σε Δομή 6 Στηλών ('timologia') ---")
        df_timologia = parse_to_timologia_df(raw_text)
        
        # Προβολή αποτελεσμάτων στην κονσόλα
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print("\n" + df_timologia.to_string(index=False))
        
        # 3. Αποθήκευση σε νέο αρχείο Excel στη μορφή timologia
        df_timologia.to_excel(excel_output, sheet_name='timologia', index=False)
        print(f"\n✅ Τα αποτελέσματα αποθηκεύτηκαν επιτυχώς στο αρχείο Excel: {excel_output}")
        
    except FileNotFoundError as e:
        print(f"❌ Σφάλμα: {e}")
    except Exception as e:
        print(f"❌ Προέκυψε σφάλμα κατά την επεξεργασία: {e}")

def parse_with_llm(ocr_text, api_key, custom_prompt):
    """
    Χρησιμοποιεί το σύγχρονο Google Gemini API (gemini-1.5-flash) για να δομήσει το OCR κείμενο.
    Επιστρέφει DataFrame έτοιμο για εμφάνιση και εξαγωγή.
    """
    if not api_key:
        raise ValueError("Δεν βρέθηκε API Key.")
        
    client = genai.Client(api_key=api_key)
    
    full_prompt = f"""
    Είσαι ένας ειδικός βοηθός ανάλυσης δεδομένων και τιμολογίων. Σου δίνεται το παρακάτω αδόμητο κείμενο που εξήχθη από ένα σύστημα OCR.
    
    ΟΔΗΓΙΕΣ ΧΡΗΣΤΗ / ΠΡΟΔΙΑΓΡΑΦΕΣ:
    {custom_prompt}
    
    ΣΗΜΑΝΤΙΚΟΣ ΚΑΝΟΝΑΣ ΜΟΡΦΟΠΟΙΗΣΗΣ:
    Η απάντησή σου ΠΡΕΠΕΙ να είναι ΑΥΣΤΗΡΑ ένα έγκυρο JSON Array (λίστα). Δεν πρέπει να περιέχει καμία άλλη επεξήγηση, Markdown blocks (όπως ```json) ή εισαγωγικό κείμενο. Μόνο το raw JSON array.
    Το JSON array θα περιέχει dictionaries. Τα κλειδιά (keys) των dictionaries πρέπει να ταιριάζουν ακριβώς με τις στήλες που περιγράφονται στις οδηγίες. Αν κάποιο δεδομένο λείπει, βάλε "-".

    ΚΕΙΜΕΝΟ OCR:
    {ocr_text}
    """
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=full_prompt
    )
    
    try:
        # Καθαρισμός τυχόν markdown formatting από το response
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        df = pd.DataFrame(data)
        
        # Αν η απάντηση δεν είναι σωστή λίστα
        if df.empty and isinstance(data, dict):
            df = pd.DataFrame([data])
            
        return df
    except json.JSONDecodeError as e:
        raise ValueError(f"Το μοντέλο δεν επέστρεψε έγκυρο JSON. Απάντηση:\n{response.text}") from e
