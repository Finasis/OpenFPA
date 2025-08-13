import pandas as pd
from sqlalchemy import create_engine, text

# DB credentials
user = "root"
password = "your_password"
host = "localhost"
port = 5432
database = "openfpa_db"

db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(db_url)

# Load ODS Data
ods_file = 'excel_templates/OpenFPA_Input_Template.ods'
revenues_df = pd.read_excel(ods_file, sheet_name='Revenues', engine='odf')
costs_df = pd.read_excel(ods_file, sheet_name='Costs', engine='odf')
kpis_df = pd.read_excel(ods_file, sheet_name='KPIs', engine='odf')

with engine.connect() as conn:
    with conn.begin():  # transaction

        # Insert Revenues
        for _, row in revenues_df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO revenues (date, customer, revenue_amount)
                    VALUES (:date, :customer, :revenue_amount)
                """),
                {
                    "date": row['Date'],
                    "customer": row['Customer'],
                    "revenue_amount": row['Revenue_Amount']
                }
            )

        # Insert Costs
        for _, row in costs_df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO costs (date, cost_type, cost_amount)
                    VALUES (:date, :cost_type, :cost_amount)
                """),
                {
                    "date": row['Date'],
                    "cost_type": row['Cost_Type'],
                    "cost_amount": row['Cost_Amount']
                }
            )

        # Insert KPIs
        for _, row in kpis_df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO kpis (kpi_name, target_value, actual_value)
                    VALUES (:kpi_name, :target_value, :actual_value)
                """),
                {
                    "kpi_name": row['KPI_Name'],
                    "target_value": row['Target_Value'],
                    "actual_value": row['Actual_Value']
                }
            )

print("Data successfully imported into PostgreSQL database!")

