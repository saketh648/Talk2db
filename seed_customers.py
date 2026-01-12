import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def seed_customers():
    # 1. Create Sample Customer Data
    # These names MUST match some names in your 'sales_table' for the JOIN to work
    n_customers = 24
    data = {
        'customer_name': [f"Customer_{i}" for i in range(1, n_customers + 1)],
        'loyalty_segment': ['VIP', 'Regular', 'New', 'VIP', 'Regular', 'VIP'] * 4,
        'plan_type': ['Gold', 'Silver', 'Platinum', 'Gold', 'Silver', 'Bronze'] * 4
    }
    df = pd.DataFrame(data)

    # 2. Connect to Neon
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    # 3. Upload to Cloud
    print("🚀 Creating 'customers_table' in Neon Cloud...")
    df.to_sql('customers_table', engine, if_exists='replace', index=False)
    print("✅ Successfully seeded customers_table!")

if __name__ == "__main__":
    seed_customers()