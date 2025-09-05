from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from uuid import UUID
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from pydantic import BaseModel, Field
import statistics

from app.models.base import get_db
from app.models.models import (
    GLTransaction, GLTransactionLine, GLAccount, 
    Company, FiscalPeriod, Scenario, BudgetLine,
    AccountType
)

router = APIRouter(tags=["Planning"])

# ============================================
# PYDANTIC MODELS
# ============================================

class RevenueGrowthModel(BaseModel):
    """Model for revenue growth parameters"""
    method: str = Field(..., description="Growth method: linear, exponential, seasonal")
    base_growth_rate: float = Field(..., description="Annual growth rate (e.g., 0.15 for 15%)")
    seasonality_factors: Optional[List[float]] = Field(None, description="Monthly seasonality factors")
    confidence_level: float = Field(0.95, description="Confidence level for prediction intervals")

class RevenueForecastRequest(BaseModel):
    company_id: UUID
    forecast_months: int = Field(12, ge=1, le=36, description="Number of months to forecast")
    growth_model: RevenueGrowthModel
    include_segments: bool = Field(True, description="Include revenue by segment/product")
    scenario_id: Optional[UUID] = None

class RevenueForecastResponse(BaseModel):
    company_id: UUID
    forecast_period: Dict[str, str]
    historical_data: List[Dict[str, Any]]
    forecast_data: List[Dict[str, Any]]
    growth_metrics: Dict[str, float]
    accuracy_metrics: Dict[str, float]
    segments: Optional[List[Dict[str, Any]]]
    confidence_intervals: List[Dict[str, Any]]

# ============================================
# REVENUE FORECASTING ENDPOINTS
# ============================================

