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
I2. nstall dependencies:


pip install -r requirements.txt

Configure Environment Variables: Create a .env file with your keys for Groq, Pinecone, and Neon.

3.Run the App:

streamlit run app.py