import sys
import re
import cv2
import pytesseract as ps
import pandas as pd

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
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(resized, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Εκτέλεση OCR με PSM 6 (Single uniform block of text)
    text = ps.image_to_string(thresh, lang='ell', config='--psm 6')
    return text

def parse_to_timologia_df(ocr_text):
    """
    Αναλύει το κείμενο OCR και το μετατρέπει σε DataFrame με τη δομή 6 στηλών
    του φύλλου 'timologia':
    ['ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ', 'ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ', 'ΜΟΝ. ΜΕΤΡ.', 'ΠΟΣΟΤ.', 'ΤΙΜΗ ΜΟΝΑΔΑΣ', 'ΣΥΝΟΛΟ ΑΞΙΑΣ']
    """
    lines = ocr_text.split('\n')
    records = []

    # Λέξεις κλειδιά για παράλειψη κεφαλίδων/υποσέλιδων
    ignore_keywords = [
        "ΑΡΙΘΜΟΣ", "ΠΑΡΑΣΤΑΤΙΚΟΥ", "ΠΑΡΛΑΣΤΑΤΙΚΟΥ", "ΧΟΡΗΓΗΣΑΤΕ", "ΧΟΕΗΓΗΣΑΤΕ",
        "ΠΕΡΙΓΡΑΦΗ", "ΕΘΕΩΡΗΘΗ", "ΥΠΟΓΡΑΦΗ", "ΣΦΡΑΓΙΔΑ", "ΔΙΑΤΑΚΤΙΚΗ",
        "ΠΩΛΗΣΕΩΝ", "ΗΜΕΡΟΜΗΝΙΑ", "ΙΜΕΓΟΜΙΝΗΙΑ", "ΩΡΑ", "ΣΕΛΙΔΑ"
    ]

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

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # 1. Καθαρισμός θορύβου χαρακτήρων
        line_clean = re.sub(r'[\[\]\{\}\|”"«»\~]', '', line_str)

        # 2. Έλεγχος αν είναι γραμμή επικεφαλίδας ή υπογραφής
        if any(keyword in line_clean.upper() for keyword in ignore_keywords):
            continue

        # 3. Εξαγωγή Κωδικού Είδους (π.χ. 228. 0016 -> 2280016, 55.001 -> 55001)
        code_match = re.match(r'^([0-9]{2,4}[\.,\s]+[0-9]{3,6}|[0-9]{5,6})', line_clean)
        if code_match:
            raw_code = code_match.group(0)
            code = re.sub(r'[^\d]', '', raw_code)[:6]
            line_clean = line_clean[len(raw_code):].strip()
        else:
            code = '-'

        # 4. Εξαγωγή Μονάδας Μέτρησης (τεμά, Κιλά, Κιβώ)
        u_match = re.search(r'\b(τεμά|κιλά|κιβώ|κτν|τεμ|κιλ|kg|gr)\b', line_clean, re.IGNORECASE)
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

        # 5. Εντοπισμός αριθμών για Ποσότητα, Τιμή Μονάδας, Σύνολο Αξίας
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

        # 6. Εξαγωγή Περιγραφής Εμπορεύματος
        desc = line_clean
        if u_match:
            desc = desc.replace(u_match.group(0), '')
        for num in nums_to_remove:
            desc = desc.replace(num, '')

        desc = re.sub(r'[^a-zA-Zα-ωΑ-Ω0-9\s\.\-\/\(\)]', '', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()

        # Προσθήκη εγγραφής αν περιέχει έγκυρη περιγραφή
        if len(desc) > 2 and (synolo != '-' or timi_mon != '-'):
            records.append({
                'ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ': code,
                'ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ': desc,
                'ΜΟΝ. ΜΕΤΡ.': unit,
                'ΠΟΣΟΤ.': posot,
                'ΤΙΜΗ ΜΟΝΑΔΑΣ': timi_mon,
                'ΣΥΝΟΛΟ ΑΞΙΑΣ': synolo
            })

    # Μετατροπή σε DataFrame με τις 6 ακριβείς στήλες του 'timologia'
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

