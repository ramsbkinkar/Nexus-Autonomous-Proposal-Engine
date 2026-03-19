import os
import pandas as pd
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()

def log_approval_to_azure(client_req, draft_text, approver_role):
    print("Initiating Azure Blob upload...")
    
    # 1. Connect to Azure Storage
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = "rfp-logs"
    blob_name = "Enterprise_Audit_Log.xlsx"
    
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    
    # 2. Extract a rough cost estimate from the text (Simple fallback search)
    # We look for the dollar sign in the text to grab the cost
    cost_estimate = "Unknown"
    if "$" in draft_text:
        parts = draft_text.split("$")
        if len(parts) > 1:
            cost_estimate = "$" + parts[1].split()[0].strip() # Grabs the first number after $
            
    # 3. Create the New Row Data
    new_data = {
        "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Client Snippet": [client_req[:50] + "..."],
        "Approver Role": [approver_role],
        "Estimated Cost": [cost_estimate],
        "System Status": ["Approved - Email Pending"]
    }
    df_new = pd.DataFrame(new_data)
    
    # 4. Download existing Excel file OR create a new one if it's the first time
    try:
        download_stream = blob_client.download_blob().readall()
        df_existing = pd.read_excel(BytesIO(download_stream))
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        print("Existing log found. Appending data...")
    except Exception as e:
        print("No existing log found. Creating new master log...")
        df_combined = df_new

    # 5. Convert back to Excel format in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_combined.to_excel(writer, index=False, sheet_name="Audit Log")
    
    # 6. Upload and Overwrite the Blob in Azure
    output.seek(0)
    blob_client.upload_blob(output, overwrite=True)
    print("SUCCESS: Audit Log securely updated in Azure Blob Storage.")
    return True