"""
estate_analyzer.utilities.llm_utils
* If the PDF has text layer send that text to GPT-4o-mini.
* If not, send the pdf as a file to GPT-4o-mini.

Returned object is validated by Pydantic.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from textwrap import shorten
from typing import Annotated, Literal

import openai
from pydantic import BaseModel, Field, ValidationError

from estate_analyzer.utilities.pdf_utils import extract_text_from_pdf, PDFData

class EstateInfo(BaseModel):
    client_name: Annotated[str, Field(..., alias="clientName")]
    client_address: Annotated[str, Field(..., alias="clientAddress")]
    document_date: Annotated[str, Field(..., alias="documentDate")]
    title: str
    summary: str
    n_pages: int

    @staticmethod
    def json_schema() -> str:

        """ Return a compact JSON string for the prompt. """
        example = {
            "clientName": "Claudia Sheinbaum",
            "clientAddress": "Los Pinos, Mexico City",
            "documentDate": "2023-10-01",
            "title": "Last Will and Testament",
            "summary": "This is a summary of the document.",
            "n_pages": 5,
        }
        return json.dumps(example)
    
SYSTEM_MSG = (" You are a legal-document extraction engine. "
              " Return ONLY valid JSON matching the schema given."
              " Do not wrap it in markdown or prose. ")

USER_TEMPLATE