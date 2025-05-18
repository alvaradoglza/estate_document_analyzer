from __future__ import annotations

import textwrap
from pathlib import Path
from datetime import date, datetime

import streamlit as st
from pydantic import ValidationError

from estate_analyzer.utilities.llm_utils import analyze_document, EstateInfo

def fmt_date(raw):
    """Return YYYY-MM-DD for datetime objects, or the raw string / em-dash."""
    if isinstance(raw, (date, datetime)):
        return raw.strftime("%Y-%m-%d")
    return raw or "—"

st.set_page_config(page_title="Estate Document Analyzer", layout="centered")

st.title("Estate Document Analyzer")
st.markdown(
    textwrap.dedent(
        """
        Upload a **Will, Trust, Healthcare Directive, or Power of Attorney** PDF  
        and let an LLM pull out the key facts.
        """
    )
)

uploaded = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded:
    tmp_path = Path("tmp") / uploaded.name
    tmp_path.parent.mkdir(exist_ok=True)
    tmp_path.write_bytes(uploaded.getbuffer())

    st.info(f"Processing **{uploaded.name}** …")

    with st.spinner("Calling LLM, please wait …"):
        try:
            info: EstateInfo = analyze_document(tmp_path)
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

    pretty = {
        "Client Name":    info.client_name,
        "Client Address": info.client_address,
        "Document Date":  fmt_date(info.document_date),
        "Title":          info.title,
        "Pages":          info.n_pages,
    }

    with st.container():
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        for key, val in pretty.items():
            col1, col2 = st.columns([1, 3], gap="small")
            col1.markdown(f"**{key}**")
            col2.markdown(str(val))
        st.markdown("</div>", unsafe_allow_html=True)


else:
    st.caption("← Upload a PDF to get started.")
