
import pandas as pd
import mysql.connector

# Database connection parameters
db_config = {
    'user': 'root',
    'password': 'your_password',
    'host': 'localhost',
    'database': 'openfpa_db'
}

# Connect to MySQL Database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Load Excel Data
excel_file = 'excel_templates/OpenFPA_Input_Template.xlsx'
revenues_df = pd.read_excel(excel_file, sheet_name='Revenues')
costs_df = pd.read_excel(excel_file, sheet_name='Costs')
kpis_df = pd.read_excel(excel_file, sheet_name='KPIs')

# Insert Revenues
for _, row in revenues_df.iterrows():
    cursor.execute("""
        INSERT INTO revenues (date, customer, revenue_amount)
        VALUES (%s, %s, %s)
    """, (row['Date'], row['Customer'], row['Revenue_Amount']))

# Insert Costs
for _, row in costs_df.iterrows():
    cursor.execute("""
        INSERT INTO costs (date, cost_type, cost_amount)
        VALUES (%s, %s, %s)
    """, (row['Date'], row['Cost_Type'], row['Cost_Amount']))

# Insert KPIs
for _, row in kpis_df.iterrows():
    cursor.execute("""
        INSERT INTO kpis (kpi_name, target_value, actual_value)
        VALUES (%s, %s, %s)
    """, (row['KPI_Name'], row['Target_Value'], row['Actual_Value']))

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()

print("Data successfully imported into MySQL database!")
