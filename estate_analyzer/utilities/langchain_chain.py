"""
estate_analyzer.utilities.langchain_chain


A LangChain Runnable for estate-document
information extraction.


* If `has_text` is True then chain does {"text": str}
* If `has_text` is False then chain does {"pdf_path": Path}

The chain:

    PromptTemplate goes to ChatOpenAI then PydanticOutputParser
"""

from __future__ import annotations

from pathlib import Path
from textwrap import shorten
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
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
    """Return a chain that takes plain text."""
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
    parser = PydanticOutputParser(pydantic_object=EstateInfo)

    user_prompt = (
        "Extract clientName, clientAddress, documentDate, title, summary, n_pages "
        "from the attached PDF. Respond ONLY with JSON exactly like this example:\n"
        "{schema}"
    ).format(schema=EstateInfo.json_schema(indent=0))

    def _invoke(inputs: Dict[str, Any]) -> EstateInfo:
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
    """Upload the PDF once, return its file_id."""
    client = OpenAI()
    up = client.files.create(file=path.open("rb"), purpose="user_data")
    return up.id

def get_estate_chain(has_text: bool):
    return _text_chain() if has_text else _pdf_chain()