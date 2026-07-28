# Automated Payroll & Invoice Processing System (OCR & PDF)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source Python application engineered for automating payroll data visualization and processing unstructured document images/PDFs into structured tabular data schemas. The system combines Computer Vision (OpenCV), Optical Character Recognition (Tesseract OCR), Direct PDF Stream Parsing (PyMuPDF), and Regular Expressions (Regex) within a Streamlit Web Interface.

---

## Technical Overview & System Architecture

The application is structured into a modular decoupled architecture:

* **Presentation Layer (`app_webb.py`):** Interactive Streamlit web interface supporting multi-sheet Excel file analysis and multi-format document ingestion (JPG, PNG, PDF).
* **Processing & Extraction Engine (`dokimi_app.py`):** 
  * **Digital PDF Parsing:** Direct text stream extraction via PyMuPDF for digital documents.
  * **Scanned Image/PDF Pipeline:** Image preprocessing via OpenCV (Binarization, Grayscale conversion, Gaussian Blur noise reduction, and Otsu's Thresholding) feeding into Tesseract OCR (Greek language model `--psm 6`).
  * **ETL & Dynamic Slicing:** Dynamic table header/footer bounds detection using list slicing (`lines[start_idx:end_idx]`) to isolate item rows, followed by regex pattern matching for product codes, descriptions, units of measure, and decimal-formatted pricing.
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

## Repository Structure

```text
efarmogi_mistotrofodosia/
├── app_webb.py           # Streamlit Web Application Interface
├── dokimi_app.py         # Document Ingestion, Computer Vision & ETL Engine
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

To run the document parsing engine independently via CLI:

```bash
python dokimi_app.py
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

The entire processing pipeline executes strictly on local system hardware (`localhost`). No document streams, images, or payroll data are transmitted to external third-party cloud services.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
