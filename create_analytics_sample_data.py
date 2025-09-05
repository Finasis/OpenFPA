#!/usr/bin/env python3
"""
Create comprehensive sample data for analytics functionality
"""
import requests
import json
import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import random

BASE_URL = "http://localhost:8000/api/v1"

def get_company_id():
    """Get the first company ID"""
    response = requests.get(f"{BASE_URL}/companies")
    companies = response.json()
    if companies:
        return companies[0]['id']
    return None

def create_sample_transactions(company_id):
    """Create comprehensive sample transactions for analytics"""
    
    # Get GL accounts
    response = requests.get(f"{BASE_URL}/companies/{company_id}/gl-accounts")
    gl_accounts = response.json()
    
    # Get fiscal periods  
    response = requests.get(f"{BASE_URL}/companies/{company_id}/fiscal-periods")
    fiscal_periods = response.json()
    
    # Get scenarios
    response = requests.get(f"{BASE_URL}/companies/{company_id}/scenarios")
    scenarios = response.json()
    
    # Get cost centers
    response = requests.get(f"{BASE_URL}/companies/{company_id}/cost-centers")
    cost_centers = response.json()
    
    print(f"Found {len(gl_accounts)} GL accounts, {len(fiscal_periods)} fiscal periods, {len(scenarios)} scenarios, {len(cost_centers)} cost centers")
    
    if not all([gl_accounts, fiscal_periods, scenarios, cost_centers]):
        print("Missing required data. Creating basic structure first...")
        create_basic_structure(company_id)
        return create_sample_transactions(company_id)
    
    # Create transactions for last 18 months to show trends
    transactions_created = 0
    
    # Get current date and work backwards
    current_date = date.today().replace(day=1)  # First of current month
    
    for month_offset in range(18):  # Last 18 months
        transaction_date = current_date - relativedelta(months=month_offset)
        
        # Find matching fiscal period
        fiscal_period = None
        for fp in fiscal_periods:
            fp_start = datetime.strptime(fp['start_date'], '%Y-%m-%d').date()
            fp_end = datetime.strptime(fp['end_date'], '%Y-%m-%d').date()
            if fp_start <= transaction_date <= fp_end:
                fiscal_period = fp
                break
        
        if not fiscal_period:
            continue
            
        print(f"Creating transactions for {transaction_date.strftime('%Y-%m')}")
        
        # Create actuals and budget transactions for each GL account
        for gl_account in gl_accounts:
            account_type = gl_account['account_type']
            
            # Create budget transaction (if budget scenario exists)
            budget_scenario = next((s for s in scenarios if s['type'] == 'budget'), None)
            if budget_scenario:
                budget_amount = generate_budget_amount(account_type, gl_account['code'])
                
                transaction_data = {
                    "company_id": company_id,
                    "cost_center_id": random.choice(cost_centers)['id'],
                    "gl_account_id": gl_account['id'],
                    "fiscal_period_id": fiscal_period['id'],
                    "scenario_id": budget_scenario['id'],
                    "transaction_date": transaction_date.isoformat(),
                    "amount": budget_amount,
                    "currency_code": "USD",
                    "description": f"Budget {gl_account['name']} - {transaction_date.strftime('%Y-%m')}",
                    "reference": f"BUD-{transaction_date.strftime('%Y%m')}-{gl_account['code']}"
                }
                
                try:
                    response = requests.post(f"{BASE_URL}/companies/{company_id}/transactions", json=transaction_data)
                    if response.status_code == 201:
                        transactions_created += 1
                except Exception as e:
                    print(f"Error creating budget transaction: {e}")
            
            # Create actual transaction
            actual_scenario = next((s for s in scenarios if s['type'] == 'actual'), None)
            if actual_scenario:
                # Generate actual amount with variance from budget
                budget_base = generate_budget_amount(account_type, gl_account['code'])
                variance = random.uniform(-0.20, 0.15)  # -20% to +15% variance
                actual_amount = budget_base * (1 + variance)
                
                # Add seasonality (Q4 boost, Q1 dip for revenue)
                month = transaction_date.month
                if account_type == 'revenue':
                    if month in [11, 12]:  # Nov, Dec boost
                        actual_amount *= 1.15
                    elif month in [1, 2]:  # Jan, Feb dip  
                        actual_amount *= 0.90
                elif account_type == 'expense':
                    if month in [11, 12]:  # Higher expenses in Q4
                        actual_amount *= 1.10
                
                transaction_data = {
                    "company_id": company_id,
                    "cost_center_id": random.choice(cost_centers)['id'],
                    "gl_account_id": gl_account['id'],
                    "fiscal_period_id": fiscal_period['id'],
                    "scenario_id": actual_scenario['id'],
                    "transaction_date": transaction_date.isoformat(),
                    "amount": round(actual_amount, 2),
                    "currency_code": "USD",
                    "description": f"Actual {gl_account['name']} - {transaction_date.strftime('%Y-%m')}",
                    "reference": f"ACT-{transaction_date.strftime('%Y%m')}-{gl_account['code']}"
                }
                
                try:
                    response = requests.post(f"{BASE_URL}/companies/{company_id}/transactions", json=transaction_data)
                    if response.status_code == 201:
                        transactions_created += 1
                except Exception as e:
                    print(f"Error creating actual transaction: {e}")
    
    print(f"Created {transactions_created} sample transactions")
    return transactions_created

