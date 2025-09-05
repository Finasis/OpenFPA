# OpenFP&A API - FastAPI + SQLAlchemy Implementation

A modern Financial Planning & Analysis (FP&A) system built with FastAPI and SQLAlchemy 2.0.

## Features

- **Multi-company support** with hierarchical organizational structure
- **Chart of Accounts** with account types and hierarchies
- **Flexible fiscal periods** management
- **Budget & Forecast** scenarios with versioning
- **GL Transaction** tracking with double-entry bookkeeping
- **KPI Management** and tracking
- **User Management** with company-level access control
- **RESTful API** with automatic documentation

## Tech Stack

- **FastAPI** - Modern web framework for building APIs
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** - Primary database
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server

## Project Structure

```
/home/marioled/dev/cloud/
├── app/
│   ├── models/
│   │   ├── base.py          # Database connection and base model
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py       # Pydantic schemas for validation
│   ├── crud/
│   │   ├── crud_base.py     # Generic CRUD operations
│   │   └── crud_operations.py # Entity-specific CRUD operations
│   ├── api/
│   │   └── routes.py        # API endpoints
│   └── main.py              # FastAPI application
├── database_schema.sql      # PostgreSQL schema
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables example
└── README.md               # This file
```

## Installation

### Option 1: Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   cd /home/marioled/dev/cloud
   ```

2. **Start services with Docker Compose**
   ```bash
   # Start PostgreSQL, pgAdmin, and the application
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop services
   docker-compose down
   
   # Stop and remove volumes (careful - this deletes data!)
   docker-compose down -v
   ```

3. **Access the services**
   - **API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **Frontend**: http://localhost:3000

### Option 2: Manual Installation

1. **Clone the repository**
   ```bash
   cd /home/marioled/dev/cloud
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Using Docker for just PostgreSQL
   docker run --name openfpa-postgres \
     -e POSTGRES_USER=openfpa_user \
     -e POSTGRES_PASSWORD=openfpa_pass \
     -e POSTGRES_DB=openfpa \
     -p 5432:5432 \
     -d postgres:16-alpine
   
   # Or create database manually if PostgreSQL is installed
   createdb openfpa
   psql -d openfpa -f database_schema.sql
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

6. **Run the application**
   ```bash
   python -m app.main
   ```

   The API will be available at `http://localhost:8000`

## Docker Configuration

The Docker setup includes:

- **PostgreSQL 16**: Database server with persistent volume
- **FastAPI Application**: Auto-reloading development server

### Environment Variables

Configure in `.env` file:

```env
# PostgreSQL
POSTGRES_USER=openfpa_user
POSTGRES_PASSWORD=openfpa_pass
POSTGRES_DB=openfpa
POSTGRES_PORT=5432

# Application
APP_PORT=8000
DATABASE_URL=postgresql://openfpa_user:openfpa_pass@localhost:5432/openfpa
```

### Docker Commands

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Execute commands in container
docker-compose exec postgres psql -U openfpa_user -d openfpa
docker-compose exec app python -c "from app.models.base import engine; from app.models.models import Base; Base.metadata.create_all(engine)"

# Restart a service
docker-compose restart app

# Stop all services
docker-compose down

# Remove all data (careful!)
docker-compose down -v
```

## API Documentation

Once running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Companies
- `POST /api/v1/companies` - Create company
- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/{id}` - Get company
- `PUT /api/v1/companies/{id}` - Update company
- `DELETE /api/v1/companies/{id}` - Delete company

### Cost Centers
- `POST /api/v1/cost-centers` - Create cost center
- `GET /api/v1/companies/{id}/cost-centers` - List cost centers
- `GET /api/v1/cost-centers/{id}` - Get cost center
- `PUT /api/v1/cost-centers/{id}` - Update cost center

### GL Accounts
- `POST /api/v1/gl-accounts` - Create GL account
- `GET /api/v1/companies/{id}/gl-accounts` - List GL accounts
- `GET /api/v1/gl-accounts/{id}` - Get GL account
- `PUT /api/v1/gl-accounts/{id}` - Update GL account

### Fiscal Periods
- `POST /api/v1/fiscal-periods` - Create fiscal period
- `GET /api/v1/companies/{id}/fiscal-periods` - List fiscal periods
- `POST /api/v1/fiscal-periods/{id}/close` - Close period

### Scenarios (Budgets/Forecasts)
- `POST /api/v1/scenarios` - Create scenario
- `GET /api/v1/companies/{id}/scenarios` - List scenarios
- `POST /api/v1/scenarios/{id}/approve` - Approve scenario

### Budget Lines
- `POST /api/v1/budget-lines` - Create budget line
- `GET /api/v1/scenarios/{id}/budget-lines` - List budget lines
- `PUT /api/v1/budget-lines/{id}` - Update budget line

### GL Transactions
- `POST /api/v1/gl-transactions` - Create transaction with lines
- `GET /api/v1/gl-transactions/{id}` - Get transaction
- `POST /api/v1/gl-transactions/{id}/post` - Post transaction

### KPIs
- `POST /api/v1/kpis` - Create KPI
- `GET /api/v1/companies/{id}/kpis` - List KPIs

### Users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user

## Example Usage

### Create a Company
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/companies",
    json={
        "code": "ACME",
        "name": "Acme Corporation",
        "currency_code": "USD",
        "fiscal_year_start_month": 1
    }
)
company = response.json()
print(f"Created company: {company['id']}")
```

### Create a GL Transaction
```python
response = requests.post(
    "http://localhost:8000/api/v1/gl-transactions",
    json={
        "company_id": company_id,
        "fiscal_period_id": period_id,
        "transaction_date": "2024-01-15",
        "description": "Sales revenue",
        "lines": [
            {
                "gl_account_id": cash_account_id,
                "cost_center_id": sales_cc_id,
                "debit_amount": 1000,
                "credit_amount": 0,
                "description": "Cash received"
            },
            {
                "gl_account_id": revenue_account_id,
                "cost_center_id": sales_cc_id,
                "debit_amount": 0,
                "credit_amount": 1000,
                "description": "Sales revenue"
            }
        ]
    }
)
```

## Database Migrations

For production, use Alembic for database migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## Testing

Create a test file `test_api.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_company():
    response = client.post(
        "/api/v1/companies",
        json={"code": "TEST", "name": "Test Corp", "currency_code": "USD"}
    )
    assert response.status_code == 200
    assert response.json()["code"] == "TEST"
```

Run tests:
```bash
pytest test_api.py
```

## Production Deployment

1. Use environment variables for sensitive configuration
2. Set up proper database connection pooling
3. Use a production ASGI server (Gunicorn with Uvicorn workers)
4. Implement authentication and authorization
5. Set up logging and monitoring
6. Configure CORS properly for your frontend domain

## License

MIT
