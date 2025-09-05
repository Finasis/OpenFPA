from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date

from ..models.base import get_db
from ..services import (
    VarianceAnalysisService,
    KPIManagementService,
    ForecastingService,
    DashboardService
)

router = APIRouter()

# ============================================
# VARIANCE ANALYSIS ENDPOINTS
# ============================================

@router.get("/variance-analysis/{company_id}/{fiscal_period_id}", tags=["Analytics"])
async def get_variance_analysis(
    company_id: str,
    fiscal_period_id: str,
    cost_center_id: Optional[str] = Query(None),
    gl_account_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get variance analysis for a fiscal period"""
    service = VarianceAnalysisService(db)
    return await service.calculate_variance_for_period(
        company_id, fiscal_period_id, cost_center_id, gl_account_id
    )

@router.get("/variance-analysis/trends/{company_id}/{gl_account_id}", tags=["Analytics"])
async def get_variance_trends(
    company_id: str,
    gl_account_id: str,
    periods: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db)
):
    """Get variance trends over multiple periods"""
    service = VarianceAnalysisService(db)
    return await service.get_variance_trends(company_id, gl_account_id, periods)

@router.get("/variance-analysis/top-variances/{company_id}/{fiscal_period_id}", tags=["Analytics"])
async def get_top_variances(
    company_id: str,
    fiscal_period_id: str,
    limit: int = Query(10, ge=1, le=50),
    variance_type: str = Query("absolute", regex="^(absolute|percentage)$"),
    db: Session = Depends(get_db)
):
    """Get top variances for a period"""
    service = VarianceAnalysisService(db)
    return await service.get_top_variances(company_id, fiscal_period_id, limit, variance_type)

@router.get("/variance-analysis/summary/{company_id}/{fiscal_period_id}", tags=["Analytics"])
async def get_variance_summary_by_account_type(
    company_id: str,
    fiscal_period_id: str,
    db: Session = Depends(get_db)
):
    """Get variance summary grouped by account type"""
    service = VarianceAnalysisService(db)
    return await service.get_variance_summary_by_account_type(company_id, fiscal_period_id)

# ============================================
# KPI MANAGEMENT ENDPOINTS
# ============================================

@router.get("/kpis/financial/{company_id}/{fiscal_period_id}", tags=["Analytics"])
async def get_financial_kpis(
    company_id: str,
    fiscal_period_id: str,
    db: Session = Depends(get_db)
):
    """Calculate standard financial KPIs automatically"""
    service = KPIManagementService(db)
    return await service.calculate_financial_kpis(company_id, fiscal_period_id)

@router.get("/kpis/trends/{kpi_id}", tags=["Analytics"])
async def get_kpi_trends(
    kpi_id: str,
    periods: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db)
):
    """Get KPI trends over multiple periods"""
    service = KPIManagementService(db)
    return await service.get_kpi_trends(kpi_id, periods)

@router.get("/kpis/dashboard/{company_id}/{fiscal_period_id}", tags=["Analytics"])
async def get_kpi_dashboard_summary(
    company_id: str,
    fiscal_period_id: str,
    db: Session = Depends(get_db)
):
    """Get KPI summary for dashboard display"""
    service = KPIManagementService(db)
    return await service.get_kpi_dashboard_summary(company_id, fiscal_period_id)

@router.get("/kpis/performance/{company_id}/{fiscal_year}", tags=["Analytics"])
async def get_kpi_performance_summary(
    company_id: str,
    fiscal_year: int,
    db: Session = Depends(get_db)
):
    """Get overall KPI performance summary for the year"""
    service = KPIManagementService(db)
    return await service.get_kpi_performance_summary(company_id, fiscal_year)

@router.get("/kpis/alerts/{company_id}/{fiscal_period_id}", tags=["Analytics"])
async def get_kpi_alerts(
    company_id: str,
    fiscal_period_id: str,
    variance_threshold: float = Query(10.0, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """Get KPIs that are significantly off target"""
    service = KPIManagementService(db)
    return await service.get_kpi_alerts(company_id, fiscal_period_id, variance_threshold)

# ============================================
# FORECASTING ENDPOINTS
# ============================================

@router.get("/forecasting/historical/{company_id}/{gl_account_id}", tags=["Analytics"])
async def get_historical_data(
    company_id: str,
    gl_account_id: str,
    periods: int = Query(24, ge=6, le=60),
    db: Session = Depends(get_db)
):
    """Get historical actuals for forecasting"""
    service = ForecastingService(db)
    return await service.get_historical_data(company_id, gl_account_id, periods)

@router.post("/forecasting/linear-trend/{company_id}/{gl_account_id}", tags=["Analytics"])
async def create_linear_trend_forecast(
    company_id: str,
    gl_account_id: str,
    forecast_periods: int = Query(12, ge=1, le=24),
    historical_periods: int = Query(24, ge=6, le=60),
    db: Session = Depends(get_db)
):
    """Create linear trend forecast using historical data"""
    service = ForecastingService(db)
    return await service.create_linear_trend_forecast(
        company_id, gl_account_id, forecast_periods, historical_periods
    )

@router.post("/forecasting/seasonal/{company_id}/{gl_account_id}", tags=["Analytics"])
async def create_seasonal_forecast(
    company_id: str,
    gl_account_id: str,
    forecast_periods: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """Create seasonal forecast using historical patterns"""
    service = ForecastingService(db)
    return await service.create_seasonal_forecast(company_id, gl_account_id, forecast_periods)

@router.post("/forecasting/moving-average/{company_id}/{gl_account_id}", tags=["Analytics"])
async def create_moving_average_forecast(
    company_id: str,
    gl_account_id: str,
    window_size: int = Query(6, ge=3, le=12),
    forecast_periods: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """Create moving average forecast"""
    service = ForecastingService(db)
    return await service.create_moving_average_forecast(
        company_id, gl_account_id, window_size, forecast_periods
    )

@router.post("/forecasting/driver-based/{company_id}/{gl_account_id}", tags=["Analytics"])
async def create_driver_based_forecast(
    company_id: str,
    gl_account_id: str,
    forecast_periods: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """Create forecast based on business drivers"""
    service = ForecastingService(db)
    return await service.create_driver_based_forecast(company_id, gl_account_id, forecast_periods)

@router.get("/forecasting/accuracy/{forecast_model_id}", tags=["Analytics"])
async def get_forecast_accuracy(
    forecast_model_id: str,
    periods_back: int = Query(6, ge=2, le=24),
    db: Session = Depends(get_db)
):
    """Calculate forecast accuracy for a model"""
    service = ForecastingService(db)
    return await service.get_forecast_accuracy(forecast_model_id, periods_back)

# ============================================
# DASHBOARD ENDPOINTS
# ============================================

@router.get("/dashboard/executive/{company_id}", tags=["Analytics"])
async def get_executive_dashboard(
    company_id: str,
    fiscal_period_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get comprehensive executive dashboard data"""
    service = DashboardService(db)
    return await service.get_executive_dashboard_data(company_id, fiscal_period_id)

@router.get("/dashboard/operational/{company_id}", tags=["Analytics"])
async def get_operational_dashboard(
    company_id: str,
    cost_center_id: Optional[str] = Query(None),
    fiscal_period_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get operational dashboard data for department managers"""
    service = DashboardService(db)
    return await service.get_operational_dashboard_data(
        company_id, cost_center_id, fiscal_period_id
    )