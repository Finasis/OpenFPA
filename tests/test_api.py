from fastapi.testclient import TestClient
from app.main import app
import pytest
from uuid import uuid4

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "OpenFP&A API"
    assert data["version"] == "1.0.0"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_company():
    company_data = {
        "code": f"TEST_{uuid4().hex[:8]}",
        "name": "Test Company",
        "currency_code": "USD",
        "fiscal_year_start_month": 1
    }
    response = client.post("/api/v1/companies", json=company_data)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == company_data["code"]
    assert data["name"] == company_data["name"]
    assert "id" in data
    return data["id"]

def test_get_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_company_not_found():
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/companies/{fake_id}")
    assert response.status_code == 404

def test_create_cost_center():
    # First create a company
    company_data = {
        "code": f"CC_TEST_{uuid4().hex[:8]}",
        "name": "CC Test Company",
        "currency_code": "USD"
    }
    company_response = client.post("/api/v1/companies", json=company_data)
    company_id = company_response.json()["id"]
    
    # Then create a cost center
    cost_center_data = {
        "company_id": company_id,
        "code": "CC001",
        "name": "Sales Department"
    }
    response = client.post("/api/v1/cost-centers", json=cost_center_data)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "CC001"
    assert data["name"] == "Sales Department"

def test_create_gl_transaction_balanced():
    # Create test data first
    company_data = {
        "code": f"GL_TEST_{uuid4().hex[:8]}",
        "name": "GL Test Company",
        "currency_code": "USD"
    }
    company_response = client.post("/api/v1/companies", json=company_data)
    company_id = company_response.json()["id"]
    
    # Create GL accounts
    cash_account = {
        "company_id": company_id,
        "account_number": "1000",
        "name": "Cash",
        "account_type": "ASSET"
    }
    cash_response = client.post("/api/v1/gl-accounts", json=cash_account)
    cash_id = cash_response.json()["id"]
    
    revenue_account = {
        "company_id": company_id,
        "account_number": "4000",
        "name": "Sales Revenue",
        "account_type": "REVENUE"
    }
    revenue_response = client.post("/api/v1/gl-accounts", json=revenue_account)
    revenue_id = revenue_response.json()["id"]
    
    # Create cost center
    cost_center = {
        "company_id": company_id,
        "code": "SALES",
        "name": "Sales Dept"
    }
    cc_response = client.post("/api/v1/cost-centers", json=cost_center)
    cc_id = cc_response.json()["id"]
    
    # Create fiscal period
    period = {
        "company_id": company_id,
        "fiscal_year": 2024,
        "period_number": 1,
        "period_name": "January 2024",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
    period_response = client.post("/api/v1/fiscal-periods", json=period)
    period_id = period_response.json()["id"]
    
    # Create balanced transaction
    transaction = {
        "company_id": company_id,
        "fiscal_period_id": period_id,
        "transaction_date": "2024-01-15",
        "description": "Sales transaction",
        "lines": [
            {
                "gl_account_id": cash_id,
                "cost_center_id": cc_id,
                "debit_amount": 1000,
                "credit_amount": 0,
                "description": "Cash received"
            },
            {
                "gl_account_id": revenue_id,
                "cost_center_id": cc_id,
                "debit_amount": 0,
                "credit_amount": 1000,
                "description": "Sales revenue"
            }
        ]
    }
    
    response = client.post("/api/v1/gl-transactions", json=transaction)
    assert response.status_code == 200
    data = response.json()
    assert len(data["transaction_lines"]) == 2

def test_create_gl_transaction_unbalanced():
    # Create minimal test data
    company_data = {
        "code": f"UNBAL_TEST_{uuid4().hex[:8]}",
        "name": "Unbalanced Test",
        "currency_code": "USD"
    }
    company_response = client.post("/api/v1/companies", json=company_data)
    company_id = company_response.json()["id"]
    
    # Create accounts and other required data (simplified)
    account = {
        "company_id": company_id,
        "account_number": "9999",
        "name": "Test Account",
        "account_type": "ASSET"
    }
    account_response = client.post("/api/v1/gl-accounts", json=account)
    account_id = account_response.json()["id"]
    
    cc = {
        "company_id": company_id,
        "code": "TEST",
        "name": "Test CC"
    }
    cc_response = client.post("/api/v1/cost-centers", json=cc)
    cc_id = cc_response.json()["id"]
    
    period = {
        "company_id": company_id,
        "fiscal_year": 2024,
        "period_number": 1,
        "period_name": "Jan",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
    period_response = client.post("/api/v1/fiscal-periods", json=period)
    period_id = period_response.json()["id"]
    
    # Create unbalanced transaction (should fail)
    transaction = {
        "company_id": company_id,
        "fiscal_period_id": period_id,
        "transaction_date": "2024-01-15",
        "lines": [
            {
                "gl_account_id": account_id,
                "cost_center_id": cc_id,
                "debit_amount": 1000,
                "credit_amount": 0
            }
        ]
    }
    
    response = client.post("/api/v1/gl-transactions", json=transaction)
    assert response.status_code == 400
    assert "must equal" in response.json()["detail"].lower()