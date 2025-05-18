"""
estate_analyzer.utilities.llm_utils  

    analyze_document(pdf_path: str | Path) -> EstateInfo
"""

from __future__ import annotations
from pathlib import Path
from textwrap import shorten

from estate_analyzer.utilities.pdf_utils import extract_text
from estate_analyzer.utilities.langchain_chain import get_estate_chain
from estate_analyzer.utilities.llm_schema import EstateInfo


def analyze_document(pdf_path: str | Path) -> EstateInfo:
    pdf_path = Path(pdf_path).expanduser().resolve()
    pdf_data = extract_text(pdf_path)

    chain = get_estate_chain(has_text=pdf_data.has_text_layer)

    if pdf_data.has_text_layer:
        short_text = shorten(pdf_data.text, width=12000, placeholder=" […] ")
        raw = chain.invoke({"document_text": short_text})
    else:
        raw = chain({"pdf_path": pdf_path})

    # chain already returns a validated EstateInfo object
    info: EstateInfo = raw.copy(update={"n_pages": pdf_data.n_pages or raw.n_pages})
    return info
