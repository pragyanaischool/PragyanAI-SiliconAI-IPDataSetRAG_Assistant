import streamlit as st
from langchain_groq import ChatGroq

# Dictionary of UI Translations for Multi-Language Interface Support
UI_TEXTS = {
    "English": {
        "title": " Page 2: Expert Multi-IP Silicon RAG Assistant",
        "subtitle": "Select IP models, customize extraction profiles, refine your questions, and query specifications in your preferred language.",
        "select_ip": "Active Target IP Core(s)",
        "api_key": "Groq API Key",
        "lang_label": "Interface & Response Language",
        "input_placeholder": "Ask technical questions regarding specifications, registers, or RTL code...",
        "refine_header": "🔍 AI Query Refinement & Validation",
        "refine_prompt": "Our AI architect has refined your query for maximum engineering precision. Is this what you are looking for? Edit if needed and submit:",
        "submit_refined": "🚀 Confirm & Execute Query",
        "kg_header": "🕸️ Dynamic IP Knowledge Graph",
        "kg_caption": "Visualizing relationship entities and protocol hierarchies extracted from retrieved context:",
        "citations": "📚 Referenced Citations:"
    },
    "Japanese (日本語)": {
        "title": " ページ 2: エキスパートマルチIPシリコン RAG アシスタント",
        "subtitle": "IPモデルを選択し、抽出プロファイルをカスタマイズし、質問を洗練させ、お好みの言語で仕様を照会します。",
        "select_ip": "アクティブな対象IPコア",
        "api_key": "Groq APIキー",
        "lang_label": "インターフェースと応答の言語",
        "input_placeholder": "仕様、レジスタ、またはRTLコードに関する技術的な質問をしてください...",
        "refine_header": "🔍 AIクエリの洗練と検証",
        "refine_prompt": "AIアーキテクトがエンジニアリング精度を高めるためにクエリを洗練させました。お探しの内容ですか？必要に応じて編集して送信してください：",
        "submit_refined": "🚀 確認してクエリを実行",
        "kg_header": "🕸️ 動的IP知識グラフ",
        "kg_caption": "取得したコンテキストから抽出されたリレーションシップエンティティとプロトコル階層の視覚化：",
        "citations": "📚 参照された引用:"
    },
    "German (Deutsch)": {
        "title": " Seite 2: Experten Multi-IP Silicon RAG Assistent",
        "subtitle": "Wählen Sie IP-Modelle aus, passen Sie Extraktionsprofile an, verfeinern Sie Fragen und fragen Sie Spezifikationen ab.",
        "select_ip": "Aktive Ziel-IP-Kerne",
        "api_key": "Groq API-Schlüssel",
        "lang_label": "Schnittstellen- und Antwortsprache",
        "input_placeholder": "Stellen Sie technische Fragen zu Spezifikationen, Registern oder RTL-Code...",
        "refine_header": "🔍 KI-Abfrageverfeinerung & Validierung",
        "refine_prompt": "Unsere KI hat Ihre Anfrage verfeinert. Ist das wonach Sie suchen? Bei Bedarf bearbeiten und absenden:",
        "submit_refined": "🚀 Bestätigen & Ausführen",
        "kg_header": "🕸️ Dynamischer IP-Wissensgraph",
        "kg_caption": "Visualisierung von Entitäten und Protokollhierarchien aus dem abgerufenen Kontext:",
        "citations": "📚 Zitierte Quellen:"
    },
    "Mandarin (中文)": {
        "title": " 页面 2: 专家多 IP 芯片 RAG 助手",
        "subtitle": "选择 IP 模型、自定义提取配置文件、精炼您的问题，并以您首选的语言查询。",
        "select_ip": "活动目标 IP 核心",
        "api_key": "Groq API 密钥",
        "lang_label": "界面与响应语言",
        "input_placeholder": "询问关于规格、寄存器或 RTL 代码的技术问题...",
        "refine_header": "🔍 AI 问题精炼与验证",
        "refine_prompt": "我们的 AI 架构师已优化了您的提问。这是您要找的内容吗？如有需要可进行编辑并提交：",
        "submit_refined": "🚀 确认并执行查询",
        "kg_header": "🕸️ 动态 IP 知识图谱",
        "kg_caption": "可视化从检索到的上下文中提取的实体关系与协议层次结构：",
        "citations": "📚 参考引用:"
    }
}

