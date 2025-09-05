from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.models.models import GLTransaction, GLTransactionLine
from app.schemas.schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse,
    CostCenterCreate, CostCenterUpdate, CostCenterResponse,
    GLAccountCreate, GLAccountUpdate, GLAccountResponse,
    FiscalPeriodCreate, FiscalPeriodUpdate, FiscalPeriodResponse,
    ScenarioCreate, ScenarioUpdate, ScenarioResponse,
    BudgetLineCreate, BudgetLineUpdate, BudgetLineResponse,
    GLTransactionCreate, GLTransactionUpdate, GLTransactionResponse,
    KPICreate, KPIUpdate, KPIResponse,
    UserCreate, UserUpdate, UserResponse,
    PaginatedResponse
)
from app.crud.crud_operations import (
    crud_company, crud_cost_center, crud_gl_account,
    crud_fiscal_period, crud_scenario, crud_budget_line,
    crud_gl_transaction, crud_kpi, crud_user
)

# Import analytics routes (temporarily commented out)
# from .analytics_routes import router as analytics_router

router = APIRouter()

# Company endpoints
@router.post("/companies", response_model=CompanyResponse, tags=["Companies"])
async def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = crud_company.get_by_code(db, code=company.code)
    if db_company:
        raise HTTPException(status_code=400, detail="Company code already exists")
    return crud_company.create(db, obj_in=company)

@router.get("/companies", response_model=List[CompanyResponse], tags=["Companies"])
async def read_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    if active_only:
        companies = crud_company.get_active_companies(db, skip=skip, limit=limit)
    else:
        companies = crud_company.get_multi(db, skip=skip, limit=limit)
    return companies

