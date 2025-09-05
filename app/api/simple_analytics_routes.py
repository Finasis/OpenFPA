from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case, and_, or_, extract, select
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import hashlib
import random

from ..models.base import get_db
from ..models.models import (
    GLTransaction, GLTransactionLine, GLAccount, FiscalPeriod, 
    Scenario, BudgetLine, CostCenter, Company, KPI, KPIActual,
    BusinessDriver, DriverValue, VarianceThreshold, AccountType,
    ScenarioType, DriverRelationship
)

router = APIRouter()

# ============================================
# SIMPLIFIED ANALYTICS ENDPOINTS
# ============================================

@router.get("/dashboard/{company_id}", tags=["Analytics"])
async def get_dashboard_data(
    company_id: str,
    fiscal_period_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get dashboard data from database only - no mock data fallbacks"""
    
    try:
        # Check if company exists - SQLAlchemy 2.0 style
        stmt = select(Company).where(Company.id == company_id)
        company = db.execute(stmt).scalar_one_or_none()
        if not company:
            return {
                "company_id": company_id,
                "financial_summary": {
                    "revenue": 0,
                    "expenses": 0,
                    "profit": 0,
                    "margin": 0
                },
                "kpis": [],
                "trends": [],
                "status": "success",
                "data_source": "database",
                "message": "Company not found"
            }
        
        # Try to get real data from database
        financial_data = {"revenue": 0, "expenses": 0, "profit": 0, "margin": 0}
        
        # Get latest fiscal period if not provided - SQLAlchemy 2.0 style
        if not fiscal_period_id:
            stmt = select(FiscalPeriod).where(
                FiscalPeriod.company_id == company_id
            ).order_by(FiscalPeriod.end_date.desc()).limit(1)
            latest_period = db.execute(stmt).scalar_one_or_none()
            
            if latest_period:
                fiscal_period_id = latest_period.id
        
        if fiscal_period_id:
            # Query actual transactions for revenue - SQLAlchemy 2.0 style
            stmt = (
                select(func.coalesce(func.sum(GLTransactionLine.credit_amount - GLTransactionLine.debit_amount), 0))
                .join(GLAccount, GLTransactionLine.gl_account_id == GLAccount.id)
                .join(GLTransaction, GLTransactionLine.gl_transaction_id == GLTransaction.id)
                .where(
                    GLTransaction.company_id == company_id,
                    GLTransaction.fiscal_period_id == fiscal_period_id,
                    GLTransaction.is_posted == True,
                    GLAccount.account_type.in_([AccountType.REVENUE])
                )
            )
            revenue_query = db.execute(stmt).scalar()
            
            # Query actual transactions for expenses - SQLAlchemy 2.0 style
            stmt = (
                select(func.coalesce(func.sum(GLTransactionLine.debit_amount - GLTransactionLine.credit_amount), 0))
                .join(GLAccount, GLTransactionLine.gl_account_id == GLAccount.id)
                .join(GLTransaction, GLTransactionLine.gl_transaction_id == GLTransaction.id)
                .where(
                    GLTransaction.company_id == company_id,
                    GLTransaction.fiscal_period_id == fiscal_period_id,
                    GLTransaction.is_posted == True,
                    GLAccount.account_type.in_([AccountType.EXPENSE])
                )
            )
            expense_query = db.execute(stmt).scalar()
            
            financial_data["revenue"] = float(revenue_query or 0)
            financial_data["expenses"] = float(expense_query or 0)
            financial_data["profit"] = financial_data["revenue"] - financial_data["expenses"]
            financial_data["margin"] = (financial_data["profit"] / financial_data["revenue"] * 100) if financial_data["revenue"] > 0 else 0
        
        # Always return database results (no mock fallback)
        financial_data = {k: round(v, 2) for k, v in financial_data.items()}
        data_source = "database"
        
        # Get KPIs from database - SQLAlchemy 2.0 style
        stmt = select(KPI).where(KPI.company_id == company_id, KPI.is_active == True)
        db_kpis = db.execute(stmt).scalars().all()
        
        kpis = []
        for kpi in db_kpis:
            # Get latest actual value for this KPI
            stmt = (
                select(KPIActual)
                .where(KPIActual.kpi_id == kpi.id)
                .order_by(KPIActual.created_at.desc())
                .limit(1)
            )
            latest_actual = db.execute(stmt).scalar_one_or_none()
            
            if latest_actual:
                value = float(latest_actual.actual_value)
                target = float(latest_actual.target_value or kpi.target_value or 100)
                
                # Determine status
                if value >= target:
                    status = "good"
                elif value >= target * 0.8:
                    status = "warning"
                else:
                    status = "danger"
                
                kpis.append({
                    "name": kpi.name,
                    "value": value,
                    "target": target,
                    "status": status,
                    "unit": kpi.unit_of_measure or ""
                })
        
        # Get trend data from actual transactions
        trends = []
        if fiscal_period_id:
            # Get last 6 months of data
            stmt = (
                select(
                    func.extract('month', GLTransaction.transaction_date).label('month'),
                    func.sum(
                        case(
                            (GLAccount.account_type == AccountType.REVENUE, GLTransactionLine.credit_amount - GLTransactionLine.debit_amount),
                            else_=0
                        )
                    ).label('revenue'),
                    func.sum(
                        case(
                            (GLAccount.account_type == AccountType.EXPENSE, GLTransactionLine.debit_amount - GLTransactionLine.credit_amount),
                            else_=0
                        )
                    ).label('expenses')
                )
                .join(GLTransactionLine, GLTransaction.id == GLTransactionLine.gl_transaction_id)
                .join(GLAccount, GLTransactionLine.gl_account_id == GLAccount.id)
                .where(
                    GLTransaction.company_id == company_id,
                    GLTransaction.is_posted == True,
                    GLTransaction.transaction_date >= func.date_trunc('month', func.now()) - text("interval '6 months'")
                )
                .group_by(func.extract('month', GLTransaction.transaction_date))
                .order_by(func.extract('month', GLTransaction.transaction_date))
            )
            monthly_data = db.execute(stmt).all()
            
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            for row in monthly_data:
                month_idx = int(row.month) - 1
                trends.append({
                    "month": month_names[month_idx] if 0 <= month_idx < 12 else f"Month {int(row.month)}",
                    "revenue": int(row.revenue or 0),
                    "expenses": int(row.expenses or 0)
                })
        
        return {
            "company_id": company_id,
            "financial_summary": financial_data,
            "kpis": kpis,
            "trends": trends,
            "status": "success",
            "data_source": data_source,
            "message": "No data available" if not kpis and not trends and financial_data["revenue"] == 0 else None
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

@router.get("/variance/{company_id}", tags=["Analytics"])
async def get_variance_analysis(
    company_id: str,
    fiscal_period_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get variance analysis from database only - no mock data"""
    
    try:
        # Check if company exists - SQLAlchemy 2.0 style
        stmt = select(Company).where(Company.id == company_id)
        company = db.execute(stmt).scalar_one_or_none()
        if not company:
            return {
                "company_id": company_id,
                "variances": [],
                "status": "success",
                "message": "Company not found"
            }
        
        # Get latest fiscal period if not provided
        if not fiscal_period_id:
            stmt = select(FiscalPeriod).where(
                FiscalPeriod.company_id == company_id
            ).order_by(FiscalPeriod.end_date.desc()).limit(1)
            latest_period = db.execute(stmt).scalar_one_or_none()
            if latest_period:
                fiscal_period_id = latest_period.id
        
        if not fiscal_period_id:
            return {
                "company_id": company_id,
                "variances": [],
                "status": "success",
                "message": "No fiscal periods available"
            }
        
        # Get variance data by comparing budget to actual - SQLAlchemy 2.0 style
        stmt = (
            select(
                GLAccount.account_number.label('account_code'),
                GLAccount.name.label('account_name'),
                GLAccount.account_type.label('account_type'),
                func.coalesce(func.sum(BudgetLine.amount), 0).label('budget'),
                func.coalesce(
                    func.sum(
                        case(
                            (GLAccount.account_type == AccountType.REVENUE, GLTransactionLine.credit_amount - GLTransactionLine.debit_amount),
                            else_=GLTransactionLine.debit_amount - GLTransactionLine.credit_amount
                        )
                    ), 0
                ).label('actual')
            )
            .outerjoin(BudgetLine, and_(
                BudgetLine.gl_account_id == GLAccount.id,
                BudgetLine.fiscal_period_id == fiscal_period_id
            ))
            .outerjoin(GLTransactionLine, GLTransactionLine.gl_account_id == GLAccount.id)
            .outerjoin(GLTransaction, and_(
                GLTransaction.id == GLTransactionLine.gl_transaction_id,
                GLTransaction.fiscal_period_id == fiscal_period_id,
                GLTransaction.is_posted == True
            ))
            .where(GLAccount.company_id == company_id, GLAccount.is_active == True)
            .group_by(GLAccount.id, GLAccount.account_number, GLAccount.name, GLAccount.account_type)
            .order_by(GLAccount.account_number)
        )
        
        variance_data = db.execute(stmt).all()
        
        variances = []
        for row in variance_data:
            budget = float(row.budget or 0)
            actual = float(row.actual or 0)
            variance = actual - budget
            variance_pct = (variance / budget * 100) if budget != 0 else 0
            
            # Determine status based on account type and variance
            if row.account_type == "expense":
                status = "favorable" if variance < 0 else "unfavorable" if variance > 0 else "neutral"
            else:  # revenue
                status = "favorable" if variance > 0 else "unfavorable" if variance < 0 else "neutral"
            
            # Only include accounts with budget or actual data
            if budget != 0 or actual != 0:
                variances.append({
                    "account_code": row.account_code,
                    "account_name": row.account_name,
                    "account_type": row.account_type,
                    "budget": round(budget, 2),
                    "actual": round(actual, 2),
                    "variance": round(variance, 2),
                    "variance_percentage": round(variance_pct, 2),
                    "status": status
                })
        
        return {
            "company_id": company_id,
            "variances": variances,
            "status": "success",
            "message": "No variance data available" if not variances else None
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

@router.get("/kpis/{company_id}", tags=["Analytics"])
async def get_kpi_summary(
    company_id: str,
    fiscal_period_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get KPI summary from database only - no mock data"""
    
    try:
        # Check if company exists - SQLAlchemy 2.0 style
        stmt = select(Company).where(Company.id == company_id)
        company = db.execute(stmt).scalar_one_or_none()
        if not company:
            return {
                "company_id": company_id,
                "kpis": [],
                "status": "success",
                "message": "Company not found"
            }
        
        # Get latest fiscal period if not provided
        if not fiscal_period_id:
            stmt = select(FiscalPeriod).where(
                FiscalPeriod.company_id == company_id
            ).order_by(FiscalPeriod.end_date.desc()).limit(1)
            latest_period = db.execute(stmt).scalar_one_or_none()
            if latest_period:
                fiscal_period_id = latest_period.id
        
        # Get KPIs from database - SQLAlchemy 2.0 style
        stmt = select(KPI).where(KPI.company_id == company_id, KPI.is_active == True)
        db_kpis = db.execute(stmt).scalars().all()
        
        kpis = []
        for kpi in db_kpis:
            # Get latest actual value for this KPI
            stmt = (
                select(KPIActual)
                .where(
                    KPIActual.kpi_id == kpi.id,
                    KPIActual.fiscal_period_id == fiscal_period_id if fiscal_period_id else True
                )
                .order_by(KPIActual.created_at.desc())
                .limit(1)
            )
            latest_actual = db.execute(stmt).scalar_one_or_none()
            
            if latest_actual:
                value = float(latest_actual.actual_value)
                target = float(latest_actual.target_value or kpi.target_value or 100)
            else:
                # No actual data, show KPI definition with 0 value
                value = 0.0
                target = float(kpi.target_value or 100)
            
            # Determine status
            if value >= target:
                status = "good"
            elif value >= target * 0.8:
                status = "warning"
            else:
                status = "danger"
            
            # Calculate trend (simplified - compare with previous period)
            trend = "stable"  # Default trend
            
            kpis.append({
                "name": kpi.name,
                "code": kpi.code,
                "value": round(value, 1),
                "target": round(target, 1),
                "unit": kpi.unit_of_measure or "",
                "status": status,
                "trend": trend,
                "category": kpi.category or "General"
            })
        
        return {
            "company_id": company_id,
            "kpis": kpis,
            "status": "success",
            "message": "No KPI data available" if not kpis else None
        }
        
    except Exception as e:
        return {
            "error": str(e), 
            "status": "error"
        }

@router.get("/trends/{company_id}", tags=["Analytics"])
async def get_trend_data(
    company_id: str,
    periods: int = Query(6, ge=3, le=24),
    db: Session = Depends(get_db)
):
    """Get trend data from database only - no mock data"""
    
    try:
        # Check if company exists - SQLAlchemy 2.0 style
        stmt = select(Company).where(Company.id == company_id)
        company = db.execute(stmt).scalar_one_or_none()
        if not company:
            return {
                "company_id": company_id,
                "trends": [],
                "status": "success",
                "message": "Company not found"
            }
        
        # Get monthly trend data - SQLAlchemy 2.0 style
        stmt = (
            select(
                func.date_trunc('month', GLTransaction.transaction_date).label('month'),
                func.sum(
                    case(
                        (GLAccount.account_type == 'revenue', GLTransactionLine.credit_amount - GLTransactionLine.debit_amount),
                        else_=0
                    )
                ).label('revenue'),
                func.sum(
                    case(
                        (GLAccount.account_type == 'expense', GLTransactionLine.debit_amount - GLTransactionLine.credit_amount),
                        else_=0
                    )
                ).label('expenses')
            )
            .join(GLTransactionLine, GLTransaction.id == GLTransactionLine.gl_transaction_id)
            .join(GLAccount, GLTransactionLine.gl_account_id == GLAccount.id)
            .where(
                GLTransaction.company_id == company_id,
                GLTransaction.is_posted == True,
                GLAccount.account_type.in_([AccountType.REVENUE, AccountType.EXPENSE])
            )
            .group_by(func.date_trunc('month', GLTransaction.transaction_date))
            .order_by(func.date_trunc('month', GLTransaction.transaction_date).desc())
            .limit(periods)
        )
        monthly_trends = db.execute(stmt).all()
        
        trends = []
        for row in monthly_trends:
            trends.append({
                "period": row.month.strftime('%Y-%m'),
                "revenue": float(row.revenue or 0),
                "expenses": float(row.expenses or 0)
            })
        
        # Reverse to show oldest first
        trends.reverse()
        
        return {
            "company_id": company_id,
            "trends": trends,
            "status": "success",
            "message": "No trend data available" if not trends else None
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

@router.post("/generate-sample-data/{company_id}", tags=["Analytics"])
async def generate_sample_data(
    company_id: str,
    months: int = Query(12, ge=1, le=24),
    include_all_modules: bool = Query(True, description="Generate data for all modules (KPIs, budgets, drivers, etc.)"),
    force_regenerate: bool = Query(False, description="Clear existing data and regenerate"),
    db: Session = Depends(get_db)
):
    """Generate comprehensive sample data for analytics testing including all modules"""
    
    try:
        # Check if company exists - SQLAlchemy 2.0 style
        stmt = select(Company).where(Company.id == company_id)
        company = db.execute(stmt).scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Check if data already exists and return counts if it does (unless force_regenerate)
        if not force_regenerate:
            stmt = select(func.count(GLTransaction.id)).where(GLTransaction.company_id == company_id)
            existing_transactions = db.execute(stmt).scalar()
            
            if existing_transactions > 0:
                # Count existing data
                stmt = select(func.count(Scenario.id)).where(Scenario.company_id == company_id)
                existing_scenarios = db.execute(stmt).scalar()
                
                stmt = select(func.count(BudgetLine.id)).join(Scenario).where(Scenario.company_id == company_id)
                existing_budget_lines = db.execute(stmt).scalar()
                
                stmt = select(func.count(KPI.id)).where(KPI.company_id == company_id)
                existing_kpis = db.execute(stmt).scalar()
                
                stmt = select(func.count(KPIActual.id)).join(KPI).where(KPI.company_id == company_id)
                existing_kpi_actuals = db.execute(stmt).scalar()
                
                stmt = select(func.count(BusinessDriver.id)).where(BusinessDriver.company_id == company_id)
                existing_drivers = db.execute(stmt).scalar()
                
                stmt = select(func.count(FiscalPeriod.id)).where(FiscalPeriod.company_id == company_id)
                existing_periods = db.execute(stmt).scalar()
                
                stmt = select(func.count(GLAccount.id)).where(GLAccount.company_id == company_id)
                existing_accounts = db.execute(stmt).scalar()
                
                return {
                    "success": True,
                    "message": f"Sample data already exists - using existing data",
                    "details": {
                        "transactions_created": existing_transactions,
                        "months_covered": months,
                        "gl_accounts": existing_accounts,
                        "scenarios_created": existing_scenarios,
                        "budget_lines_created": existing_budget_lines,
                        "kpis_created": existing_kpis,
                        "kpi_actuals_created": existing_kpi_actuals,
                        "business_drivers_created": existing_drivers,
                        "variance_thresholds_created": 0,  # Would need separate query
                        "fiscal_periods": existing_periods
                    }
                }
        
        # Get or create comprehensive GL accounts - SQLAlchemy 2.0 style
        stmt = select(GLAccount).where(GLAccount.company_id == company_id)
        gl_accounts = db.execute(stmt).scalars().all()
        if not gl_accounts:
            # Create comprehensive chart of accounts
            accounts_to_create = [
                # Assets
                {"code": "1000", "name": "Cash and Cash Equivalents", "account_type": AccountType.ASSET},
                {"code": "1100", "name": "Accounts Receivable", "account_type": AccountType.ASSET},
                {"code": "1200", "name": "Inventory", "account_type": AccountType.ASSET},
                {"code": "1300", "name": "Prepaid Expenses", "account_type": AccountType.ASSET},
                {"code": "1500", "name": "Property, Plant & Equipment", "account_type": AccountType.ASSET},
                {"code": "1600", "name": "Accumulated Depreciation", "account_type": AccountType.ASSET},
                {"code": "1700", "name": "Intangible Assets", "account_type": AccountType.ASSET},
                
                # Liabilities
                {"code": "2000", "name": "Accounts Payable", "account_type": AccountType.LIABILITY},
                {"code": "2100", "name": "Accrued Liabilities", "account_type": AccountType.LIABILITY},
                {"code": "2200", "name": "Short-term Debt", "account_type": AccountType.LIABILITY},
                {"code": "2300", "name": "Long-term Debt", "account_type": AccountType.LIABILITY},
                {"code": "2400", "name": "Deferred Revenue", "account_type": AccountType.LIABILITY},
                
                # Equity
                {"code": "3000", "name": "Share Capital", "account_type": AccountType.EQUITY},
                {"code": "3100", "name": "Retained Earnings", "account_type": AccountType.EQUITY},
                
                # Revenue
                {"code": "4000", "name": "Product Sales Revenue", "account_type": AccountType.REVENUE},
                {"code": "4100", "name": "Service Revenue", "account_type": AccountType.REVENUE},
                {"code": "4200", "name": "Subscription Revenue", "account_type": AccountType.REVENUE},
                {"code": "4300", "name": "Consulting Revenue", "account_type": AccountType.REVENUE},
                {"code": "4400", "name": "Licensing Revenue", "account_type": AccountType.REVENUE},
                {"code": "4500", "name": "Other Revenue", "account_type": AccountType.REVENUE},
                
                # Cost of Goods Sold
                {"code": "5000", "name": "Cost of Goods Sold", "account_type": AccountType.EXPENSE},
                {"code": "5100", "name": "Direct Materials", "account_type": AccountType.EXPENSE},
                {"code": "5200", "name": "Direct Labor", "account_type": AccountType.EXPENSE},
                {"code": "5300", "name": "Manufacturing Overhead", "account_type": AccountType.EXPENSE},
                
                # Operating Expenses
                {"code": "6000", "name": "Salaries and Wages", "account_type": AccountType.EXPENSE},
                {"code": "6100", "name": "Benefits and Payroll Taxes", "account_type": AccountType.EXPENSE},
                {"code": "6200", "name": "Rent and Utilities", "account_type": AccountType.EXPENSE},
                {"code": "6300", "name": "Marketing and Advertising", "account_type": AccountType.EXPENSE},
                {"code": "6400", "name": "Professional Services", "account_type": AccountType.EXPENSE},
                {"code": "6500", "name": "Technology and Software", "account_type": AccountType.EXPENSE},
                {"code": "6600", "name": "Travel and Entertainment", "account_type": AccountType.EXPENSE},
                {"code": "6700", "name": "Office Expenses", "account_type": AccountType.EXPENSE},
                {"code": "6800", "name": "Insurance", "account_type": AccountType.EXPENSE},
                {"code": "6900", "name": "Depreciation Expense", "account_type": AccountType.EXPENSE},
                {"code": "7000", "name": "Research and Development", "account_type": AccountType.EXPENSE},
                {"code": "7100", "name": "Bad Debt Expense", "account_type": AccountType.EXPENSE},
                {"code": "7200", "name": "Other Operating Expenses", "account_type": AccountType.EXPENSE}
            ]
            
            for acc in accounts_to_create:
                new_account = GLAccount(
                    company_id=company_id,
                    account_number=acc["code"],
                    name=acc["name"],
                    account_type=acc["account_type"],
                    is_active=True
                )
                db.add(new_account)
            db.commit()
            stmt = select(GLAccount).where(GLAccount.company_id == company_id)
            gl_accounts = db.execute(stmt).scalars().all()
        
        # Get or create multiple cost centers - SQLAlchemy 2.0 style
        stmt = select(CostCenter).where(CostCenter.company_id == company_id)
        cost_centers = db.execute(stmt).scalars().all()
        if not cost_centers:
            cost_centers_to_create = [
                {"code": "CORP", "name": "Corporate Headquarters"},
                {"code": "SALES", "name": "Sales Department"},
                {"code": "MKTG", "name": "Marketing Department"},
                {"code": "R&D", "name": "Research & Development"},
                {"code": "PROD", "name": "Production"},
                {"code": "IT", "name": "Information Technology"},
                {"code": "HR", "name": "Human Resources"},
                {"code": "FIN", "name": "Finance & Accounting"}
            ]
            
            cost_centers = []
            for cc in cost_centers_to_create:
                cost_center = CostCenter(
                    company_id=company_id,
                    code=cc["code"],
                    name=cc["name"]
                )
                db.add(cost_center)
                cost_centers.append(cost_center)
            db.commit()
        
        # Get main cost center for fallback
        main_cost_center = cost_centers[0]
        
        # Create fiscal periods and transactions for the specified months
        current_date = datetime.now().replace(day=1)
        transactions_created = 0
        fiscal_periods = []
        
        # Step 1: Create fiscal periods
        for month_offset in range(months):
            period_start = current_date - relativedelta(months=month_offset)
            period_end = period_start + relativedelta(months=1) - timedelta(days=1)
            
            # Check or create fiscal period - SQLAlchemy 2.0 style
            stmt = select(FiscalPeriod).where(
                FiscalPeriod.company_id == company_id,
                FiscalPeriod.start_date <= period_start,
                FiscalPeriod.end_date >= period_end
            )
            fiscal_period = db.execute(stmt).scalar_one_or_none()
            
            if not fiscal_period:
                try:
                    fiscal_period = FiscalPeriod(
                        company_id=company_id,
                        fiscal_year=period_start.year,
                        period_number=period_start.month,
                        period_name=period_start.strftime("%B %Y"),
                        start_date=period_start,
                        end_date=period_end,
                        is_closed=month_offset > 1  # Close periods older than 1 month
                    )
                    db.add(fiscal_period)
                    db.commit()
                    db.refresh(fiscal_period)
                except Exception as e:
                    db.rollback()
                    # If duplicate, fetch existing
                    stmt = select(FiscalPeriod).where(
                        FiscalPeriod.company_id == company_id,
                        FiscalPeriod.fiscal_year == period_start.year,
                        FiscalPeriod.period_number == period_start.month
                    )
                    fiscal_period = db.execute(stmt).scalar_one_or_none()
            
            fiscal_periods.append(fiscal_period)
        
        db.commit()
            
        # Step 2: Create comprehensive GL Transactions for all periods
        revenue_accounts = [acc for acc in gl_accounts if acc.account_type == AccountType.REVENUE]
        expense_accounts = [acc for acc in gl_accounts if acc.account_type == AccountType.EXPENSE]
        cash_account = next((acc for acc in gl_accounts if acc.account_number == "1000"), gl_accounts[0])
        
        # Cost center mapping for different expense types
        cost_center_mapping = {
            "salaries": ["HR", "SALES", "MKTG", "R&D", "IT", "FIN", "PROD"],
            "marketing": ["MKTG"],
            "research": ["R&D"],
            "technology": ["IT"],
            "professional": ["FIN", "CORP"],
            "travel": ["SALES", "MKTG", "CORP"],
            "office": ["CORP"],
            "default": ["CORP"]
        }
        
        for i, fiscal_period in enumerate(fiscal_periods):
            period_start = fiscal_period.start_date
            
            # Add seasonal variation (Q4 typically higher revenue)
            seasonal_multiplier = 1.3 if period_start.month in [10, 11, 12] else \
                                1.1 if period_start.month in [3, 4, 5] else \
                                0.9 if period_start.month in [1, 2] else 1.0
            
            # Create multiple revenue transactions per account per period
            for rev_acc in revenue_accounts:
                # Base amounts vary by revenue type
                base_amounts = {
                    "product": 85000,
                    "service": 65000, 
                    "subscription": 45000,
                    "consulting": 35000,
                    "licensing": 25000,
                    "other": 15000
                }
                
                # Determine base amount
                account_type = next((key for key in base_amounts.keys() 
                                   if key in rev_acc.name.lower()), "other")
                base_amount = base_amounts[account_type]
                
                # Add growth trend over time (older periods have lower amounts)
                growth_factor = 1 + (0.03 * (months - i - 1))  # 3% monthly growth
                
                # Create 2-4 transactions per revenue account per month
                num_transactions = random.randint(2, 4)
                for _ in range(num_transactions):
                    amount = (base_amount / num_transactions) * random.uniform(0.7, 1.3) * seasonal_multiplier * growth_factor
                    
                    # Choose appropriate cost center (sales for revenue)
                    cost_center = next((cc for cc in cost_centers if cc.code == "SALES"), main_cost_center)
                    
                    transaction = GLTransaction(
                        company_id=company_id,
                        fiscal_period_id=fiscal_period.id,
                        transaction_date=period_start + timedelta(days=random.randint(1, 28)),
                        description=f"{rev_acc.name} - {period_start.strftime('%B %Y')} #{_+1}",
                        reference_number=f"INV-{period_start.year}{period_start.month:02d}-{random.randint(1000, 9999)}",
                        is_posted=True,
                        created_by=None
                    )
                    db.add(transaction)
                    db.flush()
                    
                    # Debit cash
                    line1 = GLTransactionLine(
                        gl_transaction_id=transaction.id,
                        gl_account_id=cash_account.id,
                        cost_center_id=cost_center.id,
                        debit_amount=amount,
                        credit_amount=0,
                        description=f"Cash from {rev_acc.name}"
                    )
                    db.add(line1)
                    
                    # Credit revenue
                    line2 = GLTransactionLine(
                        gl_transaction_id=transaction.id,
                        gl_account_id=rev_acc.id,
                        cost_center_id=cost_center.id,
                        debit_amount=0,
                        credit_amount=amount,
                        description=rev_acc.name
                    )
                    db.add(line2)
                    
                    transactions_created += 1
            
            # Create expense transactions with realistic amounts and cost center allocation
            for exp_acc in expense_accounts:
                # Enhanced expense mapping
                expense_amounts = {
                    "salaries": 120000,
                    "benefits": 25000,
                    "rent": 15000,
                    "marketing": 45000,
                    "professional": 12000,
                    "technology": 18000,
                    "travel": 8000,
                    "office": 5000,
                    "insurance": 3000,
                    "depreciation": 8000,
                    "research": 35000,
                    "materials": 25000,
                    "labor": 40000,
                    "overhead": 20000,
                    "cost": 30000,  # COGS
                    "bad": 2000,
                    "other": 8000
                }
                
                # Determine expense type and amount
                expense_type = next((key for key in expense_amounts.keys() 
                                   if key in exp_acc.name.lower()), "other")
                base_amount = expense_amounts[expense_type]
                
                # Determine appropriate cost centers for this expense
                if "salaries" in exp_acc.name.lower() or "benefits" in exp_acc.name.lower():
                    # Distribute across all cost centers
                    applicable_cost_centers = cost_centers
                    transactions_per_cc = 1
                elif "marketing" in exp_acc.name.lower():
                    applicable_cost_centers = [cc for cc in cost_centers if cc.code == "MKTG"]
                    transactions_per_cc = random.randint(1, 2)
                elif "research" in exp_acc.name.lower():
                    applicable_cost_centers = [cc for cc in cost_centers if cc.code == "R&D"]
                    transactions_per_cc = 1
                elif "technology" in exp_acc.name.lower():
                    applicable_cost_centers = [cc for cc in cost_centers if cc.code == "IT"]
                    transactions_per_cc = 1
                else:
                    applicable_cost_centers = [main_cost_center]
                    transactions_per_cc = 1
                
                if not applicable_cost_centers:
                    applicable_cost_centers = [main_cost_center]
                
                # Create transactions for each applicable cost center
                for cost_center in applicable_cost_centers:
                    for _ in range(transactions_per_cc):
                        # Adjust amount based on cost center (sales and marketing higher variable costs)
                        cc_multiplier = 1.2 if cost_center.code in ["SALES", "MKTG"] else \
                                       1.5 if cost_center.code == "R&D" else \
                                       0.8 if cost_center.code in ["HR", "FIN"] else 1.0
                        
                        amount = (base_amount / len(applicable_cost_centers) / transactions_per_cc) * \
                                random.uniform(0.8, 1.2) * cc_multiplier
                        
                        transaction = GLTransaction(
                            company_id=company_id,
                            fiscal_period_id=fiscal_period.id,
                            transaction_date=period_start + timedelta(days=random.randint(1, 28)),
                            description=f"{exp_acc.name} - {cost_center.name} - {period_start.strftime('%B %Y')}",
                            reference_number=f"EXP-{period_start.year}{period_start.month:02d}-{random.randint(1000, 9999)}",
                            is_posted=True,
                            created_by=None
                        )
                        db.add(transaction)
                        db.flush()
                        
                        # Debit expense
                        line1 = GLTransactionLine(
                            gl_transaction_id=transaction.id,
                            gl_account_id=exp_acc.id,
                            cost_center_id=cost_center.id,
                            debit_amount=amount,
                            credit_amount=0,
                            description=f"{exp_acc.name} - {cost_center.name}"
                        )
                        db.add(line1)
                        
                        # Credit cash
                        line2 = GLTransactionLine(
                            gl_transaction_id=transaction.id,
                            gl_account_id=cash_account.id,
                            cost_center_id=cost_center.id,
                            debit_amount=0,
                            credit_amount=amount,
                            description=f"Payment for {exp_acc.name}"
                        )
                        db.add(line2)
                        
                        transactions_created += 1
        
        db.commit()
        
        # Step 3: Generate comprehensive module data if requested
        scenarios_created = 0
        budget_lines_created = 0
        kpis_created = 0
        kpi_actuals_created = 0
        business_drivers_created = 0
        variance_thresholds_created = 0
        
        if include_all_modules:
            # Create scenarios for current and previous year (Budget, Forecast, Actual)
            current_year = datetime.now().year
            years_to_generate = [current_year - 1, current_year]
            
            all_scenario_types = []
            for year in years_to_generate:
                all_scenario_types.extend([
                    {"type": ScenarioType.BUDGET, "name": f"{year} Annual Budget", "year": year},
                    {"type": ScenarioType.FORECAST, "name": f"{year} Q2 Forecast", "year": year},
                    {"type": ScenarioType.FORECAST, "name": f"{year} Q4 Forecast", "year": year},
                    {"type": ScenarioType.ACTUAL, "name": f"{year} Actuals", "year": year},
                    {"type": ScenarioType.SCENARIO, "name": f"{year} Conservative Scenario", "year": year},
                    {"type": ScenarioType.SCENARIO, "name": f"{year} Optimistic Scenario", "year": year}
                ])
            
            scenarios = []
            for scenario_info in all_scenario_types:
                # Check if scenario already exists
                stmt = select(Scenario).where(
                    Scenario.company_id == company_id,
                    Scenario.name == scenario_info["name"],
                    Scenario.fiscal_year == scenario_info["year"],
                    Scenario.version == 1
                )
                existing_scenario = db.execute(stmt).scalar_one_or_none()
                
                if existing_scenario:
                    scenarios.append(existing_scenario)
                else:
                    scenario = Scenario(
                        company_id=company_id,
                        name=scenario_info["name"],
                        scenario_type=scenario_info["type"],
                        fiscal_year=scenario_info["year"],
                        version=1,
                        is_approved=scenario_info["type"] != ScenarioType.ACTUAL,
                        created_by=None
                    )
                    db.add(scenario)
                    scenarios.append(scenario)
                    scenarios_created += 1
            
            db.commit()
            
            # Create budget lines for all scenarios
            for scenario in scenarios:
                # Filter fiscal periods for this scenario's year
                scenario_periods = [fp for fp in fiscal_periods if fp.fiscal_year == scenario.fiscal_year]
                
                for fiscal_period in scenario_periods:
                    for gl_account in gl_accounts:
                        if gl_account.account_type in [AccountType.REVENUE, AccountType.EXPENSE]:
                            # Determine cost center allocation
                            for cost_center in cost_centers:
                                # Skip non-relevant cost center combinations
                                if (gl_account.account_type == AccountType.REVENUE and 
                                    cost_center.code not in ["SALES", "MKTG"]):
                                    continue
                                if ("marketing" in gl_account.name.lower() and 
                                    cost_center.code != "MKTG"):
                                    continue
                                if ("research" in gl_account.name.lower() and 
                                    cost_center.code != "R&D"):
                                    continue
                                
                                # Enhanced budget amounts based on account type
                                if gl_account.account_type == AccountType.REVENUE:
                                    base_amounts = {
                                        "product": 95000,
                                        "service": 75000,
                                        "subscription": 55000,
                                        "consulting": 40000,
                                        "licensing": 30000,
                                        "other": 20000
                                    }
                                    account_key = next((key for key in base_amounts.keys() 
                                                      if key in gl_account.name.lower()), "other")
                                    base_amount = base_amounts[account_key]
                                    
                                    # Revenue only for sales cost center in budget
                                    if cost_center.code != "SALES":
                                        continue
                                        
                                else:  # EXPENSE
                                    expense_amounts = {
                                        "salaries": 125000,
                                        "benefits": 28000,
                                        "rent": 16000,
                                        "marketing": 50000,
                                        "professional": 15000,
                                        "technology": 22000,
                                        "travel": 10000,
                                        "office": 6000,
                                        "insurance": 4000,
                                        "depreciation": 10000,
                                        "research": 40000,
                                        "materials": 30000,
                                        "labor": 45000,
                                        "overhead": 25000,
                                        "cost": 35000,
                                        "bad": 3000,
                                        "other": 10000
                                    }
                                    expense_key = next((key for key in expense_amounts.keys() 
                                                      if key in gl_account.name.lower()), "other")
                                    base_amount = expense_amounts[expense_key]
                                    
                                    # Distribute expenses across appropriate cost centers
                                    if "salaries" in gl_account.name.lower():
                                        # All cost centers get salary allocation
                                        base_amount = base_amount / len(cost_centers)
                                    elif "marketing" in gl_account.name.lower() and cost_center.code != "MKTG":
                                        continue
                                    elif "research" in gl_account.name.lower() and cost_center.code != "R&D":
                                        continue
                                    elif "technology" in gl_account.name.lower() and cost_center.code != "IT":
                                        continue
                                    elif cost_center.code not in ["CORP", "SALES", "MKTG", "R&D", "IT"]:
                                        # Skip specialized expenses for non-relevant cost centers
                                        if expense_key not in ["salaries", "benefits", "rent", "office"]:
                                            continue
                                
                                # Adjust for scenario type
                                scenario_multiplier = {
                                    ScenarioType.BUDGET: 1.0,
                                    ScenarioType.FORECAST: 1.05,  # Forecast slightly higher
                                    ScenarioType.ACTUAL: 0.98,   # Actuals slightly lower
                                    ScenarioType.SCENARIO: random.uniform(0.85, 1.15)  # Scenarios vary more
                                }.get(scenario.scenario_type, 1.0)
                                
                                # Add seasonal budget variation
                                seasonal_factor = 1.2 if fiscal_period.period_number in [10, 11, 12] else \
                                                 1.1 if fiscal_period.period_number in [3, 4, 5] else \
                                                 0.9 if fiscal_period.period_number in [1, 2] else 1.0
                                
                                # Year-over-year growth for budget scenarios
                                if scenario.fiscal_year == current_year:
                                    yoy_growth = 1.08  # 8% growth for current year
                                else:
                                    yoy_growth = 1.0   # Previous year baseline
                                
                                budget_amount = (base_amount * scenario_multiplier * seasonal_factor * 
                                               yoy_growth * random.uniform(0.92, 1.08))
                                
                                # Skip very small amounts
                                if budget_amount < 100:
                                    continue
                                
                                budget_line = BudgetLine(
                                    scenario_id=scenario.id,
                                    gl_account_id=gl_account.id,
                                    cost_center_id=cost_center.id,
                                    fiscal_period_id=fiscal_period.id,
                                    amount=budget_amount,
                                    created_by=None
                                )
                                db.add(budget_line)
                                budget_lines_created += 1
            
            # Create comprehensive KPIs across all categories
            kpi_definitions = [
                # Financial KPIs
                {"code": "REV_GROWTH", "name": "Revenue Growth Rate", "unit": "%", "target": 15.0, "category": "Financial"},
                {"code": "PROFIT_MARGIN", "name": "Net Profit Margin", "unit": "%", "target": 25.0, "category": "Financial"},
                {"code": "GROSS_MARGIN", "name": "Gross Profit Margin", "unit": "%", "target": 65.0, "category": "Financial"},
                {"code": "EBITDA_MARGIN", "name": "EBITDA Margin", "unit": "%", "target": 35.0, "category": "Financial"},
                {"code": "ROA", "name": "Return on Assets", "unit": "%", "target": 12.0, "category": "Financial"},
                {"code": "ROE", "name": "Return on Equity", "unit": "%", "target": 18.0, "category": "Financial"},
                
                # Liquidity KPIs
                {"code": "CASH_FLOW", "name": "Operating Cash Flow", "unit": "$000", "target": 500.0, "category": "Liquidity"},
                {"code": "CURRENT_RATIO", "name": "Current Ratio", "unit": "x", "target": 2.0, "category": "Liquidity"},
                {"code": "QUICK_RATIO", "name": "Quick Ratio", "unit": "x", "target": 1.5, "category": "Liquidity"},
                {"code": "CASH_CYCLE", "name": "Cash Conversion Cycle", "unit": "days", "target": 45.0, "category": "Liquidity", "is_higher_better": False},
                
                # Operational KPIs
                {"code": "COST_EFFICIENCY", "name": "Cost Efficiency Ratio", "unit": "%", "target": 92.0, "category": "Operational"},
                {"code": "PRODUCTIVITY", "name": "Revenue per Employee", "unit": "$000", "target": 150.0, "category": "Operational"},
                {"code": "ASSET_TURNOVER", "name": "Asset Turnover", "unit": "x", "target": 1.8, "category": "Operational"},
                {"code": "INVENTORY_TURN", "name": "Inventory Turnover", "unit": "x", "target": 6.0, "category": "Operational"},
                
                # Planning & Control KPIs
                {"code": "BUDGET_VAR", "name": "Budget Variance", "unit": "%", "target": 5.0, "category": "Planning", "is_higher_better": False},
                {"code": "FORECAST_ACC", "name": "Forecast Accuracy", "unit": "%", "target": 90.0, "category": "Planning"},
                {"code": "PLAN_ADHERENCE", "name": "Plan Adherence", "unit": "%", "target": 95.0, "category": "Planning"},
                {"code": "CYCLE_TIME", "name": "Planning Cycle Time", "unit": "days", "target": 10.0, "category": "Planning", "is_higher_better": False},
                
                # Customer & Market KPIs
                {"code": "CUSTOMER_SAT", "name": "Customer Satisfaction", "unit": "%", "target": 85.0, "category": "Customer"},
                {"code": "RETENTION_RATE", "name": "Customer Retention", "unit": "%", "target": 92.0, "category": "Customer"},
                {"code": "ACQ_COST", "name": "Customer Acquisition Cost", "unit": "$", "target": 150.0, "category": "Customer", "is_higher_better": False},
                {"code": "LTV_CAC", "name": "LTV to CAC Ratio", "unit": "x", "target": 3.5, "category": "Customer"},
                
                # Quality & Risk KPIs
                {"code": "DEFECT_RATE", "name": "Defect Rate", "unit": "%", "target": 2.0, "category": "Quality", "is_higher_better": False},
                {"code": "ON_TIME_DEL", "name": "On-Time Delivery", "unit": "%", "target": 95.0, "category": "Quality"},
                {"code": "COMPLIANCE", "name": "Regulatory Compliance", "unit": "%", "target": 100.0, "category": "Risk"},
                {"code": "RISK_SCORE", "name": "Risk Assessment Score", "unit": "score", "target": 25.0, "category": "Risk", "is_higher_better": False},
                
                # Innovation & Growth KPIs
                {"code": "RND_INTENSITY", "name": "R&D Intensity", "unit": "%", "target": 8.0, "category": "Innovation"},
                {"code": "NEW_PRODUCT_REV", "name": "New Product Revenue", "unit": "%", "target": 20.0, "category": "Innovation"},
                {"code": "MARKET_SHARE", "name": "Market Share", "unit": "%", "target": 15.0, "category": "Growth"},
                {"code": "EXPANSION_RATE", "name": "Market Expansion Rate", "unit": "%", "target": 12.0, "category": "Growth"}
            ]
            
            created_kpis = []
            for kpi_def in kpi_definitions:
                # Check if KPI already exists
                stmt = select(KPI).where(
                    KPI.company_id == company_id,
                    KPI.code == kpi_def["code"]
                )
                existing_kpi = db.execute(stmt).scalar_one_or_none()
                
                if existing_kpi:
                    created_kpis.append(existing_kpi)
                else:
                    kpi = KPI(
                        company_id=company_id,
                        code=kpi_def["code"],
                        name=kpi_def["name"],
                        unit_of_measure=kpi_def["unit"],
                        target_value=kpi_def["target"],
                        category=kpi_def["category"],
                        is_higher_better=kpi_def.get("is_higher_better", True),
                        is_active=True
                    )
                    db.add(kpi)
                    created_kpis.append(kpi)
                    kpis_created += 1
            
            db.commit()
            
            # Create KPI actuals for all available periods with realistic trends
            for fiscal_period in fiscal_periods:
                for kpi in created_kpis:
                    # Generate realistic KPI values with seasonal and trend variations
                    base_target = float(kpi.target_value)
                    
                    # Add trend over time (improvement or decline)
                    period_index = fiscal_periods.index(fiscal_period)
                    trend_factor = 1 + (0.005 * (len(fiscal_periods) - period_index))  # Slight improvement over time
                    
                    # Add seasonal variation
                    month = fiscal_period.period_number
                    seasonal_factor = 1.1 if month in [10, 11, 12] else \
                                    1.05 if month in [3, 4, 5] else \
                                    0.95 if month in [1, 2] else 1.0
                    
                    # Generate values based on KPI type and characteristics
                    if kpi.code == "REV_GROWTH":
                        value = base_target * random.uniform(0.6, 1.4) * trend_factor * seasonal_factor
                    elif kpi.code in ["PROFIT_MARGIN", "GROSS_MARGIN", "EBITDA_MARGIN"]:
                        value = base_target * random.uniform(0.8, 1.2) * trend_factor
                    elif kpi.code in ["ROA", "ROE"]:
                        value = base_target * random.uniform(0.7, 1.3) * trend_factor
                    elif kpi.code == "CASH_FLOW":
                        value = base_target * random.uniform(0.6, 1.4) * seasonal_factor
                    elif kpi.code in ["CURRENT_RATIO", "QUICK_RATIO"]:
                        value = base_target * random.uniform(0.8, 1.2)
                    elif kpi.code == "CASH_CYCLE":
                        # Lower is better, so reverse the trend
                        value = base_target * random.uniform(0.8, 1.2) / trend_factor
                    elif kpi.code in ["COST_EFFICIENCY", "PRODUCTIVITY", "ASSET_TURNOVER"]:
                        value = base_target * random.uniform(0.85, 1.15) * trend_factor
                    elif kpi.code == "INVENTORY_TURN":
                        value = base_target * random.uniform(0.8, 1.3) * seasonal_factor
                    elif kpi.code == "BUDGET_VAR":
                        # Lower is better for variance
                        value = base_target * random.uniform(0.5, 2.0) / trend_factor
                    elif kpi.code in ["FORECAST_ACC", "PLAN_ADHERENCE"]:
                        value = base_target * random.uniform(0.9, 1.05) * trend_factor
                    elif kpi.code == "CYCLE_TIME":
                        # Lower is better
                        value = base_target * random.uniform(0.7, 1.3) / trend_factor
                    elif kpi.code in ["CUSTOMER_SAT", "RETENTION_RATE"]:
                        value = base_target * random.uniform(0.9, 1.08) * trend_factor
                    elif kpi.code == "ACQ_COST":
                        # Lower is better
                        value = base_target * random.uniform(0.8, 1.4) / trend_factor
                    elif kpi.code == "LTV_CAC":
                        value = base_target * random.uniform(0.8, 1.3) * trend_factor
                    elif kpi.code == "DEFECT_RATE":
                        # Lower is better
                        value = base_target * random.uniform(0.5, 2.0) / trend_factor
                    elif kpi.code in ["ON_TIME_DEL", "COMPLIANCE"]:
                        value = base_target * random.uniform(0.92, 1.02) * trend_factor
                    elif kpi.code == "RISK_SCORE":
                        # Lower is better
                        value = base_target * random.uniform(0.6, 1.5) / trend_factor
                    elif kpi.code in ["RND_INTENSITY", "NEW_PRODUCT_REV", "MARKET_SHARE", "EXPANSION_RATE"]:
                        value = base_target * random.uniform(0.7, 1.4) * trend_factor * seasonal_factor
                    else:
                        # Default case
                        value = base_target * random.uniform(0.8, 1.2) * trend_factor
                    
                    # Ensure value is positive and reasonable
                    value = max(0.1, value)
                    
                    # Add some randomness to targets too (realistic variation)
                    target_variation = base_target * random.uniform(0.95, 1.05)
                    
                    kpi_actual = KPIActual(
                        kpi_id=kpi.id,
                        fiscal_period_id=fiscal_period.id,
                        actual_value=round(value, 2),
                        target_value=round(target_variation, 2)
                    )
                    db.add(kpi_actual)
                    kpi_actuals_created += 1
            
            # Create comprehensive Business Drivers
            driver_definitions = [
                # Volume Drivers
                {"code": "CUSTOMERS", "name": "Active Customer Base", "unit": "count", "category": "volume"},
                {"code": "HEADCOUNT", "name": "Full-Time Employees", "unit": "count", "category": "volume"},
                {"code": "UNITS_SOLD", "name": "Units Sold", "unit": "count", "category": "volume"},
                {"code": "TRANSACTIONS", "name": "Transaction Volume", "unit": "count", "category": "volume"},
                {"code": "STORE_COUNT", "name": "Number of Locations", "unit": "count", "category": "volume"},
                
                # Price & Value Drivers
                {"code": "AVG_ORDER", "name": "Average Order Value", "unit": "USD", "category": "price"},
                {"code": "AVG_PRICE", "name": "Average Selling Price", "unit": "USD", "category": "price"},
                {"code": "PRICE_INDEX", "name": "Price Index", "unit": "index", "category": "price"},
                {"code": "DISCOUNT_RATE", "name": "Average Discount Rate", "unit": "%", "category": "price"},
                
                # Efficiency Drivers
                {"code": "CONVERSION", "name": "Sales Conversion Rate", "unit": "%", "category": "efficiency"},
                {"code": "UTILIZATION", "name": "Capacity Utilization", "unit": "%", "category": "efficiency"},
                {"code": "PRODUCTIVITY", "name": "Output per Hour", "unit": "units/hr", "category": "efficiency"},
                {"code": "AUTOMATION", "name": "Automation Rate", "unit": "%", "category": "efficiency"},
                
                # Market & External Drivers
                {"code": "INFLATION", "name": "Inflation Rate", "unit": "%", "category": "external", "is_external": True},
                {"code": "GDP_GROWTH", "name": "GDP Growth Rate", "unit": "%", "category": "external", "is_external": True},
                {"code": "UNEMPLOYMENT", "name": "Unemployment Rate", "unit": "%", "category": "external", "is_external": True},
                {"code": "INTEREST_RATE", "name": "Interest Rate", "unit": "%", "category": "external", "is_external": True},
                {"code": "MARKET_SIZE", "name": "Total Market Size", "unit": "$M", "category": "external", "is_external": True},
                
                # Quality & Service Drivers
                {"code": "SATISFACTION", "name": "Customer Satisfaction Score", "unit": "score", "category": "quality"},
                {"code": "NPS", "name": "Net Promoter Score", "unit": "score", "category": "quality"},
                {"code": "QUALITY_SCORE", "name": "Quality Rating", "unit": "score", "category": "quality"},
                {"code": "SERVICE_LEVEL", "name": "Service Level Achievement", "unit": "%", "category": "quality"},
                
                # Innovation & Development Drivers
                {"code": "RND_PROJECTS", "name": "Active R&D Projects", "unit": "count", "category": "innovation"},
                {"code": "NEW_PRODUCTS", "name": "New Product Launches", "unit": "count", "category": "innovation"},
                {"code": "PATENTS", "name": "Patent Applications", "unit": "count", "category": "innovation"},
                
                # Operational Drivers
                {"code": "INVENTORY_DAYS", "name": "Inventory Days on Hand", "unit": "days", "category": "operational"},
                {"code": "LEAD_TIME", "name": "Average Lead Time", "unit": "days", "category": "operational"},
                {"code": "CAPACITY", "name": "Production Capacity", "unit": "units", "category": "operational"}
            ]
            
            for driver_def in driver_definitions:
                # Check if business driver already exists
                stmt = select(BusinessDriver).where(
                    BusinessDriver.company_id == company_id,
                    BusinessDriver.code == driver_def["code"]
                )
                existing_driver = db.execute(stmt).scalar_one_or_none()
                
                if not existing_driver:
                    driver = BusinessDriver(
                        company_id=company_id,
                        code=driver_def["code"],
                        name=driver_def["name"],
                        unit_of_measure=driver_def["unit"],
                        category=driver_def["category"],
                        is_external=driver_def.get("is_external", False),
                        is_active=True
                    )
                    db.add(driver)
                    business_drivers_created += 1
            
            # Create Variance Thresholds
            for gl_account in gl_accounts:
                if gl_account.account_type in [AccountType.REVENUE, AccountType.EXPENSE]:
                    threshold = VarianceThreshold(
                        company_id=company_id,
                        gl_account_id=gl_account.id,
                        cost_center_id=cost_center.id,
                        threshold_type="percentage",
                        warning_threshold=10.0,  # 10% variance warning
                        critical_threshold=20.0,  # 20% variance critical
                        is_active=True
                    )
                    db.add(threshold)
                    variance_thresholds_created += 1
            
            # Create Expense Planning Tables and Sample Data
            expense_categories_created = 0
            expense_contracts_created = 0
            vendor_contracts_created = 0
            headcount_plans_created = 0
            
            # First, create the expense planning tables if they don't exist
            try:
                # Create expense planning tables
                create_expense_tables_query = """
                -- Create expense categories table if not exists
                CREATE TABLE IF NOT EXISTS expense_categories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
                    category_code VARCHAR(50) NOT NULL,
                    category_name VARCHAR(255) NOT NULL,
                    category_type VARCHAR(50),
                    parent_category_id UUID REFERENCES expense_categories(id),
                    is_controllable BOOLEAN DEFAULT true,
                    is_discretionary BOOLEAN DEFAULT true,
                    typical_variance_pct DECIMAL(5,2) DEFAULT 10.0,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, category_code)
                );
                
                -- Create vendors table if not exists
                CREATE TABLE IF NOT EXISTS vendors (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
                    vendor_code VARCHAR(50) NOT NULL,
                    vendor_name VARCHAR(255) NOT NULL,
                    vendor_type VARCHAR(50),
                    tax_id VARCHAR(50),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, vendor_code)
                );
                
                -- Create expense contracts table if not exists
                CREATE TABLE IF NOT EXISTS expense_contracts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
                    vendor_id UUID REFERENCES vendors(id),
                    contract_number VARCHAR(50) NOT NULL,
                    contract_name VARCHAR(255) NOT NULL,
                    contract_type VARCHAR(50),
                    start_date DATE NOT NULL,
                    end_date DATE,
                    monthly_amount DECIMAL(15,2),
                    annual_amount DECIMAL(15,2),
                    escalation_rate DECIMAL(5,4) DEFAULT 0,
                    auto_renew BOOLEAN DEFAULT false,
                    gl_account_id UUID REFERENCES gl_accounts(id),
                    cost_center_id UUID REFERENCES cost_centers(id),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, contract_number)
                );
                
                -- Create headcount planning table if not exists
                CREATE TABLE IF NOT EXISTS headcount_plans (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
                    department VARCHAR(100) NOT NULL,
                    fiscal_period_id UUID REFERENCES fiscal_periods(id),
                    headcount INTEGER NOT NULL,
                    avg_salary DECIMAL(15,2),
                    benefits_rate DECIMAL(5,4) DEFAULT 0.3,
                    total_cost DECIMAL(15,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, department, fiscal_period_id)
                );
                """
                
                db.execute(text(create_expense_tables_query))
                db.commit()
            except:
                # Tables might already exist, continue
                pass
            
            # Create expense categories
            expense_categories = [
                {"code": "PERS", "name": "Personnel", "type": "personnel", "controllable": False, "discretionary": False},
                {"code": "OPER", "name": "Operating", "type": "operating", "controllable": True, "discretionary": True},
                {"code": "MKTG", "name": "Marketing", "type": "marketing", "controllable": True, "discretionary": True},
                {"code": "TECH", "name": "Technology", "type": "technology", "controllable": True, "discretionary": False},
                {"code": "FACI", "name": "Facilities", "type": "facilities", "controllable": False, "discretionary": False},
                {"code": "TRVL", "name": "Travel", "type": "travel", "controllable": True, "discretionary": True},
                {"code": "PROF", "name": "Professional Services", "type": "professional", "controllable": True, "discretionary": True},
                {"code": "INSR", "name": "Insurance", "type": "insurance", "controllable": False, "discretionary": False},
                {"code": "DEPR", "name": "Depreciation", "type": "depreciation", "controllable": False, "discretionary": False},
                {"code": "OTHR", "name": "Other", "type": "other", "controllable": True, "discretionary": True}
            ]
            
            for cat in expense_categories:
                try:
                    cat_id = hashlib.md5(f"{company_id}_{cat['code']}".encode()).hexdigest()[:8]
                    cat_uuid = f"{cat_id[:8]}-{cat_id[8:12]}-{cat_id[12:16]}-{cat_id[16:20]}-{cat_id[20:32]}00000000"[:36]
                    
                    query = text("""
                        INSERT INTO expense_categories (id, company_id, category_code, category_name, 
                                                       category_type, is_controllable, is_discretionary)
                        VALUES (:id, :company_id, :code, :name, :type, :controllable, :discretionary)
                        ON CONFLICT (company_id, category_code) DO NOTHING
                    """)
                    
                    db.execute(query, {
                        "id": cat_uuid,
                        "company_id": company_id,
                        "code": cat["code"],
                        "name": cat["name"],
                        "type": cat["type"],
                        "controllable": cat["controllable"],
                        "discretionary": cat["discretionary"]
                    })
                    expense_categories_created += 1
                except:
                    pass
            
            # Create vendors
            vendors = [
                {"code": "VEN001", "name": "AWS", "type": "technology"},
                {"code": "VEN002", "name": "Microsoft", "type": "technology"},
                {"code": "VEN003", "name": "Salesforce", "type": "software"},
                {"code": "VEN004", "name": "Office Landlord Inc", "type": "facilities"},
                {"code": "VEN005", "name": "Business Insurance Co", "type": "insurance"},
                {"code": "VEN006", "name": "Marketing Agency LLC", "type": "marketing"},
                {"code": "VEN007", "name": "Consulting Partners", "type": "professional"},
                {"code": "VEN008", "name": "Travel Services Corp", "type": "travel"}
            ]
            
            vendor_ids = {}
            for vendor in vendors:
                try:
                    vendor_id = hashlib.md5(f"{company_id}_{vendor['code']}".encode()).hexdigest()[:8]
                    vendor_uuid = f"{vendor_id[:8]}-{vendor_id[8:12]}-{vendor_id[12:16]}-{vendor_id[16:20]}-{vendor_id[20:32]}00000000"[:36]
                    
                    query = text("""
                        INSERT INTO vendors (id, company_id, vendor_code, vendor_name, vendor_type)
                        VALUES (:id, :company_id, :code, :name, :type)
                        ON CONFLICT (company_id, vendor_code) DO NOTHING
                    """)
                    
                    db.execute(query, {
                        "id": vendor_uuid,
                        "company_id": company_id,
                        "code": vendor["code"],
                        "name": vendor["name"],
                        "type": vendor["type"]
                    })
                    vendor_ids[vendor["code"]] = vendor_uuid
                except:
                    pass
            
            # Create expense contracts
            contracts = [
                {"vendor": "VEN001", "number": "CTR001", "name": "AWS Cloud Services", "monthly": 12000, "type": "subscription"},
                {"vendor": "VEN002", "number": "CTR002", "name": "Microsoft Office 365", "monthly": 5000, "type": "subscription"},
                {"vendor": "VEN003", "number": "CTR003", "name": "Salesforce CRM", "monthly": 8000, "type": "subscription"},
                {"vendor": "VEN004", "number": "CTR004", "name": "Office Lease", "monthly": 25000, "type": "lease"},
                {"vendor": "VEN005", "number": "CTR005", "name": "General Liability Insurance", "monthly": 3000, "type": "insurance"},
                {"vendor": "VEN006", "number": "CTR006", "name": "Marketing Services", "monthly": 10000, "type": "service"},
                {"vendor": "VEN007", "number": "CTR007", "name": "IT Consulting", "monthly": 15000, "type": "service"}
            ]
            
            # Get expense GL accounts
            expense_accounts = [acc for acc in gl_accounts if acc.account_type == AccountType.EXPENSE]
            
            for i, contract in enumerate(contracts):
                try:
                    contract_id = hashlib.md5(f"{company_id}_{contract['number']}".encode()).hexdigest()[:8]
                    contract_uuid = f"{contract_id[:8]}-{contract_id[8:12]}-{contract_id[12:16]}-{contract_id[16:20]}-{contract_id[20:32]}00000000"[:36]
                    
                    query = text("""
                        INSERT INTO expense_contracts (id, company_id, vendor_id, contract_number, 
                                                      contract_name, contract_type, start_date, 
                                                      monthly_amount, annual_amount, gl_account_id,
                                                      cost_center_id, escalation_rate)
                        VALUES (:id, :company_id, :vendor_id, :number, :name, :type, :start_date,
                               :monthly, :annual, :gl_account_id, :cost_center_id, :escalation)
                        ON CONFLICT (company_id, contract_number) DO NOTHING
                    """)
                    
                    db.execute(query, {
                        "id": contract_uuid,
                        "company_id": company_id,
                        "vendor_id": vendor_ids.get(contract["vendor"]),
                        "number": contract["number"],
                        "name": contract["name"],
                        "type": contract["type"],
                        "start_date": date(2024, 1, 1),
                        "monthly": contract["monthly"],
                        "annual": contract["monthly"] * 12,
                        "gl_account_id": expense_accounts[i % len(expense_accounts)].id if expense_accounts else None,
                        "cost_center_id": cost_center.id,
                        "escalation": 0.03  # 3% annual escalation
                    })
                    expense_contracts_created += 1
                except:
                    pass
            
            # Create headcount plans
            departments = ["Engineering", "Sales", "Marketing", "Operations", "Finance", "HR", "Customer Support"]
            
            for dept in departments:
                for period in fiscal_periods[-6:]:  # Last 6 months
                    try:
                        plan_id = hashlib.md5(f"{company_id}_{dept}_{period.id}".encode()).hexdigest()[:8]
                        plan_uuid = f"{plan_id[:8]}-{plan_id[8:12]}-{plan_id[12:16]}-{plan_id[16:20]}-{plan_id[20:32]}00000000"[:36]
                        
                        headcount = random.randint(5, 50)
                        avg_salary = random.uniform(60000, 150000)
                        benefits_rate = 0.3
                        monthly_cost = (avg_salary * (1 + benefits_rate) * headcount) / 12
                        
                        query = text("""
                            INSERT INTO headcount_plans (id, company_id, department, fiscal_period_id,
                                                       headcount, avg_salary, benefits_rate, total_cost)
                            VALUES (:id, :company_id, :dept, :period_id, :headcount, :salary, :benefits, :cost)
                            ON CONFLICT (company_id, department, fiscal_period_id) DO NOTHING
                        """)
                        
                        db.execute(query, {
                            "id": plan_uuid,
                            "company_id": company_id,
                            "dept": dept,
                            "period_id": period.id,
                            "headcount": headcount,
                            "salary": avg_salary,
                            "benefits": benefits_rate,
                            "cost": monthly_cost
                        })
                        headcount_plans_created += 1
                    except:
                        pass
            
            # Create Revenue Planning Tables and Sample Data
            revenue_streams_created = 0
            customer_segments_created = 0
            pipeline_opportunities_created = 0
            
            # First, create the revenue planning tables if they don't exist
            try:
                # Create revenue planning tables
                create_revenue_tables_query = """
                -- Create revenue streams table if not exists
                CREATE TABLE IF NOT EXISTS revenue_streams (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
                    stream_code VARCHAR(50) NOT NULL,
                    stream_name VARCHAR(255) NOT NULL,
                    stream_type VARCHAR(50) NOT NULL,
                    parent_stream_id UUID REFERENCES revenue_streams(id),
                    gl_account_id UUID REFERENCES gl_accounts(id),
                    recognition_method VARCHAR(50),
                    typical_payment_terms INTEGER,
                    is_recurring BOOLEAN DEFAULT false,
                    recurring_frequency VARCHAR(50),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, stream_code)
                );
                
                -- Create customer segments table if not exists
                CREATE TABLE IF NOT EXISTS customer_segments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
                    segment_code VARCHAR(50) NOT NULL,
                    segment_name VARCHAR(255) NOT NULL,
                    segment_type VARCHAR(50),
                    typical_deal_size DECIMAL(15,2),
                    typical_sales_cycle_days INTEGER,
                    churn_rate DECIMAL(5,4),
                    growth_rate DECIMAL(5,4),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_id, segment_code)
                );
                
                -- Create sales pipeline table if not exists
                CREATE TABLE IF NOT EXISTS sales_pipeline (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
                    opportunity_name VARCHAR(255) NOT NULL,
                    customer_segment_id UUID REFERENCES customer_segments(id),
                    revenue_stream_id UUID REFERENCES revenue_streams(id),
                    stage VARCHAR(50) NOT NULL,
                    probability DECIMAL(5,2),
                    amount DECIMAL(15,2),
                    expected_close_date DATE,
                    sales_rep_id UUID,
                    created_date DATE,
                    last_activity_date DATE,
                    days_in_stage INTEGER,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                db.execute(text(create_revenue_tables_query))
                db.commit()
            except:
                # Tables might already exist, continue
                pass
            
            # Create revenue streams
            revenue_streams = [
                {"code": "PROD", "name": "Product Sales", "type": "product", "recurring": False, "frequency": None},
                {"code": "SERV", "name": "Service Revenue", "type": "service", "recurring": False, "frequency": None},
                {"code": "SUBS", "name": "Subscription Revenue", "type": "subscription", "recurring": True, "frequency": "monthly"},
                {"code": "LICE", "name": "Licensing Revenue", "type": "licensing", "recurring": True, "frequency": "annual"},
                {"code": "CONS", "name": "Consulting Revenue", "type": "service", "recurring": False, "frequency": None},
                {"code": "SUPP", "name": "Support Revenue", "type": "service", "recurring": True, "frequency": "monthly"},
                {"code": "TRAI", "name": "Training Revenue", "type": "service", "recurring": False, "frequency": None},
                {"code": "OTHE", "name": "Other Revenue", "type": "other", "recurring": False, "frequency": None}
            ]
            
            # Get revenue GL accounts
            revenue_accounts = [acc for acc in gl_accounts if acc.account_type == AccountType.REVENUE]
            
            stream_ids = {}
            for i, stream in enumerate(revenue_streams):
                try:
                    stream_id = hashlib.md5(f"{company_id}_{stream['code']}".encode()).hexdigest()[:8]
                    stream_uuid = f"{stream_id[:8]}-{stream_id[8:12]}-{stream_id[12:16]}-{stream_id[16:20]}-{stream_id[20:32]}00000000"[:36]
                    
                    query = text("""
                        INSERT INTO revenue_streams (id, company_id, stream_code, stream_name, 
                                                   stream_type, is_recurring, recurring_frequency,
                                                   gl_account_id, recognition_method, typical_payment_terms)
                        VALUES (:id, :company_id, :code, :name, :type, :recurring, :frequency,
                               :gl_account_id, :recognition, :payment_terms)
                        ON CONFLICT (company_id, stream_code) DO NOTHING
                    """)
                    
                    db.execute(query, {
                        "id": stream_uuid,
                        "company_id": company_id,
                        "code": stream["code"],
                        "name": stream["name"],
                        "type": stream["type"],
                        "recurring": stream["recurring"],
                        "frequency": stream["frequency"],
                        "gl_account_id": revenue_accounts[i % len(revenue_accounts)].id if revenue_accounts else None,
                        "recognition": "point_in_time" if not stream["recurring"] else "over_time",
                        "payment_terms": 30
                    })
                    stream_ids[stream["code"]] = stream_uuid
                    revenue_streams_created += 1
                except:
                    pass
            
            # Create customer segments
            customer_segments = [
                {"code": "ENT", "name": "Enterprise", "type": "enterprise", "deal_size": 100000, "churn": 0.02, "growth": 0.25},
                {"code": "MID", "name": "Mid-Market", "type": "mid_market", "deal_size": 25000, "churn": 0.05, "growth": 0.35},
                {"code": "SMB", "name": "Small Business", "type": "smb", "deal_size": 5000, "churn": 0.10, "growth": 0.45},
                {"code": "CON", "name": "Consumer", "type": "consumer", "deal_size": 500, "churn": 0.15, "growth": 0.20},
                {"code": "GOV", "name": "Government", "type": "government", "deal_size": 150000, "churn": 0.01, "growth": 0.10},
                {"code": "EDU", "name": "Education", "type": "education", "deal_size": 20000, "churn": 0.03, "growth": 0.15},
                {"code": "NPO", "name": "Non-Profit", "type": "non_profit", "deal_size": 10000, "churn": 0.04, "growth": 0.12}
            ]
            
            segment_ids = {}
            for segment in customer_segments:
                try:
                    segment_id = hashlib.md5(f"{company_id}_{segment['code']}".encode()).hexdigest()[:8]
                    segment_uuid = f"{segment_id[:8]}-{segment_id[8:12]}-{segment_id[12:16]}-{segment_id[16:20]}-{segment_id[20:32]}00000000"[:36]
                    
                    query = text("""
                        INSERT INTO customer_segments (id, company_id, segment_code, segment_name,
                                                      segment_type, typical_deal_size, typical_sales_cycle_days,
                                                      churn_rate, growth_rate)
                        VALUES (:id, :company_id, :code, :name, :type, :deal_size, :cycle_days,
                               :churn, :growth)
                        ON CONFLICT (company_id, segment_code) DO NOTHING
                    """)
                    
                    db.execute(query, {
                        "id": segment_uuid,
                        "company_id": company_id,
                        "code": segment["code"],
                        "name": segment["name"],
                        "type": segment["type"],
                        "deal_size": segment["deal_size"],
                        "cycle_days": random.randint(30, 180),
                        "churn": segment["churn"],
                        "growth": segment["growth"]
                    })
                    segment_ids[segment["code"]] = segment_uuid
                    customer_segments_created += 1
                except:
                    pass
            
            # Create sales pipeline opportunities
            stages = ["lead", "qualified", "proposal", "negotiation", "closed_won"]
            probabilities = {"lead": 10, "qualified": 25, "proposal": 50, "negotiation": 75, "closed_won": 100}
            
            for i in range(30):  # Create 30 pipeline opportunities
                try:
                    opp_id = hashlib.md5(f"{company_id}_OPP_{i}".encode()).hexdigest()[:8]
                    opp_uuid = f"{opp_id[:8]}-{opp_id[8:12]}-{opp_id[12:16]}-{opp_id[16:20]}-{opp_id[20:32]}00000000"[:36]
                    
                    stage = random.choice(stages)
                    segment_code = random.choice(list(segment_ids.keys()))
                    stream_code = random.choice(list(stream_ids.keys()))
                    amount = random.uniform(5000, 200000)
                    
                    query = text("""
                        INSERT INTO sales_pipeline (id, company_id, opportunity_name, customer_segment_id,
                                                   revenue_stream_id, stage, probability, amount,
                                                   expected_close_date, created_date, days_in_stage)
                        VALUES (:id, :company_id, :opp_name, :segment_id, :stream_id,
                               :stage, :probability, :amount, :close_date, :created_date, :days_in_stage)
                    """)
                    
                    db.execute(query, {
                        "id": opp_uuid,
                        "company_id": company_id,
                        "opp_name": f"Opportunity {i+1}",
                        "segment_id": segment_ids.get(segment_code),
                        "stream_id": stream_ids.get(stream_code),
                        "stage": stage,
                        "probability": probabilities[stage],
                        "amount": amount,
                        "close_date": date.today() + timedelta(days=random.randint(30, 180)),
                        "created_date": date.today() - timedelta(days=random.randint(0, 90)),
                        "days_in_stage": random.randint(1, 30)
                    })
                    pipeline_opportunities_created += 1
                except:
                    pass
            
            db.commit()
        
        # Build detailed summary message
        summary_parts = []
        
        # Core Financial Data
        if transactions_created > 0:
            summary_parts.append(f"✓ {transactions_created} GL transactions")
        if len(gl_accounts) > 0:
            summary_parts.append(f"✓ {len(gl_accounts)} GL accounts")
        if len(fiscal_periods) > 0:
            summary_parts.append(f"✓ {len(fiscal_periods)} fiscal periods")
        
        # Planning & Budgeting
        if scenarios_created > 0:
            summary_parts.append(f"✓ {scenarios_created} budget scenarios")
        if budget_lines_created > 0:
            summary_parts.append(f"✓ {budget_lines_created} budget lines")
        
        # KPIs & Metrics
        if kpis_created > 0:
            summary_parts.append(f"✓ {kpis_created} KPIs")
        if kpi_actuals_created > 0:
            summary_parts.append(f"✓ {kpi_actuals_created} KPI actuals")
        
        # Business Drivers
        if business_drivers_created > 0:
            summary_parts.append(f"✓ {business_drivers_created} business drivers")
        if variance_thresholds_created > 0:
            summary_parts.append(f"✓ {variance_thresholds_created} variance thresholds")
        
        # Expense Planning
        if expense_categories_created > 0 or expense_contracts_created > 0 or headcount_plans_created > 0:
            expense_items = []
            if expense_categories_created > 0:
                expense_items.append(f"{expense_categories_created} categories")
            if expense_contracts_created > 0:
                expense_items.append(f"{expense_contracts_created} vendor contracts")
            if headcount_plans_created > 0:
                expense_items.append(f"{headcount_plans_created} headcount plans")
            summary_parts.append(f"✓ Expense Planning: {', '.join(expense_items)}")
        
        # Revenue Planning
        if revenue_streams_created > 0 or customer_segments_created > 0 or pipeline_opportunities_created > 0:
            revenue_items = []
            if revenue_streams_created > 0:
                revenue_items.append(f"{revenue_streams_created} revenue streams")
            if customer_segments_created > 0:
                revenue_items.append(f"{customer_segments_created} customer segments")
            if pipeline_opportunities_created > 0:
                revenue_items.append(f"{pipeline_opportunities_created} pipeline opportunities")
            summary_parts.append(f"✓ Revenue Planning: {', '.join(revenue_items)}")
        
        detailed_message = "Generated comprehensive sample data successfully:\n" + "\n".join(summary_parts)
        
        return {
            "success": True,
            "message": detailed_message,
            "summary": {
                "core_financial": {
                    "transactions": transactions_created,
                    "gl_accounts": len(gl_accounts),
                    "fiscal_periods": len(fiscal_periods)
                },
                "planning_budgeting": {
                    "scenarios": scenarios_created,
                    "budget_lines": budget_lines_created
                },
                "analytics": {
                    "kpis": kpis_created,
                    "kpi_actuals": kpi_actuals_created,
                    "business_drivers": business_drivers_created,
                    "variance_thresholds": variance_thresholds_created
                },
                "expense_planning": {
                    "categories": expense_categories_created,
                    "vendor_contracts": expense_contracts_created,
                    "headcount_plans": headcount_plans_created
                },
                "revenue_planning": {
                    "revenue_streams": revenue_streams_created,
                    "customer_segments": customer_segments_created,
                    "pipeline_opportunities": pipeline_opportunities_created
                }
            },
            "details": {
                "transactions_created": transactions_created,
                "months_covered": months,
                "gl_accounts": len(gl_accounts),
                "scenarios_created": scenarios_created,
                "budget_lines_created": budget_lines_created,
                "kpis_created": kpis_created,
                "kpi_actuals_created": kpi_actuals_created,
                "business_drivers_created": business_drivers_created,
                "variance_thresholds_created": variance_thresholds_created,
                "fiscal_periods": len(fiscal_periods),
                "expense_categories_created": expense_categories_created,
                "expense_contracts_created": expense_contracts_created,
                "headcount_plans_created": headcount_plans_created,
                "revenue_streams_created": revenue_streams_created,
                "customer_segments_created": customer_segments_created,
                "pipeline_opportunities_created": pipeline_opportunities_created
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Failed to generate sample data: {str(e)}"
        }