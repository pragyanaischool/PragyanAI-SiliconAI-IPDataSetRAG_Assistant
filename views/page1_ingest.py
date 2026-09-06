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

def render():
    st.title("📂 Page 1: IP Core & Knowledge Base Ingestion")
    st.markdown("Register semiconductor IP cores (e.g., `AXI_DMA`, `RISCV_Core`, `SPI_Master`), ingest documentation across multiple formats, download PDF datasheets via URL, and retrieve academic research.")

    # 1. IP Model Registration
    st.subheader("1. Register or Select Semiconductor IP Model")
    with st.form("ip_registration_form"):
        ip_name_input = st.text_input(
            "IP Model Identifier", 
            placeholder="e.g., AMBA_AXI4_Interconnect, RISCV_RV32I, SPI_Engine"
        )
        submitted = st.form_submit_button("Register / Set Active IP Container")
        
        if submitted and ip_name_input.strip():
            clean_ip_name = ip_name_input.strip().replace(" ", "_")
            st.session_state.current_ip = clean_ip_name
            if clean_ip_name not in st.session_state.ip_metadata:
                st.session_state.ip_metadata[clean_ip_name] = []
            st.success(f"Active IP context configured: **{clean_ip_name}**")

    # Guard: Require active IP container
    if "current_ip" not in st.session_state:
        st.info("👈 Please define and register an IP Model name above to begin ingesting files.")
        return

    active_ip = st.session_state.current_ip
    st.markdown(f"### 📥 Ingesting Resources into: `{active_ip}`")

    # Ingestion Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Local Files (PDF / DOCX / PPT / XLSX / RTL)",
        "🔗 Direct PDF URL Link",
        "🌐 Web Links & Wikipedia",
        "📚 ArXiv Research Papers"
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
            key="local_uploader"
        )
        if st.button("Process Uploaded Files", key="btn_local_process"):
            if uploaded_files:
                with st.spinner("Parsing and chunking documents..."):
                    for file in uploaded_files:
                        file_path = os.path.join("temp_ip_data", file.name)
                        with open(file_path, "wb") as f:
                            f.write(file.getbuffer())

                        # PDF Processing
                        if file.name.lower().endswith(".pdf"):
                            with fitz.open(file_path) as doc:
                                for page_num, page in enumerate(doc):
                                    text = page.get_text()
                                    if text.strip():
                                        new_docs.append(Document(
                                            page_content=text,
                                            metadata={
                                                "source": file.name,
                                                "page": page_num + 1,
                                                "ip": active_ip,
                                                "type": "PDF Datasheet"
                                            }
                                        ))
                        # DOCX Processing
                        elif file.name.lower().endswith(".docx"):
                            doc_obj = DocxDocument(file_path)
                            full_text = "\n".join([p.text for p in doc_obj.paragraphs if p.text.strip()])
                            new_docs.append(Document(
                                page_content=full_text,
                                metadata={
                                    "source": file.name,
                                    "page": 1,
                                    "ip": active_ip,
                                    "type": "Word Document"
                                }
                            ))
                        # PPTX Processing
                        elif file.name.lower().endswith(".pptx"):
                            prs = Presentation(file_path)
                            for slide_idx, slide in enumerate(prs.slides):
                                slide_text = ""
                                for shape in slide.shapes:
                                    if shape.has_text_frame:
                                        for p in shape.text_frame.paragraphs:
                                            slide_text += p.text + "\n"
                                if slide_text.strip():
                                    new_docs.append(Document(
                                        page_content=slide_text,
                                        metadata={
                                            "source": file.name,
                                            "page": slide_idx + 1,
                                            "ip": active_ip,
                                            "type": "Presentation Slide"
                                        }
                                    ))
                        # Excel Processing
                        elif file.name.lower().endswith(".xlsx"):
                            xls = pd.ExcelFile(file_path)
                            for sheet in xls.sheet_names:
                                df = pd.read_excel(file_path, sheet_name=sheet)
                                new_docs.append(Document(
                                    page_content=f"Sheet: {sheet}\n\n" + df.to_markdown(index=False),
                                    metadata={
                                        "source": f"{file.name} [{sheet}]",
                                        "page": 1,
                                        "ip": active_ip,
                                        "type": "Excel Register Map"
                                    }
                                ))
                        # Verilog / VHDL Code Processing
                        else:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                code_body = f.read()
                            new_docs.append(Document(
                                page_content=code_body,
                                metadata={
                                    "source": file.name,
                                    "page": 1,
                                    "ip": active_ip,
                                    "type": "HDL Code"
                                }
                            ))

                        st.session_state.ip_metadata[active_ip].append(file.name)
                    st.success(f"Extracted {len(new_docs)} document nodes from local files!")
            else:
                st.warning("Please choose one or more files first.")

    # TAB 2: PDF URL DOWNLOAD
    with tab2:
        st.markdown("##### Download and Ingest Remote Datasheet / Manual via Direct URL")
        pdf_url = st.text_input("Direct PDF Web Link", placeholder="https://example.com/datasheets/axi_stream_spec.pdf")
        if st.button("Download & Ingest PDF Link", key="btn_url_download"):
            if pdf_url.strip():
                with st.spinner("Downloading and parsing remote PDF..."):
                    raw_filename = pdf_url.split("/")[-1].split("?")[0]
                    if not raw_filename.lower().endswith(".pdf"):
                        raw_filename = "downloaded_spec.pdf"
                    target_path = os.path.join("temp_ip_data", raw_filename)

                    if download_pdf_from_url(pdf_url.strip(), target_path):
                        with fitz.open(target_path) as doc:
                            for page_num, page in enumerate(doc):
                                text = page.get_text()
                                if text.strip():
                                    new_docs.append(Document(
                                        page_content=text,
                                        metadata={
                                            "source": pdf_url,
                                            "page": page_num + 1,
                                            "ip": active_ip,
                                            "type": "Remote PDF Spec"
                                        }
                                    ))
                        st.session_state.ip_metadata[active_ip].append(pdf_url)
                        st.success(f"Downloaded and parsed {len(new_docs)} pages from URL!")
            else:
                st.warning("Please provide a valid PDF link.")

    # TAB 3: WEB & WIKIPEDIA
    with tab3:
        st.markdown("##### Ingest Online Documentation, Specs, or Wikipedia Protocols")
        web_url = st.text_input("Vendor Documentation URL", placeholder="https://en.wikipedia.org/wiki/Advanced_eXtensible_Interface")
        wiki_query = st.text_input("Wikipedia Topic Search", placeholder="e.g., Serial Peripheral Interface")
        
        if st.button("Ingest Web / Wikipedia Data", key="btn_web_ingest"):
            with st.spinner("Extracting content..."):
                if web_url.strip():
                    page_text = scrape_web_page(web_url.strip())
                    if page_text:
                        new_docs.append(Document(
                            page_content=page_text[:8000],
                            metadata={
                                "source": web_url.strip(),
                                "page": 1,
                                "ip": active_ip,
                                "type": "Web Article"
                            }
                        ))
                        st.session_state.ip_metadata[active_ip].append(web_url.strip())
                
                if wiki_query.strip():
                    try:
                        wiki_content = wikipedia.summary(wiki_query.strip(), sentences=12)
                        new_docs.append(Document(
                            page_content=wiki_content,
                            metadata={
                                "source": f"Wikipedia: {wiki_query.strip()}",
                                "page": 1,
                                "ip": active_ip,
                                "type": "Wikipedia Entry"
                            }
                        ))
                        st.session_state.ip_metadata[active_ip].append(f"Wikipedia: {wiki_query.strip()}")
                    except Exception as e:
                        st.error(f"Wikipedia lookup error: {e}")

                if new_docs:
                    st.success("Web & Wikipedia content fetched and indexed!")

    # TAB 4: ARXIV RESEARCH PAPERS
    with tab4:
        st.markdown("##### Query and Ingest ArXiv Hardware/ASIC Research Papers")
        arxiv_query = st.text_input("Research Topic", placeholder="e.g., AXI Protocol Verification, RISC-V Branch Predictor")
        max_papers = st.slider("Number of Papers", min_value=1, max_value=5, value=2)

        if st.button("Fetch Academic Papers", key="btn_arxiv_fetch"):
            if arxiv_query.strip():
                with st.spinner("Querying ArXiv API..."):
                    client = arxiv.Search(query=arxiv_query.strip(), max_results=max_papers)
                    for paper in client.results():
                        body = f"Title: {paper.title}\nAuthors: {', '.join([a.name for a in paper.authors])}\n\nAbstract:\n{paper.summary}"
                        new_docs.append(Document(
                            page_content=body,
                            metadata={
                                "source": f"ArXiv: {paper.title}",
                                "page": 1,
                                "ip": active_ip,
                                "type": "ArXiv Research Paper"
                            }
                        ))
                        st.session_state.ip_metadata[active_ip].append(f"ArXiv: {paper.title}")
                    st.success(f"Indexed {len(new_docs)} ArXiv papers!")
            else:
                st.warning("Please provide a research query.")

    # Vector Storage Commit
    if new_docs:
        with st.spinner("Generating embeddings and committing to vector store..."):
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            if active_ip in st.session_state.ip_databases:
                st.session_state.ip_databases[active_ip].add_documents(new_docs)
            else:
                st.session_state.ip_databases[active_ip] = FAISS.from_documents(new_docs, embeddings)
        st.toast(f"Knowledge Base updated for {active_ip}!", icon="✅")