def generate_budget_amount(account_type, account_code):
    """Generate realistic budget amounts based on account type"""
    base_amounts = {
        'revenue': {
            '4000': 80000,   # Sales revenue
            '4100': 25000,   # Service revenue  
            '4200': 15000,   # Other revenue
        },
        'expense': {
            '5000': 35000,   # Salaries
            '5100': 12000,   # Benefits
            '5200': 8000,    # Marketing
            '5300': 5000,    # Office rent
            '5400': 3000,    # Utilities
            '5500': 2000,    # Professional services
        },
        'asset': {
            '1000': 50000,   # Cash
            '1100': 25000,   # Accounts receivable
            '1200': 15000,   # Inventory
        },
        'liability': {
            '2000': 20000,   # Accounts payable
            '2100': 15000,   # Accrued expenses
        }
    }
    
    # Get base amount or generate random one
    if account_type in base_amounts and account_code in base_amounts[account_type]:
        base = base_amounts[account_type][account_code]
    else:
        # Generate based on account type
        if account_type == 'revenue':
            base = random.uniform(10000, 100000)
        elif account_type == 'expense':
            base = random.uniform(5000, 50000)
        elif account_type == 'asset':
            base = random.uniform(10000, 80000)
        else:  # liability
            base = random.uniform(5000, 30000)
    
    # Add some randomization
    variance = random.uniform(0.8, 1.2)
    return round(base * variance, 2)

def create_basic_structure(company_id):
    """Create basic GL accounts, cost centers, etc. if missing"""
    print("Creating basic data structure...")
    
    # Create cost centers
    cost_centers = [
        {"name": "Sales", "code": "SALES", "description": "Sales Department"},
        {"name": "Marketing", "code": "MKT", "description": "Marketing Department"},
        {"name": "Operations", "code": "OPS", "description": "Operations Department"},
        {"name": "IT", "code": "IT", "description": "Information Technology"}
    ]
    
    for cc in cost_centers:
        try:
            requests.post(f"{BASE_URL}/companies/{company_id}/cost-centers", json=cc)
        except:
            pass
    
    # Create GL accounts
    gl_accounts = [
        {"code": "4000", "name": "Sales Revenue", "account_type": "revenue"},
        {"code": "4100", "name": "Service Revenue", "account_type": "revenue"},
        {"code": "4200", "name": "Other Revenue", "account_type": "revenue"},
        {"code": "5000", "name": "Salaries Expense", "account_type": "expense"},
        {"code": "5100", "name": "Benefits Expense", "account_type": "expense"},
        {"code": "5200", "name": "Marketing Expense", "account_type": "expense"},
        {"code": "5300", "name": "Office Rent", "account_type": "expense"},
        {"code": "5400", "name": "Utilities", "account_type": "expense"},
    ]
    
    for gl in gl_accounts:
        try:
            requests.post(f"{BASE_URL}/companies/{company_id}/gl-accounts", json=gl)
        except:
            pass
    
    # Create scenarios
    scenarios = [
        {"name": "Budget 2024", "type": "budget", "description": "Annual budget for 2024"},
        {"name": "Actuals", "type": "actual", "description": "Actual results"},
        {"name": "Forecast", "type": "forecast", "description": "Updated forecast"}
    ]
    
    for scenario in scenarios:
        try:
            requests.post(f"{BASE_URL}/companies/{company_id}/scenarios", json=scenario)
        except:
            pass
    
    # Create fiscal periods (last 24 months)
    current_date = date.today().replace(day=1)
    
    for month_offset in range(24):
        period_start = current_date - relativedelta(months=month_offset)
        period_end = period_start + relativedelta(months=1) - relativedelta(days=1)
        
        fiscal_period = {
            "name": f"{period_start.strftime('%B %Y')}",
            "start_date": period_start.isoformat(),
            "end_date": period_end.isoformat(),
            "period_type": "monthly",
            "fiscal_year": period_start.year,
            "status": "closed" if month_offset > 0 else "open"
        }
        
        try:
            requests.post(f"{BASE_URL}/companies/{company_id}/fiscal-periods", json=fiscal_period)
        except:
            pass

def main():
    company_id = get_company_id()
    if not company_id:
        print("No companies found. Please create a company first.")
        return
    
    print(f"Creating sample data for company: {company_id}")
    
    # Create sample transactions
    transactions_created = create_sample_transactions(company_id)
    
    print(f"Sample data creation complete!")
    print(f"- Company ID: {company_id}")
    print(f"- Transactions created: {transactions_created}")
    print("\nYou can now test the analytics endpoints!")

if __name__ == "__main__":
    main()