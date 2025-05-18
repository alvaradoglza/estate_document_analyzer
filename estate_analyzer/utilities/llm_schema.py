"""
estate_analyzer.utilities.llm_schema

* Defines the Pydantic model for the structured information format

"""

from __future__ import annotations
import json
from pydantic import BaseModel, Field, ConfigDict


class EstateInfo(BaseModel):
    """ Schema for extracted estate information. """
    model_config = ConfigDict(populate_by_name=True)

    client_name: str = Field(..., alias="clientName")
    client_address: str = Field(..., alias="clientAddress")
    document_date: str = Field(..., alias="documentDate")
    title: str
    summary: str
    n_pages: int

    @classmethod
    def json_schema(cls, **kwargs):
        """ 
        Return the JSON schema for the Pydantic model. 

        Args:
            **kwargs: Additional arguments to pass to json.dumps.

        Returns:
            Exammple JSON schema for LLM input.

        """
        example = {
            "clientName": "Claudia Sheinbaum",
            "clientAddress": "Los Pinos 123, Mexico City, Mexico",
            "documentDate": "2025-05-17",
            "title": "Last Will and Testament",
            "summary": "One-paragraph summary…",
            "n_pages": 12,
        }
        return json.dumps(example, **kwargs)
    
