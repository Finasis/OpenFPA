from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from datetime import datetime, date
from decimal import Decimal

from ..models.models import KPI, KPIActual, FiscalPeriod, GLAccount, GLTransactionLine

class KPIManagementService:
    """Service for KPI calculations, tracking, and analysis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_financial_kpis(
        self,
        company_id: str,
        fiscal_period_id: str
    ) -> Dict[str, Any]:
        """Calculate standard financial KPIs automatically"""
        
        # Get financial data for the period
        query = """
        SELECT 
            ga.account_type,
            SUM(CASE 
                WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                WHEN ga.account_type IN ('liability', 'equity', 'revenue') THEN gtl.credit_amount - gtl.debit_amount
                ELSE 0
            END) as amount
        FROM gl_accounts ga
        JOIN gl_transaction_lines gtl ON gtl.gl_account_id = ga.id
        JOIN gl_transactions gt ON gt.id = gtl.gl_transaction_id
        WHERE gt.company_id = :company_id 
            AND gt.fiscal_period_id = :fiscal_period_id
            AND gt.is_posted = true
        GROUP BY ga.account_type
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'fiscal_period_id': fiscal_period_id
        })
        
        amounts = {row.account_type: row.amount for row in result}
        
        # Calculate standard KPIs
        revenue = amounts.get('revenue', 0)
        expenses = amounts.get('expense', 0)
        assets = amounts.get('asset', 0)
        liabilities = amounts.get('liability', 0)
        equity = amounts.get('equity', 0)
        
        kpis = {
            'revenue': revenue,
            'total_expenses': expenses,
            'gross_profit': revenue - expenses,
            'gross_margin_percentage': (revenue - expenses) / revenue * 100 if revenue != 0 else 0,
            'total_assets': assets,
            'total_liabilities': liabilities,
            'total_equity': equity,
            'debt_to_equity_ratio': liabilities / equity if equity != 0 else None,
            'return_on_assets': (revenue - expenses) / assets * 100 if assets != 0 else None
        }
        
        return kpis
    
    async def get_kpi_trends(
        self,
        kpi_id: str,
        periods: int = 12
    ) -> List[Dict[str, Any]]:
        """Get KPI trends over multiple periods"""
        
        query = """
        SELECT 
            fp.fiscal_year,
            fp.period_number,
            fp.period_name,
            ka.actual_value,
            ka.target_value,
            CASE 
                WHEN ka.target_value = 0 THEN NULL
                ELSE ((ka.actual_value - ka.target_value) / ABS(ka.target_value)) * 100
            END as variance_percentage,
            CASE 
                WHEN k.is_higher_better AND ka.actual_value >= ka.target_value THEN 'on_target'
                WHEN NOT k.is_higher_better AND ka.actual_value <= ka.target_value THEN 'on_target'
                ELSE 'off_target'
            END as performance_status
        FROM kpi_actuals ka
        JOIN kpis k ON k.id = ka.kpi_id
        JOIN fiscal_periods fp ON fp.id = ka.fiscal_period_id
        WHERE ka.kpi_id = :kpi_id
        ORDER BY fp.fiscal_year DESC, fp.period_number DESC
        LIMIT :periods
        """
        
        result = self.db.execute(text(query), {
            'kpi_id': kpi_id,
            'periods': periods
        })
        
        return [dict(row._mapping) for row in result]
    
    async def get_kpi_dashboard_summary(
        self,
        company_id: str,
        fiscal_period_id: str
    ) -> List[Dict[str, Any]]:
        """Get KPI summary for dashboard display"""
        
        query = """
        SELECT 
            k.id,
            k.code,
            k.name,
            k.category,
            k.unit_of_measure,
            k.is_higher_better,
            ka.actual_value,
            ka.target_value,
            CASE 
                WHEN ka.target_value IS NULL OR ka.target_value = 0 THEN NULL
                ELSE ((ka.actual_value - ka.target_value) / ABS(ka.target_value)) * 100
            END as variance_percentage,
            CASE 
                WHEN ka.target_value IS NULL THEN 'no_target'
                WHEN k.is_higher_better AND ka.actual_value >= ka.target_value THEN 'on_target'
                WHEN NOT k.is_higher_better AND ka.actual_value <= ka.target_value THEN 'on_target'
                WHEN ABS((ka.actual_value - ka.target_value) / ka.target_value) <= 0.05 THEN 'close_to_target'
                ELSE 'off_target'
            END as performance_status,
            ka.notes
        FROM kpis k
        LEFT JOIN kpi_actuals ka ON ka.kpi_id = k.id AND ka.fiscal_period_id = :fiscal_period_id
        WHERE k.company_id = :company_id 
            AND k.is_active = true
        ORDER BY k.category, k.name
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'fiscal_period_id': fiscal_period_id
        })
        
        return [dict(row._mapping) for row in result]
    
    async def calculate_custom_kpi(
        self,
        kpi_id: str,
        fiscal_period_id: str,
        formula: str
    ) -> Optional[Decimal]:
        """Calculate custom KPI based on formula"""
        
        # Get KPI definition
        kpi = self.db.query(KPI).filter(KPI.id == kpi_id).first()
        if not kpi:
            return None
        
        # Basic formula evaluation (in production, use a more secure parser)
        try:
            # Get financial data for substitution
            financial_data = await self.calculate_financial_kpis(kpi.company_id, fiscal_period_id)
            
            # Simple variable substitution (extend as needed)
            evaluated_formula = formula
            for key, value in financial_data.items():
                evaluated_formula = evaluated_formula.replace(f"{{{key}}}", str(value or 0))
            
            # Evaluate basic mathematical expressions
            # WARNING: In production, use a safe expression evaluator
            result = eval(evaluated_formula)
            return Decimal(str(result))
            
        except Exception:
            return None
    
    async def get_kpi_performance_summary(
        self,
        company_id: str,
        fiscal_year: int
    ) -> Dict[str, Any]:
        """Get overall KPI performance summary for the year"""
        
        query = """
        SELECT 
            k.category,
            COUNT(*) as total_kpis,
            COUNT(CASE 
                WHEN k.is_higher_better AND ka.actual_value >= ka.target_value THEN 1
                WHEN NOT k.is_higher_better AND ka.actual_value <= ka.target_value THEN 1
            END) as on_target_count,
            COUNT(CASE WHEN ka.target_value IS NULL THEN 1 END) as no_target_count,
            AVG(CASE 
                WHEN ka.target_value = 0 THEN NULL
                ELSE ABS((ka.actual_value - ka.target_value) / ka.target_value) * 100
            END) as avg_variance_percentage
        FROM kpis k
        LEFT JOIN kpi_actuals ka ON ka.kpi_id = k.id
        LEFT JOIN fiscal_periods fp ON fp.id = ka.fiscal_period_id
        WHERE k.company_id = :company_id 
            AND k.is_active = true
            AND (fp.fiscal_year = :fiscal_year OR fp.fiscal_year IS NULL)
        GROUP BY k.category
        ORDER BY k.category
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'fiscal_year': fiscal_year
        })
        
        categories = [dict(row._mapping) for row in result]
        
        # Calculate overall summary
        total_kpis = sum(cat['total_kpis'] for cat in categories)
        total_on_target = sum(cat['on_target_count'] for cat in categories)
        
        return {
            'categories': categories,
            'overall_summary': {
                'total_kpis': total_kpis,
                'on_target_count': total_on_target,
                'on_target_percentage': (total_on_target / total_kpis * 100) if total_kpis > 0 else 0,
                'avg_performance': sum(cat['avg_variance_percentage'] or 0 for cat in categories) / len(categories) if categories else 0
            }
        }
    
    async def get_kpi_alerts(
        self,
        company_id: str,
        fiscal_period_id: str,
        variance_threshold: float = 10.0
    ) -> List[Dict[str, Any]]:
        """Get KPIs that are significantly off target"""
        
        query = """
        SELECT 
            k.code,
            k.name,
            k.category,
            ka.actual_value,
            ka.target_value,
            CASE 
                WHEN ka.target_value = 0 THEN NULL
                ELSE ((ka.actual_value - ka.target_value) / ABS(ka.target_value)) * 100
            END as variance_percentage,
            CASE 
                WHEN k.is_higher_better AND ka.actual_value < ka.target_value THEN 'below_target'
                WHEN NOT k.is_higher_better AND ka.actual_value > ka.target_value THEN 'above_target'
            END as alert_type
        FROM kpis k
        JOIN kpi_actuals ka ON ka.kpi_id = k.id
        WHERE k.company_id = :company_id 
            AND ka.fiscal_period_id = :fiscal_period_id
            AND k.is_active = true
            AND ka.target_value IS NOT NULL
            AND ka.target_value != 0
            AND ABS((ka.actual_value - ka.target_value) / ka.target_value) * 100 > :variance_threshold
        ORDER BY ABS((ka.actual_value - ka.target_value) / ka.target_value) DESC
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'fiscal_period_id': fiscal_period_id,
            'variance_threshold': variance_threshold
        })
        
        return [dict(row._mapping) for row in result]