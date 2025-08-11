import pandas as pd
from sqlalchemy import create_engine

def print_table_data(table_name):
    # Replace these with your actual DB credentials
    user = "root"
    password = "your_password"
    host = "localhost"
    port = 5432
    database = "openfpa_db"

    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(db_url)

    try:
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, engine)
        print(f"\nData from table '{table_name}':")
        print(df)
    except Exception as e:
        print(f"Error fetching data from {table_name}: {e}")
    finally:
        engine.dispose()

# Usage example:
print_table_data("revenues")
print_table_data('costs')
print_table_data('kpis')
