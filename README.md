# ⚡ Nexus: Autonomous Enterprise Proposal Engine

An enterprise-grade, multi-agent AI pipeline built to compress the traditional 3-week RFP (Request for Proposal) response process into 45 seconds. 

Nexus utilizes a LangGraph-powered AI architecture to autonomously research client backgrounds, query internal capability databases (RAG), and draft highly technical cloud architecture proposals with human-in-the-loop security auditing.

## 🧠 System Architecture

This application simulates a fully autonomous enterprise sales and engineering workflow:

1. **Client Ingestion:** Accepts raw, unstructured RFP text or client requirements.
2. **Agent 1 (The Researcher):** Connects to the live internet (DuckDuckGo Search) to pull real-time client context and queries an **Azure AI Search** Vector Database to retrieve past company case studies.
3. **Agent 2 (The Solutions Architect):** Synthesizes the research and drafts a comprehensive, highly technical proposal, including generating a dynamic Mermaid.js architecture diagram.
4. **Human-in-the-Loop (Approval Gate):** A simulated Cloud Architect reviews the draft. If rejected, the feedback is dynamically routed back to the AI for iterative revision.
5. **Azure Security Auditing:** Upon approval, the action is logged permanently to a secure **Microsoft Azure Key Vault** for compliance.
6. **Artifact Compilation:** The system compiles a branded Client PDF, renders the architecture diagram, generates an internal Project Knowledge Guide, and automatically dispatches calendar invites and emails.

## 🛠️ Tech Stack
* **Framework:** Streamlit
* **AI Orchestration:** LangChain & LangGraph (Multi-Agent framework)
* **LLM:** OpenAI (GPT-4o / GPT-3.5)
* **Vector Database (RAG):** Azure AI Search
* **Security & Audit:** Azure Key Vault & Azure Identity
* **Live Web Search:** DuckDuckGo Search API
* **Document Generation:** `xhtml2pdf`, Markdown
* **Email Automation:** SMTP (`smtplib`)

## 🚀 Live Demo
[Insert your Streamlit Cloud URL here]

> **Note on Sandbox Preview:** Depending on browser security policies, the native PDF preview may be sandboxed. You can view the raw markdown directly in the UI or use the "Quick Downloads" sidebar to view the compiled artifacts.

## 💡 Quick Start Prompt
Want to test the live demo? Copy and paste this prompt into Step 1:
> *"We are Netflix. We are experiencing high latency in our video streaming telemetry data across the US East region. We need a highly scalable, real-time cloud architecture to ingest, process, and visualize millions of concurrent user events. We prefer an AWS-based solution."*
