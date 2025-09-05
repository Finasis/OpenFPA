from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.base import get_db
from app.services.planning.expense_planning import ExpensePlanningService

router = APIRouter(prefix="/expense", tags=["Expense Planning"])

# ============================================
# PYDANTIC MODELS
# ============================================

class ExpenseForecastMethod(BaseModel):
    """Expense forecasting method configuration"""
    method: str = Field(..., description="Forecasting method: incremental, zero_based, driver_based, activity_based")
    growth_rate: Optional[float] = Field(0.03, description="Annual growth rate for incremental method")
    inflation_rate: Optional[float] = Field(0.02, description="Inflation rate")
    cost_reduction_target: Optional[float] = Field(None, description="Cost reduction target percentage")

class HeadcountPlan(BaseModel):
    """Headcount planning parameters"""
    department: str
    headcount: int
    avg_salary: float
    benefits_rate: float = 0.3

class ExpenseForecastRequest(BaseModel):
    company_id: UUID
    forecast_months: int = Field(12, ge=1, le=36)
    method: ExpenseForecastMethod
    headcount_plan: Optional[Dict[str, HeadcountPlan]] = None
    driver_assumptions: Optional[Dict[str, float]] = None
    activities: Optional[List[Dict[str, Any]]] = None
    include_contracts: bool = True
    include_categories: bool = True

class ExpenseForecastResponse(BaseModel):
    company_id: UUID
    method: str
    forecast_data: List[Dict[str, Any]]
    category_breakdown: Optional[List[Dict[str, Any]]]
    total_forecast: float
    assumptions: Dict[str, Any]
    contract_obligations: Optional[Dict[str, Any]]
    sensitivity_analysis: Optional[Dict[str, Any]]

class ExpensePlanCreate(BaseModel):
    company_id: UUID
    plan_name: str
    plan_type: str  # 'zero_based', 'incremental', 'activity_based', 'driver_based'
    fiscal_year: int
    scenario_id: Optional[UUID] = None
    notes: Optional[str] = None

class ExpenseCategoryCreate(BaseModel):
    company_id: UUID
    category_code: str
    category_name: str
    category_type: str  # 'personnel', 'operating', 'capital', 'marketing', 'travel', 'facilities'
    parent_category_id: Optional[UUID] = None
    is_controllable: bool = True
    is_discretionary: bool = False
    typical_variance_pct: float = 5.0

class VendorContractCreate(BaseModel):
    company_id: UUID
    vendor_id: UUID
    contract_number: str
    contract_name: str
    contract_type: str  # 'subscription', 'lease', 'service', 'maintenance'
    start_date: date
    end_date: Optional[date] = None
    monthly_amount: float
    annual_amount: Optional[float] = None
    escalation_rate: Optional[float] = 0
    auto_renew: bool = False
    gl_account_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None

class ExpenseVarianceRequest(BaseModel):
    company_id: UUID
    period_id: UUID
    expense_plan_id: Optional[UUID] = None
    category_filter: Optional[str] = None

# ============================================
# EXPENSE FORECASTING ENDPOINTS
# ============================================

