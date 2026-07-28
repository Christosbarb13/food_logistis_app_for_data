# 📊 Εφαρμογή Μισθοτροφοδοσίας & OCR Αναγνώρισης Τιμολογίων (Open Source)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Μια ανοιχτού κώδικα (**Open Source**) εφαρμογή σε **Python** για την επεξεργασία αρχείων μισθοδοσίας Excel, καθώς και την αυτοματοποιημένη αναγνώριση κειμένου/δεδομένων από εικόνες παραστατικών και **τιμολογίων** με τη χρήση **Computer Vision (OpenCV)** και **OCR (Tesseract)**.

---

## 🌟 Κύρια Χαρακτηριστικά (Features)

* **🖥️ Web Interface (Streamlit Dashboard):** Διαδραστικό περιβάλλον χρήστη (`app_webb.py`) με 2 κύριες καρτέλες:
  * **📁 Επεξεργασία Excel:** Φόρτωση, επιλογή φύλλων (sheets) και προβολή δεδομένων μισθοδοσίας σε πραγματικό χρόνο.
  * **📷 Αναγνώριση Παραστατικών (timologia):** Ανέβασμα εικόνας (JPG/PNG), αυτόματος καθαρισμός, αναγνώριση κειμένου και εξαγωγή σε δομημένο πίνακα 6 στηλών.
* **🖼️ Επεξεργασία Εικόνας (OpenCV Pipeline):** 
  * Μετατροπή σε Grayscale.
  * Διπλασιασμός ανάλυσης (2x Resize) για βελτίωση αναγνωρισιμότητας μικρών γραμμάτων.
  * Αφαίρεση θορύβου με Gaussian Blur.
  * Διφασική Κατωφλιοποίηση (Otsu Thresholding) για απόλυτο διαχωρισμό κειμένου και φόντου.
* **🧠 Έξυπνη Εξαγωγή Δεδομένων (ETL Engine):**
  * Φιλτράρισμα θορύβου επικεφαλίδων (Header Noise Suppression).
  * Αναγνώριση 6ψήφιων Κωδικών Είδους με Regular Expressions (Regex).
  * Αυτόματη αναγνώριση Μονάδων Μέτρησης (`τεμά`, `Κιλά`, `Κιβώ`).
  * Μορφοποίηση δεκαδικών αριθμών σε αυστηρή μορφή 2 δεκαδικών ψηφίων (π.χ. `12.03`).
* **📥 Εξαγωγή σε Excel:** Δυνατότητα λήψης των αναγνωρισμένων δεδομένων απευθείας σε αρχείο `.xlsx` στη μορφή `timologia`.

---

## 📋 Δομή 6 Στηλών (Schema 'timologia')

Τα εξαγόμενα δεδομένα από κάθε τιμολόγιο μορφοποιούνται στους παρακάτω 6 άξονες:
1. `ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ`
2. `ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ`
3. `ΜΟΝ. ΜΕΤΡ.`
4. `ΠΟΣΟΤ.`
5. `ΤΙΜΗ ΜΟΝΑΔΑΣ`
6. `ΣΥΝΟΛΟ ΑΞΙΑΣ`

---

## 📁 Δομή Έργου (Project Structure)

```text
efarmogi_mistotrofodosia/
├── app_webb.py           # Η κύρια Web Εφαρμογή σε Streamlit (Frontend & UI)
├── dokimi_app.py         # Ο "Κινητήρας" OCR & Computer Vision (Backend Engine)
├── app.py                # Δοκιμαστικό CLI script για ανάγνωση Excel
├── run_app.bat           # 1-Click Εκτελέσιμο Αρχείο Εκκίνησης για Windows
├── dokimi.jpg            # Δείγμα παραστατικού για δοκιμές OCR
├── requirements.txt      # Απαιτούμενες βιβλιοθήκες Python
├── LICENSE               # Άδεια χρήσης Open Source (MIT License)
├── .gitignore            # Αρχεία που εξαιρούνται από το Git
└── README.md             # Τεκμηρίωση έργου
```

---

## 🛠️ Προαπαιτούμενα & Εγκατάσταση

### 1. Εγκατάσταση Tesseract OCR Engine
Για τη λειτουργία του OCR απαιτείται η εγκατάσταση του Tesseract στο σύστημά σας:
* **Windows:** Κατεβάστε τον installer από το [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) και βεβαιωθείτε ότι περιλαμβάνεται το ελληνικό πακέτο γλωσσών (`ell`).
* Προεπιλεγμένη διαδρομή Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 2. Εγκατάσταση Εξαρτήσεων Python
Εκτελέστε στο τερματικό:
```bash
pip install -r requirements.txt
```

---

## 💻 Πώς να Εκτελέσετε την Εφαρμογή Τοπικά

### ⚡ Τρόπος 1: 1-Click Εκκίνηση (Windows Batch File)
Διπλό κλικ στο αρχείο **`run_app.bat`** για να ξεκινήσει αυτόματα η εφαρμογή στον browser σας!

### 💻 Τρόπος 2: Μέσω Τερματικού
* **Web Εφαρμογή (Streamlit):**
  ```bash
  streamlit run app_webb.py
  ```
* **OCR Engine (CLI / Testing):**
  ```bash
  python dokimi_app.py
  ```

---

## 📦 Δημιουργία Αυτόνομου Εκτελέσιμου Αρχείου (.EXE)

Αν θέλετε να δημιουργήσετε ένα αυτόνομο αρχείο `.exe` με το PyInstaller:

1. Εγκαταστήστε το PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Δημιουργήστε το εκτελέσιμο:
   ```bash
   pyinstaller --noconfirm --onedir --windowed --add-data "dokimi_app.py;." app_webb.py
   ```

---

## 🔓 Προσαρμογή & Open Source

Το έργο διατίθεται υπό την άδεια **MIT License**. Οποιοσδήποτε μπορεί να κάνει `fork` ή `clone` το αποθετήριο, να τροποποιήσει τους κανόνες Regex στο `dokimi_app.py` ή να προσαρμόσει τις στήλες του πίνακα στις δικές του εταιρικές ανάγκες.

---

## 🚀 Οδηγίες Ανεβάσματος στο GitHub

```bash
git init
git add .
git commit -m "Initial commit: Open Source Payroll & Invoice OCR App"
git branch -M main
git remote add origin https://github.com/USERNAME/YOUR-REPO-NAME.git
git push -u origin main
```
