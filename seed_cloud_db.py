import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def seed_database():
    # 1. Generate Sample Data
    np.random.seed(42)
    n_rows = 100
    data = {
        'transaction_id': range(1, n_rows + 1),
        'date': pd.date_range(start='2025-01-01', periods=n_rows, freq='D'),
        'customer_name': [f"Customer_{i}" for i in np.random.randint(1, 25, n_rows)],
        'product_category': np.random.choice(['Electronics', 'Furniture', 'Software', 'Apparel'], n_rows),
        'amt': np.random.uniform(100, 5000, n_rows).round(2),
        'status_id': np.random.choice([1, 1, 1, 4], n_rows), # 1=Active, 4=Churned
        'region': np.random.choice(['North', 'South', 'East', 'West'], n_rows)
    }
    df = pd.DataFrame(data)

    # 2. Connect to Neon Cloud
    # Ensure your .env has DATABASE_URL=postgresql://user:pass@host/neondb
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL not found in .env")
        return

    # Create SQLAlchemy engine
    engine = create_engine(db_url)

    # 3. Push to Cloud
    print("🚀 Uploading data to Neon Cloud...")
    df.to_sql('sales_table', engine, if_exists='replace', index=False)
    print("✅ Successfully seeded 'sales_table' in the cloud!")

if __name__ == "__main__":
    seed_database()