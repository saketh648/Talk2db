import streamlit as st
import os
import pandas as pd
import numpy as np
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

# --- UI Styling ---
st.markdown("""
    <style>
    /* 1. Target the input field specifically */
    .stTextInput input {
        color: #000000 !important;      /* Solid black text */
        background-color: #FFFFFF !important; /* Solid white background */
        border: 2px solid #4A90E2 !important; /* Clear blue border */
        
        /* THE CRITICAL FIX: Forces a visible blinking cursor */
        caret-color: #4A90E2 !important; 
    }

    /* 2. Ensure placeholder text is also visible */
    .stTextInput input::placeholder {
        color: #888888 !important; /* Medium grey for placeholder */
    }

    /* 3. Highlight the input box when you click/focus on it */
    .stTextInput>div>div>input:focus {
        border-color: #0056b3 !important; /* Darker blue on focus */
        box-shadow: 0 0 5px rgba(0, 86, 179, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_connections():
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = PineconeVectorStore(
            index_name=os.getenv("PINECONE_INDEX_NAME"), 
            embedding=embeddings
        )
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"))
        db_url = os.getenv("DATABASE_URL")
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_name = engine.url.database
        return vectorstore, llm, engine, db_name, True
    except Exception as e:
        return None, None, None, str(e), False

vectorstore, llm, engine, db_info, is_connected = init_connections()

# --- Sidebar ---
with st.sidebar:
    st.title("🛠️ NexusQuery Control")
    if is_connected:
        st.success(f"✅ Connected to: **{db_info}**")
    else:
        st.error("❌ Connection to DB failed")
    st.divider()
    show_sql = st.checkbox("Show AI-Generated SQL", value=True)
    if st.button("🔄 Clear Cache"):
        st.cache_resource.clear()
        st.rerun()

st.title("🌐 Talk2DB: Scalable Relational Agent")

if not is_connected:
    st.stop()

with st.form("query_form", border=False):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_query = st.text_input(label="Enter your business question:", placeholder="e.g., Show churned users", label_visibility="collapsed")
    with col2:
        submit_button = st.form_submit_button("🚀 Run Query", use_container_width=True)

if submit_button and user_query:
    # 1. VIZ DETECTION & QUERY CLEANING
    query_lower = user_query.lower()
    viz_type = "pie" if "pie" in query_lower else "line" if "line" in query_lower else "bar"
    
    # 2. AGENTIC DISCOVERY & EXECUTION LOOP
    attempt, max_retries = 0, 2
    success = False
    error_feedback, sql_raw = "", ""

    while attempt < max_retries and not success:
        with st.spinner(f"🔍 {'Attempt 2: Refining...' if attempt > 0 else 'Generating SQL...'}"):
            try:
                # STEP A: DYNAMIC DISCOVERY
                current_k = 4 if attempt == 0 else 8
                docs = vectorstore.similarity_search(user_query, k=current_k)
                schema_context = "\n".join([d.page_content for d in docs])

                # STEP B: RELATIONAL SQL GENERATION
                prompt = f"""
                System: You are a professional PostgreSQL Expert. Generate a SQL query using ONLY the schema context below.

                ### Discovered Schema:
                {schema_context}
                ### Mandatory Workflow:
                1. **Pre-check tables needed**: Dont hallucinate columns will be this specific table, columns can be in any table for example customer name cant be in customer table maybe in sales table so dont hallucinate check discovered schema or vector db and act.
                2. **Strict Adherence**: If 'status_id' is only in 'sales_table', do NOT list 'customers_table' as a requirement.
                3. **SQL Generation**: Write the SQL using ONLY the tables you listed in Step 1.
                ### GENERIC EXECUTION PROTOCOL (Mandatory):
                1. **Column Ownership Check**: For every column needed in your 'WHERE' or 'SELECT' clauses, you MUST find its parent table in the 'Discovered Schema' provided above.
                2. **Path of Least Resistance**: 
                - Identify the table that contains the MOST columns required for this query. 
                - If one table contains both the target data (e.g., names) and the filter (e.g., status_id), use ONLY that table. 
                - Do NOT perform a JOIN if a single table can satisfy the query.
                3. **No Hallucinated Columns**: If a column name is not explicitly listed under a table in the 'Discovered Schema', that table DOES NOT have that column.

                ### Strict Generation Rules:
                1. **Efficiency First**: If all columns (like 'status_id') exist in one table, do NOT perform a JOIN.
                2. **Dynamic Aliasing**: Assign a short alias (e.g., t1, t2) to every table.
                3. **Explicit Column Scoping**: Prefix EVERY column (e.g., t1.status_id) to prevent UndefinedColumn errors.
                5. **Aggregation**: Use SUM() or COUNT() with GROUP BY for rankings/top lists.
                6. **Output**: Return ONLY the SQL code inside ```sql blocks.

                {f"⚠️ FIX ERROR: {error_feedback}" if attempt > 0 else ""}
                Question: {user_query}
                SQL:
                """

                response = llm.invoke(prompt)
                sql_raw = response.content.split("```sql")[1].split("```")[0].strip()

                # STEP C: SECURE EXECUTION
                with engine.connect() as conn:
                    df = pd.read_sql(text(sql_raw), conn)
                    # JSON Safety: Replace NaN/Inf for Charting
                    df = df.replace([np.inf, -np.inf], np.nan).where(pd.notnull(df), None)
                    success = True

            except Exception as e:
                attempt += 1
                error_feedback = str(e)
                if attempt == max_retries:
                    st.error(f"❌ Failed after {max_retries} attempts.")
                    st.warning(f"Last Error: {error_feedback}")

    # 3. RESULTS & VISUALIZATION
    if success and not df.empty:
        col_data, col_viz = st.columns([1, 1])
        with col_data:
            st.subheader("📋 Results")
            st.dataframe(df, use_container_width=True)
            if show_sql: st.code(sql_raw, language="sql")
        with col_viz:
            st.subheader(f"📈 {viz_type.title()} Chart")
            nums = df.select_dtypes(include=['number']).columns
            cats = df.select_dtypes(include=['object', 'datetime']).columns
            if len(nums) > 0 and len(cats) > 0:
                if viz_type == "pie": fig = px.pie(df, names=cats[0], values=nums[0])
                elif viz_type == "line": fig = px.line(df, x=cats[0], y=nums[0])
                else: fig = px.bar(df, x=cats[0], y=nums[0], color=cats[0])
                st.plotly_chart(fig, use_container_width=True)