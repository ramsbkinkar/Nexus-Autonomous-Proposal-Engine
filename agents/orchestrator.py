import os
from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from agents.tools import search_past_projects, search_live_web


# Import the tool we just tested!
from agents.tools import search_past_projects

load_dotenv()

# 1. Define the LangGraph State (The "Memory" that passes between agents)
class RFPState(TypedDict):
    client_requirements: str
    research_context: str
    draft_proposal: str
    architecture_diagram: str  # <--- ADD THIS LINE
    feedback: str
    revision_count: int
    status: str

# 2. Initialize our Two Models (Multi-Model Flex!)
print("Initializing Models...")
orchestrator_llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_ORCHESTRATOR"), # gpt-4o-mini
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.2
)

writer_llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_WRITER"), # gpt-4o
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.7 # Slightly higher creativity for writing
)

# 3. Define the AI Nodes (The Workers)
def research_node(state: RFPState):
    print("\n-> [Agent 1: Researcher] Analyzing requirements & gathering data...")
    
    # --- TASK 1: INTERNAL RAG SEARCH ---
    
    rag_prompt = f"""
    Extract 3-4 search keywords from these client requirements to find relevant past IT case studies. 
    CRITICAL INSTRUCTION 1: You MUST include the client's specific industry (e.g., 'Logistics', 'Healthcare', 'Finance') as one of the key search terms.
    CRITICAL INSTRUCTION 2: Return ONLY a comma-separated list of keywords. Do not include any introductory text, numbers, or bullet points.
    Client Requirements: {state['client_requirements']}
    """
    rag_keywords = orchestrator_llm.invoke(rag_prompt).content
    print(f"   RAG Keywords: {rag_keywords}")
    rag_results = search_past_projects.invoke(rag_keywords)

    # --- TASK 2: LIVE WEB SEARCH ---
    web_prompt = f"""
    Extract ONLY the name of the client's company from these requirements. 
    If no specific company name is found, reply with the exact word 'NONE'.
    Client Requirements: {state['client_requirements']}
    """
    company_name = orchestrator_llm.invoke(web_prompt).content.strip()
    
    web_results = "No live web data required."
    if company_name != "NONE" and "NONE" not in company_name.upper():
        print(f"   Company Identified: {company_name}. Querying Bing...")
        web_query = f"{company_name} recent company news or current strategic goals"
        web_results = search_live_web.invoke(web_query)

    # --- TASK 3: COMBINE DATA ---
    combined_context = f"--- PAST INTERNAL CASE STUDIES ---\n{rag_results}\n\n--- LIVE COMPANY NEWS (BING API) ---\n{web_results}"
    print("\n" + "="*40)
    print(f"🔍 [DEBUG] RAG DB FOUND:\n{rag_results[:300]}...\n")
    print(f"🌍 [DEBUG] DUCKDUCKGO FOUND:\n{web_results[:300]}...")
    print("="*40 + "\n")
    
    return {"research_context": combined_context, "status": "research_done"}

def drafting_node(state: RFPState):
    print("-> [Agent 2: Writer] Drafting the Enterprise Proposal...")
    sys_msg = SystemMessage(content="You are an elite Enterprise Cloud Architect and Proposal Writer for a top-tier consulting firm.")
    
    prompt_text = f"""
    Write a professional, compelling 2-page project proposal based on the following:
    
    CLIENT REQUIREMENTS:
    {state['client_requirements']}
    
    OUR PAST CASE STUDIES:
    {state['research_context']}
    
    MANAGER FEEDBACK TO INCORPORATE (If any):
    {state.get('feedback', 'None')}
    
    CRITICAL RULES:
    1. You MUST explicitly cite the exact 'ROI & Impact' metrics and 'Total Project Cost' from the provided case studies to prove our past success. 
    2. Do NOT invent or hallucinate implementation timelines. If a timeline is not provided, estimate a realistic one based strictly on the technical scope.
    3. Format the output strictly in beautiful Markdown. Include a bolded 'Proposed Architecture' section and an 'Estimated Cost & Timeline' section.
    4. At the very end of your response, you MUST include a Mermaid.js flowchart mapping out the proposed cloud architecture. Enclose the Mermaid code strictly inside a ```mermaid``` markdown block.
    5. You MUST incorporate any 'LIVE COMPANY NEWS' provided into the opening introduction paragraph to prove to the client that we understand their current business trajectory.
    6. DO NOT wrap your entire response in a markdown code block (e.g., ```markdown). Output standard text only.
    7. Under the 'Proposed Architecture' section, you MUST write a full, detailed paragraph explaining the architecture. DO NOT leave it blank.
    7. CRITICAL: DO NOT include a 'Proposed Architecture Flowchart' or 'Diagram' heading at the end of the document. The system will attach the diagram automatically. End your document immediately after the Conclusion.
    """
    
    draft = writer_llm.invoke([sys_msg, HumanMessage(content=prompt_text)]).content
    new_count = state.get("revision_count", 0) + 1
    
    # Extract Mermaid code if it exists
    diagram_code = ""
    if "```mermaid" in draft:
        parts = draft.split("```mermaid")
        proposal_text = parts[0].strip()
        # Grab everything inside the mermaid block
        diagram_code = parts[1].split("```")[0].strip()
    else:
        proposal_text = draft
    
    return {
        "draft_proposal": proposal_text, 
        "architecture_diagram": diagram_code, # <--- Pass it to the state
        "status": "awaiting_approval", 
        "revision_count": new_count
    }

def review_router(state: RFPState):
    # This acts as our Human-in-the-loop pause.
    if state["status"] == "awaiting_approval":
        return END
    elif state["status"] == "needs_revision":
        return "drafting_node"
    return END

# 4. Build the LangGraph Workflow
print("Building the Agentic Graph...")
workflow = StateGraph(RFPState)

workflow.add_node("research_node", research_node)
workflow.add_node("drafting_node", drafting_node)

workflow.set_entry_point("research_node")
workflow.add_edge("research_node", "drafting_node")
workflow.add_conditional_edges("drafting_node", review_router)

rfp_app = workflow.compile()

# 5. Terminal Test Block
if __name__ == "__main__":
    print("\n--- INITIATING LANGGRAPH TEST ---")
    
    # A dummy client request
    dummy_request = "We are a mid-sized corporate law firm. We need a secure AI system to help our paralegals search through 10,000 old PDF case files quickly. We want to use Azure and need it to be highly accurate to avoid legal hallucinations."
    
    test_state = {
        "client_requirements": dummy_request,
        "research_context": "",
        "draft_proposal": "",
        "feedback": "",
        "revision_count": 0,
        "status": "start"
    }
    
    # Run the graph!
    result = rfp_app.invoke(test_state)
    
    print("\n\n" + "="*50)
    print("=== FINAL DRAFT PROPOSAL GENERATED ===")
    print("="*50 + "\n")
    print(result["draft_proposal"])