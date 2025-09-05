from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from datetime import datetime, date
from decimal import Decimal

from ..models.models import (
    FiscalPeriod, GLAccount, CostCenter, 
    BudgetLine, Scenario, GLTransaction, GLTransactionLine
)

class VarianceAnalysisService:
    """Service for variance analysis calculations and insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_variance_for_period(
        self,
        company_id: str,
        fiscal_period_id: str,
        cost_center_id: Optional[str] = None,
        gl_account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculate variance between actual and budget for a fiscal period"""
        
        # Base query for variance calculation
        query = """
        SELECT 
            fp.id as fiscal_period_id,
            fp.period_name,
            ga.id as gl_account_id,
            ga.account_number,
            ga.name as account_name,
            ga.account_type,
            cc.id as cost_center_id,
            cc.name as cost_center_name,
            COALESCE(actuals.actual_amount, 0) as actual_amount,
            COALESCE(budget.budget_amount, 0) as budget_amount,
            COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0) as variance_amount,
            CASE 
                WHEN COALESCE(budget.budget_amount, 0) = 0 THEN NULL
                ELSE ((COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0)) / 
                      ABS(budget.budget_amount)) * 100
            END as variance_percentage
        FROM fiscal_periods fp
        CROSS JOIN gl_accounts ga
        CROSS JOIN cost_centers cc
        LEFT JOIN (
            SELECT 
                gt.fiscal_period_id,
                gtl.gl_account_id,
                gtl.cost_center_id,
                SUM(CASE 
                    WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                    ELSE gtl.credit_amount - gtl.debit_amount
                END) as actual_amount
            FROM gl_transactions gt
            JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
            JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
            WHERE gt.is_posted = true AND gt.company_id = :company_id
            GROUP BY gt.fiscal_period_id, gtl.gl_account_id, gtl.cost_center_id
        ) actuals ON actuals.fiscal_period_id = fp.id 
            AND actuals.gl_account_id = ga.id 
            AND actuals.cost_center_id = cc.id
        LEFT JOIN (
            SELECT 
                bl.fiscal_period_id,
                bl.gl_account_id,
                bl.cost_center_id,
                SUM(bl.amount) as budget_amount
            FROM budget_lines bl
            JOIN scenarios s ON s.id = bl.scenario_id
            WHERE s.scenario_type = 'budget' 
                AND s.is_approved = true 
                AND s.company_id = :company_id
            GROUP BY bl.fiscal_period_id, bl.gl_account_id, bl.cost_center_id
        ) budget ON budget.fiscal_period_id = fp.id 
            AND budget.gl_account_id = ga.id 
            AND budget.cost_center_id = cc.id
        WHERE fp.company_id = :company_id 
            AND ga.company_id = :company_id 
            AND cc.company_id = :company_id
            AND fp.id = :fiscal_period_id
        """
        
        # Add filters
        params = {
            'company_id': company_id,
            'fiscal_period_id': fiscal_period_id
        }
        
        if cost_center_id:
            query += " AND cc.id = :cost_center_id"
            params['cost_center_id'] = cost_center_id
            
        if gl_account_id:
            query += " AND ga.id = :gl_account_id" 
            params['gl_account_id'] = gl_account_id
            
        query += " AND (actuals.actual_amount IS NOT NULL OR budget.budget_amount IS NOT NULL)"
        query += " ORDER BY ga.account_number, cc.name"
        
        result = self.db.execute(text(query), params)
        return [dict(row._mapping) for row in result]
    
    async def get_variance_trends(
        self,
        company_id: str,
        gl_account_id: str,
        periods: int = 12
    ) -> List[Dict[str, Any]]:
        """Get variance trends over multiple periods"""
        
        query = """
        SELECT 
            fp.fiscal_year,
            fp.period_number,
            fp.period_name,
            COALESCE(actuals.actual_amount, 0) as actual_amount,
            COALESCE(budget.budget_amount, 0) as budget_amount,
            COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0) as variance_amount
        FROM fiscal_periods fp
        LEFT JOIN (
            SELECT 
                gt.fiscal_period_id,
                SUM(CASE 
                    WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                    ELSE gtl.credit_amount - gtl.debit_amount
                END) as actual_amount
            FROM gl_transactions gt
            JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
            JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
            WHERE gt.is_posted = true 
                AND gt.company_id = :company_id
                AND gtl.gl_account_id = :gl_account_id
            GROUP BY gt.fiscal_period_id
        ) actuals ON actuals.fiscal_period_id = fp.id
        LEFT JOIN (
            SELECT 
                bl.fiscal_period_id,
                SUM(bl.amount) as budget_amount
            FROM budget_lines bl
            JOIN scenarios s ON s.id = bl.scenario_id
            WHERE s.scenario_type = 'budget' 
                AND s.is_approved = true 
                AND s.company_id = :company_id
                AND bl.gl_account_id = :gl_account_id
            GROUP BY bl.fiscal_period_id
        ) budget ON budget.fiscal_period_id = fp.id
        WHERE fp.company_id = :company_id
        ORDER BY fp.fiscal_year DESC, fp.period_number DESC
        LIMIT :periods
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'gl_account_id': gl_account_id,
            'periods': periods
        })
        
        return [dict(row._mapping) for row in result]
    
    async def get_top_variances(
        self,
        company_id: str,
        fiscal_period_id: str,
        limit: int = 10,
        variance_type: str = 'absolute'  # 'absolute' or 'percentage'
    ) -> List[Dict[str, Any]]:
        """Get top variances for a period"""
        
        order_by = "ABS(variance_amount) DESC" if variance_type == 'absolute' else "ABS(variance_percentage) DESC"
        
        query = f"""
        SELECT 
            ga.account_number,
            ga.name as account_name,
            ga.account_type,
            cc.name as cost_center_name,
            COALESCE(actuals.actual_amount, 0) as actual_amount,
            COALESCE(budget.budget_amount, 0) as budget_amount,
            COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0) as variance_amount,
            CASE 
                WHEN COALESCE(budget.budget_amount, 0) = 0 THEN NULL
                ELSE ((COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0)) / 
                      ABS(budget.budget_amount)) * 100
            END as variance_percentage
        FROM gl_accounts ga
        CROSS JOIN cost_centers cc
        LEFT JOIN (
            SELECT 
                gtl.gl_account_id,
                gtl.cost_center_id,
                SUM(CASE 
                    WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                    ELSE gtl.credit_amount - gtl.debit_amount
                END) as actual_amount
            FROM gl_transactions gt
            JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
            JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
            WHERE gt.is_posted = true 
                AND gt.company_id = :company_id
                AND gt.fiscal_period_id = :fiscal_period_id
            GROUP BY gtl.gl_account_id, gtl.cost_center_id
        ) actuals ON actuals.gl_account_id = ga.id AND actuals.cost_center_id = cc.id
        LEFT JOIN (
            SELECT 
                bl.gl_account_id,
                bl.cost_center_id,
                SUM(bl.amount) as budget_amount
            FROM budget_lines bl
            JOIN scenarios s ON s.id = bl.scenario_id
            WHERE s.scenario_type = 'budget' 
                AND s.is_approved = true 
                AND s.company_id = :company_id
                AND bl.fiscal_period_id = :fiscal_period_id
            GROUP BY bl.gl_account_id, bl.cost_center_id
        ) budget ON budget.gl_account_id = ga.id AND budget.cost_center_id = cc.id
        WHERE ga.company_id = :company_id 
            AND cc.company_id = :company_id
            AND (actuals.actual_amount IS NOT NULL OR budget.budget_amount IS NOT NULL)
        ORDER BY {order_by}
        LIMIT :limit
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'fiscal_period_id': fiscal_period_id,
            'limit': limit
        })
        
        return [dict(row._mapping) for row in result]
    
    async def get_variance_summary_by_account_type(
        self,
        company_id: str,
        fiscal_period_id: str
    ) -> List[Dict[str, Any]]:
        """Get variance summary grouped by account type"""
        
        query = """
        SELECT 
            ga.account_type,
            COUNT(*) as account_count,
            SUM(COALESCE(actuals.actual_amount, 0)) as total_actual,
            SUM(COALESCE(budget.budget_amount, 0)) as total_budget,
            SUM(COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0)) as total_variance,
            CASE 
                WHEN SUM(COALESCE(budget.budget_amount, 0)) = 0 THEN NULL
                ELSE (SUM(COALESCE(actuals.actual_amount, 0) - COALESCE(budget.budget_amount, 0)) / 
                      ABS(SUM(COALESCE(budget.budget_amount, 0)))) * 100
            END as variance_percentage
        FROM gl_accounts ga
        LEFT JOIN (
            SELECT 
                gtl.gl_account_id,
                SUM(CASE 
                    WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                    ELSE gtl.credit_amount - gtl.debit_amount
                END) as actual_amount
            FROM gl_transactions gt
            JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
            JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
            WHERE gt.is_posted = true 
                AND gt.company_id = :company_id
                AND gt.fiscal_period_id = :fiscal_period_id
            GROUP BY gtl.gl_account_id
        ) actuals ON actuals.gl_account_id = ga.id
        LEFT JOIN (
            SELECT 
                bl.gl_account_id,
                SUM(bl.amount) as budget_amount
            FROM budget_lines bl
            JOIN scenarios s ON s.id = bl.scenario_id
            WHERE s.scenario_type = 'budget' 
                AND s.is_approved = true 
                AND s.company_id = :company_id
                AND bl.fiscal_period_id = :fiscal_period_id
            GROUP BY bl.gl_account_id
        ) budget ON budget.gl_account_id = ga.id
        WHERE ga.company_id = :company_id
        GROUP BY ga.account_type
        ORDER BY ga.account_type
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'fiscal_period_id': fiscal_period_id
        })
        
        return [dict(row._mapping) for row in result]