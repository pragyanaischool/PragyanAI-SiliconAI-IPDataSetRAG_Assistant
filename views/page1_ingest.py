import streamlit as st
import os
import requests
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import arxiv
import wikipedia
from bs4 import BeautifulSoup

def download_pdf_from_url(url: str, save_path: str) -> bool:
    """Downloads a PDF file from a direct public link."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        st.error(f"Failed to download PDF from URL: {e}")
    return False

def scrape_web_page(url: str) -> str:
    """Extracts text content from a general website link."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        st.error(f"Failed to scrape web page: {e}")
        return ""

def render():
    st.title("📂 Page 1: Multi-Source Knowledge Base Ingestion")
    st.markdown("Ingest PDFs (local uploads or direct URL links), Excel spreadsheets, Word/PPT docs, Wikipedia summaries, Research Papers, and Web Links into your target IP model.")

    if "ip_databases" not in st.session_state:
        st.session_state.ip_databases = {}
    if "ip_metadata" not in st.session_state:
        st.session_state.ip_metadata = {}

    # IP Target Selection Form
    with st.form("ip_registration_form"):
        st.subheader("1. Select or Register IP Model / Dataset Container")
        ip_name = st.text_input("IP Model Name (e.g., AXI_DMA_Controller, RISCV_Core, SPI_IP)")
        submitted = st.form_submit_button("Set Active IP Container")
        if submitted and ip_name:
            st.session_state.current_ip = ip_name
            if ip_name not in st.session_state.ip_databases:
                st.session_state.ip_metadata[ip_name] = []
            st.success(f"Active IP Context set to: **{ip_name}**")

    if "current_ip" in st.session_state:
        active_ip = st.session_state.current_ip
        st.info(f"Active Ingestion Target: **{active_ip}**")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📁 Local Files (PDF/DOC/PPT/Excel/Verilog)", 
            "🔗 PDF URL Link", 
            "🌐 Web & Wikipedia", 
            "📚 Research Papers (ArXiv)"
        ])

        new_docs = []
        os.makedirs("temp_ingest_data", exist_ok=True)

        # Tab 1: Local Files Ingestion
        with tab1:
            st.markdown("### Upload Structured Files")
            uploaded_files = st.file_uploader(
                "Upload files", 
                type=["pdf", "docx", "pptx", "xlsx", "v", "vhdl", "txt"], 
                accept_multiple_files=True
            )
            if st.button("Process Local Files", key="btn_local"):
                if uploaded_files:
                    for file in uploaded_files:
                        path = os.path.join("temp_ingest_data", file.name)
                        with open(path, "wb") as f:
                            f.write(file.getbuffer())
                        
                        # Format-specific parsing logic
                        if file.name.endswith(".pdf"):
                            with fitz.open(path) as doc:
                                for p_num, page in enumerate(doc):
                                    new_docs.append(Document(
                                        page_content=page.get_text(), 
                                        metadata={"source": file.name, "page": p_num + 1, "ip": active_ip, "type": "PDF Datasheet"}
                                    ))
                        elif file.name.endswith(".docx"):
                            doc_obj = DocxDocument(path)
                            text = "\n".join([p.text for p in doc_obj.paragraphs if p.text.strip()])
                            new_docs.append(Document(
                                page_content=text, 
                                metadata={"source": file.name, "page": 1, "ip": active_ip, "type": "Word Document"}
                            ))
                        elif file.name.endswith(".pptx"):
                            prs = Presentation(path)
                            for s_idx, slide in enumerate(prs.slides):
                                slide_text = "".join([p.text + "\n" for shape in slide.shapes if shape.has_text_frame for p in shape.text_frame.paragraphs])
                                new_docs.append(Document(
                                    page_content=slide_text, 
                                    metadata={"source": file.name, "page": s_idx + 1, "ip": active_ip, "type": "Presentation Slide"}
                                ))
                        elif file.name.endswith(".xlsx"):
                            xls = pd.ExcelFile(path)
                            for sheet in xls.sheet_names:
                                df = pd.read_excel(path, sheet_name=sheet)
                                new_docs.append(Document(
                                    page_content=df.to_markdown(index=False), 
                                    metadata={"source": f"{file.name} (Sheet: {sheet})", "page": 1, "ip": active_ip, "type": "Excel Sheet"}
                                ))
                        else:  # Verilog / Source Code files
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                new_docs.append(Document(
                                    page_content=f.read(), 
                                    metadata={"source": file.name, "page": 1, "ip": active_ip, "type": "Verilog/Code"}
                                ))
                        
                        st.session_state.ip_metadata[active_ip].append(file.name)
                    st.success(f"Successfully processed local files for {active_ip}!")

        # Tab 2: PDF URL Link Ingestion
        with tab2:
            st.markdown("### Ingest PDF via Direct Link")
            pdf_url = st.text_input("Enter Direct PDF Download URL")
            if st.button("Download & Process PDF URL", key="btn_pdf_url"):
                if pdf_url:
                    filename = pdf_url.split("/")[-1].split("?")[0]
                    if not filename.endswith(".pdf"):
                        filename = "downloaded_spec.pdf"
                    save_path = os.path.join("temp_ingest_data", filename)
                    
                    if download_pdf_from_url(pdf_url, save_path):
                        with fitz.open(save_path) as doc:
                            for p_num, page in enumerate(doc):
                                new_docs.append(Document(
                                    page_content=page.get_text(), 
                                    metadata={"source": pdf_url, "page": p_num + 1, "ip": active_ip, "type": "PDF Web Link"}
                                ))
                        st.session_state.ip_metadata[active_ip].append(pdf_url)
                        st.success("Successfully downloaded and ingested PDF from URL!")

        # Tab 3: Web Links & Wikipedia Ingestion
        with tab3:
            st.markdown("### Web Links & Wikipedia Ingestion")
            web_link = st.text_input("Enter General Web Link (URL)")
            wiki_topic = st.text_input("Enter Wikipedia Topic Search Query")
            
            if st.button("Ingest Web/Wiki Content", key="btn_web"):
                if web_link:
                    content = scrape_web_page(web_link)
                    if content:
                        new_docs.append(Document(
                            page_content=content, 
                            metadata={"source": web_link, "page": 1, "ip": active_ip, "type": "Web Link"}
                        ))
                        st.session_state.ip_metadata[active_ip].append(web_link)
                if wiki_topic:
                    try:
                        wiki_summary = wikipedia.summary(wiki_topic, sentences=10)
                        new_docs.append(Document(
                            page_content=wiki_summary, 
                            metadata={"source": f"Wikipedia: {wiki_topic}", "page": 1, "ip": active_ip, "type": "Wikipedia"}
                        ))
                        st.session_state.ip_metadata[active_ip].append(f"Wikipedia: {wiki_topic}")
                    except Exception as e:
                        st.error(f"Wikipedia fetch error: {e}")
                if web_link or wiki_topic:
                    st.success("Successfully ingested Web/Wiki data!")

        # Tab 4: Research Papers (ArXiv) Ingestion
        with tab4:
            st.markdown("### Search & Ingest Research Papers")
            research_query = st.text_input("Search ArXiv Topic (e.g., 'AXI Bus Protocol Verification' or 'RISC-V architecture')")
            max_results = st.slider("Number of Papers", 1, 5, 2)
            
            if st.button("Fetch Research Papers", key="btn_arxiv"):
                if research_query:
                    search_client = arxiv.Search(query=research_query, max_results=max_results)
                    for paper in search_client.results():
                        paper_text = f"Title: {paper.title}\nAuthors: {', '.join([a.name for a in paper.authors])}\nAbstract: {paper.summary}"
                        new_docs.append(Document(
                            page_content=paper_text, 
                            metadata={"source": f"ArXiv: {paper.title}", "page": 1, "ip": active_ip, "type": "Research Paper"}
                        ))
                        st.session_state.ip_metadata[active_ip].append(f"ArXiv: {paper.title}")
                    st.success("Successfully fetched and indexed research papers!")

        # Commit accumulated documents into FAISS vector database
        if new_docs:
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            if active_ip in st.session_state.ip_databases:
                st.session_state.ip_databases[active_ip].add_documents(new_docs)
            else:
                st.session_state.ip_databases[active_ip] = FAISS.from_documents(new_docs, embeddings)