def render():
    # Multi-Language Selection in Sidebar
    selected_lang = st.sidebar.selectbox(" Select Language / 言語 / Sprache", list(UI_TEXTS.keys()), index=0)
    t = UI_TEXTS.get(selected_lang, UI_TEXTS["English"])

    # Custom Extraction Studio Sidebar Controls
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Custom Extraction Studio")
    custom_extraction_mode = st.sidebar.selectbox(
        "Extraction Profile", 
        ["Standard Silicon Architect", "Register Map (JSON/Table)", "UVM Testbench Generator", "Timing & Clock Domain Constraints", "Custom Instructions"]
    )
    
    user_custom_rule = ""
    if custom_extraction_mode == "Custom Instructions":
        user_custom_rule = st.sidebar.text_area(
            "Add-on Extraction Rule", 
            placeholder="e.g., Always output register offsets in hexadecimal and include C header definitions."
        )

    profile_instructions = {
        "Standard Silicon Architect": "Focus on rigorous handshaking, synchronous reset behavior, and structural RTL.",
        "Register Map (JSON/Table)": "Strictly extract register bit-fields into structured Markdown tables including Offset, Bit Range, Access Type (RO/RW), and Reset Value.",
        "UVM Testbench Generator": "Generate Universal Verification Methodology (UVM) sequence, driver, and monitor stubs matching the IP interface.",
        "Timing & Clock Domain Constraints": "Focus entirely on clock frequencies, setup/hold constraints, and asynchronous clock domain crossing (CDC) safety.",
        "Custom Instructions": user_custom_rule
    }
    active_profile_instruction = profile_instructions.get(custom_extraction_mode, "")

    st.image("PragyanAI_Transperent.png")
    st.title(t["title"])
    st.markdown(t["subtitle"])

    if "ip_databases" not in st.session_state or not st.session_state.ip_databases:
        st.warning("⚠️ No IP models found. Navigate to **Page 1: Ingestion & IP Management** to register an IP first.")
        return

    available_ips = list(st.session_state.ip_databases.keys())

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_ips = st.multiselect(t["select_ip"], available_ips, default=[available_ips[0]] if available_ips else [])
    with col2:
        groq_api_key = st.text_input(t["api_key"], type="password", help="Sign up at console.groq.com")

    if not selected_ips or not groq_api_key:
        st.info("💡 Please select at least one IP model and enter your Groq API key to begin.")
        return

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, groq_api_key=groq_api_key)

    session_key = "_".join(sorted(selected_ips))
    if "multi_chat_histories" not in st.session_state:
        st.session_state.multi_chat_histories = {}
    if session_key not in st.session_state.multi_chat_histories:
        st.session_state.multi_chat_histories[session_key] = []

    chat_history = st.session_state.multi_chat_histories[session_key]

    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if "pending_user_query" not in st.session_state:
        st.session_state.pending_user_query = ""
    if "refined_query_draft" not in st.session_state:
        st.session_state.refined_query_draft = ""
    if "show_refinement_box" not in st.session_state:
        st.session_state.show_refinement_box = False

    user_query = st.chat_input(t["input_placeholder"])

    if user_query:
        st.session_state.pending_user_query = user_query
        refiner_prompt = f"As a principal silicon architect, refine and structure this user question for high-precision technical vector retrieval and RTL analysis. Return ONLY the refined query string: '{user_query}'"
        refined_res = llm.invoke(refiner_prompt)
        st.session_state.refined_query_draft = refined_res.content.strip()
        st.session_state.show_refinement_box = True
        st.rerun()

    if st.session_state.show_refinement_box:
        st.markdown("---")
        st.info(t["refine_header"])
        st.markdown(t["refine_prompt"])
        
        final_query_to_run = st.text_area("Edit Refined Query:", value=st.session_state.refined_query_draft, height=80)
        
        col_sub1, col_sub2 = st.columns([1, 4])
        with col_sub1:
            if st.button(t["submit_refined"], type="primary"):
                st.session_state.show_refinement_box = False
                execute_rag_query(final_query_to_run, selected_ips, llm, chat_history, selected_lang, t, active_profile_instruction)
                st.rerun()
        with col_sub2:
            if st.button("❌ Cancel"):
                st.session_state.show_refinement_box = False
                st.rerun()
        st.markdown("---")

def execute_rag_query(query: str, selected_ips: list, llm, chat_history: list, lang: str, t: dict, extraction_directive: str):
    chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.spinner("Executing multi-IP retrieval, applying custom extraction rules, and synthesizing response..."):
        retrieved_chunks = []
        for ip in selected_ips:
            vector_db = st.session_state.ip_databases[ip]
            hits = vector_db.similarity_search(query, k=3)
            retrieved_chunks.extend(hits)

        st.session_state.last_references = retrieved_chunks

        context_text = ""
        citations_list = []
        for idx, chunk in enumerate(retrieved_chunks):
            meta = chunk.metadata
            ip_label = meta.get("ip", "General")
            src_name = meta.get("source", "Unknown")
            doc_type = meta.get("type", "Spec")
            page_idx = meta.get("page", 1)

            context_text += f"\n--- Reference [{idx+1}] | IP: {ip_label} | Source: {src_name} | Page/Slide: {page_idx} ---\n"
            context_text += chunk.page_content[:1500] + "\n"
            citations_list.append(f"- **[{ip_label}]** `{src_name}` ({doc_type}, Page: {page_idx})")

        # Generate Dynamic Knowledge Graph in Mermaid format
        kg_prompt = f"""Based on the following hardware context, extract key entities (IP blocks, signals, registers, protocols) and their directional relationships. Generate a valid Mermaid.js graph string (using graph TD format) representing these connections. Return ONLY the mermaid code block syntax starting with graph TD:
        
        Context:
        {context_text[:3000]}
        """
        kg_res = llm.invoke(kg_prompt)
        mermaid_code = kg_res.content.replace("```mermaid", "").replace("```", "").strip()

        # Expert System Prompt with Active Custom Extraction Directive & Language Localization
        system_prompt = f"""You are a Principal Silicon Architect and Senior RTL Verification Specialist. 
Respond entirely in the requested interface language: **{lang}**.

### Active Custom Extraction Directive:
{extraction_directive}

=== RETRIEVED HARDWARE CONTEXT ===
{context_text}
==================================
"""

        messages = [("system", system_prompt)]
        for prev_turn in chat_history[-7:-1]:
            messages.append(("human" if prev_turn["role"] == "user" else "ai", prev_turn["content"]))
        messages.append(("human", query))

        response = llm.invoke(messages)
        answer = response.content

        if mermaid_code:
            answer += f"\n\n### {t['kg_header']}\n{t['kg_caption']}\n```mermaid\n{mermaid_code}\n```"

        unique_citations = list(set(citations_list))
        if unique_citations:
            answer += f"\n\n---\n**{t['citations']}**\n" + "\n".join(unique_citations[:5])

        chat_history.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
