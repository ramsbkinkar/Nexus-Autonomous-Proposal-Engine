import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch

# Load the keys from .env
load_dotenv()

print("1. Loading API Keys...")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
embedding_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_EMBEDDING")

# Initialize the Embedding Model
print("2. Initializing Embedding Model...")
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=embedding_deployment,
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=azure_endpoint,
    api_key=azure_api_key,
)

# Connect to Azure AI Search
print("3. Connecting to Azure AI Search...")
index_name = "rfp-case-studies"
vector_store = AzureSearch(
    azure_search_endpoint=search_endpoint,
    azure_search_key=search_key,
    index_name=index_name,
    embedding_function=embeddings.embed_query,
)

# Load the Dummy Case Studies
print("4. Loading and chunking documents...")
# This points to your newly moved data folder!
loader = DirectoryLoader('./data/dummy_case_studies/', glob="*.txt", loader_cls=TextLoader)
documents = loader.load()

# Chunk the text so the AI can digest it easily
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_documents(documents)

# Upload to Azure
print(f"5. Uploading {len(docs)} document chunks to Azure AI Search...")
vector_store.add_documents(documents=docs)
print("SUCCESS! RAG Database is ready.")