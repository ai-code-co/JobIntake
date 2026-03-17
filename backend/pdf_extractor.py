import logging
import os

import pdfplumber


DEFAULT_X_TOLERANCE = 1
DEFAULT_Y_TOLERANCE = 1


# Some PDFs have malformed font metadata; pdfminer logs noisy warnings for them.
# Parsing still succeeds in most cases, so keep logs clean by default.
if os.getenv("PDF_SUPPRESS_FONT_WARNINGS", "1").strip().lower() in ("1", "true", "yes", "on"):
    logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)


def _extract_page_text(page) -> str:
    text = page.extract_text(
        x_tolerance=DEFAULT_X_TOLERANCE,
        y_tolerance=DEFAULT_Y_TOLERANCE,
    )
    if text and text.strip():
        return text

    words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
    if words:
        return " ".join(word.get("text", "") for word in words if word.get("text"))

    return ""


def extract_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = _extract_page_text(page)
            if page_text:
                pages.append(page_text)

    return "\n".join(pages)
