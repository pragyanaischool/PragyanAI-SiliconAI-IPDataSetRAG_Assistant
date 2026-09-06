import streamlit as st
from langchain_groq import ChatGroq

def render():
    st.title("💬 Page 2: Expert Multi-IP Silicon RAG Assistant")
    st.markdown("Select **one or multiple semiconductor IP models** to query specifications, compare interconnects, analyze register maps, and generate synthesis-ready Verilog/VHDL code.")

    # Verify IP availability
    if "ip_databases" not in st.session_state or not st.session_state.ip_databases:
        st.warning("⚠️ No IP models found. Navigate to **Page 1: Ingestion & IP Management** to register an IP and upload datasheets first.")
        return

    available_ips = list(st.session_state.ip_databases.keys())

    col1, col2 = st.columns([2, 1])
    with col1:
        selected_ips = st.multiselect(
            "Active Target IP Core(s)",
            available_ips,
            default=[available_ips[0]] if available_ips else []
        )
    with col2:
        groq_api_key = st.text_input("Groq API Key", type="password", help="Sign up at console.groq.com")

    if not selected_ips:
        st.info("Select at least one IP model to chat.")
        return

    if not groq_api_key:
        st.info("💡 Enter your Groq API key to initialize the Llama-3.3 hardware reasoning model.")
        return

    # Initialize ChatGroq LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        groq_api_key=groq_api_key
    )

    # Unique conversation state key per selection combination
    session_key = "_".join(sorted(selected_ips))
    if session_key not in st.session_state.multi_chat_histories:
        st.session_state.multi_chat_histories[session_key] = []

    chat_history = st.session_state.multi_chat_histories[session_key]

    # Render Chat History
    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input Bar
    user_query = st.chat_input(f"Ask technical questions regarding: {', '.join(selected_ips)}...")

    if user_query:
        chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.spinner("Searching IP vector databases and reasoning through hardware logic..."):
            # Multi-IP Vector Retrieval
            retrieved_chunks = []
            for ip in selected_ips:
                vector_db = st.session_state.ip_databases[ip]
                # Pull top 3 matches per selected IP
                hits = vector_db.similarity_search(user_query, k=3)
                retrieved_chunks.extend(hits)

            # Save global audit reference for Page 3
            st.session_state.last_references = retrieved_chunks

            # Construct Grounding Context & Source Citations
            context_text = ""
            citations_list = []
            for idx, chunk in enumerate(retrieved_chunks):
                meta = chunk.metadata
                ip_label = meta.get("ip", "General")
                src_name = meta.get("source", "Unknown")
                doc_type = meta.get("type", "Spec")
                page_idx = meta.get("page", 1)

                context_text += f"\n--- Reference [{idx+1}] | IP: {ip_label} | Source: {src_name} | Page/Slide: {page_idx} | Type: {doc_type} ---\n"
                context_text += chunk.page_content[:1800] + "\n"

                citations_list.append(f"- **[{ip_label}]** `{src_name}` ({doc_type}, Page/Slide: {page_idx})")

            # Senior Silicon Architect System Prompt
            system_prompt = f"""You are a Principal Silicon Architect and Senior RTL Verification Specialist with over 25 years of industry experience in ASIC/SoC architectures, embedded protocols (AMBA AXI/AHB/APB, PCIe, SPI, I2C, UART), and CPU cores (RISC-V, ARM).

Analyze the user's inquiry with professional rigor and respond using the following standards:
1. **Architectural Rigor:** Explain low-level hardware mechanisms clearly (e.g., backpressure via VALID/READY handshakes, pipeline hazards, clock domain crossing (CDC) synchronization, synchronous vs asynchronous resets).
2. **Synthesis-Ready RTL:** When generating Verilog or VHDL, adhere strictly to industry synthesis guidelines:
   - Separate combinational and sequential blocks cleanly.
   - Use non-blocking (`<=`) assignments for sequential registers, blocking (`=`) for combinational logic.
   - Ensure complete case coverage or assign default values to eliminate unwanted latches.
   - Provide explicit port direction, bit-width declarations, and active-low/active-high reset conventions.
3. **Register Bit-Fields:** If detailing register maps, present them in clear Markdown tables indicating Offset, Bit Range, Name, Type (R/W, RO, W1C), and Functional Description.
4. **Cross-IP Integration:** If multiple IPs are referenced, clarify protocol adaptation, bus arbitration, or bridge logic required between them.
5. **Contextual Grounding:** Prioritize information from the retrieved context below. If critical parameters are unspecified in the context, clearly highlight your engineering assumptions.

=== RETRIEVED HARDWARE CONTEXT ===
{context_text}
==================================
"""

            # Message Payload with Conversational Continuity
            messages = [("system", system_prompt)]
            
            # Append prior turns (last 6 messages max to stay concise)
            for prev_turn in chat_history[-7:-1]:
                if prev_turn["role"] == "user":
                    messages.append(("human", prev_turn["content"]))
                else:
                    messages.append(("ai", prev_turn["content"]))
            
            messages.append(("human", user_query))

            # Model Inference via Groq
            try:
                response = llm.invoke(messages)
                answer = response.content

                # Append Citation Summary
                unique_citations = list(set(citations_list))
                if unique_citations:
                    answer += "\n\n---\n**📚 Referenced Citations:**\n" + "\n".join(unique_citations[:5])
                    answer += "\n\n*(Inspect full text segments and code snippets on **Page 3: References & Citation Dashboard**)*"

                chat_history.append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.markdown(answer)

            except Exception as e:
                st.error(f"Error during LLM invocation: {e}")
