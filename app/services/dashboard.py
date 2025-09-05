from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from datetime import datetime, date, timedelta
from decimal import Decimal

from ..models.models import (
    Dashboard, DashboardWidget, KPI, KPIActual, FiscalPeriod, 
    GLAccount, Company, Scenario, BudgetLine
)
from .variance_analysis import VarianceAnalysisService
from .kpi_management import KPIManagementService

class DashboardService:
    """Service for executive and operational dashboards"""
    
    def __init__(self, db: Session):
        self.db = db
        self.variance_service = VarianceAnalysisService(db)
        self.kpi_service = KPIManagementService(db)
    
    async def get_executive_dashboard_data(
        self,
        company_id: str,
        fiscal_period_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive executive dashboard data"""
        
        # Get current period if not specified
        if not fiscal_period_id:
            current_period = self.db.execute(text("""
                SELECT id FROM fiscal_periods 
                WHERE company_id = :company_id 
                    AND start_date <= CURRENT_DATE 
                    AND end_date >= CURRENT_DATE
                LIMIT 1
            """), {'company_id': company_id}).fetchone()
            
            if current_period:
                fiscal_period_id = current_period.id
            else:
                return {'error': 'No current fiscal period found'}
        
        # Get financial summary
        financial_summary = await self._get_financial_summary(company_id, fiscal_period_id)
        
        # Get KPI summary  
        kpi_summary = await self.kpi_service.get_kpi_dashboard_summary(company_id, fiscal_period_id)
        
        # Get top variances
        top_variances = await self.variance_service.get_top_variances(
            company_id, fiscal_period_id, limit=5
        )
        
        # Get variance by account type
        variance_by_type = await self.variance_service.get_variance_summary_by_account_type(
            company_id, fiscal_period_id
        )
        
        # Get budget vs actual trend (last 12 months)
        trend_data = await self._get_budget_actual_trend(company_id, 12)
        
        # Get alerts
        kpi_alerts = await self.kpi_service.get_kpi_alerts(company_id, fiscal_period_id)
        
        return {
            'financial_summary': financial_summary,
            'kpi_summary': {
                'kpis': kpi_summary,
                'performance_stats': await self._calculate_kpi_performance_stats(kpi_summary)
            },
            'variance_analysis': {
                'top_variances': top_variances,
                'by_account_type': variance_by_type
            },
            'trends': trend_data,
            'alerts': kpi_alerts,
            'period_info': await self._get_period_info(fiscal_period_id)
        }
    
    async def _get_financial_summary(
        self,
        company_id: str,
        fiscal_period_id: str
    ) -> Dict[str, Any]:
        """Get high-level financial summary"""
        
        query = """
        SELECT 
            ga.account_type,
            SUM(CASE 
                WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                WHEN ga.account_type IN ('liability', 'equity', 'revenue') THEN gtl.credit_amount - gtl.debit_amount
                ELSE 0
            END) as actual_amount,
            SUM(COALESCE(bl.amount, 0)) as budget_amount
        FROM gl_accounts ga
        LEFT JOIN gl_transaction_lines gtl ON gtl.gl_account_id = ga.id
        LEFT JOIN gl_transactions gt ON gt.id = gtl.gl_transaction_id 
            AND gt.company_id = :company_id 
            AND gt.fiscal_period_id = :fiscal_period_id
            AND gt.is_posted = true
        LEFT JOIN budget_lines bl ON bl.gl_account_id = ga.id
            AND bl.fiscal_period_id = :fiscal_period_id
        LEFT JOIN scenarios s ON s.id = bl.scenario_id 
            AND s.scenario_type = 'budget' 
            AND s.is_approved = true
        WHERE ga.company_id = :company_id
        GROUP BY ga.account_type
        ORDER BY ga.account_type
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'fiscal_period_id': fiscal_period_id
        })
        
        data = [dict(row._mapping) for row in result.fetchall()]
        
        # Calculate key metrics
        revenue_actual = next((d['actual_amount'] for d in data if d['account_type'] == 'revenue'), 0) or 0
        revenue_budget = next((d['budget_amount'] for d in data if d['account_type'] == 'revenue'), 0) or 0
        expense_actual = next((d['actual_amount'] for d in data if d['account_type'] == 'expense'), 0) or 0
        expense_budget = next((d['budget_amount'] for d in data if d['account_type'] == 'expense'), 0) or 0
        
        return {
            'revenue': {
                'actual': float(revenue_actual),
                'budget': float(revenue_budget),
                'variance': float(revenue_actual - revenue_budget),
                'variance_percentage': float((revenue_actual - revenue_budget) / revenue_budget * 100) if revenue_budget != 0 else 0
            },
            'expenses': {
                'actual': float(expense_actual),
                'budget': float(expense_budget),
                'variance': float(expense_actual - expense_budget),
                'variance_percentage': float((expense_actual - expense_budget) / expense_budget * 100) if expense_budget != 0 else 0
            },
            'profit': {
                'actual': float(revenue_actual - expense_actual),
                'budget': float(revenue_budget - expense_budget),
                'variance': float((revenue_actual - expense_actual) - (revenue_budget - expense_budget)),
                'margin_actual': float((revenue_actual - expense_actual) / revenue_actual * 100) if revenue_actual != 0 else 0,
                'margin_budget': float((revenue_budget - expense_budget) / revenue_budget * 100) if revenue_budget != 0 else 0
            },
            'by_account_type': data
        }
    
    async def _get_budget_actual_trend(
        self,
        company_id: str,
        periods: int = 12
    ) -> List[Dict[str, Any]]:
        """Get budget vs actual trend over time"""
        
        query = """
        SELECT 
            fp.fiscal_year,
            fp.period_number,
            fp.period_name,
            SUM(CASE 
                WHEN ga.account_type = 'revenue' THEN gtl.credit_amount - gtl.debit_amount
                WHEN ga.account_type = 'expense' THEN gtl.debit_amount - gtl.credit_amount
                ELSE 0
            END) as net_actual,
            SUM(CASE 
                WHEN ga.account_type = 'revenue' AND bl.amount > 0 THEN bl.amount
                WHEN ga.account_type = 'expense' AND bl.amount > 0 THEN -bl.amount
                ELSE COALESCE(bl.amount, 0)
            END) as net_budget
        FROM fiscal_periods fp
        LEFT JOIN gl_transactions gt ON gt.fiscal_period_id = fp.id AND gt.company_id = :company_id
        LEFT JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
        LEFT JOIN gl_accounts ga ON ga.id = gtl.gl_account_id AND ga.account_type IN ('revenue', 'expense')
        LEFT JOIN budget_lines bl ON bl.fiscal_period_id = fp.id AND bl.gl_account_id = ga.id
        LEFT JOIN scenarios s ON s.id = bl.scenario_id 
            AND s.scenario_type = 'budget' 
            AND s.is_approved = true
        WHERE fp.company_id = :company_id
            AND (gt.is_posted = true OR gt.is_posted IS NULL)
        GROUP BY fp.fiscal_year, fp.period_number, fp.period_name
        ORDER BY fp.fiscal_year DESC, fp.period_number DESC
        LIMIT :periods
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'periods': periods
        })
        
        return [dict(row._mapping) for row in result.fetchall()]
    
    def _calculate_kpi_performance_stats(
        self,
        kpi_summary: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate KPI performance statistics"""
        
        if not kpi_summary:
            return {'total': 0, 'on_target': 0, 'off_target': 0, 'no_target': 0}
        
        stats = {
            'total': len(kpi_summary),
            'on_target': len([k for k in kpi_summary if k['performance_status'] == 'on_target']),
            'off_target': len([k for k in kpi_summary if k['performance_status'] == 'off_target']),
            'close_to_target': len([k for k in kpi_summary if k['performance_status'] == 'close_to_target']),
            'no_target': len([k for k in kpi_summary if k['performance_status'] == 'no_target'])
        }
        
        stats['on_target_percentage'] = (stats['on_target'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return stats
    
    async def _get_period_info(
        self,
        fiscal_period_id: str
    ) -> Dict[str, Any]:
        """Get fiscal period information"""
        
        query = """
        SELECT 
            fp.fiscal_year,
            fp.period_number,
            fp.period_name,
            fp.start_date,
            fp.end_date,
            fp.is_closed,
            c.name as company_name
        FROM fiscal_periods fp
        JOIN companies c ON c.id = fp.company_id
        WHERE fp.id = :fiscal_period_id
        """
        
        result = self.db.execute(text(query), {'fiscal_period_id': fiscal_period_id}).fetchone()
        
        if result:
            period_data = dict(result._mapping)
            
            # Calculate days remaining in period
            today = date.today()
            end_date = period_data['end_date']
            
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            days_remaining = (end_date - today).days if end_date > today else 0
            
            period_data['days_remaining'] = days_remaining
            period_data['is_current_period'] = (
                period_data['start_date'] <= today <= period_data['end_date']
            )
            
            return period_data
        
        return {}
    
    async def get_operational_dashboard_data(
        self,
        company_id: str,
        cost_center_id: Optional[str] = None,
        fiscal_period_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get operational dashboard data for department managers"""
        
        # Get current period if not specified
        if not fiscal_period_id:
            current_period = self.db.execute(text("""
                SELECT id FROM fiscal_periods 
                WHERE company_id = :company_id 
                    AND start_date <= CURRENT_DATE 
                    AND end_date >= CURRENT_DATE
                LIMIT 1
            """), {'company_id': company_id}).fetchone()
            
            if current_period:
                fiscal_period_id = current_period.id
        
        # Get departmental budget vs actual
        departmental_data = await self._get_departmental_performance(
            company_id, fiscal_period_id, cost_center_id
        )
        
        # Get expense breakdown
        expense_breakdown = await self._get_expense_breakdown(
            company_id, fiscal_period_id, cost_center_id
        )
        
        # Get budget utilization
        budget_utilization = await self._get_budget_utilization(
            company_id, fiscal_period_id, cost_center_id
        )
        
        return {
            'departmental_performance': departmental_data,
            'expense_breakdown': expense_breakdown,
            'budget_utilization': budget_utilization,
            'period_info': await self._get_period_info(fiscal_period_id)
        }
    
    async def _get_departmental_performance(
        self,
        company_id: str,
        fiscal_period_id: str,
        cost_center_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get departmental performance data"""
        
        where_clause = ""
        params = {'company_id': company_id, 'fiscal_period_id': fiscal_period_id}
        
        if cost_center_id:
            where_clause = "AND cc.id = :cost_center_id"
            params['cost_center_id'] = cost_center_id
        
        query = f"""
        SELECT 
            cc.name as department_name,
            COUNT(DISTINCT ga.id) as accounts_count,
            SUM(COALESCE(actuals.actual_amount, 0)) as total_actual,
            SUM(COALESCE(budget.budget_amount, 0)) as total_budget,
            SUM(COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0)) as total_variance,
            CASE 
                WHEN SUM(COALESCE(budget.budget_amount, 0)) = 0 THEN NULL
                ELSE (SUM(COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0)) / 
                      ABS(SUM(COALESCE(budget.budget_amount, 0)))) * 100
            END as variance_percentage
        FROM cost_centers cc
        CROSS JOIN gl_accounts ga
        LEFT JOIN (
            SELECT 
                gtl.cost_center_id,
                gtl.gl_account_id,
                SUM(gtl.debit_amount - gtl.credit_amount) as actual_amount
            FROM gl_transaction_lines gtl
            JOIN gl_transactions gt ON gt.id = gtl.gl_transaction_id
            WHERE gt.company_id = :company_id 
                AND gt.fiscal_period_id = :fiscal_period_id
                AND gt.is_posted = true
            GROUP BY gtl.cost_center_id, gtl.gl_account_id
        ) actuals ON actuals.cost_center_id = cc.id AND actuals.gl_account_id = ga.id
        LEFT JOIN (
            SELECT 
                bl.cost_center_id,
                bl.gl_account_id,
                SUM(bl.amount) as budget_amount
            FROM budget_lines bl
            JOIN scenarios s ON s.id = bl.scenario_id
            WHERE s.scenario_type = 'budget' 
                AND s.is_approved = true 
                AND s.company_id = :company_id
                AND bl.fiscal_period_id = :fiscal_period_id
            GROUP BY bl.cost_center_id, bl.gl_account_id
        ) budget ON budget.cost_center_id = cc.id AND budget.gl_account_id = ga.id
        WHERE cc.company_id = :company_id 
            AND ga.company_id = :company_id 
            {where_clause}
        GROUP BY cc.name
        ORDER BY ABS(SUM(COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0))) DESC
        """
        
        result = self.db.execute(text(query), params)
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _get_expense_breakdown(
        self,
        company_id: str,
        fiscal_period_id: str,
        cost_center_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get expense breakdown by account"""
        
        where_clause = ""
        params = {'company_id': company_id, 'fiscal_period_id': fiscal_period_id}
        
        if cost_center_id:
            where_clause = "AND gtl.cost_center_id = :cost_center_id"
            params['cost_center_id'] = cost_center_id
        
        query = f"""
        SELECT 
            ga.account_number,
            ga.name as account_name,
            SUM(gtl.debit_amount - gtl.credit_amount) as actual_amount,
            SUM(gtl.debit_amount - gtl.credit_amount) * 100.0 / 
                SUM(SUM(gtl.debit_amount - gtl.credit_amount)) OVER() as percentage
        FROM gl_accounts ga
        JOIN gl_transaction_lines gtl ON gtl.gl_account_id = ga.id
        JOIN gl_transactions gt ON gt.id = gtl.gl_transaction_id
        WHERE ga.account_type = 'expense'
            AND ga.company_id = :company_id
            AND gt.fiscal_period_id = :fiscal_period_id
            AND gt.is_posted = true
            {where_clause}
        GROUP BY ga.account_number, ga.name
        HAVING SUM(gtl.debit_amount - gtl.credit_amount) > 0
        ORDER BY SUM(gtl.debit_amount - gtl.credit_amount) DESC
        """
        
        result = self.db.execute(text(query), params)
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _get_budget_utilization(
        self,
        company_id: str,
        fiscal_period_id: str,
        cost_center_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get budget utilization summary"""
        
        where_clause = ""
        params = {'company_id': company_id, 'fiscal_period_id': fiscal_period_id}
        
        if cost_center_id:
            where_clause = "AND bl.cost_center_id = :cost_center_id"
            params['cost_center_id'] = cost_center_id
        
        query = f"""
        SELECT 
            SUM(COALESCE(actuals.actual_amount, 0)) as total_spent,
            SUM(COALESCE(bl.amount, 0)) as total_budget,
            COUNT(DISTINCT bl.gl_account_id) as budget_accounts,
            COUNT(DISTINCT actuals.gl_account_id) as accounts_with_actuals
        FROM budget_lines bl
        JOIN scenarios s ON s.id = bl.scenario_id
        LEFT JOIN (
            SELECT 
                gtl.gl_account_id,
                gtl.cost_center_id,
                SUM(gtl.debit_amount - gtl.credit_amount) as actual_amount
            FROM gl_transaction_lines gtl
            JOIN gl_transactions gt ON gt.id = gtl.gl_transaction_id
            WHERE gt.company_id = :company_id 
                AND gt.fiscal_period_id = :fiscal_period_id
                AND gt.is_posted = true
            GROUP BY gtl.gl_account_id, gtl.cost_center_id
        ) actuals ON actuals.gl_account_id = bl.gl_account_id 
            AND actuals.cost_center_id = bl.cost_center_id
        WHERE s.scenario_type = 'budget' 
            AND s.is_approved = true 
            AND s.company_id = :company_id
            AND bl.fiscal_period_id = :fiscal_period_id
            {where_clause}
        """
        
        result = self.db.execute(text(query), params).fetchone()
        
        if result:
            data = dict(result._mapping)
            total_budget = data['total_budget'] or 0
            total_spent = data['total_spent'] or 0
            
            return {
                'total_budget': float(total_budget),
                'total_spent': float(total_spent),
                'remaining_budget': float(total_budget - total_spent),
                'utilization_percentage': float(total_spent / total_budget * 100) if total_budget > 0 else 0,
                'budget_accounts': data['budget_accounts'],
                'accounts_with_actuals': data['accounts_with_actuals']
            }
        
        return {
            'total_budget': 0,
            'total_spent': 0,
            'remaining_budget': 0,
            'utilization_percentage': 0,
            'budget_accounts': 0,
            'accounts_with_actuals': 0
        }