# 🌐 Talk2DB: Scalable Cloud SQL Agent

Talk2DB is an intelligent data assistant that translates natural language questions into executable PostgreSQL queries. Using a **RAG (Retrieval-Augmented Generation)** architecture, it dynamically discovers database schemas to perform complex multi-table JOINs and provides real-time data visualizations.

## 🚀 Key Features
* **Natural Language to SQL:** Query your database without writing a single line of code.
* **Autonomous Scaling:** Uses a metadata crawler to handle 100+ tables via Pinecone vector search.
* **Relational Intelligence:** Automatically performs INNER JOINs across Sales, Customer, and Shipping tables.
* **Cloud-Native:** Fully integrated with Neon PostgreSQL and Streamlit Community Cloud.

## 🛠️ Tech Stack
* **LLM:** Llama 3.3-70b (via Groq)
* **Vector Store:** Pinecone
* **Database:** Neon PostgreSQL
* **Frontend:** Streamlit
* **Framework:** LangChain & SQLAlchemy

## 📦 Installation & Setup
1. **Clone the repo:**
   ```bash
   git clone [https://github.com/your-username/talk2db.git](https://github.com/your-username/talk2db.git)
   cd talk2db
2. **Install dependencies:**


   pip install -r requirements.txt

3. **Configure Environment Variables: Create a .env file with your keys for Groq, Pinecone, and Neon.**
      GROQ_API_KEY=your_groq_api_key
      PINECONE_API_KEY=your_pinecone_api_key
      NEON_DATABASE_URL=postgresql://user:password@host/dbname

4. **Run the App:**
   streamlit run app.py

5. **📈 Future Improvements**
   🏗️ Metadata Crawler (Dynamic Schema Sync)
   Real-time Updates: Implement a crawler function using SQLAlchemy to fetch newly added tables or modified columns and update Pinecone embeddings automatically.

   Schema Evolution: Detect changes in data types or constraints to ensure the LLM always has the most accurate context.

   🛡️ Security & Guardrails
   Read-Only Enforcement: Add a validation layer to prevent any non-SELECT queries (e.g., DROP, DELETE, UPDATE) from being executed.

   SQL Sanitization: Use a parser to verify generated SQL structure before sending it to the database.

   📊 Enhanced Visualization
   Auto-Charting: Integrate Plotly to automatically select the best chart type (Bar, Line, Pie) based on the query result set.