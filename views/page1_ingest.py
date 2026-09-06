import streamlit as st
import os
import requests
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd
from bs4 import BeautifulSoup
import arxiv
import wikipedia

from langchain_core.documents import Document
from utils.vector_store import initialize_vector_persistence, rebuild_and_retain_vector_store
from utils.database import (
    init_db, 
    db_add_ip, 
    db_add_document, 
    db_remove_document, 
    db_get_all_groups_and_ips, 
    db_get_file_registry,
    db_get_document_counts
)

def download_pdf_from_url(url: str, save_path: str) -> bool:
    """Downloads a public PDF document directly from a web URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return True
        st.error(f"Download returned status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error downloading PDF from URL: {e}")
    return False

def scrape_web_page(url: str) -> str:
    """Extracts visible text cleanly from a target website URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        st.error(f"Error scraping web link: {e}")
        return ""

def render():
    st.image("PragyanAI_Transperent.png")
    st.title("IP Core & Knowledge Base Management (SQL + FAISS CPU)")
    st.markdown("Organize semiconductor IPs stored persistently in SQLite database, manage added documents, ingest multi-source data into **FAISS CPU Vector Store**, and retain information across sessions.")

    # Initialize SQLite and Vector Persistence Structures
    init_db()
    initialize_vector_persistence()

    # Sync SQLite groups into session state
    st.session_state.ip_groups = db_get_all_groups_and_ips()
    existing_groups = sorted(list(set(st.session_state.ip_groups.values())))

    # ==========================================
    # SECTION 1: SELECT GROUP & MODEL CONTAINER
    # ==========================================
    st.subheader("1. Select Existing Group / Protocol Family or Create New")
    
    with st.form("ip_registration_form"):
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            group_action_options = ["Select Existing Group"] + existing_groups + ["+ Create New Group"]
            selected_group_action = st.selectbox("Protocol Group Management", group_action_options)
            
            group_name_input = ""
            if selected_group_action == "+ Create New Group":
                group_name_input = st.text_input("Enter New Group / Protocol Family Name", placeholder="e.g., PCIe, AMBA, SPI, RISCV")
            elif selected_group_action != "Select Existing Group":
                group_name_input = selected_group_action
            else:
                group_name_input = st.text_input("IP Group / Protocol Family", placeholder="e.g., PCIe, AMBA, SPI, RISCV")

        with col_g2:
            ip_name_input = st.text_input(
                "IP Model / Version Identifier", 
                placeholder="e.g., PCIe_Gen2, AXI4_Interconnect"
            )
            
        submitted = st.form_submit_button("Register / Set Active IP Container")
        
        if submitted and ip_name_input.strip() and group_name_input.strip():
            clean_ip_name = ip_name_input.strip().replace(" ", "_")
            clean_group_name = group_name_input.strip().replace(" ", "_")
            
            st.session_state.current_ip = clean_ip_name
            db_add_ip(clean_group_name, clean_ip_name)
            st.session_state.ip_groups = db_get_all_groups_and_ips()
            
            if clean_ip_name not in st.session_state.ip_raw_docs:
                st.session_state.ip_raw_docs[clean_ip_name] = []
                
            st.success(f"Active IP configured under Group **[{clean_group_name}]**: **{clean_ip_name}** (Persisted in SQLite)")

    if "current_ip" not in st.session_state:
        st.info("👈 Please select or define a Group and IP Model Identifier above to begin managing documents.")
        return

    active_ip = st.session_state.current_ip
    active_group = st.session_state.ip_groups.get(active_ip, "General")
    st.markdown(f"### Managing Knowledge Base for: `{active_ip}` (Family Group: *{active_group}*)")

    # Fetch document registry and file counts from SQLite backend
    registry = db_get_file_registry(active_ip)
    doc_counts = db_get_document_counts()
    total_files_for_ip = doc_counts.get(active_ip, 0)

    # ==========================================
    # SECTION 2: VIEW ADDED DOCUMENTS & DETAILS
    # ==========================================
    st.markdown("---")
    st.subheader(" Document Database & Stored Details (SQLite Backed)")
    
    has_vector_store = active_ip in st.session_state.ip_databases
    if has_vector_store:
        st.success(f"✅ FAISS CPU Vector Store active with `{len(st.session_state.ip_raw_docs.get(active_ip, []))}` embedded chunks.")
    else:
        st.warning("⚠️ FAISS vector store memory is empty. If files are listed in SQLite below, re-index or add them to rebuild vectors.")

    if registry:
        st.write(f"Total active documents/sources indexed under Group **[{active_group}]** / IP **`{active_ip}`**: **{total_files_for_ip}** file(s)")
        
        for source_name, meta in list(registry.items()):
            with st.expander(f" [{meta['type']}] {source_name} — ({meta['pages']} pages/segments)"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**IP Family Group:** `{active_group}`")
                    st.write(f"**Document Type:** `{meta['type']}`")
                with col_b:
                    st.write(f"**Total Pages / Sections:** `{meta['pages']}`")
                    st.write(f"**Source Identifier:** `{source_name}`")
                
                st.markdown("**Stored Metadata & Brief Overview (Retained in SQLite):**")
                st.info(meta['brief'])

                # Option to remove specific document from SQLite and FAISS
                if st.button(f" Remove Document: {source_name}", key=f"del_{active_ip}_{source_name}"):
                    if active_ip in st.session_state.ip_raw_docs:
                        st.session_state.ip_raw_docs[active_ip] = [
                            doc for doc in st.session_state.ip_raw_docs[active_ip] 
                            if doc.metadata.get("source") != source_name
                        ]
                    db_remove_document(active_ip, source_name)
                    rebuild_and_retain_vector_store(active_ip)
                    st.success(f"Successfully removed '{source_name}' from SQLite and updated FAISS CPU vector store!")
                    st.rerun()
    else:
        st.info("No documents added to this IP yet. Use the ingestion tabs below to add files.")

    # ==========================================
    # SECTION 3: ADD NEW FILES & SOURCES
    # ==========================================
    st.markdown("---")
    st.subheader(" Add New Files & Knowledge Sources (Saves to SQL & FAISS CPU)")

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. Local Files (PDF / DOCX / PPT / XLSX / RTL)",
        "2. Direct PDF URL Link",
        "3. Web Links & Wikipedia",
        "4. ArXiv Research Papers"
    ])

    new_docs = []
    os.makedirs("temp_ip_data", exist_ok=True)

    # TAB 1: LOCAL FILES
    with tab1:
        st.markdown("##### Upload Specification Sheets, Register Maps, or Verilog/VHDL Source Files")
        uploaded_files = st.file_uploader(
            "Supported formats: PDF, DOCX, PPTX, XLSX, V, SV, VHDL, TXT",
            type=["pdf", "docx", "pptx", "xlsx", "v", "sv", "vhdl", "txt"],
            accept_multiple_files=True,
            key="local_uploader_new"
        )
        if st.button("Process & Save to SQLite & FAISS", key="btn_local_process"):
            if uploaded_files:
                with st.spinner("Parsing documents, updating SQLite, and generating FAISS CPU embeddings..."):
                    if active_ip not in st.session_state.ip_raw_docs:
                        st.session_state.ip_raw_docs[active_ip] = []

                    for file in uploaded_files:
                        # Check if already stored in SQLite database to prevent duplicate processing
                        if file.name in registry:
                            st.info(f"ℹ️ '{file.name}' is already registered in SQLite for `{active_ip}`. Skipping re-processing.")
                            continue

                        file_path = os.path.join("temp_ip_data", file.name)
                        with open(file_path, "wb") as f:
                            f.write(file.getbuffer())

                        file_page_count = 0
                        full_extracted_text = ""

                        # PDF Processing
                        if file.name.lower().endswith(".pdf"):
                            with fitz.open(file_path) as doc:
                                file_page_count = len(doc)
                                for page_num, page in enumerate(doc):
                                    text = page.get_text()
                                    if text.strip():
                                        full_extracted_text += text + "\n"
                                        new_docs.append(Document(
                                            page_content=text,
                                            metadata={
                                                "source": file.name,
                                                "page": page_num + 1,
                                                "ip": active_ip,
                                                "group": active_group,
                                                "type": "PDF Datasheet"
                                            }
                                        ))
                            doc_type = "PDF Datasheet"
                        # DOCX Processing
                        elif file.name.lower().endswith(".docx"):
                            doc_obj = DocxDocument(file_path)
                            full_extracted_text = "\n".join([p.text for p in doc_obj.paragraphs if p.text.strip()])
                            file_page_count = 1
                            doc_type = "Word Document"
                            new_docs.append(Document(
                                page_content=full_extracted_text,
                                metadata={"source": file.name, "page": 1, "ip": active_ip, "group": active_group, "type": doc_type}
                            ))
                        # PPTX Processing
                        elif file.name.lower().endswith(".pptx"):
                            prs = Presentation(file_path)
                            file_page_count = len(prs.slides)
                            doc_type = "Presentation Slide"
                            for slide_idx, slide in enumerate(prs.slides):
                                slide_text = ""
                                for shape in slide.shapes:
                                    if shape.has_text_frame:
                                        for p in shape.text_frame.paragraphs:
                                            slide_text += p.text + "\n"
                                if slide_text.strip():
                                    full_extracted_text += slide_text + "\n"
                                    new_docs.append(Document(
                                        page_content=slide_text,
                                        metadata={"source": file.name, "page": slide_idx + 1, "ip": active_ip, "group": active_group, "type": doc_type}
                                    ))
                        # Excel Processing
                        elif file.name.lower().endswith(".xlsx"):
                            xls = pd.ExcelFile(file_path)
                            file_page_count = len(xls.sheet_names)
                            doc_type = "Excel Register Map"
                            for sheet in xls.sheet_names:
                                df = pd.read_excel(file_path, sheet_name=sheet)
                                sheet_md = f"Sheet: {sheet}\n\n" + df.to_markdown(index=False)
                                full_extracted_text += sheet_md + "\n"
                                new_docs.append(Document(
                                    page_content=sheet_md,
                                    metadata={"source": f"{file.name} [{sheet}]", "page": 1, "ip": active_ip, "group": active_group, "type": doc_type}
                                ))
                        # Verilog / VHDL Code Processing
                        else:
                            doc_type = "HDL Code"
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                full_extracted_text = f.read()
                            file_page_count = 1
                            new_docs.append(Document(
                                page_content=full_extracted_text,
                                metadata={"source": file.name, "page": 1, "ip": active_ip, "group": active_group, "type": doc_type}
                            ))

                        brief_summary = full_extracted_text[:400].replace("\n", " ") + "..." if len(full_extracted_text) > 400 else full_extracted_text
                        brief_text = f"Group: {active_group}. Excerpt: {brief_summary}"
                        
                        # Save document record persistently to SQLite database
                        db_add_document(active_ip, file.name, doc_type, file_page_count, brief_text)

                    if new_docs:
                        st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                        rebuild_and_retain_vector_store(active_ip)
                        st.success(f"Successfully processed local files, saved metadata to SQLite, and indexed in FAISS CPU for `{active_ip}`!")
                        st.rerun()
                    else:
                        st.info("No new files were processed (all uploaded files were already registered in SQLite).")
            else:
                st.warning("Please choose one or more files first.")

    # TAB 2: PDF URL DOWNLOAD
    with tab2:
        st.markdown("##### Download and Ingest Remote Datasheet / Manual via Direct URL")
        pdf_url = st.text_input("Direct PDF Web Link", placeholder="https://example.com/datasheets/axi_stream_spec.pdf", key="url_input_new")
        if st.button("Download & Save to SQLite", key="btn_url_download_new"):
            if pdf_url.strip():
                if pdf_url in registry:
                    st.info(f"ℹ️ URL '{pdf_url}' is already registered in SQLite.")
                else:
                    with st.spinner("Downloading, parsing, saving to SQLite, and embedding vectors..."):
                        raw_filename = pdf_url.split("/")[-1].split("?")[0]
                        if not raw_filename.lower().endswith(".pdf"):
                            raw_filename = "downloaded_spec.pdf"
                        target_path = os.path.join("temp_ip_data", raw_filename)

                        if download_pdf_from_url(pdf_url.strip(), target_path):
                            if active_ip not in st.session_state.ip_raw_docs:
                                st.session_state.ip_raw_docs[active_ip] = []

                            full_text = ""
                            with fitz.open(target_path) as doc:
                                page_count = len(doc)
                                for page_num, page in enumerate(doc):
                                    text = page.get_text()
                                    if text.strip():
                                        full_text += text + "\n"
                                        new_docs.append(Document(
                                            page_content=text,
                                            metadata={"source": pdf_url, "page": page_num + 1, "ip": active_ip, "group": active_group, "type": "Remote PDF Spec"}
                                        ))
                            
                            brief = full_text[:400].replace("\n", " ") + "..."
                            brief_text = f"Remote PDF document. Excerpt: {brief}"
                            
                            db_add_document(active_ip, pdf_url, "Remote PDF Spec", page_count, brief_text)
                            st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                            rebuild_and_retain_vector_store(active_ip)
                            st.success("Remote PDF saved to SQLite and indexed in FAISS CPU successfully!")
                            st.rerun()
            else:
                st.warning("Please provide a valid PDF link.")

    # TAB 3: WEB & WIKIPEDIA
    with tab3:
        st.markdown("##### Ingest Online Documentation, Specs, or Wikipedia Protocols")
        web_url = st.text_input("Vendor Documentation URL", placeholder="https://en.wikipedia.org/wiki/PCI_Express", key="web_input_new")
        wiki_query = st.text_input("Wikipedia Topic Search", placeholder="e.g., PCI Express", key="wiki_input_new")
        
        if st.button("Ingest & Save to SQLite", key="btn_web_ingest_new"):
            with st.spinner("Extracting content and saving to database..."):
                if active_ip not in st.session_state.ip_raw_docs:
                    st.session_state.ip_raw_docs[active_ip] = []

                if web_url.strip() and web_url.strip() not in registry:
                    page_text = scrape_web_page(web_url.strip())
                    if page_text:
                        new_docs.append(Document(
                            page_content=page_text[:8000],
                            metadata={"source": web_url.strip(), "page": 1, "ip": active_ip, "group": active_group, "type": "Web Article"}
                        ))
                        db_add_document(active_ip, web_url.strip(), "Web Article", 1, f"Web article. Excerpt: {page_text[:300]}...")
                
                wiki_key = f"Wikipedia: {wiki_query.strip()}"
                if wiki_query.strip() and wiki_key not in registry:
                    try:
                        wiki_content = wikipedia.summary(wiki_query.strip(), sentences=12)
                        new_docs.append(Document(
                            page_content=wiki_content,
                            metadata={"source": wiki_key, "page": 1, "ip": active_ip, "group": active_group, "type": "Wikipedia Entry"}
                        ))
                        db_add_document(active_ip, wiki_key, "Wikipedia Entry", 1, f"Wikipedia overview. Excerpt: {wiki_content[:300]}...")
                    except Exception as e:
                        st.error(f"Wikipedia lookup error: {e}")

                if new_docs:
                    st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                    rebuild_and_retain_vector_store(active_ip)
                    st.success("Web & Wikipedia content saved to SQLite and indexed in FAISS CPU!")
                    st.rerun()
                else:
                    st.info("No new web or Wikipedia content was added (sources already exist in registry).")

    # TAB 4: ARXIV RESEARCH PAPERS
    with tab4:
        st.markdown("##### Query and Ingest ArXiv Hardware/ASIC Research Papers")
        arxiv_query = st.text_input("Research Topic", placeholder="e.g., PCI Express protocol verification", key="arxiv_input_new")
        max_papers = st.slider("Number of Papers", min_value=1, max_value=5, value=2, key="arxiv_slider_new")

        if st.button("Fetch & Save Papers to SQLite", key="btn_arxiv_fetch_new"):
            if arxiv_query.strip():
                with st.spinner("Querying ArXiv API and saving to SQLite..."):
                    if active_ip not in st.session_state.ip_raw_docs:
                        st.session_state.ip_raw_docs[active_ip] = []

                    client = arxiv.Search(query=arxiv_query.strip(), max_results=max_papers)
                    for paper in client.results():
                        source_label = f"ArXiv: {paper.title}"
                        if source_label in registry:
                            continue
                        body = f"Title: {paper.title}\nAuthors: {', '.join([a.name for a in paper.authors])}\n\nAbstract:\n{paper.summary}"
                        new_docs.append(Document(
                            page_content=body,
                            metadata={"source": source_label, "page": 1, "ip": active_ip, "group": active_group, "type": "ArXiv Research Paper"}
                        ))
                        db_add_document(active_ip, source_label, "ArXiv Research Paper", 1, f"Paper by {', '.join([a.name for a in paper.authors])}. Abstract: {paper.summary[:300]}...")
                    
                    if new_docs:
                        st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                        rebuild_and_retain_vector_store(active_ip)
                        st.success(f"Saved new papers to SQLite and indexed in FAISS CPU!")
                        st.rerun()
                    else:
                        st.info("All retrieved papers are already registered in SQLite.")
            else:
                st.warning("Please provide a research query.")
                