@router.post("/forecast", response_model=ExpenseForecastResponse)
async def generate_expense_forecast(
    request: ExpenseForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generate expense forecast using various budgeting methods.
    Supports incremental, zero-based, driver-based, and activity-based budgeting.
    """
    
    service = ExpensePlanningService(db)
    
    # Prepare forecast parameters
    forecast_params = {
        'method': request.method.method,
        'forecast_months': request.forecast_months,
        'growth_rate': request.method.growth_rate,
        'inflation_rate': request.method.inflation_rate,
        'cost_reduction_target': request.method.cost_reduction_target,
        'headcount_plan': request.headcount_plan,
        'driver_assumptions': request.driver_assumptions,
        'activities': request.activities
    }
    
    # Generate forecast
    forecast = await service.generate_expense_forecast(
        str(request.company_id),
        forecast_params
    )
    
    # Get contract obligations if requested
    contract_obligations = None
    if request.include_contracts:
        contract_obligations = await service.get_contract_obligations(
            str(request.company_id),
            request.forecast_months
        )
    
    # Add contract obligations to forecast
    if contract_obligations:
        forecast['contract_obligations'] = contract_obligations
    
    # Ensure all required and optional fields are present
    if 'sensitivity_analysis' not in forecast:
        forecast['sensitivity_analysis'] = None
    
    if 'category_breakdown' not in forecast:
        forecast['category_breakdown'] = None
    
    if 'assumptions' not in forecast:
        # Build assumptions from forecast params
        forecast['assumptions'] = {
            'method': forecast_params['method'],
            'forecast_months': forecast_params['forecast_months'],
            'growth_rate': forecast_params.get('growth_rate'),
            'inflation_rate': forecast_params.get('inflation_rate'),
            'cost_reduction_target': forecast_params.get('cost_reduction_target')
        }
        # Add method-specific assumptions
        if 'driver_assumptions' in forecast:
            forecast['assumptions']['driver_assumptions'] = forecast['driver_assumptions']
        if 'personnel_costs' in forecast:
            forecast['assumptions']['personnel_costs'] = forecast['personnel_costs']
        if 'operating_expenses' in forecast:
            forecast['assumptions']['operating_expenses'] = forecast['operating_expenses']
    
    return ExpenseForecastResponse(**forecast)

@router.post("/plans", response_model=Dict[str, str])
async def create_expense_plan(
    plan: ExpensePlanCreate,
    db: Session = Depends(get_db)
):
    """Create a new expense plan/budget"""
    
    service = ExpensePlanningService(db)
    
    plan_id = await service.create_expense_plan(
        str(plan.company_id),
        plan.plan_name,
        plan.plan_type,
        plan.fiscal_year,
        str(plan.scenario_id) if plan.scenario_id else None
    )
    
    return {"plan_id": plan_id, "status": "created"}

@router.get("/plans/{company_id}")
async def get_expense_plans(
    company_id: UUID,
    fiscal_year: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get expense plans for a company"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        ep.*,
        s.name as scenario_name,
        u1.email as created_by_email,
        u2.email as approved_by_email
    FROM expense_plans ep
    LEFT JOIN scenarios s ON s.id = ep.scenario_id
    LEFT JOIN users u1 ON u1.id = ep.created_by
    LEFT JOIN users u2 ON u2.id = ep.approved_by
    WHERE ep.company_id = :company_id
    """
    
    params = {'company_id': str(company_id)}
    
    if fiscal_year:
        query += " AND ep.fiscal_year = :fiscal_year"
        params['fiscal_year'] = fiscal_year
    
    if status:
        query += " AND ep.status = :status"
        params['status'] = status
    
    query += " ORDER BY ep.fiscal_year DESC, ep.created_at DESC"
    
    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]

