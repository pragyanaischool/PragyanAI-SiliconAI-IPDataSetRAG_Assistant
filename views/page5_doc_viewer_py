import streamlit as st
import os
import fitz  # PyMuPDF
from langchain_groq import ChatGroq

def render():
    st.image("PragyanAI_Transperent.png")
    st.title("Document Viewer & Page-by-Page RAG Summarizer")
    st.markdown("Select an IP group and model, browse ingested specification documents, view content page-by-page or slide-by-slide, and run AI RAG summarization on specific pages.")

    # Check if IP databases or raw docs exist
    if "ip_raw_docs" not in st.session_state or not st.session_state.ip_raw_docs:
        st.warning("⚠️ No documents found. Please ingest specification sheets or files on **Page 1: IP Core & Knowledge Base Management** first.")
        return

    ip_groups = st.session_state.get("ip_groups", {})
    ip_raw_docs = st.session_state.ip_raw_docs
    ip_file_registry = st.session_state.get("ip_file_registry", {})

    available_ips = list(ip_raw_docs.keys())
    unique_groups = sorted(list(set(ip_groups.get(ip, "General") for ip in available_ips)))

    # Step 1: Select Group and IP Model
    st.markdown("---")
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        selected_group = st.selectbox("Select Protocol Group / Family", unique_groups, key="viewer_group_sel")
        ips_in_group = [ip for ip in available_ips if ip_groups.get(ip, "General") == selected_group]
    with col_sel2:
        selected_ip = st.selectbox("Select IP Model / Version", ips_in_group, key="viewer_ip_sel")

    # Step 2: Select Document from Registry
    registry = ip_file_registry.get(selected_ip, {})
    if not registry:
        st.info(f"💡 No registered files found under `{selected_ip}`.")
        return

    source_names = list(registry.keys())
    selected_source = st.selectbox("Select Document File to View", source_names, key="viewer_source_sel")

    file_meta = registry[selected_source]
    doc_type = file_meta.get("type", "Document")
    total_pages = file_meta.get("pages", 1)

    st.markdown(f"**Document Type:** `{doc_type}` | **Total Pages / Sections / Slides:** `{total_pages}`")

    # Filter raw docs for this specific IP and source
    source_docs = [
        d for d in ip_raw_docs.get(selected_ip, []) 
        if d.metadata.get("source") == selected_source
    ]

    if not source_docs:
        st.warning("⚠️ Could not locate text chunks for this document in raw memory.")
        return

    # Step 3: Page Navigation Slider / Number Input
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([3, 1])
    with col_nav1:
        page_num = st.slider("Navigate Page / Slide / Section", min_value=1, max_value=max(1, total_pages), value=1, key="doc_page_slider")
    with col_nav2:
        direct_page = st.number_input("Jump to Page", min_value=1, max_value=max(1, total_pages), value=page_num, key="doc_page_num_input")
        if direct_page != page_num:
            page_num = direct_page

    # Find the corresponding document chunk for the selected page
    current_chunk = next((d for d in source_docs if d.metadata.get("page", 1) == page_num), None)
    
    if not current_chunk and source_docs:
        # Fallback to index if exact page metadata isn't matched
        idx = min(page_num - 1, len(source_docs) - 1)
        current_chunk = source_docs[idx]

    # Step 4: Display Content Depending on Document Type
    st.markdown(f"###  Viewing: `{selected_source}` — [Page / Slide {page_num} of {total_pages}]")

    if doc_type == "PDF Datasheet" or doc_type == "Remote PDF Spec":
        st.info(" **PDF Page View Mode**")
        st.text_area("Page Text Content", value=current_chunk.page_content if current_chunk else "", height=350, key="pdf_text_view")
        
        # Optional: Render visual PDF page preview if local file exists
        local_pdf_path = os.path.join("temp_ip_data", selected_source)
        if os.path.exists(local_pdf_path):
            try:
                with fitz.open(local_pdf_path) as pdf_file:
                    if page_num <= len(pdf_file):
                        page_obj = pdf_file[page_num - 1]
                        pix = page_obj.get_pixmap(dpi=150)
                        img_path = f"temp_ip_data/page_{page_num}.png"
                        pix.save(img_path)
                        st.image(img_path, caption=f"Rendered View - Page {page_num}", use_container_width=True)
            except Exception:
                pass

    elif doc_type == "Presentation Slide":
        st.info(" **Presentation Slide View Mode**")
        st.markdown(f"#### Slide {page_num}")
        st.code(current_chunk.page_content if current_chunk else "", language="markdown")

    elif doc_type == "Excel Register Map":
        st.info(" **Excel Register Map View Mode**")
        st.markdown(current_chunk.page_content if current_chunk else "")

    elif doc_type == "HDL Code":
        st.info("⚡ **RTL Source Code View Mode**")
        st.code(current_chunk.page_content if current_chunk else "", language="verilog")

    else:
        st.info(" **General Document View Mode**")
        st.text_area("Content", value=current_chunk.page_content if current_chunk else "", height=350, key="gen_text_view")

    # Step 5: Page-by-Page RAG Summarizer
    st.markdown("---")
    st.subheader(" Page-by-Page AI RAG Summarizer & Technical Analysis")
    
    analysis_focus = st.selectbox(
        "Select Summarization Focus", 
        [
            "Comprehensive Technical Summary", 
            "Extract Register Definitions & Bitfields", 
            "Protocol Handshaking & State Machine Analysis", 
            "Timing, Constraints & Safety Rules"
        ],
        key="sum_focus_sel"
    )

    if st.button(" Summarize & Analyze Selected Page", type="primary", key="btn_summarize_page"):
        try:
            groq_api_key = st.secrets["GROQ_API_KEY"]
            model_name = st.secrets.get("MODEL_NAME", "llama-3.3-70b-versatile")
        except Exception:
            st.error("⚠️ `GROQ_API_KEY` or `MODEL_NAME` not found in `st.secrets`.")
            return

        llm = ChatGroq(model=model_name, temperature=0.1, groq_api_key=groq_api_key)

        page_text = current_chunk.page_content if current_chunk else "No content available."

        rag_summary_prompt = f"""You are a Principal Silicon Architect and Hardware Verification Expert. 
Analyze the following text extracted from **{selected_source}** (IP Model: `{selected_ip}`, Page/Slide: `{page_num}`).

### Analysis Focus:
{analysis_focus}

### Target Page Content:
{page_text}

### Instructions:
Provide a rigorous, engineering-grade breakdown of this specific page content, highlighting critical parameters, register offsets, signal names, or protocol rules.
"""

        with st.spinner(f"Running AI analysis on Page {page_num} using `{model_name}`..."):
            response = llm.invoke(rag_summary_prompt)
            st.markdown("###  Page AI Analysis & Summary Result")
            st.markdown(response.content)
