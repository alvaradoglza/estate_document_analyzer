"""
estate_analyzer.utilities.pdf_utils  

* Try to pull text with PyMuPDF.
* If the PDF has no text layer, record that fact for later use of OpenAI visual input
* If the PDF has a text layer, use PyMuPDF to extract text.

Raises:
 - ExtractionError: cannot open or read the PDF
 - FileNotFoundError: PDF file not found
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import fitz

class PDFData(NamedTuple):
    """ Structured return type from func: extract_text().

    Attributes:
        text: str | None: Extracted text from the PDF, or None if no text layer.
        n_pages: int: Number of pages in the PDF.
        has_text_layer: bool: True if the PDF has a text layer, False otherwise.
    """

    text: str | None
    n_pages: int
    has_text_layer: bool

class ExtractionError(RuntimeError):
    """ Raised when PyMuPDF cannot open or read the PDF file. """
    pass

def extract_text(pdf_path: str | Path) -> PDFData:
    """
    Extract test from a PDF file using PyMuPDF, or signal that the PDF has no text layer.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        PDFData: tuple: (extracted text, number of pages, and whether the PDF has a text layer)

    Raises:
        ExtractionError: If the PDF cannot be opened or read.
    """

    pdf_path = Path(pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    try:
        with fitz.open(pdf_path) as doc:
            pages = [page.get_text() for page in doc]
            combined = "\n\n".join(pages).strip()
            return PDFData(
                text=combined if combined else None,
                n_pages=len(doc),
                has_text_layer=bool(combined),
            )
    except Exception as exc:  
        raise ExtractionError(f"PyMuPDF failed: {exc}") from exc