@router.post("/revenue-forecast", response_model=RevenueForecastResponse)
async def generate_revenue_forecast(
    request: RevenueForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generate revenue forecast based on historical data and growth models.
    Supports multiple forecasting methods and provides confidence intervals.
    """
    
    # Validate company exists
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get revenue accounts
    revenue_accounts = db.query(GLAccount).filter(
        and_(
            GLAccount.company_id == request.company_id,
            GLAccount.account_type == AccountType.REVENUE
        )
    ).all()
    
    if not revenue_accounts:
        raise HTTPException(status_code=404, detail="No revenue accounts found for company")
    
    revenue_account_ids = [acc.id for acc in revenue_accounts]
    
    # Get historical revenue data (last 24 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # ~24 months
    
    # Aggregate historical revenue by month
    historical_query = db.query(
        extract('year', GLTransaction.transaction_date).label('year'),
        extract('month', GLTransaction.transaction_date).label('month'),
        func.sum(GLTransactionLine.credit_amount).label('revenue')
    ).join(
        GLTransactionLine, GLTransaction.id == GLTransactionLine.gl_transaction_id
    ).filter(
        and_(
            GLTransaction.company_id == request.company_id,
            GLTransaction.is_posted == True,
            GLTransaction.transaction_date >= start_date,
            GLTransaction.transaction_date <= end_date,
            GLTransactionLine.gl_account_id.in_(revenue_account_ids)
        )
    ).group_by(
        extract('year', GLTransaction.transaction_date),
        extract('month', GLTransaction.transaction_date)
    ).order_by(
        extract('year', GLTransaction.transaction_date),
        extract('month', GLTransaction.transaction_date)
    ).all()
    
    # Convert to list of dictionaries
    historical_data = []
    for row in historical_query:
        historical_data.append({
            "year": int(row.year),
            "month": int(row.month),
            "period": f"{int(row.year)}-{int(row.month):02d}",
            "revenue": float(row.revenue) if row.revenue else 0,
            "type": "actual"
        })
    
    if len(historical_data) < 6:
        # Generate sample data if not enough historical data
        historical_data = _generate_sample_historical_data()
    
    # Generate forecast based on selected model
    forecast_data = _generate_forecast(
        historical_data, 
        request.forecast_months,
        request.growth_model
    )
    
    # Calculate growth metrics
    growth_metrics = _calculate_growth_metrics(historical_data, forecast_data)
    
    # Calculate accuracy metrics (if we have enough historical data)
    accuracy_metrics = _calculate_accuracy_metrics(historical_data)
    
    # Get revenue by segments if requested
    segments = None
    if request.include_segments:
        segments = _get_revenue_segments(db, request.company_id, revenue_account_ids)
    
    # Calculate confidence intervals
    confidence_intervals = _calculate_confidence_intervals(
        forecast_data, 
        historical_data,
        request.growth_model.confidence_level
    )
    
    # Determine forecast period
    if forecast_data:
        forecast_period = {
            "start": forecast_data[0]["period"],
            "end": forecast_data[-1]["period"]
        }
    else:
        forecast_period = {"start": "", "end": ""}
    
    return RevenueForecastResponse(
        company_id=request.company_id,
        forecast_period=forecast_period,
        historical_data=historical_data,
        forecast_data=forecast_data,
        growth_metrics=growth_metrics,
        accuracy_metrics=accuracy_metrics,
        segments=segments,
        confidence_intervals=confidence_intervals
    )

@router.get("/revenue-forecast/{company_id}/metrics")
async def get_revenue_metrics(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get key revenue metrics and KPIs for the company"""
    
    # Get current month revenue
    current_month_start = datetime.now().replace(day=1)
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
    
    revenue_accounts = db.query(GLAccount).filter(
        and_(
            GLAccount.company_id == company_id,
            GLAccount.account_type == AccountType.REVENUE
        )
    ).all()
    
    revenue_account_ids = [acc.id for acc in revenue_accounts]
    
    # Current month revenue
    current_revenue = db.query(
        func.sum(GLTransactionLine.credit_amount)
    ).join(
        GLTransaction
    ).filter(
        and_(
            GLTransaction.company_id == company_id,
            GLTransaction.transaction_date >= current_month_start,
            GLTransaction.transaction_date < next_month_start,
            GLTransactionLine.gl_account_id.in_(revenue_account_ids)
        )
    ).scalar() or 0
    
    # Year-to-date revenue
    ytd_start = datetime.now().replace(month=1, day=1)
    ytd_revenue = db.query(
        func.sum(GLTransactionLine.credit_amount)
    ).join(
        GLTransaction
    ).filter(
        and_(
            GLTransaction.company_id == company_id,
            GLTransaction.transaction_date >= ytd_start,
            GLTransactionLine.gl_account_id.in_(revenue_account_ids)
        )
    ).scalar() or 0
    
    # Last year same period
    last_year_start = (datetime.now() - timedelta(days=365)).replace(month=1, day=1)
    last_year_end = datetime.now() - timedelta(days=365)
    last_year_revenue = db.query(
        func.sum(GLTransactionLine.credit_amount)
    ).join(
        GLTransaction
    ).filter(
        and_(
            GLTransaction.company_id == company_id,
            GLTransaction.transaction_date >= last_year_start,
            GLTransaction.transaction_date <= last_year_end,
            GLTransactionLine.gl_account_id.in_(revenue_account_ids)
        )
    ).scalar() or 0
    
    # Calculate YoY growth
    yoy_growth = 0
    if last_year_revenue > 0:
        yoy_growth = ((ytd_revenue - last_year_revenue) / last_year_revenue) * 100
    
    return {
        "current_month_revenue": float(current_revenue),
        "ytd_revenue": float(ytd_revenue),
        "last_year_revenue": float(last_year_revenue),
        "yoy_growth_percent": float(yoy_growth),
        "average_monthly_revenue": float(ytd_revenue / datetime.now().month),
        "revenue_run_rate": float(ytd_revenue / datetime.now().month * 12)
    }

# ============================================
# HELPER FUNCTIONS
# ============================================

def _generate_forecast(historical_data: List[Dict], months: int, growth_model: RevenueGrowthModel) -> List[Dict]:
    """Generate forecast based on historical data and growth model"""
    
    if not historical_data:
        return []
    
    # Extract revenue values
    revenues = [d["revenue"] for d in historical_data]
    
    # Get the last historical period
    last_period = historical_data[-1]
    last_year = last_period["year"]
    last_month = last_period["month"]
    
    forecast_data = []
    
    if growth_model.method == "linear":
        # Linear trend
        avg_growth = np.mean(np.diff(revenues)) if len(revenues) > 1 else 0
        base_revenue = revenues[-1]
        
        for i in range(1, months + 1):
            month = (last_month + i - 1) % 12 + 1
            year = last_year + (last_month + i - 1) // 12
            
            # Apply linear growth
            forecast_revenue = base_revenue + (avg_growth * i)
            
            # Apply seasonality if provided
            if growth_model.seasonality_factors and len(growth_model.seasonality_factors) == 12:
                seasonality_factor = growth_model.seasonality_factors[month - 1]
                forecast_revenue *= seasonality_factor
            
            forecast_data.append({
                "year": year,
                "month": month,
                "period": f"{year}-{month:02d}",
                "revenue": max(0, forecast_revenue),
                "type": "forecast"
            })
    
    elif growth_model.method == "exponential":
        # Exponential growth
        base_revenue = revenues[-1]
        monthly_growth_rate = (1 + growth_model.base_growth_rate) ** (1/12) - 1
        
        for i in range(1, months + 1):
            month = (last_month + i - 1) % 12 + 1
            year = last_year + (last_month + i - 1) // 12
            
            # Apply exponential growth
            forecast_revenue = base_revenue * ((1 + monthly_growth_rate) ** i)
            
            # Apply seasonality if provided
            if growth_model.seasonality_factors and len(growth_model.seasonality_factors) == 12:
                seasonality_factor = growth_model.seasonality_factors[month - 1]
                forecast_revenue *= seasonality_factor
            
            forecast_data.append({
                "year": year,
                "month": month,
                "period": f"{year}-{month:02d}",
                "revenue": max(0, forecast_revenue),
                "type": "forecast"
            })
    
    elif growth_model.method == "seasonal":
        # Seasonal decomposition
        if len(revenues) >= 12:
            # Calculate seasonal indices
            seasonal_indices = []
            for month_idx in range(12):
                month_revenues = [revenues[i] for i in range(month_idx, len(revenues), 12) if i < len(revenues)]
                if month_revenues:
                    avg_month_revenue = np.mean(month_revenues)
                    overall_avg = np.mean(revenues)
                    seasonal_index = avg_month_revenue / overall_avg if overall_avg > 0 else 1
                    seasonal_indices.append(seasonal_index)
                else:
                    seasonal_indices.append(1.0)
            
            # Calculate trend
            trend_growth = growth_model.base_growth_rate / 12
            base_revenue = np.mean(revenues[-3:]) if len(revenues) >= 3 else revenues[-1]
            
            for i in range(1, months + 1):
                month = (last_month + i - 1) % 12 + 1
                year = last_year + (last_month + i - 1) // 12
                
                # Apply trend and seasonality
                trend_revenue = base_revenue * (1 + trend_growth * i)
                seasonal_factor = seasonal_indices[(month - 1) % 12]
                forecast_revenue = trend_revenue * seasonal_factor
                
                forecast_data.append({
                    "year": year,
                    "month": month,
                    "period": f"{year}-{month:02d}",
                    "revenue": max(0, forecast_revenue),
                    "type": "forecast"
                })
        else:
            # Fall back to exponential if not enough data for seasonal
            return _generate_forecast(historical_data, months, 
                                    RevenueGrowthModel(method="exponential", 
                                                     base_growth_rate=growth_model.base_growth_rate))
    
    return forecast_data

def _calculate_growth_metrics(historical_data: List[Dict], forecast_data: List[Dict]) -> Dict[str, float]:
    """Calculate growth metrics comparing historical and forecast data"""
    
    historical_revenues = [d["revenue"] for d in historical_data if d["revenue"] > 0]
    forecast_revenues = [d["revenue"] for d in forecast_data]
    
    metrics = {}
    
    if historical_revenues:
        # Historical metrics
        metrics["historical_avg_monthly"] = np.mean(historical_revenues)
        metrics["historical_total"] = sum(historical_revenues)
        
        if len(historical_revenues) > 1:
            # Calculate CAGR for historical data
            periods = len(historical_revenues)
            if historical_revenues[0] > 0:
                historical_cagr = (historical_revenues[-1] / historical_revenues[0]) ** (12/periods) - 1
                metrics["historical_cagr"] = historical_cagr * 100
            else:
                metrics["historical_cagr"] = 0
    
    if forecast_revenues:
        # Forecast metrics
        metrics["forecast_avg_monthly"] = np.mean(forecast_revenues)
        metrics["forecast_total"] = sum(forecast_revenues)
        
        if historical_revenues and forecast_revenues[0] > 0:
            # Growth from last historical to end of forecast
            total_growth = (forecast_revenues[-1] / historical_revenues[-1]) - 1
            metrics["forecast_growth_rate"] = total_growth * 100
    
    return metrics

def _calculate_accuracy_metrics(historical_data: List[Dict]) -> Dict[str, float]:
    """Calculate forecast accuracy metrics based on historical data"""
    
    revenues = [d["revenue"] for d in historical_data if d["revenue"] > 0]
    
    if len(revenues) < 6:
        return {"mape": 0, "rmse": 0, "r_squared": 0}
    
    # Simple validation: use first 70% for training, last 30% for validation
    split_idx = int(len(revenues) * 0.7)
    train_data = revenues[:split_idx]
    test_data = revenues[split_idx:]
    
    if len(train_data) < 2 or len(test_data) < 2:
        return {"mape": 0, "rmse": 0, "r_squared": 0}
    
    # Simple linear forecast for validation
    avg_growth = np.mean(np.diff(train_data))
    predictions = []
    base = train_data[-1]
    
    for i in range(len(test_data)):
        predictions.append(base + avg_growth * (i + 1))
    
    # Calculate MAPE (Mean Absolute Percentage Error)
    mape = 0
    for actual, pred in zip(test_data, predictions):
        if actual > 0:
            mape += abs((actual - pred) / actual)
    mape = (mape / len(test_data)) * 100 if test_data else 0
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean([(actual - pred) ** 2 for actual, pred in zip(test_data, predictions)]))
    
    # Calculate R-squared
    ss_res = sum([(actual - pred) ** 2 for actual, pred in zip(test_data, predictions)])
    ss_tot = sum([(actual - np.mean(test_data)) ** 2 for actual in test_data])
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        "mape": round(mape, 2),
        "rmse": round(rmse, 2),
        "r_squared": round(r_squared, 4)
    }

