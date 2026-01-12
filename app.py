import streamlit as st
import os
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

# Load Credentials
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="NexusQuery AI", layout="wide", page_icon="🌐")

# --- UI Styling (Fixes Invisible Text) ---
st.markdown("""
    <style>
    .stTextInput input {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 2px solid #4A90E2 !important;
    }
    .stTextInput input::placeholder { color: #666666 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Resource Loading ---
@st.cache_resource
def init_connections():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"), 
        embedding=embeddings
    )
    llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"))
    engine = create_engine(os.getenv("DATABASE_URL"))
    return vectorstore, llm, engine

vectorstore, llm, engine = init_connections()

# --- Sidebar ---
with st.sidebar:
    st.title("🛠️ NexusQuery Control")
    st.success("✅ Connected to Cloud DB")
    show_sql = st.checkbox("Show AI-Generated SQL", value=True)
    if st.button("🔄 Clear Cache"):
        st.cache_resource.clear()
        st.rerun()

# --- Main App Interface ---
st.title("🌐 Talk2DB: Scalable Relational Agent")
st.write("This agent automatically discovers tables and performs JOINS using RAG.")

user_query = st.text_input(label="Enter your business question:", key="main_query_input")

if user_query:
    with st.spinner("🔍 Discovering relevant tables and generating SQL..."):
        try:
            # 1. TABLE DISCOVERY (Scaling Logic)
            # We search Pinecone for the top 3 most relevant table schemas
            docs = vectorstore.similarity_search(user_query, k=3)
            schema_context = "\n".join([d.page_content for d in docs])

            # 2. RELATIONAL SQL GENERATION
            prompt = f"""
            System: You are a professional PostgreSQL Expert. Use the dynamically discovered schema below to generate a precise SQL query.

            ### Discovered Schema (Source of Truth):
            {schema_context}

            ### Strict Generation Rules:
            1. **Table Aliasing**: ALWAYS use short aliases for tables (e.g., 's' for sales_table, 'c' for customers_table).
            2. **Explicit Column Scoping**: Prefix EVERY column in the SELECT, JOIN, and WHERE clauses with its table alias (e.g., `s.region`, `c.loyalty_segment`) to avoid "UndefinedColumn" errors.
            3. **Relational Joins**: If the question requires data from multiple tables, use an INNER JOIN on the common key (usually 'customer_name').
            4. **Data Type Integrity**: 
            - 'status_id' is BIGINT. Use numeric values: 1 for 'active', 4 for 'churned'.
            - NEVER compare 'status_id' to string literals.
            5. **Output**: Return ONLY the SQL code inside ```sql blocks. No explanation.

            ### Example Mapping:
            - Question: "Active revenue by VIPs in North"
            - SQL: SELECT s.region, SUM(s.amt) FROM sales_table s JOIN customers_table c ON s.customer_name = c.customer_name WHERE s.status_id = 1 AND c.loyalty_segment = 'VIP' AND s.region = 'North' GROUP BY s.region;

            Question: {user_query}
            SQL:
            """
            response = llm.invoke(prompt)
            sql_raw = response.content.split("```sql")[1].split("```")[0].strip()

            # 3. Execution
            with engine.connect() as conn:
                df = pd.read_sql(sql_raw, conn)

            # 4. Results & Visualization
            if not df.empty:
                col_data, col_viz = st.columns([1, 1])
                with col_data:
                    st.subheader("📋 Data Preview")
                    st.dataframe(df, use_container_width=True)
                    if show_sql: st.code(sql_raw, language="sql")

                with col_viz:
                    st.subheader("📈 AI Visualization")
                    nums = df.select_dtypes(include=['number']).columns
                    cats = df.select_dtypes(include=['object', 'datetime']).columns
                    if len(nums) > 0 and len(cats) > 0:
                        fig = px.bar(df, x=cats[0], y=nums[0], color=cats[0], template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Direct data value returned.")
            else:
                st.warning("No results found.")

        except Exception as e:
            st.error(f"Error: {e}")