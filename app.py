import streamlit as st
import os
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
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
    /* Fixes input text and background */
    .stTextInput input {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 2px solid #4A90E2 !important;
        caret-color: #4A90E2 !important; /* Forces cursor to be visible */
    }
    .stTextInput input::placeholder { color: #666666 !important; }
    
    /* Adds focus effect to the input box */
    .stTextInput>div>div>input:focus {
        border-color: #4A90E2 !important;
        box-shadow: 0 0 0 0.1rem rgba(74, 144, 226, 0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Resource Loading with Connection Check ---
@st.cache_resource
def init_connections():
    try:
        # 1. Initialize AI Services
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME"), 
            embedding=embeddings
        )
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"))
        
        # 2. Initialize Database and Test Connection
        db_url = os.getenv("DATABASE_URL")
        engine = create_engine(db_url)
        
        # Test the connection and get DB name
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Extract database name from the URL
            db_name = engine.url.database
            
        return vectorstore, llm, engine, db_name, True
    except Exception as e:
        # Return status False and the error message
        return None, None, None, str(e), False

# Initialize backend
vectorstore, llm, engine, db_info, is_connected = init_connections()

# --- Sidebar ---
with st.sidebar:
    st.title("🛠️ NexusQuery Control")
    
    if is_connected:
        st.success(f"✅ Connected to: **{db_info}**")
    else:
        st.error("❌ Connection to DB failed")
        st.warning(f"Error: {db_info}")
        st.info("Ensure your DATABASE_URL is correct in your .env file.")
    
    st.divider()
    show_sql = st.checkbox("Show AI-Generated SQL", value=True)
    if st.button("🔄 Clear Cache"):
        st.cache_resource.clear()
        st.rerun()

# --- Main App Interface ---
st.title("🌐 Talk2DB: Scalable Relational Agent")
st.write("This agent automatically discovers tables and performs JOINS using RAG.")

# Only allow queries if connected
if not is_connected:
    st.stop()

# --- NEW: Form-based Query Input ---
with st.form("query_form", border=False):
    # Split into columns to put the button next to the input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_query = st.text_input(
            label="Enter your business question:", 
            placeholder="e.g., Show me the top 5 shipping methods by cost for churned users",
            label_visibility="collapsed",
            key="main_query_input"
        )
    
    with col2:
        # This button triggers the execution
        submit_button = st.form_submit_button("🚀 Run Query", use_container_width=True)

# Trigger logic only when button is clicked or Enter is pressed inside the form
if submit_button and user_query:
    max_retries = 2
    attempt = 0
    success = False
    error_feedback = ""
    sql_raw = ""

    # Start the Self-Correction Loop
    while attempt < max_retries and not success:
        with st.spinner(f"🔍 {'Attempt 2: Refining and Retrying...' if attempt > 0 else 'Generating SQL...'}"):
            try:
                # 1. Broaden Retrieval on Retry
                # If we failed once, pull 5 tables instead of 3 to provide more context
                current_k = 3 if attempt == 0 else 5
                docs = vectorstore.similarity_search(user_query, k=current_k)
                schema_context = "\n".join([d.page_content for d in docs])

                # 2. Build the "Aware" Prompt
                # We add the previous error message as a 'hint' to the AI
                retry_hint = ""
                if attempt > 0:
                    retry_hint = f"\n⚠️ FIX THIS ERROR: Your previous query failed with: {error_feedback}. Please re-check table aliases and column locations."
           # 2. RELATIONAL SQL GENERATION
                prompt = f"""
                System: You are a professional PostgreSQL Expert. Generate a SQL query using ONLY the schema context provided below.

                ### Discovered Schema (Source of Truth):
                {schema_context}

                ### Strict Generation Rules:
                1. **Dynamic Aliasing**: Assign a short alias (e.g., t1, t2) to every table identified in the Schema above.
                2. **Explicit Column Scoping**: Prefix EVERY column in the SELECT, JOIN, and WHERE clauses with its assigned table alias to prevent "UndefinedColumn" errors.
                3. **Multi-Table Joins**: If the user query requires data from multiple tables, perform an INNER JOIN on the common key (usually 'customer_name' or 'customer_id').
                4. **Business Logic Mapping**: 
                - If 'status_id' is used: It is a BIGINT. Use 1 for 'active' and 4 for 'churned'.
                - NEVER compare 'status_id' to strings.
                5. **Schema Adherence**: Only use columns explicitly listed in the Context above. If a column like 'status_id' is only listed under Table A, do not look for it in Table B.
                6. **Output**: Return ONLY the SQL code inside ```sql blocks.
                7. **Aggregation Requirement**: When asked for 'top methods', 'categories', or 'rankings', ALWAYS use SUM() or COUNT() with a GROUP BY clause. Do not return individual rows."

                ### Example Logic:
                - User asks for 'Active' data: Use WHERE alias.status_id = 1
                - User asks for 'Churned' data: Use WHERE alias.status_id = 4

                Question: {user_query}
                SQL:
                """


                
                response = llm.invoke(prompt)
                sql_raw = response.content.split("```sql")[1].split("```")[0].strip()

                # 3. Secure Execution
                with engine.connect() as conn:
                    # Use a transaction block to ensure auto-rollback on error
                    with conn.begin():
                        df = pd.read_sql(text(sql_raw), conn)
                        success = True # If it runs, we exit the loop

            except Exception as e:
                attempt += 1
                error_feedback = str(e)
                # Important: Reset the connection state if it crashes
                with engine.connect() as conn:
                    conn.execute(text("ROLLBACK"))
                
                if attempt == max_retries:
                    st.error(f"❌ Failed after {max_retries} attempts.")
                    st.warning(f"Last Error: {error_feedback}")

    # 4. Results & Visualization (Outside the loop)
    if success and not df.empty:
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