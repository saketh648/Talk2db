import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def seed_shipping():
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    # Create sample shipping data
    shipping_data = {
        'customer_name': [f"Customer_{i}" for i in range(1, 25)],
        'shipping_method': ['Express', 'Standard', 'Overnight', 'Standard'] * 6,
        'cost': [25.0, 10.0, 50.0, 12.0] * 6,
        'days_to_deliver': [1, 5, 1, 4] * 6
    }
    df = pd.DataFrame(shipping_data)
    
    print("🚀 Uploading 'shipping_table' to Neon...")
    df.to_sql('shipping_table', engine, if_exists='replace', index=False)
    print("✅ Success! The database is now ready for the shipping query.")

if __name__ == "__main__":
    seed_shipping()