@router.get("/categories/{company_id}")
async def get_expense_categories(
    company_id: UUID,
    category_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get expense categories with hierarchy"""
    
    from sqlalchemy import text
    
    query = """
    WITH RECURSIVE category_tree AS (
        SELECT 
            ec.*,
            0 as level,
            ARRAY[ec.id] as path
        FROM expense_categories ec
        WHERE ec.company_id = :company_id
        AND ec.parent_category_id IS NULL
        
        UNION ALL
        
        SELECT 
            ec.*,
            ct.level + 1,
            ct.path || ec.id
        FROM expense_categories ec
        JOIN category_tree ct ON ec.parent_category_id = ct.id
    )
    SELECT * FROM category_tree
    """
    
    params = {'company_id': str(company_id)}
    
    if category_type:
        query += " WHERE category_type = :category_type"
        params['category_type'] = category_type
    
    query += " ORDER BY path"
    
    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]

@router.post("/categories", response_model=Dict[str, str])
async def create_expense_category(
    category: ExpenseCategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new expense category"""
    
    from sqlalchemy import text
    import uuid
    
    category_id = str(uuid.uuid4())
    
    query = """
    INSERT INTO expense_categories (
        id, company_id, category_code, category_name, category_type,
        parent_category_id, is_controllable, is_discretionary,
        typical_variance_pct, created_at
    ) VALUES (
        :id, :company_id, :category_code, :category_name, :category_type,
        :parent_category_id, :is_controllable, :is_discretionary,
        :typical_variance_pct, :created_at
    )
    """
    
    db.execute(text(query), {
        'id': category_id,
        'company_id': str(category.company_id),
        'category_code': category.category_code,
        'category_name': category.category_name,
        'category_type': category.category_type,
        'parent_category_id': str(category.parent_category_id) if category.parent_category_id else None,
        'is_controllable': category.is_controllable,
        'is_discretionary': category.is_discretionary,
        'typical_variance_pct': category.typical_variance_pct,
        'created_at': datetime.utcnow()
    })
    
    db.commit()
    return {"category_id": category_id, "status": "created"}

@router.get("/contracts/{company_id}")
async def get_vendor_contracts(
    company_id: UUID,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get vendor contracts and obligations"""
    
    service = ExpensePlanningService(db)
    
    contracts = await service.get_contract_obligations(
        str(company_id),
        forecast_period=12
    )
    
    return contracts

@router.post("/contracts", response_model=Dict[str, str])
async def create_vendor_contract(
    contract: VendorContractCreate,
    db: Session = Depends(get_db)
):
    """Create a new vendor contract"""
    
    service = ExpensePlanningService(db)
    
    contract_id = await service.create_vendor_contract(
        str(contract.company_id),
        str(contract.vendor_id),
        contract.dict(exclude={'company_id', 'vendor_id'})
    )
    
    return {"contract_id": contract_id, "status": "created"}

@router.post("/variance-analysis")
async def analyze_expense_variance(
    request: ExpenseVarianceRequest,
    db: Session = Depends(get_db)
):
    """Analyze expense variance vs plan"""
    
    service = ExpensePlanningService(db)
    
    variance = await service.analyze_expense_variance(
        str(request.company_id),
        str(request.period_id),
        str(request.expense_plan_id) if request.expense_plan_id else None
    )
    
    return variance

@router.get("/metrics/{company_id}")
async def get_expense_metrics(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get key expense metrics and KPIs"""
    
    from sqlalchemy import text
    
    # Current month expenses
    current_month_query = """
    SELECT 
        SUM(gtl.debit_amount) as current_month_expense,
        COUNT(DISTINCT gtl.gl_account_id) as num_accounts,
        COUNT(DISTINCT gtl.cost_center_id) as num_cost_centers
    FROM gl_transactions gt
    JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
    JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
    WHERE gt.company_id = :company_id
    AND ga.account_type = 'expense'
    AND gt.transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
    AND gt.transaction_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
    """
    
    current_result = db.execute(text(current_month_query), {'company_id': str(company_id)})
    current_data = current_result.fetchone()
    
    # YTD expenses
    ytd_query = """
    SELECT 
        SUM(gtl.debit_amount) as ytd_expense,
        AVG(gtl.debit_amount) as avg_expense
    FROM gl_transactions gt
    JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
    JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
    WHERE gt.company_id = :company_id
    AND ga.account_type = 'expense'
    AND gt.transaction_date >= DATE_TRUNC('year', CURRENT_DATE)
    """
    
    ytd_result = db.execute(text(ytd_query), {'company_id': str(company_id)})
    ytd_data = ytd_result.fetchone()
    
    # Contract obligations
    contract_query = """
    SELECT 
        COUNT(*) as active_contracts,
        SUM(monthly_amount) as monthly_obligations
    FROM expense_contracts
    WHERE company_id = :company_id
    AND is_active = true
    AND (end_date IS NULL OR end_date >= CURRENT_DATE)
    """
    
    contract_result = db.execute(text(contract_query), {'company_id': str(company_id)})
    contract_data = contract_result.fetchone()
    
    return {
        'current_month_expense': float(current_data[0] or 0),
        'ytd_expense': float(ytd_data[0] or 0),
        'avg_transaction_expense': float(ytd_data[1] or 0),
        'num_expense_accounts': current_data[1] or 0,
        'num_cost_centers': current_data[2] or 0,
        'active_contracts': contract_data[0] or 0,
        'monthly_contract_obligations': float(contract_data[1] or 0),
        'expense_run_rate': float(ytd_data[0] or 0) / datetime.now().month * 12 if datetime.now().month > 0 else 0
    }

@router.get("/benchmarks/{company_id}")
async def get_expense_benchmarks(
    company_id: UUID,
    category_id: Optional[UUID] = None,
    fiscal_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get expense benchmarks for comparison"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        eb.*,
        ec.category_name,
        ec.category_type
    FROM expense_benchmarks eb
    LEFT JOIN expense_categories ec ON ec.id = eb.category_id
    WHERE eb.company_id = :company_id
    """
    
    params = {'company_id': str(company_id)}
    
    if category_id:
        query += " AND eb.category_id = :category_id"
        params['category_id'] = str(category_id)
    
    if fiscal_year:
        query += " AND eb.fiscal_year = :fiscal_year"
        params['fiscal_year'] = fiscal_year
    
    query += " ORDER BY ec.category_type, ec.category_name"
    
    result = db.execute(text(query), params)
    return [dict(row._mapping) for row in result.fetchall()]

@router.get("/cost-drivers/{company_id}")
async def get_expense_drivers(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get expense-related business drivers"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        bd.*,
        COUNT(dr.id) as num_relationships
    FROM business_drivers bd
    LEFT JOIN driver_relationships dr ON dr.business_driver_id = bd.id
    WHERE bd.company_id = :company_id
    AND bd.category IN ('expense', 'cost', 'operational')
    GROUP BY bd.id
    ORDER BY bd.category, bd.name
    """
    
    result = db.execute(text(query), {'company_id': str(company_id)})
    return [dict(row._mapping) for row in result.fetchall()]