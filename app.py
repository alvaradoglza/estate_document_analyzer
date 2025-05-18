from __future__ import annotations

import json
from pathlib import Path
import textwrap

import streamlit as st
from pydantic import ValidationError

from estate_analyzer.utilities.llm_utils import analyze_document, EstateInfo

st.set_page_config(
    page_title="Estate Document Analyzer",
    layout="centered",
)

st.title("Estate Document Analyzer")
st.markdown(
    textwrap.dedent(
        """
        Upload a **Will, Trust, Healthcare Directive, or Power of Attorney** PDF  
        and let an LLM pull out the key facts.
        """
    )
)

with st.sidebar:
    st.header("Settings")
    use_local = st.checkbox(
        "Use local model (Llama 3 via Ollama)",
        value=False,
        help="If unchecked, uses OpenAI GPT-4o-mini.",
    )

uploaded = st.file_uploader(
    "Choose a PDF file", type=["pdf"], accept_multiple_files=False
)

if uploaded:
    # Write the uploaded file to a temp path (Streamlit gives a file-like obj)
    temp_path = Path("tmp") / uploaded.name
    temp_path.parent.mkdir(exist_ok=True)
    with open(temp_path, "wb") as tmp:
        tmp.write(uploaded.getbuffer())

    st.info(f"Processing **{uploaded.name}** …")

    with st.spinner("Calling LLM, please wait …"):
        try:
            info: EstateInfo = analyze_document(temp_path)
        except ValidationError as ve:
            st.error("Model returned invalid JSON. See logs.")
            st.exception(ve)
            st.stop()
        except Exception as exc:
            st.error("Failed to analyze document.")
            st.exception(exc)
            st.stop()

    st.success("Extraction complete!")
    st.subheader("Summary")
    st.write(info.summary)

    st.subheader("Details")
    st.json(info.model_dump(by_alias=True, mode="python", exclude_none=True))

    st.markdown("---")
    st.caption(
        f"Pages: {info.n_pages}  •  Source chain: "
        f"{'Text→LLM' if info.summary else 'PDF→LLM'}"
    )
else:
    st.caption("← Upload a PDF to get started.")
