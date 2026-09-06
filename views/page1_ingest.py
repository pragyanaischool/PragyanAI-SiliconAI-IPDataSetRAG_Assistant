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
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

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

def rebuild_vector_store(ip_name: str):
    """Rebuilds the FAISS vector store for a given IP from its stored raw document list."""
    if ip_name in st.session_state.ip_raw_docs and st.session_state.ip_raw_docs[ip_name]:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        st.session_state.ip_databases[ip_name] = FAISS.from_documents(
            st.session_state.ip_raw_docs[ip_name], embeddings
        )
    else:
        if ip_name in st.session_state.ip_databases:
            del st.session_state.ip_databases[ip_name]

def render():
    st.image("PragyanAI_Transperent.png")
    st.title(" Page 1: IP Core & Knowledge Base Management")
    st.markdown("Register semiconductor IP cores, manage added documents, view brief metrics (page counts, key topics), add new sources, or remove obsolete files.")

    # Global State Initializations for Raw Document Persistence & Management
    if "ip_databases" not in st.session_state:
        st.session_state.ip_databases = {}
    if "ip_raw_docs" not in st.session_state:
        st.session_state.ip_raw_docs = {}  # {ip_name: [Document, ...]}
    if "ip_file_registry" not in st.session_state:
        st.session_state.ip_file_registry = {}  # {ip_name: {source_name: {type, pages, sample_text}}}

    # 1. IP Model Registration / Selection
    st.subheader("1. Select or Register Semiconductor IP Model")
    with st.form("ip_registration_form"):
        ip_name_input = st.text_input(
            "IP Model Identifier", 
            placeholder="e.g., AMBA_AXI4_Interconnect, RISCV_RV32I, SPI_Engine"
        )
        submitted = st.form_submit_button("Register / Set Active IP Container")
        
        if submitted and ip_name_input.strip():
            clean_ip_name = ip_name_input.strip().replace(" ", "_")
            st.session_state.current_ip = clean_ip_name
            if clean_ip_name not in st.session_state.ip_raw_docs:
                st.session_state.ip_raw_docs[clean_ip_name] = []
            if clean_ip_name not in st.session_state.ip_file_registry:
                st.session_state.ip_file_registry[clean_ip_name] = {}
            st.success(f"Active IP context configured: **{clean_ip_name}**")

    if "current_ip" not in st.session_state:
        st.info("👈 Please define and register an IP Model name above to begin managing documents.")
        return

    active_ip = st.session_state.current_ip
    st.markdown(f"###  Managing Knowledge Base for: `{active_ip}`")

    # ==========================================
    # SECTION 2: VIEW ADDED DOCUMENTS & BRIEFS
    # ==========================================
    st.markdown("---")
    st.subheader(" Document Database & Brief Overview")
    
    registry = st.session_state.ip_file_registry.get(active_ip, {})
    
    if registry:
        st.write(f"Total active documents/sources indexed: **{len(registry)}**")
        
        for source_name, meta in list(registry.items()):
            with st.expander(f" [{meta['type']}] {source_name} — ({meta['pages']} pages/segments)"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Document Type:** `{meta['type']}`")
                    st.write(f"**Total Pages / Sections:** `{meta['pages']}`")
                with col_b:
                    st.write(f"**Source Identifier:** `{source_name}`")
                
                st.markdown("**Key Topics / Brief Overview:**")
                st.info(meta['brief'])

                # Option to remove specific document
                if st.button(f" Remove Document: {source_name}", key=f"del_{active_ip}_{source_name}"):
                    # Remove from raw docs list
                    st.session_state.ip_raw_docs[active_ip] = [
                        doc for doc in st.session_state.ip_raw_docs[active_ip] 
                        if doc.metadata.get("source") != source_name
                    ]
                    # Remove from registry
                    del st.session_state.ip_file_registry[active_ip][source_name]
                    # Rebuild vector store
                    rebuild_vector_store(active_ip)
                    st.success(f"Successfully removed '{source_name}' and updated vector store!")
                    st.rerun()
    else:
        st.info("No documents added to this IP yet. Use the ingestion tabs below to add files.")

    # ==========================================
    # SECTION 3: ADD NEW FILES & SOURCES
    # ==========================================
    st.markdown("---")
    st.subheader("➕ Add New Files & Knowledge Sources")

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. Local Files (PDF / DOCX / PPT / XLSX / RTL)",
        "2. Direct PDF URL Link",
        "3. Web Links & Wikipedia",
        "4. ArXiv Research Papers"
    ])

    new_docs = []
    new_file_metadata = {}
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
        if st.button("Process & Add Uploaded Files", key="btn_local_process"):
            if uploaded_files:
                with st.spinner("Parsing documents and generating summaries..."):
                    for file in uploaded_files:
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
                                metadata={"source": file.name, "page": 1, "ip": active_ip, "type": doc_type}
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
                                        metadata={"source": file.name, "page": slide_idx + 1, "ip": active_ip, "type": doc_type}
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
                                    metadata={"source": f"{file.name} [{sheet}]", "page": 1, "ip": active_ip, "type": doc_type}
                                ))
                        # Verilog / VHDL Code Processing
                        else:
                            doc_type = "HDL Code"
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                full_extracted_text = f.read()
                            file_page_count = 1
                            new_docs.append(Document(
                                page_content=full_extracted_text,
                                metadata={"source": file.name, "page": 1, "ip": active_ip, "type": doc_type}
                            ))

                        # Generate brief overview from first 1000 characters
                        brief_summary = full_extracted_text[:400].replace("\n", " ") + "..." if len(full_extracted_text) > 400 else full_extracted_text
                        
                        st.session_state.ip_file_registry[active_ip][file.name] = {
                            "type": doc_type,
                            "pages": file_page_count,
                            "brief": f"Covers structural definitions, interface specifications, and register configurations. Excerpt: {brief_summary}"
                        }

                    # Append to raw docs and rebuild index
                    st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                    rebuild_vector_store(active_ip)
                    st.success(f"Successfully processed and added local files to `{active_ip}`!")
                    st.rerun()
            else:
                st.warning("Please choose one or more files first.")

    # TAB 2: PDF URL DOWNLOAD
    with tab2:
        st.markdown("##### Download and Ingest Remote Datasheet / Manual via Direct URL")
        pdf_url = st.text_input("Direct PDF Web Link", placeholder="https://example.com/datasheets/axi_stream_spec.pdf", key="url_input_new")
        if st.button("Download & Ingest PDF Link", key="btn_url_download_new"):
            if pdf_url.strip():
                with st.spinner("Downloading and parsing remote PDF..."):
                    raw_filename = pdf_url.split("/")[-1].split("?")[0]
                    if not raw_filename.lower().endswith(".pdf"):
                        raw_filename = "downloaded_spec.pdf"
                    target_path = os.path.join("temp_ip_data", raw_filename)

                    if download_pdf_from_url(pdf_url.strip(), target_path):
                        full_text = ""
                        with fitz.open(target_path) as doc:
                            page_count = len(doc)
                            for page_num, page in enumerate(doc):
                                text = page.get_text()
                                if text.strip():
                                    full_text += text + "\n"
                                    new_docs.append(Document(
                                        page_content=text,
                                        metadata={"source": pdf_url, "page": page_num + 1, "ip": active_ip, "type": "Remote PDF Spec"}
                                    ))
                        
                        brief = full_text[:400].replace("\n", " ") + "..."
                        st.session_state.ip_file_registry[active_ip][pdf_url] = {
                            "type": "Remote PDF Spec",
                            "pages": page_count,
                            "brief": f"Remote PDF document. Excerpt: {brief}"
                        }
                        
                        st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                        rebuild_vector_store(active_ip)
                        st.success(f"Downloaded and indexed remote PDF successfully!")
                        st.rerun()
            else:
                st.warning("Please provide a valid PDF link.")

    # TAB 3: WEB & WIKIPEDIA
    with tab3:
        st.markdown("##### Ingest Online Documentation, Specs, or Wikipedia Protocols")
        web_url = st.text_input("Vendor Documentation URL", placeholder="https://en.wikipedia.org/wiki/Advanced_eXtensible_Interface", key="web_input_new")
        wiki_query = st.text_input("Wikipedia Topic Search", placeholder="e.g., Serial Peripheral Interface", key="wiki_input_new")
        
        if st.button("Ingest Web / Wikipedia Data", key="btn_web_ingest_new"):
            with st.spinner("Extracting content..."):
                if web_url.strip():
                    page_text = scrape_web_page(web_url.strip())
                    if page_text:
                        new_docs.append(Document(
                            page_content=page_text[:8000],
                            metadata={"source": web_url.strip(), "page": 1, "ip": active_ip, "type": "Web Article"}
                        ))
                        st.session_state.ip_file_registry[active_ip][web_url.strip()] = {
                            "type": "Web Article",
                            "pages": 1,
                            "brief": f"Web scraped article. Excerpt: {page_text[:300]}..."
                        }
                
                if wiki_query.strip():
                    try:
                        wiki_content = wikipedia.summary(wiki_query.strip(), sentences=12)
                        new_docs.append(Document(
                            page_content=wiki_content,
                            metadata={"source": f"Wikipedia: {wiki_query.strip()}", "page": 1, "ip": active_ip, "type": "Wikipedia Entry"}
                        ))
                        st.session_state.ip_file_registry[active_ip][f"Wikipedia: {wiki_query.strip()}"] = {
                            "type": "Wikipedia Entry",
                            "pages": 1,
                            "brief": f"Wikipedia overview on {wiki_query.strip()}. Excerpt: {wiki_content[:300]}..."
                        }
                    except Exception as e:
                        st.error(f"Wikipedia lookup error: {e}")

                if new_docs:
                    st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                    rebuild_vector_store(active_ip)
                    st.success("Web & Wikipedia content fetched and indexed!")
                    st.rerun()

    # TAB 4: ARXIV RESEARCH PAPERS
    with tab4:
        st.markdown("##### Query and Ingest ArXiv Hardware/ASIC Research Papers")
        arxiv_query = st.text_input("Research Topic", placeholder="e.g., AXI Protocol Verification, RISC-V Branch Predictor", key="arxiv_input_new")
        max_papers = st.slider("Number of Papers", min_value=1, max_value=5, value=2, key="arxiv_slider_new")

        if st.button("Fetch Academic Papers", key="btn_arxiv_fetch_new"):
            if arxiv_query.strip():
                with st.spinner("Querying ArXiv API..."):
                    client = arxiv.Search(query=arxiv_query.strip(), max_results=max_papers)
                    for paper in client.results():
                        body = f"Title: {paper.title}\nAuthors: {', '.join([a.name for a in paper.authors])}\n\nAbstract:\n{paper.summary}"
                        source_label = f"ArXiv: {paper.title}"
                        new_docs.append(Document(
                            page_content=body,
                            metadata={"source": source_label, "page": 1, "ip": active_ip, "type": "ArXiv Research Paper"}
                        ))
                        st.session_state.ip_file_registry[active_ip][source_label] = {
                            "type": "ArXiv Research Paper",
                            "pages": 1,
                            "brief": f"Academic Research Paper by {', '.join([a.name for a in paper.authors])}. Abstract: {paper.summary[:300]}..."
                        }
                    
                    st.session_state.ip_raw_docs[active_ip].extend(new_docs)
                    rebuild_vector_store(active_ip)
                    st.success(f"Indexed {len(new_docs)} ArXiv papers!")
                    st.rerun()
            else:
                st.warning("Please provide a research query.")
