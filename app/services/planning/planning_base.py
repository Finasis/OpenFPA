from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

class PlanningBaseService(ABC):
    """
    Base service class for planning modules
    Provides common functionality for revenue, expense, and other planning services
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_fiscal_periods(
        self,
        company_id: str,
        fiscal_year: int,
        period_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get fiscal periods for planning"""
        
        query = """
        SELECT 
            id,
            fiscal_year,
            period_number,
            period_name,
            start_date,
            end_date,
            is_closed
        FROM fiscal_periods
        WHERE company_id = :company_id
        AND fiscal_year = :fiscal_year
        """
        
        params = {
            'company_id': company_id,
            'fiscal_year': fiscal_year
        }
        
        if period_count:
            query += " LIMIT :limit"
            params['limit'] = period_count
            
        query += " ORDER BY period_number"
        
        result = self.db.execute(text(query), params)
        return [dict(row._mapping) for row in result.fetchall()]
    
    def get_historical_actuals(
        self,
        company_id: str,
        account_ids: List[str],
        start_date: date,
        end_date: date,
        group_by: str = 'month'
    ) -> pd.DataFrame:
        """Get historical actual data for accounts"""
        
        if group_by == 'month':
            group_cols = "EXTRACT(year FROM gt.transaction_date), EXTRACT(month FROM gt.transaction_date)"
            select_cols = """
                EXTRACT(year FROM gt.transaction_date) as year,
                EXTRACT(month FROM gt.transaction_date) as month
            """
        elif group_by == 'quarter':
            group_cols = "EXTRACT(year FROM gt.transaction_date), EXTRACT(quarter FROM gt.transaction_date)"
            select_cols = """
                EXTRACT(year FROM gt.transaction_date) as year,
                EXTRACT(quarter FROM gt.transaction_date) as quarter
            """
        else:  # year
            group_cols = "EXTRACT(year FROM gt.transaction_date)"
            select_cols = "EXTRACT(year FROM gt.transaction_date) as year"
        
        query = f"""
        SELECT 
            {select_cols},
            ga.account_type,
            SUM(CASE 
                WHEN ga.account_type IN ('ASSET', 'EXPENSE') THEN gtl.debit_amount - gtl.credit_amount
                ELSE gtl.credit_amount - gtl.debit_amount
            END) as amount
        FROM gl_transactions gt
        JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
        JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
        WHERE gt.company_id = :company_id
        AND gt.is_posted = true
        AND gt.transaction_date >= :start_date
        AND gt.transaction_date <= :end_date
        AND gtl.gl_account_id = ANY(:account_ids)
        GROUP BY {group_cols}, ga.account_type
        ORDER BY {group_cols}
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'start_date': start_date,
            'end_date': end_date,
            'account_ids': account_ids
        })
        
        data = [dict(row._mapping) for row in result.fetchall()]
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame()
    
    def calculate_growth_rate(
        self,
        historical_values: List[float],
        method: str = 'cagr'
    ) -> float:
        """Calculate growth rate from historical values"""
        
        if not historical_values or len(historical_values) < 2:
            return 0.0
        
        # Remove zeros and negative values for calculation
        clean_values = [v for v in historical_values if v > 0]
        if len(clean_values) < 2:
            return 0.0
        
        if method == 'cagr':  # Compound Annual Growth Rate
            periods = len(clean_values) - 1
            if periods > 0 and clean_values[0] > 0:
                return (clean_values[-1] / clean_values[0]) ** (1 / periods) - 1
        
        elif method == 'average':  # Average period-over-period growth
            growth_rates = []
            for i in range(1, len(clean_values)):
                if clean_values[i-1] > 0:
                    growth = (clean_values[i] - clean_values[i-1]) / clean_values[i-1]
                    growth_rates.append(growth)
            
            if growth_rates:
                return np.mean(growth_rates)
        
        elif method == 'linear':  # Linear regression slope
            x = np.arange(len(clean_values))
            coefficients = np.polyfit(x, clean_values, 1)
            if clean_values[0] > 0:
                return coefficients[0] / clean_values[0]
        
        return 0.0
    
    def apply_seasonality(
        self,
        base_values: List[float],
        historical_data: pd.DataFrame,
        date_column: str = 'month'
    ) -> List[float]:
        """Apply seasonal factors to base values"""
        
        if historical_data.empty or date_column not in historical_data.columns:
            return base_values
        
        # Calculate seasonal indices
        seasonal_indices = {}
        
        if date_column == 'month':
            for month in range(1, 13):
                month_data = historical_data[historical_data[date_column] == month]['amount'].values
                if len(month_data) > 0:
                    avg_month = np.mean(month_data)
                    overall_avg = historical_data['amount'].mean()
                    if overall_avg > 0:
                        seasonal_indices[month] = avg_month / overall_avg
                    else:
                        seasonal_indices[month] = 1.0
                else:
                    seasonal_indices[month] = 1.0
        
        # Apply seasonal factors
        adjusted_values = []
        for i, value in enumerate(base_values):
            month = (i % 12) + 1
            seasonal_factor = seasonal_indices.get(month, 1.0)
            adjusted_values.append(value * seasonal_factor)
        
        return adjusted_values
    
    def calculate_confidence_intervals(
        self,
        forecast_values: List[float],
        historical_std: float,
        confidence_level: float = 0.95
    ) -> List[Tuple[float, float]]:
        """Calculate confidence intervals for forecast values"""
        
        # Z-scores for common confidence levels
        z_scores = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }
        
        z_score = z_scores.get(confidence_level, 1.96)
        intervals = []
        
        for i, value in enumerate(forecast_values):
            # Uncertainty increases with forecast horizon
            uncertainty_factor = 1 + (i * 0.02)  # 2% increase per period
            margin = historical_std * z_score * uncertainty_factor
            
            lower = max(0, value - margin)
            upper = value + margin
            intervals.append((lower, upper))
        
        return intervals
    
    def get_budget_comparison(
        self,
        company_id: str,
        fiscal_period_id: str,
        account_ids: List[str]
    ) -> Dict[str, Any]:
        """Get budget vs actual comparison"""
        
        query = """
        SELECT 
            ga.id as account_id,
            ga.account_number,
            ga.name as account_name,
            COALESCE(SUM(CASE 
                WHEN ga.account_type IN ('ASSET', 'EXPENSE') THEN gtl.debit_amount - gtl.credit_amount
                ELSE gtl.credit_amount - gtl.debit_amount
            END), 0) as actual_amount,
            COALESCE(bl.amount, 0) as budget_amount
        FROM gl_accounts ga
        LEFT JOIN gl_transaction_lines gtl ON gtl.gl_account_id = ga.id
        LEFT JOIN gl_transactions gt ON gt.id = gtl.gl_transaction_id 
            AND gt.fiscal_period_id = :period_id
            AND gt.is_posted = true
        LEFT JOIN budget_lines bl ON bl.gl_account_id = ga.id 
            AND bl.fiscal_period_id = :period_id
        WHERE ga.company_id = :company_id
        AND ga.id = ANY(:account_ids)
        GROUP BY ga.id, ga.account_number, ga.name, bl.amount
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'period_id': fiscal_period_id,
            'account_ids': account_ids
        })
        
        comparison = []
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            actual = float(row_dict['actual_amount'])
            budget = float(row_dict['budget_amount'])
            
            variance = actual - budget
            variance_pct = (variance / budget * 100) if budget != 0 else 0
            
            comparison.append({
                'account_id': row_dict['account_id'],
                'account_number': row_dict['account_number'],
                'account_name': row_dict['account_name'],
                'actual': actual,
                'budget': budget,
                'variance': variance,
                'variance_pct': variance_pct
            })
        
        return {
            'details': comparison,
            'total_actual': sum(c['actual'] for c in comparison),
            'total_budget': sum(c['budget'] for c in comparison),
            'total_variance': sum(c['variance'] for c in comparison)
        }
    
    @abstractmethod
    def generate_forecast(
        self,
        company_id: str,
        forecast_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate forecast - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def calculate_metrics(
        self,
        company_id: str,
        period_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate key metrics - must be implemented by subclasses"""
        pass