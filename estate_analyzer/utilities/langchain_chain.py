"""
estate_analyzer.utilities.langchain_chain

* Provide two strategies for document extraction:
    - Text-chain : use existing text layer
    - PDF-chain : upload the PDF to OpenAI and use visual input
* The caller receives a callable object that returns an EstateInfo regardless the strategy

Raises:
 - openai.OpenAIError
"""

from __future__ import annotations

from pathlib import Path
from textwrap import shorten
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from openai import OpenAI 

from estate_analyzer.utilities.llm_schema import EstateInfo


LLM_KWARGS = dict(
    model="gpt-4o-mini",
    temperature=0.0,
    max_tokens=512,
)

SYSTEM_MSG = (
    "You are a legal-document extraction engine. "
    "Return ONLY valid JSON matching the schema. No markdown."
)

def _text_chain() -> Any:
    """ 
    Build a LangChain runnable for PDFs with text layer
    
    Returns:
        Pipeline: PromptTemplate | llm | PydanticOutputParser
    """

    parser = PydanticOutputParser(pydantic_object=EstateInfo)

    user_template = (
        "Extract the following fields from the estate document text below:\n"
        "- clientName - clientAddress - documentDate - title - summary - n_pages\n\n"
        "Respond ONLY with JSON exactly like this example:\n"
        "{schema}\n\n"
        "----- BEGIN TEXT -----\n{document_text}\n----- END TEXT -----"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_MSG),
            ("user", user_template),
        ]
    ).partial(schema=EstateInfo.json_schema(indent=0))

    llm = ChatOpenAI(**LLM_KWARGS)

    return prompt | llm | parser

def _pdf_chain() -> Any:
    """
    Build a simple callable for scanned PDFs
    
    Returns:
        Callable: function that takes a PDF path and returns an EstateInfo object
    """
    parser = PydanticOutputParser(pydantic_object=EstateInfo)

    user_prompt = (
        "Extract the following fields from the estate document text below:\n"
        "- clientName - clientAddress - documentDate - title - summary - n_pages\n\n"
        "Respond ONLY with JSON exactly like this example:\n"
        "{schema}"
    ).format(schema=EstateInfo.json_schema(indent=0))

    def _invoke(inputs: Dict[str, Any]) -> EstateInfo:
        """
        Upload the PDF to OpenAI and call the LLM with the file_id and user prompt.

        Args:
            inputs: Dictionary containing the PDF path.
        
        Returns:
            EstateInfo: Pydantic validated dataclass with extracted fields
        """

        pdf_path: Path = inputs["pdf_path"]

        client = OpenAI()
        file_id = _upload_file(pdf_path)  # returns str

        messages = [
            {
                "role": "system",
                "content": SYSTEM_MSG,
            },
            {
                "role": "user",
                "content": [
                    {"type": "file", "file": {"file_id": file_id}},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=512,
            temperature=0.0,
        )

        raw_json = response.choices[0].message.content
        return parser.parse(raw_json)

    return _invoke

def _upload_file(path: Path) -> str:
    """
    Upload file path to OpenAI Files API
    
    Args:
        path
        
    Returns:
        the file_id returned by OpenAI
    """

    client = OpenAI()
    up = client.files.create(file=path.open("rb"), purpose="user_data")
    return up.id

def get_estate_chain(has_text: bool):
    """
    Decide which chain to use based on the PDF type
    
    Args:
        has_text: bool: True if the PDF has a text layer, False otherwise.
        
    Returns:
        Callable | Runnable: LangChain chain or callable function
    """

    return _text_chain() if has_text else _pdf_chain()