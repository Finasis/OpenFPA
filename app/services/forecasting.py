from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error, r2_score
import pandas as pd

from ..models.models import (
    ForecastModel, ForecastResult, GLAccount, FiscalPeriod, 
    GLTransactionLine, BudgetLine, BusinessDriver, DriverValue
)

class ForecastingService:
    """Service for statistical forecasting and predictive analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_historical_data(
        self,
        company_id: str,
        gl_account_id: str,
        periods: int = 24
    ) -> List[Dict[str, Any]]:
        """Get historical actuals for forecasting"""
        
        query = """
        SELECT 
            fp.fiscal_year,
            fp.period_number,
            fp.start_date,
            fp.end_date,
            COALESCE(SUM(CASE 
                WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                ELSE gtl.credit_amount - gtl.debit_amount
            END), 0) as actual_amount
        FROM fiscal_periods fp
        LEFT JOIN gl_transactions gt ON gt.fiscal_period_id = fp.id AND gt.company_id = :company_id
        LEFT JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id 
            AND gtl.gl_account_id = :gl_account_id
        LEFT JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
        WHERE fp.company_id = :company_id
            AND gt.is_posted = true OR gt.is_posted IS NULL
        GROUP BY fp.fiscal_year, fp.period_number, fp.start_date, fp.end_date
        ORDER BY fp.fiscal_year DESC, fp.period_number DESC
        LIMIT :periods
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'gl_account_id': gl_account_id,
            'periods': periods
        })
        
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def create_linear_trend_forecast(
        self,
        company_id: str,
        gl_account_id: str,
        forecast_periods: int = 12,
        historical_periods: int = 24
    ) -> Dict[str, Any]:
        """Create linear trend forecast using historical data"""
        
        # Get historical data
        historical_data = await self.get_historical_data(
            company_id, gl_account_id, historical_periods
        )
        
        if len(historical_data) < 6:  # Need at least 6 periods
            return {'error': 'Insufficient historical data'}
        
        # Prepare data for linear regression
        df = pd.DataFrame(historical_data)
        df['period_index'] = range(len(df))
        
        # Remove outliers (simple method - values beyond 2 standard deviations)
        mean_amount = df['actual_amount'].mean()
        std_amount = df['actual_amount'].std()
        df_clean = df[abs(df['actual_amount'] - mean_amount) <= 2 * std_amount]
        
        if len(df_clean) < 3:
            df_clean = df  # Use original data if too many outliers
        
        # Fit linear regression
        X = df_clean[['period_index']].values
        y = df_clean['actual_amount'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate model accuracy
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        mape = mean_absolute_percentage_error(y, y_pred) if min(y) != 0 else 0
        
        # Generate forecasts
        forecasts = []
        for i in range(forecast_periods):
            future_index = len(df) + i
            predicted_amount = model.predict([[future_index]])[0]
            
            # Calculate confidence interval (simple approach)
            residuals = y - y_pred
            std_residual = np.std(residuals)
            confidence_interval = 1.96 * std_residual  # 95% confidence interval
            
            forecasts.append({
                'period_index': future_index,
                'forecasted_amount': float(predicted_amount),
                'confidence_interval_low': float(predicted_amount - confidence_interval),
                'confidence_interval_high': float(predicted_amount + confidence_interval),
                'confidence_score': float(r2)
            })
        
        return {
            'model_type': 'linear_regression',
            'accuracy_metrics': {
                'r2_score': float(r2),
                'mape': float(mape)
            },
            'forecasts': forecasts,
            'historical_periods_used': len(df_clean)
        }
    
    async def create_seasonal_forecast(
        self,
        company_id: str,
        gl_account_id: str,
        forecast_periods: int = 12
    ) -> Dict[str, Any]:
        """Create seasonal forecast using historical patterns"""
        
        historical_data = await self.get_historical_data(
            company_id, gl_account_id, 36  # Need 3 years for seasonality
        )
        
        if len(historical_data) < 12:
            return {'error': 'Insufficient data for seasonal analysis'}
        
        df = pd.DataFrame(historical_data)
        
        # Calculate seasonal averages
        seasonal_patterns = df.groupby('period_number')['actual_amount'].agg([
            'mean', 'std', 'count'
        ]).reset_index()
        
        # Calculate trend
        df_sorted = df.sort_values(['fiscal_year', 'period_number'])
        trend_slope = np.polyfit(range(len(df_sorted)), df_sorted['actual_amount'], 1)[0]
        
        # Generate forecasts
        forecasts = []
        current_year = df['fiscal_year'].max()
        
        for i in range(forecast_periods):
            period_num = ((df['period_number'].max() + i) % 12) + 1
            forecast_year = current_year + ((df['period_number'].max() + i) // 12)
            
            # Get seasonal component
            seasonal_data = seasonal_patterns[seasonal_patterns['period_number'] == period_num]
            if len(seasonal_data) > 0:
                seasonal_base = seasonal_data['mean'].iloc[0]
                seasonal_std = seasonal_data['std'].iloc[0]
            else:
                seasonal_base = df['actual_amount'].mean()
                seasonal_std = df['actual_amount'].std()
            
            # Apply trend
            trend_adjustment = trend_slope * (len(df) + i)
            forecasted_amount = seasonal_base + trend_adjustment
            
            # Confidence interval based on seasonal variation
            confidence_interval = 1.96 * (seasonal_std or df['actual_amount'].std())
            
            forecasts.append({
                'period_number': period_num,
                'fiscal_year': forecast_year,
                'forecasted_amount': float(forecasted_amount),
                'confidence_interval_low': float(forecasted_amount - confidence_interval),
                'confidence_interval_high': float(forecasted_amount + confidence_interval),
                'confidence_score': 0.8  # Static confidence for seasonal model
            })
        
        return {
            'model_type': 'seasonal',
            'seasonal_patterns': seasonal_patterns.to_dict('records'),
            'trend_slope': float(trend_slope),
            'forecasts': forecasts
        }
    
    async def create_moving_average_forecast(
        self,
        company_id: str,
        gl_account_id: str,
        window_size: int = 6,
        forecast_periods: int = 12
    ) -> Dict[str, Any]:
        """Create moving average forecast"""
        
        historical_data = await self.get_historical_data(
            company_id, gl_account_id, window_size * 2
        )
        
        if len(historical_data) < window_size:
            return {'error': 'Insufficient data for moving average'}
        
        df = pd.DataFrame(historical_data)
        df = df.sort_values(['fiscal_year', 'period_number'])
        
        # Calculate moving average
        df['moving_average'] = df['actual_amount'].rolling(window=window_size).mean()
        
        # Get latest moving average for forecasting
        latest_ma = df['moving_average'].dropna().iloc[-1]
        
        # Calculate standard deviation for confidence intervals
        recent_values = df['actual_amount'].tail(window_size)
        std_dev = recent_values.std()
        
        # Generate forecasts (flat forecast based on moving average)
        forecasts = []
        for i in range(forecast_periods):
            confidence_interval = 1.96 * std_dev
            
            forecasts.append({
                'period_index': i + 1,
                'forecasted_amount': float(latest_ma),
                'confidence_interval_low': float(latest_ma - confidence_interval),
                'confidence_interval_high': float(latest_ma + confidence_interval),
                'confidence_score': 0.7  # Static confidence for moving average
            })
        
        return {
            'model_type': 'moving_average',
            'window_size': window_size,
            'latest_moving_average': float(latest_ma),
            'forecasts': forecasts
        }
    
    async def create_driver_based_forecast(
        self,
        company_id: str,
        gl_account_id: str,
        forecast_periods: int = 12
    ) -> Dict[str, Any]:
        """Create forecast based on business drivers"""
        
        # Get driver relationships for this GL account
        query = """
        SELECT 
            bd.id as driver_id,
            bd.name as driver_name,
            bd.unit_of_measure,
            dr.coefficient,
            dr.relationship_type
        FROM driver_relationships dr
        JOIN business_drivers bd ON bd.id = dr.business_driver_id
        WHERE dr.gl_account_id = :gl_account_id 
            AND dr.is_active = true
            AND bd.company_id = :company_id
        """
        
        result = self.db.execute(text(query), {
            'gl_account_id': gl_account_id,
            'company_id': company_id
        })
        
        drivers = [dict(row._mapping) for row in result.fetchall()]
        
        if not drivers:
            return {'error': 'No active driver relationships found'}
        
        forecasts = []
        
        # For each forecast period, calculate based on driver values
        for period in range(1, forecast_periods + 1):
            total_forecast = 0
            driver_contributions = []
            
            for driver in drivers:
                # Get latest driver value (in real implementation, get planned values)
                driver_query = """
                SELECT planned_value, actual_value
                FROM driver_values dv
                JOIN fiscal_periods fp ON fp.id = dv.fiscal_period_id
                WHERE dv.business_driver_id = :driver_id
                    AND fp.company_id = :company_id
                ORDER BY fp.fiscal_year DESC, fp.period_number DESC
                LIMIT 1
                """
                
                driver_result = self.db.execute(text(driver_query), {
                    'driver_id': driver['driver_id'],
                    'company_id': company_id
                }).fetchone()
                
                if driver_result:
                    # Use planned value if available, otherwise actual
                    driver_value = driver_result.planned_value or driver_result.actual_value or 0
                    
                    # Apply relationship
                    if driver['relationship_type'] == 'linear':
                        contribution = float(driver_value) * float(driver['coefficient'])
                    else:
                        contribution = float(driver_value)  # Simplified for other types
                    
                    total_forecast += contribution
                    driver_contributions.append({
                        'driver_name': driver['driver_name'],
                        'driver_value': float(driver_value),
                        'contribution': contribution
                    })
            
            forecasts.append({
                'period': period,
                'forecasted_amount': total_forecast,
                'driver_contributions': driver_contributions,
                'confidence_score': 0.85  # High confidence for driver-based forecasts
            })
        
        return {
            'model_type': 'driver_based',
            'drivers_used': drivers,
            'forecasts': forecasts
        }
    
    async def get_forecast_accuracy(
        self,
        forecast_model_id: str,
        periods_back: int = 6
    ) -> Dict[str, Any]:
        """Calculate forecast accuracy for a model"""
        
        query = """
        SELECT 
            fr.forecasted_amount,
            fr.fiscal_period_id,
            fp.fiscal_year,
            fp.period_number,
            COALESCE(SUM(CASE 
                WHEN ga.account_type IN ('asset', 'expense') THEN gtl.debit_amount - gtl.credit_amount
                ELSE gtl.credit_amount - gtl.debit_amount
            END), 0) as actual_amount
        FROM forecast_results fr
        JOIN forecast_models fm ON fm.id = fr.forecast_model_id
        JOIN fiscal_periods fp ON fp.id = fr.fiscal_period_id
        LEFT JOIN gl_transactions gt ON gt.fiscal_period_id = fp.id
        LEFT JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id 
            AND gtl.gl_account_id = fm.gl_account_id
        LEFT JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
        WHERE fr.forecast_model_id = :forecast_model_id
            AND gt.is_posted = true
        GROUP BY fr.forecasted_amount, fr.fiscal_period_id, fp.fiscal_year, fp.period_number
        ORDER BY fp.fiscal_year DESC, fp.period_number DESC
        LIMIT :periods_back
        """
        
        result = self.db.execute(text(query), {
            'forecast_model_id': forecast_model_id,
            'periods_back': periods_back
        })
        
        data = [dict(row._mapping) for row in result.fetchall()]
        
        if len(data) < 2:
            return {'error': 'Insufficient data for accuracy calculation'}
        
        # Calculate accuracy metrics
        forecasted = [row['forecasted_amount'] for row in data]
        actual = [row['actual_amount'] for row in data]
        
        # Mean Absolute Percentage Error (MAPE)
        mape = np.mean([abs((a - f) / a) for a, f in zip(actual, forecasted) if a != 0]) * 100
        
        # Mean Absolute Error (MAE)
        mae = np.mean([abs(a - f) for a, f in zip(actual, forecasted)])
        
        # Root Mean Square Error (RMSE)
        rmse = np.sqrt(np.mean([(a - f) ** 2 for a, f in zip(actual, forecasted)]))
        
        return {
            'mape': float(mape),
            'mae': float(mae),
            'rmse': float(rmse),
            'periods_analyzed': len(data),
            'accuracy_data': data
        }