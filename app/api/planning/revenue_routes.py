from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.base import get_db
from app.services.planning.revenue_planning import RevenuePlanningService

router = APIRouter(prefix="/revenue", tags=["Revenue Planning"])

# ============================================
# PYDANTIC MODELS
# ============================================

class RevenueForecastRequest(BaseModel):
    """Request model for revenue forecasting"""
    company_id: UUID
    forecast_months: int = Field(12, ge=1, le=60)
    method: str = Field('trend', description="Forecasting method")
    lookback_months: int = Field(24, ge=6, le=60)
    
    # Method-specific parameters
    trend_type: Optional[str] = 'linear'
    growth_rate: Optional[float] = 0.15
    polynomial_degree: Optional[int] = 2
    confidence_level: Optional[float] = 0.95
    
    # Driver-based parameters
    driver_assumptions: Optional[Dict[str, float]] = None
    
    # Cohort parameters
    new_cohort_size: Optional[float] = 100000
    cohort_growth_rate: Optional[float] = 0.1
    
    # Ensemble parameters
    ensemble_weights: Optional[List[float]] = None
    
    # Pipeline parameters
    stage_conversion: Optional[Dict[str, float]] = None
    
    # Feature flags
    include_segments: bool = True
    include_pipeline: bool = True
    include_seasonality: bool = True
    include_cyclical: bool = False
    cycle_period: Optional[int] = 4
    cycle_amplitude: Optional[float] = 0.1
    
    # External factors for regression
    external_factors: Optional[List[Dict[str, Any]]] = None

class RevenuePlanRequest(BaseModel):
    """Request model for creating revenue plan"""
    company_id: UUID
    plan_name: str
    plan_type: str = Field(..., description="Plan type: baseline, optimistic, pessimistic, target")
    fiscal_year: int
    scenario_id: Optional[UUID] = None
    confidence_level: float = Field(80.0, ge=0, le=100)
    notes: Optional[str] = None

class RevenueStreamRequest(BaseModel):
    """Request model for revenue stream"""
    company_id: UUID
    stream_code: str
    stream_name: str
    stream_type: str = Field(..., description="Type: product, service, subscription, licensing, other")
    parent_stream_id: Optional[UUID] = None
    gl_account_id: Optional[UUID] = None
    recognition_method: Optional[str] = 'point_in_time'
    typical_payment_terms: Optional[int] = 30
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None

class CustomerSegmentRequest(BaseModel):
    """Request model for customer segment"""
    company_id: UUID
    segment_code: str
    segment_name: str
    segment_type: Optional[str] = None
    typical_deal_size: Optional[float] = None
    typical_sales_cycle_days: Optional[int] = None
    churn_rate: Optional[float] = None
    growth_rate: Optional[float] = None

class SalesPipelineRequest(BaseModel):
    """Request model for sales pipeline opportunity"""
    company_id: UUID
    opportunity_name: str
    customer_segment_id: Optional[UUID] = None
    revenue_stream_id: Optional[UUID] = None
    stage: str
    probability: float
    amount: float
    expected_close_date: datetime
    sales_rep_id: Optional[UUID] = None

class PricingModelRequest(BaseModel):
    """Request model for pricing model"""
    company_id: UUID
    revenue_stream_id: UUID
    model_name: str
    pricing_type: str = Field(..., description="Type: fixed, tiered, usage, value, dynamic")
    base_price: Optional[float] = None
    pricing_tiers: Optional[Dict[str, Any]] = None
    discount_rules: Optional[Dict[str, Any]] = None
    effective_date: datetime
    expiration_date: Optional[datetime] = None

class VarianceAnalysisRequest(BaseModel):
    """Request model for revenue variance analysis"""
    company_id: UUID
    period_id: UUID
    revenue_plan_id: Optional[UUID] = None
    stream_filter: Optional[UUID] = None
    segment_filter: Optional[UUID] = None

# ============================================
# REVENUE FORECAST ENDPOINTS
# ============================================

