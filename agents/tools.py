import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch
from duckduckgo_search import DDGS


# Load our API keys
load_dotenv()

# 1. Reconnect to the Embedding Model
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_EMBEDDING"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

# 2. Reconnect to the Azure AI Search Free Tier
vector_store = AzureSearch(
    azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    azure_search_key=os.getenv("AZURE_SEARCH_ADMIN_KEY"),
    index_name="rfp-case-studies",
    embedding_function=embeddings.embed_query,
)

# 3. Define the Tool for the AI Agent
@tool
def search_past_projects(query: str) -> str:
    """
    Use this tool to search the company's internal database for past case studies and projects.
    Input should be a search query describing the client's industry or technical problem.
    """
    print(f"\n[Tool Execution] Searching RAG database for: '{query}'...")
    
    # Fetch the top 3 most relevant case studies
    docs = vector_store.similarity_search(query, k=3)
    
    if not docs:
        return "No relevant past projects found in the database."
    
    results = []
    for i, doc in enumerate(docs):
        results.append(f"--- Past Project {i+1} ---\n{doc.page_content}\n")
    
    return "\n".join(results)

# 4. Define the Live Web Search Tool (Native DDGS)
@tool
def search_live_web(query: str) -> str:
    """
    Use this tool to search the live internet for current events, 
    company news, or strategic goals to personalize proposals.
    """
    print(f"\n[Tool Execution] Searching Live Web for: '{query}'...")
    try:
        results_text = []
        # Talk directly to DuckDuckGo, pulling the top 3 results
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=3)
            for r in results:
                results_text.append(r.get('body', ''))
                
        final_text = " ".join(results_text)
        return final_text if final_text else "No recent news found."
    except Exception as e:
        return f"Web search failed. Error: {e}"

# A simple test block so we can run this file directly to check if it works
if __name__ == "__main__":
    print("Testing the RAG Tool...")
    # Let's test it with a dummy query matching the LegalTech case study you showed me earlier
    test_output = search_past_projects.invoke("law firm document retrieval")
    print("\n--- TEST RESULTS ---")
    print(test_output)