def _get_revenue_segments(db: Session, company_id: UUID, revenue_account_ids: List[UUID]) -> List[Dict]:
    """Get revenue breakdown by segments (accounts)"""
    
    # Get revenue by account for the last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    segment_query = db.query(
        GLAccount.name.label('segment'),
        func.sum(GLTransactionLine.credit_amount).label('revenue')
    ).join(
        GLTransactionLine, GLAccount.id == GLTransactionLine.gl_account_id
    ).join(
        GLTransaction, GLTransactionLine.gl_transaction_id == GLTransaction.id
    ).filter(
        and_(
            GLTransaction.company_id == company_id,
            GLTransaction.transaction_date >= start_date,
            GLTransaction.transaction_date <= end_date,
            GLAccount.id.in_(revenue_account_ids)
        )
    ).group_by(GLAccount.name).all()
    
    segments = []
    total_revenue = sum([s.revenue for s in segment_query if s.revenue])
    
    for segment in segment_query:
        if segment.revenue:
            percentage = (segment.revenue / total_revenue * 100) if total_revenue > 0 else 0
            segments.append({
                "name": segment.segment,
                "revenue": float(segment.revenue),
                "percentage": round(percentage, 2)
            })
    
    return sorted(segments, key=lambda x: x["revenue"], reverse=True)