@router.get("/companies/{company_id}", response_model=CompanyResponse, tags=["Companies"])
async def read_company(company_id: UUID, db: Session = Depends(get_db)):
    company = crud_company.get(db, id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/companies/{company_id}", response_model=CompanyResponse, tags=["Companies"])
async def update_company(
    company_id: UUID,
    company: CompanyUpdate,
    db: Session = Depends(get_db)
):
    db_company = crud_company.get(db, id=company_id)
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    return crud_company.update(db, db_obj=db_company, obj_in=company)

@router.delete("/companies/{company_id}", response_model=CompanyResponse, tags=["Companies"])
async def delete_company(company_id: UUID, db: Session = Depends(get_db)):
    return crud_company.remove(db, id=company_id)

# Cost Center endpoints
@router.post("/cost-centers", response_model=CostCenterResponse, tags=["Cost Centers"])
async def create_cost_center(cost_center: CostCenterCreate, db: Session = Depends(get_db)):
    db_cost_center = crud_cost_center.get_by_company_and_code(
        db, company_id=cost_center.company_id, code=cost_center.code
    )
    if db_cost_center:
        raise HTTPException(status_code=400, detail="Cost center code already exists for this company")
    return crud_cost_center.create(db, obj_in=cost_center)

@router.get("/companies/{company_id}/cost-centers", response_model=List[CostCenterResponse], tags=["Cost Centers"])
async def read_cost_centers(
    company_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    return crud_cost_center.get_by_company(db, company_id=company_id, skip=skip, limit=limit)

@router.get("/cost-centers/{cost_center_id}", response_model=CostCenterResponse, tags=["Cost Centers"])
async def read_cost_center(cost_center_id: UUID, db: Session = Depends(get_db)):
    cost_center = crud_cost_center.get(db, id=cost_center_id)
    if not cost_center:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return cost_center

@router.put("/cost-centers/{cost_center_id}", response_model=CostCenterResponse, tags=["Cost Centers"])
async def update_cost_center(
    cost_center_id: UUID,
    cost_center: CostCenterUpdate,
    db: Session = Depends(get_db)
):
    db_cost_center = crud_cost_center.get(db, id=cost_center_id)
    if not db_cost_center:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return crud_cost_center.update(db, db_obj=db_cost_center, obj_in=cost_center)

# GL Account endpoints
@router.post("/gl-accounts", response_model=GLAccountResponse, tags=["GL Accounts"])
async def create_gl_account(gl_account: GLAccountCreate, db: Session = Depends(get_db)):
    db_account = crud_gl_account.get_by_company_and_number(
        db, company_id=gl_account.company_id, account_number=gl_account.account_number
    )
    if db_account:
        raise HTTPException(status_code=400, detail="Account number already exists for this company")
    return crud_gl_account.create(db, obj_in=gl_account)

@router.get("/companies/{company_id}/gl-accounts", response_model=List[GLAccountResponse], tags=["GL Accounts"])
async def read_gl_accounts(
    company_id: UUID,
    account_type: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    if account_type:
        return crud_gl_account.get_by_type(db, company_id=company_id, account_type=account_type)
    return crud_gl_account.get_by_company(db, company_id=company_id, skip=skip, limit=limit)

@router.get("/gl-accounts/{gl_account_id}", response_model=GLAccountResponse, tags=["GL Accounts"])
async def read_gl_account(gl_account_id: UUID, db: Session = Depends(get_db)):
    gl_account = crud_gl_account.get(db, id=gl_account_id)
    if not gl_account:
        raise HTTPException(status_code=404, detail="GL account not found")
    return gl_account

@router.put("/gl-accounts/{gl_account_id}", response_model=GLAccountResponse, tags=["GL Accounts"])
async def update_gl_account(
    gl_account_id: UUID,
    gl_account: GLAccountUpdate,
    db: Session = Depends(get_db)
):
    db_account = crud_gl_account.get(db, id=gl_account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="GL account not found")
    return crud_gl_account.update(db, db_obj=db_account, obj_in=gl_account)

# Fiscal Period endpoints
@router.post("/fiscal-periods", response_model=FiscalPeriodResponse, tags=["Fiscal Periods"])
async def create_fiscal_period(fiscal_period: FiscalPeriodCreate, db: Session = Depends(get_db)):
    db_period = crud_fiscal_period.get_by_company_and_period(
        db, 
        company_id=fiscal_period.company_id,
        fiscal_year=fiscal_period.fiscal_year,
        period_number=fiscal_period.period_number
    )
    if db_period:
        raise HTTPException(status_code=400, detail="Fiscal period already exists")
    return crud_fiscal_period.create(db, obj_in=fiscal_period)

@router.get("/companies/{company_id}/fiscal-periods", response_model=List[FiscalPeriodResponse], tags=["Fiscal Periods"])
async def read_fiscal_periods(
    company_id: UUID,
    fiscal_year: int = None,
    db: Session = Depends(get_db)
):
    if fiscal_year:
        return crud_fiscal_period.get_by_company_and_year(
            db, company_id=company_id, fiscal_year=fiscal_year
        )
    return crud_fiscal_period.get_multi(db, skip=0, limit=100)

@router.post("/fiscal-periods/{period_id}/close", response_model=FiscalPeriodResponse, tags=["Fiscal Periods"])
async def close_fiscal_period(period_id: UUID, db: Session = Depends(get_db)):
    return crud_fiscal_period.close_period(db, id=period_id)

# Scenario endpoints
@router.post("/scenarios", response_model=ScenarioResponse, tags=["Scenarios"])
async def create_scenario(scenario: ScenarioCreate, db: Session = Depends(get_db)):
    db_scenario = crud_scenario.get_by_company_and_name(
        db,
        company_id=scenario.company_id,
        name=scenario.name,
        fiscal_year=scenario.fiscal_year
    )
    if db_scenario:
        raise HTTPException(status_code=400, detail="Scenario already exists")
    return crud_scenario.create(db, obj_in=scenario)

@router.get("/companies/{company_id}/scenarios", response_model=List[ScenarioResponse], tags=["Scenarios"])
async def read_scenarios(
    company_id: UUID,
    fiscal_year: int = None,
    scenario_type: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    scenarios = crud_scenario.get_multi(db, skip=skip, limit=limit)
    # Filter by company_id
    scenarios = [s for s in scenarios if s.company_id == company_id]
    if fiscal_year:
        scenarios = [s for s in scenarios if s.fiscal_year == fiscal_year]
    if scenario_type:
        scenarios = [s for s in scenarios if s.scenario_type.value == scenario_type]
    return scenarios

@router.post("/scenarios/{scenario_id}/approve", response_model=ScenarioResponse, tags=["Scenarios"])
async def approve_scenario(
    scenario_id: UUID,
    approved_by: UUID,
    db: Session = Depends(get_db)
):
    return crud_scenario.approve_scenario(db, id=scenario_id, approved_by=approved_by)

# Budget Line endpoints
@router.post("/budget-lines", response_model=BudgetLineResponse, tags=["Budget Lines"])
async def create_budget_line(budget_line: BudgetLineCreate, db: Session = Depends(get_db)):
    return crud_budget_line.create(db, obj_in=budget_line)

@router.get("/scenarios/{scenario_id}/budget-lines", response_model=List[BudgetLineResponse], tags=["Budget Lines"])
async def read_budget_lines(
    scenario_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    return crud_budget_line.get_by_scenario(db, scenario_id=scenario_id, skip=skip, limit=limit)

@router.put("/budget-lines/{budget_line_id}", response_model=BudgetLineResponse, tags=["Budget Lines"])
async def update_budget_line(
    budget_line_id: UUID,
    budget_line: BudgetLineUpdate,
    db: Session = Depends(get_db)
):
    db_budget_line = crud_budget_line.get(db, id=budget_line_id)
    if not db_budget_line:
        raise HTTPException(status_code=404, detail="Budget line not found")
    return crud_budget_line.update(db, db_obj=db_budget_line, obj_in=budget_line)

# GL Transaction endpoints
@router.post("/gl-transactions", response_model=GLTransactionResponse, tags=["GL Transactions"])
async def create_gl_transaction(transaction: GLTransactionCreate, db: Session = Depends(get_db)):
    return crud_gl_transaction.create_with_lines(db, obj_in=transaction)

@router.get("/gl-transactions/{transaction_id}", response_model=GLTransactionResponse, tags=["GL Transactions"])
async def read_gl_transaction(transaction_id: UUID, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    
    transaction = db.query(GLTransaction).options(
        joinedload(GLTransaction.company),
        joinedload(GLTransaction.fiscal_period),
        joinedload(GLTransaction.transaction_lines).joinedload(GLTransactionLine.gl_account),
        joinedload(GLTransaction.transaction_lines).joinedload(GLTransactionLine.cost_center)
    ).filter(GLTransaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.post("/gl-transactions/{transaction_id}/post", response_model=GLTransactionResponse, tags=["GL Transactions"])
async def post_gl_transaction(transaction_id: UUID, db: Session = Depends(get_db)):
    return crud_gl_transaction.post_transaction(db, id=transaction_id)

@router.post("/gl-transactions/{transaction_id}/void", response_model=GLTransactionResponse, tags=["GL Transactions"])
async def void_gl_transaction(
    transaction_id: UUID, 
    reason: dict = {"reason": ""},
    db: Session = Depends(get_db)
):
    transaction = crud_gl_transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not transaction.is_posted:
        raise HTTPException(status_code=400, detail="Cannot void an unposted transaction")
    # Mark as voided (we'll need to add this field to the model if it doesn't exist)
    # For now, we'll just return the transaction
    return transaction

@router.post("/gl-transactions/{transaction_id}/duplicate", response_model=GLTransactionResponse, tags=["GL Transactions"])
async def duplicate_gl_transaction(transaction_id: UUID, db: Session = Depends(get_db)):
    original = crud_gl_transaction.get(db, id=transaction_id)
    if not original:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Create a copy of the transaction
    from datetime import datetime
    new_transaction = GLTransactionCreate(
        company_id=original.company_id,
        fiscal_period_id=original.fiscal_period_id,
        transaction_date=datetime.utcnow().isoformat(),
        reference_number=f"COPY-{original.reference_number}" if original.reference_number else None,
        description=f"Copy of {original.description}" if original.description else "Copy of transaction",
        lines=[
            {
                "gl_account_id": line.gl_account_id,
                "cost_center_id": line.cost_center_id,
                "debit_amount": line.debit_amount,
                "credit_amount": line.credit_amount,
                "description": line.description
            }
            for line in original.transaction_lines
        ]
    )
    return crud_gl_transaction.create_with_lines(db, obj_in=new_transaction)

@router.get("/companies/{company_id}/gl-transactions", response_model=List[GLTransactionResponse], tags=["GL Transactions"])
async def read_company_gl_transactions(
    company_id: UUID,
    fiscal_period_id: UUID = None,
    is_posted: bool = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    
    query = db.query(GLTransaction).options(
        joinedload(GLTransaction.company),
        joinedload(GLTransaction.fiscal_period),
        joinedload(GLTransaction.transaction_lines).joinedload(GLTransactionLine.gl_account),
        joinedload(GLTransaction.transaction_lines).joinedload(GLTransactionLine.cost_center)
    ).filter(GLTransaction.company_id == company_id)
    
    if fiscal_period_id:
        query = query.filter(GLTransaction.fiscal_period_id == fiscal_period_id)
    if is_posted is not None:
        query = query.filter(GLTransaction.is_posted == is_posted)
    
    # Order by transaction_date descending
    query = query.order_by(GLTransaction.transaction_date.desc())
    
    transactions = query.offset(skip).limit(limit).all()
    return transactions

# KPI endpoints
@router.post("/kpis", response_model=KPIResponse, tags=["KPIs"])
async def create_kpi(kpi: KPICreate, db: Session = Depends(get_db)):
    db_kpi = crud_kpi.get_by_company_and_code(
        db, company_id=kpi.company_id, code=kpi.code
    )
    if db_kpi:
        raise HTTPException(status_code=400, detail="KPI code already exists for this company")
    return crud_kpi.create(db, obj_in=kpi)

@router.get("/companies/{company_id}/kpis", response_model=List[KPIResponse], tags=["KPIs"])
async def read_kpis(
    company_id: UUID,
    category: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    if category:
        return crud_kpi.get_by_category(db, company_id=company_id, category=category)
    return crud_kpi.get_by_company(db, company_id=company_id, skip=skip, limit=limit)

# User endpoints
@router.post("/users", response_model=UserResponse, tags=["Users"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud_user.get_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud_user.create(db, obj_in=user)

@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def read_user(user_id: UUID, db: Session = Depends(get_db)):
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: UUID,
    user: UserUpdate,
    db: Session = Depends(get_db)
):
    db_user = crud_user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud_user.update(db, db_obj=db_user, obj_in=user)