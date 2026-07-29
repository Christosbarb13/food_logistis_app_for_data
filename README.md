# Automated Payroll & Invoice Processing System (OCR, PDF & AI)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source Python application engineered for automating payroll data visualization and processing unstructured document images/PDFs into structured tabular data schemas. The system combines Computer Vision (OpenCV), Optical Character Recognition (Tesseract OCR), Direct PDF Stream Parsing (PyMuPDF), and **Advanced AI Extraction (Google Gemini)** within a Streamlit Web Interface.

---

## Technical Overview & System Architecture

The application is structured into a modular decoupled architecture:

* **Presentation Layer (`app_webb.py`):** Interactive Streamlit web interface supporting multi-sheet Excel file analysis and multi-format document ingestion (JPG, PNG, PDF). Includes a sidebar configuration for dynamic AI extraction.
* **Processing & Extraction Engine (`dokimi_app.py`):** 
  * **Digital PDF Parsing:** Direct text stream extraction via PyMuPDF for digital documents.
  * **Scanned Image/PDF Pipeline:** Image preprocessing via OpenCV (Binarization, Grayscale conversion, Gaussian Blur noise reduction, and Otsu's Thresholding) feeding into Tesseract OCR (Greek language model `--psm 4`). Supports multi-page scanned PDF iteration.
  * **Legacy Regex Engine (ETL):** Dynamic table header/footer bounds detection using list slicing and regex pattern matching for strict-schema invoices.
  * **Modern AI Engine (LLM):** Integration with `google-genai` SDK using `gemini-flash-latest`. Prompts the LLM to structure noisy OCR data into strict JSON arrays based on user-defined prompt specifications, bypassing rigid regex rules.
* **Storage Layer:** Excel binary export (`.xlsx`) adhering to the standardized `timologia` 6-column schema.

---

## Data Schema (6-Column Target Layout)

All extracted data rows are normalized into the following target schema:

| Column Index | Field Name | Description |
| :--- | :--- | :--- |
| 1 | `ΚΩΔΙΚΟΣ ΕΙΔΟΥΣ` | 6-digit product code (or `-` if unassigned) |
| 2 | `ΠΕΡΙΓΡΑΦΗ ΕΜΠΟΡΕΥΜΑΤΟΣ` | Normalized product description string |
| 3 | `ΜΟΝ. ΜΕΤΡ.` | Unit of measure (`τεμά`, `Κιλά`, `Κιβώ`) |
| 4 | `ΠΟΣΟΤ.` | Quantities formatted to 2 decimal places |
| 5 | `ΤΙΜΗ ΜΟΝΑΔΑΣ` | Unit price formatted to 2 decimal places |
| 6 | `ΣΥΝΟΛΟ ΑΞΙΑΣ` | Total row value formatted to 2 decimal places |

---

## OCR Best Practices & Image Quality

For optimal OCR text extraction and table alignment, **document quality is critical**.

* **Recommended:** Use a flatbed scanner or a high-quality office printer. Scanners ensure uniform lighting, perfect flatness, and no perspective distortion, leading to nearly 100% extraction accuracy.
* **Mobile Scanning:** If scanning via a mobile device, **avoid taking raw photos** with the default camera app. Raw photos suffer from shadows, blur, and perspective distortion which severely degrades Tesseract OCR's accuracy. Instead, use dedicated scanning applications (e.g., **Microsoft Lens**, **Adobe Scan**, **CamScanner**) to automatically crop, deskew, and enhance contrast before saving as a PDF or high-quality image.
* **AI Fallback:** If OCR quality is poor due to bad scans, enabling the Gemini AI engine often resolves parsing errors by contextually understanding the distorted text.

---

## Repository Structure

```text
efarmogi_mistotrofodosia/
├── app_webb.py           # Streamlit Web Application Interface & AI Config
├── dokimi_app.py         # Ingestion, Computer Vision, ETL & LLM Engine
├── app.py                # Command-Line Excel Inspection Script
├── run_app.bat           # Windows Batch Launcher Script
├── requirements.txt      # Python Package Dependencies Manifest
├── LICENSE               # MIT Open Source License
├── .gitignore            # Git Ingestion Ignore Specification
└── README.md             # Technical Documentation
```

---

## Prerequisites & Local Deployment

### 1. External Dependencies
* **Python:** 3.9+
* **Tesseract OCR:** Install Tesseract OCR with Greek language support (`ell`).
  * Default Windows binary location: `C:\Program Files\Tesseract-OCR\tesseract.exe`
* **Google Gemini API Key:** Required only if using the AI Extraction feature. Get it free at [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Dependency Installation
Install required Python packages via pip:

```bash
pip install -r requirements.txt
```

---

## Execution Guide

### Method 1: Windows Batch File (Single Click)
Double-click the `run_app.bat` script to initialize the Python environment and spawn the Streamlit web server on `http://localhost:8501`.

### Method 2: Command Line Interface
Execute the Streamlit application module directly:

```bash
streamlit run app_webb.py
```

---

## Standalone Binary Compilation (.EXE)

To compile the application into a standalone Windows executable directory using PyInstaller:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Compile binary:
   ```bash
   pyinstaller --noconfirm --onedir --windowed --add-data "dokimi_app.py;." app_webb.py
   ```

---

## Security & Data Privacy Statement

When running with the **Legacy Regex Engine**, the entire processing pipeline executes strictly on local system hardware (`localhost`). No document streams or payroll data are transmitted externally.
When running with the **Gemini AI Engine**, OCR text is securely transmitted to Google's Generative AI API for JSON structuring. 

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