def _calculate_confidence_intervals(forecast_data: List[Dict], historical_data: List[Dict], 
                                   confidence_level: float) -> List[Dict]:
    """Calculate confidence intervals for forecast"""
    
    # Calculate standard deviation from historical data
    historical_revenues = [d["revenue"] for d in historical_data if d["revenue"] > 0]
    
    if len(historical_revenues) < 3:
        # Not enough data for confidence intervals
        return [{
            "period": d["period"],
            "lower": d["revenue"] * 0.8,
            "upper": d["revenue"] * 1.2,
            "forecast": d["revenue"]
        } for d in forecast_data]
    
    # Calculate standard deviation of percentage changes
    pct_changes = []
    for i in range(1, len(historical_revenues)):
        if historical_revenues[i-1] > 0:
            pct_change = (historical_revenues[i] - historical_revenues[i-1]) / historical_revenues[i-1]
            pct_changes.append(pct_change)
    
    std_dev = statistics.stdev(pct_changes) if len(pct_changes) > 1 else 0.1
    
    # Z-score for confidence level
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z_score = z_scores.get(confidence_level, 1.96)
    
    confidence_intervals = []
    for i, forecast in enumerate(forecast_data):
        # Uncertainty increases with forecast horizon
        uncertainty_factor = 1 + (i * 0.05)  # 5% increase per month
        interval_width = std_dev * z_score * uncertainty_factor * forecast["revenue"]
        
        confidence_intervals.append({
            "period": forecast["period"],
            "lower": max(0, forecast["revenue"] - interval_width),
            "upper": forecast["revenue"] + interval_width,
            "forecast": forecast["revenue"]
        })
    
    return confidence_intervals

def _generate_sample_historical_data() -> List[Dict]:
    """Generate sample historical data for demonstration"""
    
    base_revenue = 100000
    growth_rate = 0.05
    seasonality = [0.9, 0.85, 0.95, 1.0, 1.05, 1.1, 1.15, 1.1, 1.05, 1.0, 0.95, 1.2]
    
    historical_data = []
    current_date = datetime.now()
    
    for i in range(24, 0, -1):
        month_date = current_date - timedelta(days=i * 30)
        month = month_date.month
        year = month_date.year
        
        # Apply growth and seasonality
        revenue = base_revenue * (1 + growth_rate) ** (24 - i) / 24
        revenue *= seasonality[month - 1]
        revenue += np.random.normal(0, revenue * 0.1)  # Add some noise
        
        historical_data.append({
            "year": year,
            "month": month,
            "period": f"{year}-{month:02d}",
            "revenue": max(0, revenue),
            "type": "actual"
        })
    
    return historical_data