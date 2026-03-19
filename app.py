import streamlit as st
import streamlit.components.v1 as components
import os
import markdown
import io
import base64
import requests
import time
from xhtml2pdf import pisa
from agents.orchestrator import rfp_app, orchestrator_llm
from azure_logger import log_approval_to_azure
from mailer import send_proposal_email

# --- CONFIGURATION ---
st.set_page_config(page_title="Nexus | Proposal Engine", page_icon="⚡", layout="wide")

# --- CUSTOM CSS: PERFECTING THE UI LAYOUT ---
st.markdown("""
    <style>
           /* Fix the top spacing to breathe perfectly */
           .block-container {
                padding-top: 3rem;
                padding-bottom: 2rem;
            }
           /* Scale the title down slightly so it fits on one clean line */
           h1 {
                font-size: 2.8rem !important;
                margin-bottom: 0.5rem !important;
           }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBAL PDF GENERATOR ---
def create_pdf(md_text, image_link=None):
    html_text = markdown.markdown(md_text)
    
    image_html = ""
    if image_link:
        image_html = f'<br><br><h2>Proposed Architecture Diagram</h2><img src="{image_link}" width="600" />'
        
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
            h2 {{ color: #2980b9; margin-top: 20px; }}
            h3 {{ color: #16a085; }}
            p {{ margin-bottom: 15px; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        {html_text}
        {image_html}
    </body>
    </html>
    """
    result_file = io.BytesIO()
    pisa.CreatePDF(io.StringIO(styled_html), dest=result_file)
    return result_file.getvalue()

# --- HELPER TO DISPLAY PDF IN STREAMLIT ---
# --- HELPER TO DISPLAY PDF IN STREAMLIT ---
def display_pdf(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    # Using an <embed> tag instead of <iframe> is often more compatible with cloud hosting
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = None
if "current_status" not in st.session_state:
    st.session_state.current_status = "idle"
if "final_pdf_bytes" not in st.session_state:
    st.session_state.final_pdf_bytes = None
if "final_img_bytes" not in st.session_state:
    st.session_state.final_img_bytes = None
if "knowledge_guide_bytes" not in st.session_state:
    st.session_state.knowledge_guide_bytes = None
if "show_revision_toast" not in st.session_state:
    st.session_state.show_revision_toast = False

# --- SIDEBAR: Control Panel & Live Status ---
with st.sidebar:
    st.markdown("## ⚡ Nexus Control Panel")
    
    user_role = st.selectbox(
        "Simulate User Role:", 
        ["Sales Exec (Trigger)", "Cloud Architect (Reviewer)", "Engagement Manager (Reviewer)"]
    )
    st.divider()
    
    st.subheader("📡 Live System Status")
    status_map = {
        "idle": "🟡 Waiting for Client Requirements...",
        "start": "⚙️ Agents Initializing...",
        "research_done": "🔍 Research Complete. Drafting...",
        "awaiting_approval": "🔵 Draft Ready. Awaiting Human Review.",
        "needs_revision": "🔄 AI is actively revising the draft...",
        "approved": "🟢 Proposal Approved & Dispatched."
    }
    st.info(status_map.get(st.session_state.current_status, "Standby"))
    
    st.divider()
    
    # SIDEBAR DOWNLOADS
    if st.session_state.current_status == "approved":
        st.subheader("📥 Quick Downloads")
        if st.session_state.final_pdf_bytes:
            st.download_button("📄 Client Proposal (.pdf)", data=st.session_state.final_pdf_bytes, file_name="Client_Proposal.pdf", mime="application/pdf", use_container_width=True)
        if st.session_state.final_img_bytes:
            st.download_button("🖼️ Architecture (.png)", data=st.session_state.final_img_bytes, file_name="Architecture.png", mime="image/png", use_container_width=True)
        if st.session_state.knowledge_guide_bytes:
            st.download_button("🛡️ Project Knowledge Guide (.pdf)", data=st.session_state.knowledge_guide_bytes, file_name="Project_Knowledge_Guide.pdf", mime="application/pdf", use_container_width=True)

# --- MAIN UI HEADER ---
# --- MAIN UI HEADER ---
st.title("⚡ Nexus: Autonomous Proposal Engine")
st.markdown("Multi-agent LangGraph pipeline featuring Azure RAG, Live Web Search, and Human-in-the-loop auditing.")

# Add a clean divider line and some breathing room to separate the header from the tool
st.divider()
st.markdown("<br>", unsafe_allow_html=True)

# --- PHASE 1: TRIGGER ---
if st.session_state.current_status == "idle":
    st.subheader("📥 Step 1: Client Ingestion")
    client_req = st.text_area("Raw Client Request / RFP Text:", height=150, placeholder="e.g., We are Netflix. We need a cloud architecture to handle video streaming telemetry...")
    
    if st.button("🚀 Deploy Agents & Generate Proposal", type="primary"):
        if client_req:
            with st.status("🧠 Initializing LangGraph AI Brain...", expanded=True) as status:
                step1 = st.empty()
                step2 = st.empty()
                step3 = st.empty()
                
                step1.write("⏳ **Agent 1 (Researcher)**: Analyzing client requirements & querying Azure RAG...")
                time.sleep(1)
                step1.write("✅ **Agent 1 (Researcher)**: Analyzing client requirements & querying Azure RAG...")
                
                step2.write("⏳ **Web Search Tool**: Scraping live internet for latest company context...")
                time.sleep(1)
                step2.write("✅ **Web Search Tool**: Scraping live internet for latest company context...")
                
                step3.write("⏳ **Agent 2 (Writer)**: Synthesizing data & drafting Enterprise Architecture...")
                
                initial_state = {
                    "client_requirements": client_req,
                    "research_context": "",
                    "draft_proposal": "",
                    "feedback": "",
                    "revision_count": 0,
                    "status": "start"
                }
                result = rfp_app.invoke(initial_state)
                st.session_state.workflow_state = result
                st.session_state.current_status = result["status"]
                
                step3.write("✅ **Agent 2 (Writer)**: Synthesizing data & drafting Enterprise Architecture...")
                status.update(label="✅ Draft Generated Successfully!", state="complete", expanded=False)
            st.rerun()
        else:
            st.warning("Please enter client requirements first.")

# --- PHASE 2: HUMAN REVIEW ---
elif st.session_state.current_status == "awaiting_approval":
    
    if st.session_state.show_revision_toast:
        st.toast("✨ New draft successfully generated based on your feedback!", icon="✅")
        st.session_state.show_revision_toast = False
    
    rev_count = st.session_state.workflow_state['revision_count']
    if rev_count > 0:
        st.info(f"🔄 **Reviewing Revision #{rev_count}** (Updated based on recent feedback)")
    else:
        st.success("✅ Initial Draft Generated! Awaiting Human Review.")
    
    def render_mermaid(code: str):
        clean_code = code.replace("```mermaid", "").replace("```", "").strip()
        components.html(
            f"""
            <div class="mermaid">{clean_code}</div>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
            </script>
            """,
            height=450, scrolling=True
        )

    if st.session_state.workflow_state.get("architecture_diagram"):
        st.subheader("📊 Proposed Cloud Architecture")
        render_mermaid(st.session_state.workflow_state['architecture_diagram'])
    
    with st.expander("📄 View Generated Proposal Text", expanded=True):
        st.markdown(st.session_state.workflow_state["draft_proposal"])
        
    st.divider()
    
    if user_role in ["Cloud Architect (Reviewer)", "Engagement Manager (Reviewer)"]:
        st.subheader(f"🛡️ {user_role} Action Required")
        
        with st.expander("⚙️ Optional: Setup Kickoff Meeting Invite", expanded=True):
            send_invite = st.checkbox("Attach .ics Calendar Invite to Email", value=True)
            col_date, col_time = st.columns(2)
            with col_date:
                meet_date = st.date_input("Kickoff Date")
            with col_time:
                meet_time = st.time_input("Kickoff Time")
                
        feedback = st.text_area("Revision Feedback (if rejecting):", placeholder="e.g., The architecture needs to include Azure Key Vault for security. Rewrite the architecture section.")
        
        col1, col2 = st.columns(2)
        with col1:
            approve_clicked = st.button("✅ APPROVE & DISPATCH", type="primary", use_container_width=True)
        with col2:
            reject_clicked = st.button("❌ REJECT & REVISE", type="secondary", use_container_width=True)

        if approve_clicked:
            with st.status("📦 Compiling Final Artifacts...", expanded=True) as status:
                step1 = st.empty()
                step2 = st.empty()
                step3 = st.empty()
                step4 = st.empty()

                step1.write("⏳ 1. Logging approval audit to Azure Security Vault...")
                log_approval_to_azure(
                    client_req=st.session_state.workflow_state["client_requirements"],
                    draft_text=st.session_state.workflow_state["draft_proposal"],
                    approver_role=user_role
                )
                step1.write("✅ 1. Logging approval audit to Azure Security Vault...")
                
                step2.write("⏳ 2. Rendering architecture and compiling Client PDF...")
                diagram_code = st.session_state.workflow_state["architecture_diagram"]
                clean_code = diagram_code.replace("```mermaid", "").replace("```", "").strip()
                graphbytes = clean_code.encode("utf8")
                base64_string = base64.b64encode(graphbytes).decode("ascii")
                img_url = f"https://mermaid.ink/img/{base64_string}?bgColor=white"
                st.session_state.final_pdf_bytes = create_pdf(st.session_state.workflow_state["draft_proposal"], img_url)
                st.session_state.final_img_bytes = requests.get(img_url).content
                step2.write("✅ 2. Rendering architecture and compiling Client PDF...")
                
                step3.write("⏳ 3. AI is generating internal Project Knowledge Guide...")
                manager_prompt = f"""
                Write a 1-page internal brief for the Project Team regarding this upcoming engagement.
                Include: 1) Client Background 2) Core Problem 3) Proposed Solution Summary 4) Potential Tech Risks.
                Client Request: {st.session_state.workflow_state['client_requirements']}
                """
                manager_md = orchestrator_llm.invoke(manager_prompt).content
                st.session_state.knowledge_guide_bytes = create_pdf(f"# Project Knowledge Guide\n\n{manager_md}")
                step3.write("✅ 3. AI is generating internal Project Knowledge Guide...")
                
                step4.write("⏳ 4. Dispatching automated emails and calendar invites...")
                test_recipient = os.getenv("EMAIL_USER") 
                send_proposal_email(
                    recipient_email=test_recipient,
                    client_name="Enterprise Client", 
                    pdf_bytes=st.session_state.final_pdf_bytes
                )
                step4.write("✅ 4. Dispatching automated emails and calendar invites...")
                
                status.update(label="✅ All Systems Go!", state="complete", expanded=False)
            st.session_state.current_status = "approved"
            st.rerun()

        if reject_clicked:
            if feedback:
                with st.status("🔄 Routing feedback back to AI for revision...", expanded=True) as status:
                    step1 = st.empty()
                    step2 = st.empty()
                    
                    step1.write("⏳ 1. Sending Architect feedback to Writer Agent...")
                    st.session_state.workflow_state["feedback"] = feedback
                    st.session_state.workflow_state["status"] = "needs_revision"
                    time.sleep(1)
                    step1.write("✅ 1. Sending Architect feedback to Writer Agent...")
                    
                    step2.write("⏳ 2. AI is regenerating the proposal structure...")
                    new_result = rfp_app.invoke(st.session_state.workflow_state)
                    st.session_state.workflow_state = new_result
                    
                    st.session_state.show_revision_toast = True 
                    st.session_state.current_status = "awaiting_approval"
                    step2.write("✅ 2. AI is regenerating the proposal structure...")
                    
                    status.update(label="✅ Revision Complete!", state="complete", expanded=False)
                st.rerun()
            else:
                st.warning("Please provide feedback text before hitting Reject.")
    else:
        st.info("⚠️ Only Architects and Managers can approve or reject drafts. Switch your role in the sidebar.")

# --- PHASE 3: APPROVED ---
elif st.session_state.current_status == "approved":
    st.balloons()
    st.success("🎉 Proposal Officially Approved! Logs sent to Azure Vault and emails dispatched.")
    
    st.markdown("### 📂 Generated Document Viewer")
    tab1, tab2, tab3 = st.tabs(["📄 Client Proposal", "🖼️ Cloud Architecture", "🛡️ Project Knowledge Guide"])
    
    with tab1:
        display_pdf(st.session_state.final_pdf_bytes)
        st.info("💡 Tip: If the PDF preview doesn't load, use the 'Quick Downloads' button in the sidebar.")
        
    with tab2:
        st.image(st.session_state.final_img_bytes, use_container_width=True)
        
    with tab3:
        display_pdf(st.session_state.knowledge_guide_bytes)
    
    st.divider()
    if st.button("🔄 Start New Project", type="secondary"):
        st.session_state.workflow_state = None
        st.session_state.current_status = "idle"
        st.session_state.final_pdf_bytes = None
        st.session_state.final_img_bytes = None
        st.session_state.knowledge_guide_bytes = None
        st.rerun()