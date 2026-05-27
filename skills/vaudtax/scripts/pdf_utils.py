"""
Utilities for reading PDF and image attachments extracted from .vaudtax files.

Usage:
    from pdf_utils import read_pdf, extract_form21_totals, extract_postfinance_3a, identify_taxpayer
"""

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def read_pdf(path, lang="fra"):
    """Extract text from a PDF (text-based or scanned) or image attachment.

    Tries pdfplumber first for text-based PDFs; falls back to OCR via
    pytesseract/pdf2image for scanned PDFs. JPEG/PNG go straight to OCR.

    Args:
        path: path to a .pdf, .jpg, .jpeg, or .png file
        lang: tesseract language code (default "fra"; use "deu" for German-only docs)

    Returns:
        Extracted text as a string.
    """
    if path.lower().endswith((".jpg", ".jpeg", ".png")):
        return pytesseract.image_to_string(Image.open(path), lang=lang)
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    if text.strip():
        return text
    # Scanned PDF — fall back to OCR
    images = convert_from_path(path, dpi=200)
    return "\n".join(pytesseract.image_to_string(img, lang=lang) for img in images)


def extract_form21_totals(text):
    """Extract 3a contributions total and 3a rachats total from form 21 EDP text.

    The field letter for the total line varies between form editions:
    - 2025 edition: field q (contributions), field x (rachats)
    - 2011 edition: field r (contributions), field s (rachats)

    Rather than relying on the letter, this function identifies lines by their
    content: the total lines always contain "Säule 3a" (or "pilier 3a") and
    "Total", and the amount (if any) is the last token on the line.

    Returns:
        (contributions, rachats) — integers in CHF, or None if absent.
    """
    contributions = rachats = None
    for line in text.splitlines():
        s = line.strip()
        last = s.split()[-1].replace("'", "") if s else ""
        amount = int(last) if last.isdigit() else None
        lower = s.lower()
        if "total" in lower and ("säule 3a" in lower or "pilier 3a" in lower or "pilastro 3a" in lower):
            if "einkauf" in lower or "rachat" in lower or "riscatti" in lower:
                rachats = amount
            else:
                contributions = amount
    return contributions, rachats


def identify_taxpayer(text, ctb1, ctb2):
    """Determine which taxpayer a document belongs to by matching its content.

    Scores each taxpayer by how many identifiers (birthdate, last name, NAVS13)
    appear in the document text. Returns the one with the higher score.

    Args:
        text: extracted text from the document (via read_pdf)
        ctb1: dict with keys 'navs13' (formatted as 756.XXXX.XXXX.XX),
              'birthdate' (YYYY-MM-DD), 'last_name', 'first_name'
        ctb2: same structure, or None if no second taxpayer

    Returns:
        "CTB1", "CTB2", or None if not determinable (tie or no match).
    """
    if ctb2 is None:
        return "CTB1"

    def score(ctb):
        s = 0
        # Birthdate: convert YYYY-MM-DD → DD.MM.YYYY (Swiss format used in all forms)
        if ctb.get("birthdate"):
            y, m, d = ctb["birthdate"].split("-")
            if f"{d}.{m}.{y}" in text:
                s += 2
        # Last name (case-insensitive)
        if ctb.get("last_name") and ctb["last_name"].lower() in text.lower():
            s += 1
        # NAVS13: strip dots/spaces for comparison
        if ctb.get("navs13"):
            raw = ctb["navs13"].replace(".", "").replace(" ", "")
            if raw in text.replace(".", "").replace(" ", ""):
                s += 2
        return s

    s1, s2 = score(ctb1), score(ctb2)
    if s1 > s2:
        return "CTB1"
    if s2 > s1:
        return "CTB2"
    return None  # tie or no identifiers found


def extract_postfinance_3a(text):
    """Extract 3a contribution amount from a PostFinance 'Attestation fiscale' PDF.

    PostFinance issues its own format (not form 21 EDP). The amount appears on a
    line like: "Année: 2024 CHF 3'000.00"

    Returns:
        Amount in CHF as an integer, or None if not found.
    """
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("Année:") and "CHF" in s:
            last = s.split()[-1].replace("'", "")
            try:
                return int(float(last))
            except ValueError:
                return None
    return None
