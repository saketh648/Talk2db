# ingest.py
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# 1. Setup Embeddings (Free, runs on your CPU)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Define your "Semantic Knowledge"
# This tells the AI what columns actually mean.
metadata_chunks = [
    # --- Data Type & Value Mapping ---
    "The 'status_id' column is a BIGINT. Mapping: 'active'=1, 'churned'=4. NEVER use strings for this column.",
    "Revenue is always the SUM of the 'amt' column in 'sales_table'.",

    # --- Strict Table Definitions ---
    "Table 'sales_table' (NOT sales_data) contains: [transaction_id, date, customer_name, product_category, amt, status_id, region].",
    "Table 'customers_table' contains: [customer_name, loyalty_segment, plan_type].",
    "Table 'shipping_table' contains: [customer_name, shipping_method, cost, days_to_deliver].",

    # --- Relational Join Logic ---
    "JOIN KEY: All tables (sales_table, customers_table, shipping_table) link via the 'customer_name' column.",
    "RULE: When joining, always alias tables: sales_table as 's', customers_table as 'c', and shipping_table as 'sh'.",
    
    # --- Column Ownership (Prevents UndefinedColumn Errors) ---
    "The 'region' and 'amt' columns exist ONLY in 'sales_table'.",
    "The 'loyalty_segment' and 'plan_type' columns exist ONLY in 'customers_table'.",
    "The 'shipping_method' and 'cost' columns exist ONLY in 'shipping_table'.",

    # --- Business Segments ---
    "Premium users: customers_table.plan_type IN ('Gold', 'Platinum').",
    "VIP users: customers_table.loyalty_segment = 'VIP'."
]

# 3. Upload to Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME") # Replace with your Pinecone index name

vectorstore = PineconeVectorStore.from_texts(
    texts=metadata_chunks,
    embedding=embeddings,
    index_name=index_name
)

print("✅ Semantic Layer uploaded to Cloud Vector DB!")