@router.post("/forecast")
async def generate_revenue_forecast(
    request: RevenueForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generate revenue forecast using selected method:
    - trend: Trend analysis (linear, exponential, polynomial)
    - seasonal: Seasonal decomposition
    - regression: Multiple regression with external factors
    - pipeline: Pipeline-based forecasting
    - driver_based: Driver-based planning
    - cohort: Cohort-based analysis
    - ml_ensemble: Ensemble of multiple methods
    """
    service = RevenuePlanningService(db)
    
    try:
        forecast_params = request.dict(exclude_unset=True)
        result = await service.generate_revenue_forecast(
            str(request.company_id),
            forecast_params
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# REVENUE PLAN ENDPOINTS
# ============================================

@router.post("/plans")
async def create_revenue_plan(
    request: RevenuePlanRequest,
    db: Session = Depends(get_db)
):
    """Create a new revenue plan"""
    service = RevenuePlanningService(db)
    
    try:
        plan_id = await service.create_revenue_plan(
            company_id=str(request.company_id),
            plan_name=request.plan_name,
            plan_type=request.plan_type,
            fiscal_year=request.fiscal_year,
            scenario_id=str(request.scenario_id) if request.scenario_id else None,
            confidence_level=request.confidence_level
        )
        return {
            "plan_id": plan_id,
            "status": "created",
            "message": f"Revenue plan '{request.plan_name}' created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans/{company_id}")
async def get_revenue_plans(
    company_id: UUID,
    fiscal_year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get revenue plans for a company"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        id,
        company_id,
        scenario_id,
        plan_name,
        plan_type,
        fiscal_year,
        version,
        status,
        total_planned_revenue,
        confidence_level,
        notes,
        created_at,
        updated_at
    FROM revenue_plans
    WHERE company_id = :company_id
    """
    
    params = {"company_id": str(company_id)}
    
    if fiscal_year:
        query += " AND fiscal_year = :fiscal_year"
        params["fiscal_year"] = fiscal_year
    
    if status:
        query += " AND status = :status"
        params["status"] = status
    
    query += " ORDER BY fiscal_year DESC, created_at DESC"
    
    result = db.execute(text(query), params)
    
    plans = []
    for row in result.fetchall():
        plans.append({
            "id": row[0],
            "company_id": row[1],
            "scenario_id": row[2],
            "plan_name": row[3],
            "plan_type": row[4],
            "fiscal_year": row[5],
            "version": row[6],
            "status": row[7],
            "total_planned_revenue": float(row[8]) if row[8] else None,
            "confidence_level": float(row[9]) if row[9] else None,
            "notes": row[10],
            "created_at": row[11].isoformat() if row[11] else None,
            "updated_at": row[12].isoformat() if row[12] else None
        })
    
    return plans

# ============================================
# REVENUE STREAM ENDPOINTS
# ============================================

@router.post("/streams")
async def create_revenue_stream(
    request: RevenueStreamRequest,
    db: Session = Depends(get_db)
):
    """Create a new revenue stream"""
    
    from sqlalchemy import text
    import uuid
    
    stream_id = str(uuid.uuid4())
    
    query = """
    INSERT INTO revenue_streams (
        id, company_id, stream_code, stream_name, stream_type,
        parent_stream_id, gl_account_id, recognition_method,
        typical_payment_terms, is_recurring, recurring_frequency
    ) VALUES (
        :id, :company_id, :stream_code, :stream_name, :stream_type,
        :parent_stream_id, :gl_account_id, :recognition_method,
        :typical_payment_terms, :is_recurring, :recurring_frequency
    )
    """
    
    try:
        db.execute(text(query), {
            "id": stream_id,
            "company_id": str(request.company_id),
            "stream_code": request.stream_code,
            "stream_name": request.stream_name,
            "stream_type": request.stream_type,
            "parent_stream_id": str(request.parent_stream_id) if request.parent_stream_id else None,
            "gl_account_id": str(request.gl_account_id) if request.gl_account_id else None,
            "recognition_method": request.recognition_method,
            "typical_payment_terms": request.typical_payment_terms,
            "is_recurring": request.is_recurring,
            "recurring_frequency": request.recurring_frequency
        })
        db.commit()
        
        return {
            "stream_id": stream_id,
            "status": "created",
            "message": f"Revenue stream '{request.stream_name}' created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/streams/{company_id}")
async def get_revenue_streams(
    company_id: UUID,
    stream_type: Optional[str] = Query(None),
    is_recurring: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get revenue streams for a company"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        rs.*,
        ga.account_name as gl_account_name,
        parent.stream_name as parent_stream_name
    FROM revenue_streams rs
    LEFT JOIN gl_accounts ga ON ga.id = rs.gl_account_id
    LEFT JOIN revenue_streams parent ON parent.id = rs.parent_stream_id
    WHERE rs.company_id = :company_id
    AND rs.is_active = true
    """
    
    params = {"company_id": str(company_id)}
    
    if stream_type:
        query += " AND rs.stream_type = :stream_type"
        params["stream_type"] = stream_type
    
    if is_recurring is not None:
        query += " AND rs.is_recurring = :is_recurring"
        params["is_recurring"] = is_recurring
    
    query += " ORDER BY rs.stream_code"
    
    result = db.execute(text(query), params)
    
    streams = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        streams.append({
            "id": row_dict["id"],
            "stream_code": row_dict["stream_code"],
            "stream_name": row_dict["stream_name"],
            "stream_type": row_dict["stream_type"],
            "parent_stream_id": row_dict["parent_stream_id"],
            "parent_stream_name": row_dict.get("parent_stream_name"),
            "gl_account_name": row_dict.get("gl_account_name"),
            "recognition_method": row_dict["recognition_method"],
            "is_recurring": row_dict["is_recurring"],
            "recurring_frequency": row_dict["recurring_frequency"]
        })
    
    return streams

# ============================================
# CUSTOMER SEGMENT ENDPOINTS
# ============================================

@router.post("/segments")
async def create_customer_segment(
    request: CustomerSegmentRequest,
    db: Session = Depends(get_db)
):
    """Create a new customer segment"""
    
    from sqlalchemy import text
    import uuid
    
    segment_id = str(uuid.uuid4())
    
    query = """
    INSERT INTO customer_segments (
        id, company_id, segment_code, segment_name, segment_type,
        typical_deal_size, typical_sales_cycle_days, churn_rate, growth_rate
    ) VALUES (
        :id, :company_id, :segment_code, :segment_name, :segment_type,
        :typical_deal_size, :typical_sales_cycle_days, :churn_rate, :growth_rate
    )
    """
    
    try:
        db.execute(text(query), {
            "id": segment_id,
            "company_id": str(request.company_id),
            "segment_code": request.segment_code,
            "segment_name": request.segment_name,
            "segment_type": request.segment_type,
            "typical_deal_size": request.typical_deal_size,
            "typical_sales_cycle_days": request.typical_sales_cycle_days,
            "churn_rate": request.churn_rate,
            "growth_rate": request.growth_rate
        })
        db.commit()
        
        return {
            "segment_id": segment_id,
            "status": "created",
            "message": f"Customer segment '{request.segment_name}' created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/segments/{company_id}")
async def get_customer_segments(
    company_id: UUID,
    segment_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get customer segments for a company"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        cs.*,
        COUNT(sp.id) as pipeline_opportunities,
        SUM(sp.amount) as pipeline_value
    FROM customer_segments cs
    LEFT JOIN sales_pipeline sp ON sp.customer_segment_id = cs.id AND sp.is_active = true
    WHERE cs.company_id = :company_id
    AND cs.is_active = true
    """
    
    params = {"company_id": str(company_id)}
    
    if segment_type:
        query += " AND cs.segment_type = :segment_type"
        params["segment_type"] = segment_type
    
    query += " GROUP BY cs.id ORDER BY cs.segment_code"
    
    result = db.execute(text(query), params)
    
    segments = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        segments.append({
            "id": row_dict["id"],
            "segment_code": row_dict["segment_code"],
            "segment_name": row_dict["segment_name"],
            "segment_type": row_dict["segment_type"],
            "typical_deal_size": float(row_dict["typical_deal_size"]) if row_dict["typical_deal_size"] else None,
            "typical_sales_cycle_days": row_dict["typical_sales_cycle_days"],
            "churn_rate": float(row_dict["churn_rate"]) if row_dict["churn_rate"] else None,
            "growth_rate": float(row_dict["growth_rate"]) if row_dict["growth_rate"] else None,
            "pipeline_opportunities": row_dict["pipeline_opportunities"],
            "pipeline_value": float(row_dict["pipeline_value"]) if row_dict["pipeline_value"] else 0
        })
    
    return segments

# ============================================
# SALES PIPELINE ENDPOINTS
# ============================================

@router.post("/pipeline")
async def create_pipeline_opportunity(
    request: SalesPipelineRequest,
    db: Session = Depends(get_db)
):
    """Create a new sales pipeline opportunity"""
    
    from sqlalchemy import text
    import uuid
    
    opportunity_id = str(uuid.uuid4())
    
    query = """
    INSERT INTO sales_pipeline (
        id, company_id, opportunity_name, customer_segment_id,
        revenue_stream_id, stage, probability, amount,
        expected_close_date, sales_rep_id, created_date
    ) VALUES (
        :id, :company_id, :opportunity_name, :customer_segment_id,
        :revenue_stream_id, :stage, :probability, :amount,
        :expected_close_date, :sales_rep_id, CURRENT_DATE
    )
    """
    
    try:
        db.execute(text(query), {
            "id": opportunity_id,
            "company_id": str(request.company_id),
            "opportunity_name": request.opportunity_name,
            "customer_segment_id": str(request.customer_segment_id) if request.customer_segment_id else None,
            "revenue_stream_id": str(request.revenue_stream_id) if request.revenue_stream_id else None,
            "stage": request.stage,
            "probability": request.probability,
            "amount": request.amount,
            "expected_close_date": request.expected_close_date,
            "sales_rep_id": str(request.sales_rep_id) if request.sales_rep_id else None
        })
        db.commit()
        
        return {
            "opportunity_id": opportunity_id,
            "status": "created",
            "message": f"Pipeline opportunity '{request.opportunity_name}' created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pipeline/{company_id}")
async def get_pipeline_opportunities(
    company_id: UUID,
    stage: Optional[str] = Query(None),
    segment_id: Optional[UUID] = Query(None),
    stream_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """Get sales pipeline opportunities"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        sp.*,
        cs.segment_name,
        rs.stream_name
    FROM sales_pipeline sp
    LEFT JOIN customer_segments cs ON cs.id = sp.customer_segment_id
    LEFT JOIN revenue_streams rs ON rs.id = sp.revenue_stream_id
    WHERE sp.company_id = :company_id
    AND sp.is_active = true
    """
    
    params = {"company_id": str(company_id)}
    
    if stage:
        query += " AND sp.stage = :stage"
        params["stage"] = stage
    
    if segment_id:
        query += " AND sp.customer_segment_id = :segment_id"
        params["segment_id"] = str(segment_id)
    
    if stream_id:
        query += " AND sp.revenue_stream_id = :stream_id"
        params["stream_id"] = str(stream_id)
    
    query += " ORDER BY sp.expected_close_date"
    
    result = db.execute(text(query), params)
    
    opportunities = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        opportunities.append({
            "id": row_dict["id"],
            "opportunity_name": row_dict["opportunity_name"],
            "segment_name": row_dict.get("segment_name"),
            "stream_name": row_dict.get("stream_name"),
            "stage": row_dict["stage"],
            "probability": float(row_dict["probability"]),
            "amount": float(row_dict["amount"]),
            "weighted_amount": float(row_dict["amount"]) * float(row_dict["probability"]) / 100,
            "expected_close_date": row_dict["expected_close_date"].isoformat() if row_dict["expected_close_date"] else None,
            "days_in_stage": row_dict["days_in_stage"]
        })
    
    return opportunities

@router.get("/pipeline/summary/{company_id}")
async def get_pipeline_summary(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get pipeline summary by stage"""
    
    service = RevenuePlanningService(db)
    
    try:
        summary = await service._get_pipeline_metrics(str(company_id))
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# PRICING MODEL ENDPOINTS
# ============================================

@router.post("/pricing")
async def create_pricing_model(
    request: PricingModelRequest,
    db: Session = Depends(get_db)
):
    """Create a new pricing model"""
    
    from sqlalchemy import text
    import uuid
    import json
    
    model_id = str(uuid.uuid4())
    
    query = """
    INSERT INTO pricing_models (
        id, company_id, revenue_stream_id, model_name, pricing_type,
        base_price, pricing_tiers, discount_rules, effective_date, expiration_date
    ) VALUES (
        :id, :company_id, :revenue_stream_id, :model_name, :pricing_type,
        :base_price, :pricing_tiers, :discount_rules, :effective_date, :expiration_date
    )
    """
    
    try:
        db.execute(text(query), {
            "id": model_id,
            "company_id": str(request.company_id),
            "revenue_stream_id": str(request.revenue_stream_id),
            "model_name": request.model_name,
            "pricing_type": request.pricing_type,
            "base_price": request.base_price,
            "pricing_tiers": json.dumps(request.pricing_tiers) if request.pricing_tiers else None,
            "discount_rules": json.dumps(request.discount_rules) if request.discount_rules else None,
            "effective_date": request.effective_date,
            "expiration_date": request.expiration_date
        })
        db.commit()
        
        return {
            "model_id": model_id,
            "status": "created",
            "message": f"Pricing model '{request.model_name}' created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pricing/{company_id}")
async def get_pricing_models(
    company_id: UUID,
    stream_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get pricing models for a company"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        pm.*,
        rs.stream_name
    FROM pricing_models pm
    JOIN revenue_streams rs ON rs.id = pm.revenue_stream_id
    WHERE pm.company_id = :company_id
    """
    
    params = {"company_id": str(company_id)}
    
    if stream_id:
        query += " AND pm.revenue_stream_id = :stream_id"
        params["stream_id"] = str(stream_id)
    
    if active_only:
        query += " AND pm.is_active = true AND (pm.expiration_date IS NULL OR pm.expiration_date > CURRENT_DATE)"
    
    query += " ORDER BY pm.effective_date DESC"
    
    result = db.execute(text(query), params)
    
    models = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        models.append({
            "id": row_dict["id"],
            "stream_name": row_dict["stream_name"],
            "model_name": row_dict["model_name"],
            "pricing_type": row_dict["pricing_type"],
            "base_price": float(row_dict["base_price"]) if row_dict["base_price"] else None,
            "effective_date": row_dict["effective_date"].isoformat() if row_dict["effective_date"] else None,
            "expiration_date": row_dict["expiration_date"].isoformat() if row_dict["expiration_date"] else None,
            "is_active": row_dict["is_active"]
        })
    
    return models

# ============================================
# METRICS AND ANALYSIS ENDPOINTS
# ============================================

@router.get("/metrics/{company_id}")
async def get_revenue_metrics(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get key revenue metrics including MRR, ARR, and growth rates"""
    
    service = RevenuePlanningService(db)
    
    try:
        metrics = await service._calculate_recurring_metrics(str(company_id))
        
        # Add additional metrics
        segments = await service._analyze_revenue_segments(str(company_id))
        pipeline = await service._get_pipeline_metrics(str(company_id))
        
        return {
            "recurring_metrics": metrics,
            "segments": segments,
            "pipeline": pipeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/variance-analysis")
async def analyze_revenue_variance(
    request: VarianceAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze variance between actual and planned revenue"""
    
    from sqlalchemy import text
    
    query = """
    WITH actual_revenue AS (
        SELECT 
            fp.id as period_id,
            SUM(gtl.credit_amount) as actual_amount
        FROM fiscal_periods fp
        LEFT JOIN gl_transactions gt ON gt.company_id = fp.company_id
            AND gt.transaction_date BETWEEN fp.start_date AND fp.end_date
            AND gt.is_posted = true
        LEFT JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
        LEFT JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
        WHERE fp.id = :period_id
        AND ga.account_type = 'revenue'
        GROUP BY fp.id
    ),
    planned_revenue AS (
        SELECT 
            rfl.fiscal_period_id as period_id,
            SUM(rfl.forecast_amount) as planned_amount
        FROM revenue_forecast_lines rfl
        WHERE rfl.fiscal_period_id = :period_id
    """
    
    if request.revenue_plan_id:
        query += " AND rfl.revenue_plan_id = :plan_id"
    
    if request.stream_filter:
        query += " AND rfl.revenue_stream_id = :stream_id"
    
    if request.segment_filter:
        query += " AND rfl.customer_segment_id = :segment_id"
    
    query += """
        GROUP BY rfl.fiscal_period_id
    )
    SELECT 
        ar.actual_amount,
        pr.planned_amount,
        (ar.actual_amount - pr.planned_amount) as variance,
        CASE 
            WHEN pr.planned_amount > 0 THEN 
                ((ar.actual_amount - pr.planned_amount) / pr.planned_amount * 100)
            ELSE 0
        END as variance_pct
    FROM actual_revenue ar
    LEFT JOIN planned_revenue pr ON pr.period_id = ar.period_id
    """
    
    params = {
        "period_id": str(request.period_id),
        "plan_id": str(request.revenue_plan_id) if request.revenue_plan_id else None,
        "stream_id": str(request.stream_filter) if request.stream_filter else None,
        "segment_id": str(request.segment_filter) if request.segment_filter else None
    }
    
    result = db.execute(text(query), {k: v for k, v in params.items() if v is not None})
    row = result.fetchone()
    
    if row:
        return {
            "period_id": str(request.period_id),
            "actual_revenue": float(row[0]) if row[0] else 0,
            "planned_revenue": float(row[1]) if row[1] else 0,
            "variance": float(row[2]) if row[2] else 0,
            "variance_pct": float(row[3]) if row[3] else 0,
            "status": "over_target" if row[2] and row[2] > 0 else "under_target"
        }
    
    return {
        "period_id": str(request.period_id),
        "actual_revenue": 0,
        "planned_revenue": 0,
        "variance": 0,
        "variance_pct": 0,
        "status": "no_data"
    }

@router.get("/cohorts/{company_id}")
async def get_cohort_analysis(
    company_id: UUID,
    segment_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """Get cohort analysis with retention curves"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        rc.cohort_name,
        rc.cohort_date,
        rc.initial_customers,
        rc.initial_revenue,
        cr.period_offset,
        cr.retained_customers,
        cr.retained_revenue,
        cr.retention_rate,
        cr.revenue_retention_rate
    FROM revenue_cohorts rc
    LEFT JOIN cohort_retention cr ON cr.cohort_id = rc.id
    WHERE rc.company_id = :company_id
    """
    
    params = {"company_id": str(company_id)}
    
    if segment_id:
        query += " AND rc.customer_segment_id = :segment_id"
        params["segment_id"] = str(segment_id)
    
    query += " ORDER BY rc.cohort_date DESC, cr.period_offset"
    
    result = db.execute(text(query), params)
    
    cohorts = {}
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        cohort_name = row_dict["cohort_name"]
        
        if cohort_name not in cohorts:
            cohorts[cohort_name] = {
                "cohort_name": cohort_name,
                "cohort_date": row_dict["cohort_date"].isoformat() if row_dict["cohort_date"] else None,
                "initial_customers": row_dict["initial_customers"],
                "initial_revenue": float(row_dict["initial_revenue"]) if row_dict["initial_revenue"] else 0,
                "retention_curve": []
            }
        
        if row_dict["period_offset"] is not None:
            cohorts[cohort_name]["retention_curve"].append({
                "month": row_dict["period_offset"],
                "retained_customers": row_dict["retained_customers"],
                "retained_revenue": float(row_dict["retained_revenue"]) if row_dict["retained_revenue"] else 0,
                "retention_rate": float(row_dict["retention_rate"]) if row_dict["retention_rate"] else 0,
                "revenue_retention_rate": float(row_dict["revenue_retention_rate"]) if row_dict["revenue_retention_rate"] else 0
            })
    
    return list(cohorts.values())

@router.get("/seasonality/{company_id}")
async def get_seasonality_patterns(
    company_id: UUID,
    stream_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """Get revenue seasonality patterns"""
    
    from sqlalchemy import text
    
    query = """
    SELECT 
        rs.stream_name,
        rse.month_number,
        rse.seasonality_index,
        rse.historical_avg
    FROM revenue_seasonality rse
    LEFT JOIN revenue_streams rs ON rs.id = rse.revenue_stream_id
    WHERE rse.company_id = :company_id
    AND rse.is_active = true
    """
    
    params = {"company_id": str(company_id)}
    
    if stream_id:
        query += " AND rse.revenue_stream_id = :stream_id"
        params["stream_id"] = str(stream_id)
    
    query += " ORDER BY rs.stream_name, rse.month_number"
    
    result = db.execute(text(query), params)
    
    seasonality = {}
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        stream_name = row_dict["stream_name"] or "Overall"
        
        if stream_name not in seasonality:
            seasonality[stream_name] = {
                "stream": stream_name,
                "monthly_indices": {}
            }
        
        seasonality[stream_name]["monthly_indices"][row_dict["month_number"]] = {
            "index": float(row_dict["seasonality_index"]) if row_dict["seasonality_index"] else 1.0,
            "historical_avg": float(row_dict["historical_avg"]) if row_dict["historical_avg"] else 0
        }
    
    return list(seasonality.values())