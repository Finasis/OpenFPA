# 📊 OpenFP&A — Open-Source Financial Planning & Analysis Toolkit

**OpenFP&A** is an open-source toolkit designed to automate **Financial Planning & Analysis (FP&A)** workflows for **SMEs, consultants, and finance professionals**.

No expensive software. No SaaS lock-ins. Just transparent, modular tools you control — built for real-world business needs.

---

## ✨ Key Features
- Excel-based financial data input (Revenues, Costs, KPIs)
- Automated **MySQL database structure** for scalable data management
- Python-powered analysis reports (P&L Statements, KPI Dashboards)
- Modular roadmap: **Budgeting & Forecasting modules coming soon**
- Designed for **SMEs, Controllers, CFOs, Financial Consultants**

---

## 📂 Project Structure
| Folder                | Purpose                                                    |
|-----------------------|------------------------------------------------------------|
| `/docs`                | Documentation, guides, and user manuals                    |
| `/excel_templates`     | Excel input templates (Revenues, Costs, KPIs)               |
| `/sql_scripts`         | SQL scripts for database creation and data management      |
| `/python_scripts`      | Python scripts for automated analysis and reporting        |
| `/lookerstudio`        | Dashboard configurations for visualization (upcoming)      |
| `/budgeting_module`    | Budgeting tools (planned module)                           |
| `/forecasting_module`  | Forecasting models (planned module)                        |

---

## Dependencies
- python: pandas, sqlalchemy

---

## 🚀 How to Get Started
1. **Clone this repository**:
    ```bash
    git clone https://github.com/Finasis/OpenFPA.git
    cd OpenFPA

2. **Start postgres database**
    ```bash
    docker-compose up -d

    Check if database schema has been succesfully created
    ```bash
    sql_scripts/check-db.sh


3. **Import data**
    ```bash
    python3 python_scripts/import_excel_to_postgres.py

    Check if data from excel has been added
    ```bash
    python python_scripts/print_table_data.py

4. **Stop database**
    ```bash
    docker-compose down

    If you want to remove data
    ```bash
    docker-compose down -v

