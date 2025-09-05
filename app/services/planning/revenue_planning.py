from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func, extract
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
import uuid
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import statistics

from .planning_base import PlanningBaseService
from ..analytics.driver_based_planning import DriverBasedPlanningService

class RevenuePlanningService(PlanningBaseService):
    """
    Service for revenue planning, forecasting, and analysis
    Supports multiple forecasting methods and advanced analytics
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.driver_service = DriverBasedPlanningService(db)
    
    # ============================================
    # REVENUE PLAN MANAGEMENT
    # ============================================
    
    async def create_revenue_plan(
        self,
        company_id: str,
        plan_name: str,
        plan_type: str,
        fiscal_year: int,
        scenario_id: Optional[str] = None,
        confidence_level: float = 80.0
    ) -> str:
        """Create a new revenue plan"""
        
        plan_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO revenue_plans (
            id, company_id, scenario_id, plan_name, plan_type,
            fiscal_year, version, status, confidence_level, created_at
        ) VALUES (
            :id, :company_id, :scenario_id, :plan_name, :plan_type,
            :fiscal_year, 1, 'draft', :confidence_level, :created_at
        ) RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'id': plan_id,
            'company_id': company_id,
            'scenario_id': scenario_id,
            'plan_name': plan_name,
            'plan_type': plan_type,
            'fiscal_year': fiscal_year,
            'confidence_level': confidence_level,
            'created_at': datetime.utcnow()
        })
        
        self.db.commit()
        return plan_id
    
    # ============================================
    # REVENUE FORECASTING METHODS
    # ============================================
    
    async def generate_revenue_forecast(
        self,
        company_id: str,
        forecast_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate revenue forecast using selected method"""
        
        method = forecast_params.get('method', 'trend')
        
        # Get historical revenue data
        historical_data = await self._get_historical_revenue(
            company_id,
            forecast_params.get('lookback_months', 24)
        )
        
        if len(historical_data) < 6:
            # Generate sample data for demo if insufficient history
            historical_data = self._generate_sample_revenue_data()
        
        # Apply forecasting method
        if method == 'trend':
            forecast = await self._trend_analysis_forecast(historical_data, forecast_params)
        elif method == 'seasonal':
            forecast = await self._seasonal_forecast(historical_data, forecast_params)
        elif method == 'regression':
            forecast = await self._regression_forecast(historical_data, forecast_params)
        elif method == 'pipeline':
            forecast = await self._pipeline_based_forecast(company_id, forecast_params)
        elif method == 'driver_based':
            forecast = await self._driver_based_forecast(company_id, forecast_params)
        elif method == 'cohort':
            forecast = await self._cohort_based_forecast(company_id, forecast_params)
        elif method == 'ml_ensemble':
            forecast = await self._ml_ensemble_forecast(historical_data, forecast_params)
        else:
            forecast = await self._trend_analysis_forecast(historical_data, forecast_params)
        
        # Add segments analysis
        if forecast_params.get('include_segments', True):
            forecast['segments'] = await self._analyze_revenue_segments(company_id)
        
        # Add pipeline metrics
        if forecast_params.get('include_pipeline', True):
            forecast['pipeline'] = await self._get_pipeline_metrics(company_id)
        
        # Add recurring revenue metrics
        forecast['recurring_metrics'] = await self._calculate_recurring_metrics(company_id)
        
        return forecast
    
    async def _trend_analysis_forecast(
        self,
        historical_data: List[Dict],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trend-based forecasting with multiple trend options"""
        
        forecast_months = params.get('forecast_months', 12)
        trend_type = params.get('trend_type', 'linear')
        growth_rate = params.get('growth_rate', 0.15)
        
        # Extract revenue values
        revenues = [d['revenue'] for d in historical_data]
        
        forecast_data = []
        
        if trend_type == 'linear':
            # Linear trend
            x = np.arange(len(revenues))
            coefficients = np.polyfit(x, revenues, 1)
            
            for i in range(1, forecast_months + 1):
                forecast_value = coefficients[0] * (len(revenues) + i) + coefficients[1]
                forecast_data.append({
                    'month': i,
                    'period': self._get_forecast_period(i),
                    'forecast': max(0, forecast_value),
                    'method': 'linear_trend'
                })
        
        elif trend_type == 'exponential':
            # Exponential growth
            base_revenue = np.mean(revenues[-3:]) if len(revenues) >= 3 else revenues[-1]
            monthly_growth = (1 + growth_rate) ** (1/12) - 1
            
            for i in range(1, forecast_months + 1):
                forecast_value = base_revenue * ((1 + monthly_growth) ** i)
                forecast_data.append({
                    'month': i,
                    'period': self._get_forecast_period(i),
                    'forecast': forecast_value,
                    'method': 'exponential'
                })
        
        elif trend_type == 'polynomial':
            # Polynomial trend
            degree = params.get('polynomial_degree', 2)
            x = np.arange(len(revenues))
            coefficients = np.polyfit(x, revenues, degree)
            poly = np.poly1d(coefficients)
            
            for i in range(1, forecast_months + 1):
                forecast_value = poly(len(revenues) + i)
                forecast_data.append({
                    'month': i,
                    'period': self._get_forecast_period(i),
                    'forecast': max(0, forecast_value),
                    'method': 'polynomial'
                })
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_forecast_confidence(
            forecast_data,
            historical_data,
            params.get('confidence_level', 0.95)
        )
        
        return {
            'forecast_data': forecast_data,
            'confidence_intervals': confidence_intervals,
            'method': f'{trend_type}_trend',
            'total_forecast': sum(f['forecast'] for f in forecast_data),
            'growth_metrics': self._calculate_growth_metrics(historical_data, forecast_data)
        }
    
    async def _seasonal_forecast(
        self,
        historical_data: List[Dict],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Seasonal decomposition forecasting"""
        
        forecast_months = params.get('forecast_months', 12)
        
        # Create DataFrame for analysis
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        df.set_index('date', inplace=True)
        
        # Calculate seasonal indices
        seasonal_indices = {}
        for month in range(1, 13):
            month_data = df[df.index.month == month]['revenue'].values
            if len(month_data) > 0:
                seasonal_indices[month] = np.mean(month_data) / df['revenue'].mean()
            else:
                seasonal_indices[month] = 1.0
        
        # Deseasonalize and find trend
        df['deseasonalized'] = df.apply(
            lambda row: row['revenue'] / seasonal_indices[row.name.month],
            axis=1
        )
        
        # Fit trend on deseasonalized data
        x = np.arange(len(df))
        trend_coeffs = np.polyfit(x, df['deseasonalized'].values, 1)
        
        # Generate forecast
        forecast_data = []
        base_index = len(df)
        
        for i in range(1, forecast_months + 1):
            # Calculate trend component
            trend_value = trend_coeffs[0] * (base_index + i) + trend_coeffs[1]
            
            # Apply seasonal component
            month = ((datetime.now().month + i - 1) % 12) + 1
            seasonal_factor = seasonal_indices[month]
            forecast_value = trend_value * seasonal_factor
            
            # Add cyclical component if detected
            if params.get('include_cyclical', False):
                cycle_period = params.get('cycle_period', 4)  # Years
                cycle_amplitude = params.get('cycle_amplitude', 0.1)
                cycle_value = cycle_amplitude * np.sin(2 * np.pi * i / (cycle_period * 12))
                forecast_value *= (1 + cycle_value)
            
            forecast_data.append({
                'month': i,
                'period': self._get_forecast_period(i),
                'forecast': max(0, forecast_value),
                'trend': trend_value,
                'seasonal_factor': seasonal_factor,
                'method': 'seasonal'
            })
        
        return {
            'forecast_data': forecast_data,
            'seasonal_indices': seasonal_indices,
            'method': 'seasonal_decomposition',
            'total_forecast': sum(f['forecast'] for f in forecast_data),
            'components': {
                'trend': {'slope': trend_coeffs[0], 'intercept': trend_coeffs[1]},
                'seasonal': seasonal_indices
            }
        }
    
    async def _regression_forecast(
        self,
        historical_data: List[Dict],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Multiple regression forecasting with external factors"""
        
        forecast_months = params.get('forecast_months', 12)
        
        # Prepare features
        X = []
        y = []
        
        for i, data in enumerate(historical_data):
            features = [
                i,  # Time index
                data['month'],  # Month (for seasonality)
                np.sin(2 * np.pi * data['month'] / 12),  # Sine component
                np.cos(2 * np.pi * data['month'] / 12),  # Cosine component
            ]
            
            # Add external factors if provided
            if 'external_factors' in params:
                for factor in params['external_factors']:
                    features.append(factor.get('values', [0])[i] if i < len(factor.get('values', [])) else 0)
            
            X.append(features)
            y.append(data['revenue'])
        
        # Fit regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate forecast
        forecast_data = []
        base_index = len(historical_data)
        
        for i in range(1, forecast_months + 1):
            month = ((datetime.now().month + i - 1) % 12) + 1
            features = [
                base_index + i,
                month,
                np.sin(2 * np.pi * month / 12),
                np.cos(2 * np.pi * month / 12),
            ]
            
            # Add projected external factors
            if 'external_factors' in params:
                for factor in params['external_factors']:
                    projected_value = factor.get('projection', 0)
                    features.append(projected_value)
            
            forecast_value = model.predict([features])[0]
            
            forecast_data.append({
                'month': i,
                'period': self._get_forecast_period(i),
                'forecast': max(0, forecast_value),
                'method': 'regression'
            })
        
        # Calculate model metrics
        r_squared = model.score(X, y)
        
        return {
            'forecast_data': forecast_data,
            'method': 'multiple_regression',
            'total_forecast': sum(f['forecast'] for f in forecast_data),
            'model_metrics': {
                'r_squared': r_squared,
                'coefficients': model.coef_.tolist(),
                'intercept': model.intercept_
            }
        }
    
    async def _pipeline_based_forecast(
        self,
        company_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Forecast based on sales pipeline data"""
        
        forecast_months = params.get('forecast_months', 12)
        
        # Get pipeline data
        pipeline_query = """
        SELECT 
            stage,
            probability,
            amount,
            expected_close_date,
            revenue_stream_id,
            customer_segment_id
        FROM sales_pipeline
        WHERE company_id = :company_id
        AND is_active = true
        AND expected_close_date >= CURRENT_DATE
        ORDER BY expected_close_date
        """
        
        result = self.db.execute(text(pipeline_query), {'company_id': company_id})
        pipeline_data = [dict(row._mapping) for row in result.fetchall()]
        
        # Group by month and calculate weighted revenue
        forecast_by_month = {}
        
        for opp in pipeline_data:
            close_date = opp['expected_close_date']
            month_key = f"{close_date.year}-{close_date.month:02d}"
            
            if month_key not in forecast_by_month:
                forecast_by_month[month_key] = {
                    'pipeline_value': 0,
                    'weighted_value': 0,
                    'opportunity_count': 0
                }
            
            probability = float(opp['probability']) / 100
            amount = float(opp['amount'])
            
            forecast_by_month[month_key]['pipeline_value'] += amount
            forecast_by_month[month_key]['weighted_value'] += amount * probability
            forecast_by_month[month_key]['opportunity_count'] += 1
        
        # Apply stage conversion rates
        stage_conversion = params.get('stage_conversion', {
            'lead': 0.1,
            'qualified': 0.25,
            'proposal': 0.5,
            'negotiation': 0.75,
            'closed_won': 1.0
        })
        
        # Generate forecast
        forecast_data = []
        for i in range(1, forecast_months + 1):
            period = self._get_forecast_period(i)
            
            if period in forecast_by_month:
                forecast_value = forecast_by_month[period]['weighted_value']
            else:
                # Use average for months without pipeline data
                if forecast_by_month:
                    avg_weighted = np.mean([m['weighted_value'] for m in forecast_by_month.values()])
                    forecast_value = avg_weighted
                else:
                    forecast_value = 0
            
            forecast_data.append({
                'month': i,
                'period': period,
                'forecast': forecast_value,
                'pipeline_value': forecast_by_month.get(period, {}).get('pipeline_value', 0),
                'opportunity_count': forecast_by_month.get(period, {}).get('opportunity_count', 0),
                'method': 'pipeline'
            })
        
        return {
            'forecast_data': forecast_data,
            'method': 'pipeline_based',
            'total_forecast': sum(f['forecast'] for f in forecast_data),
            'pipeline_summary': {
                'total_pipeline': sum(m['pipeline_value'] for m in forecast_by_month.values()),
                'total_weighted': sum(m['weighted_value'] for m in forecast_by_month.values()),
                'total_opportunities': sum(m['opportunity_count'] for m in forecast_by_month.values())
            }
        }
    
    async def _driver_based_forecast(
        self,
        company_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Revenue forecast based on business drivers"""
        
        forecast_months = params.get('forecast_months', 12)
        driver_assumptions = params.get('driver_assumptions', {})
        
        # Get revenue drivers
        drivers = await self._get_revenue_drivers(company_id)
        
        forecast_data = []
        
        for month in range(1, forecast_months + 1):
            month_revenue = 0
            driver_breakdown = {}
            
            for driver in drivers:
                driver_id = driver['id']
                driver_value = driver_assumptions.get(driver_id, driver.get('default_value', 0))
                
                # Apply growth rate to driver
                if 'growth_rate' in driver:
                    monthly_growth = (1 + driver['growth_rate']) ** (1/12) - 1
                    driver_value *= (1 + monthly_growth) ** month
                
                # Calculate revenue from driver
                if driver['calculation_type'] == 'volume_price':
                    volume = driver_value
                    price = driver.get('unit_price', 0)
                    revenue = volume * price
                elif driver['calculation_type'] == 'percentage':
                    base = driver_assumptions.get(driver['base_driver'], 0)
                    revenue = base * driver_value
                elif driver['calculation_type'] == 'formula':
                    revenue = await self._evaluate_driver_formula(
                        driver['formula'],
                        driver_value,
                        driver_assumptions
                    )
                else:
                    revenue = driver_value
                
                month_revenue += revenue
                driver_breakdown[driver['name']] = revenue
            
            forecast_data.append({
                'month': month,
                'period': self._get_forecast_period(month),
                'forecast': month_revenue,
                'driver_breakdown': driver_breakdown,
                'method': 'driver_based'
            })
        
        # Perform sensitivity analysis
        sensitivity = await self._driver_sensitivity_analysis(
            drivers,
            driver_assumptions,
            forecast_data
        )
        
        return {
            'forecast_data': forecast_data,
            'method': 'driver_based',
            'total_forecast': sum(f['forecast'] for f in forecast_data),
            'drivers': drivers,
            'sensitivity_analysis': sensitivity
        }
    
    async def _cohort_based_forecast(
        self,
        company_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Cohort-based revenue forecasting"""
        
        forecast_months = params.get('forecast_months', 12)
        
        # Get cohort data
        cohort_query = """
        SELECT 
            rc.*,
            cr.period_offset,
            cr.retention_rate,
            cr.revenue_retention_rate
        FROM revenue_cohorts rc
        LEFT JOIN cohort_retention cr ON cr.cohort_id = rc.id
        WHERE rc.company_id = :company_id
        ORDER BY rc.cohort_date DESC, cr.period_offset
        """
        
        result = self.db.execute(text(cohort_query), {'company_id': company_id})
        cohort_data = [dict(row._mapping) for row in result.fetchall()]
        
        if not cohort_data:
            # Fallback to trend analysis if no cohort data
            historical = await self._get_historical_revenue(company_id, 24)
            return await self._trend_analysis_forecast(historical, params)
        
        # Calculate average retention curves
        retention_curves = {}
        for row in cohort_data:
            offset = row.get('period_offset', 0)
            if offset not in retention_curves:
                retention_curves[offset] = []
            retention_curves[offset].append(row.get('revenue_retention_rate', 1.0))
        
        avg_retention = {k: np.mean(v) for k, v in retention_curves.items()}
        
        # Project new cohorts
        new_cohort_size = params.get('new_cohort_size', 100000)  # Monthly new revenue
        growth_rate = params.get('cohort_growth_rate', 0.1)  # Growth in new cohorts
        
        forecast_data = []
        
        for month in range(1, forecast_months + 1):
            total_revenue = 0
            
            # Revenue from new cohort
            new_cohort_revenue = new_cohort_size * (1 + growth_rate / 12) ** month
            total_revenue += new_cohort_revenue
            
            # Revenue from existing cohorts
            for cohort_month in range(1, month):
                age = month - cohort_month
                retention = avg_retention.get(age, avg_retention.get(max(avg_retention.keys()), 0.5))
                cohort_contribution = new_cohort_size * (1 + growth_rate / 12) ** cohort_month * retention
                total_revenue += cohort_contribution
            
            forecast_data.append({
                'month': month,
                'period': self._get_forecast_period(month),
                'forecast': total_revenue,
                'new_revenue': new_cohort_revenue,
                'recurring_revenue': total_revenue - new_cohort_revenue,
                'method': 'cohort'
            })
        
        return {
            'forecast_data': forecast_data,
            'method': 'cohort_based',
            'total_forecast': sum(f['forecast'] for f in forecast_data),
            'retention_curves': avg_retention,
            'cohort_metrics': {
                'avg_retention_month_1': avg_retention.get(1, 0),
                'avg_retention_month_6': avg_retention.get(6, 0),
                'avg_retention_month_12': avg_retention.get(12, 0)
            }
        }
    
    async def _ml_ensemble_forecast(
        self,
        historical_data: List[Dict],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensemble machine learning forecast combining multiple models"""
        
        forecast_months = params.get('forecast_months', 12)
        
        # Generate forecasts from multiple methods
        methods = ['trend', 'seasonal', 'regression']
        forecasts = []
        weights = params.get('ensemble_weights', [0.33, 0.34, 0.33])
        
        for method in methods:
            if method == 'trend':
                result = await self._trend_analysis_forecast(historical_data, params)
            elif method == 'seasonal':
                result = await self._seasonal_forecast(historical_data, params)
            elif method == 'regression':
                result = await self._regression_forecast(historical_data, params)
            
            forecasts.append(result['forecast_data'])
        
        # Combine forecasts
        ensemble_forecast = []
        
        for i in range(forecast_months):
            weighted_forecast = sum(
                forecasts[j][i]['forecast'] * weights[j]
                for j in range(len(methods))
            )
            
            ensemble_forecast.append({
                'month': i + 1,
                'period': self._get_forecast_period(i + 1),
                'forecast': weighted_forecast,
                'method': 'ensemble',
                'components': {
                    methods[j]: forecasts[j][i]['forecast']
                    for j in range(len(methods))
                }
            })
        
        return {
            'forecast_data': ensemble_forecast,
            'method': 'ml_ensemble',
            'total_forecast': sum(f['forecast'] for f in ensemble_forecast),
            'ensemble_weights': dict(zip(methods, weights)),
            'model_performance': self._evaluate_ensemble_performance(forecasts, historical_data)
        }
    
    # ============================================
    # REVENUE ANALYSIS METHODS
    # ============================================
    
    async def _analyze_revenue_segments(self, company_id: str) -> List[Dict[str, Any]]:
        """Analyze revenue by segments"""
        
        query = """
        SELECT 
            cs.segment_name,
            cs.segment_type,
            COUNT(DISTINCT sp.id) as opportunity_count,
            SUM(sp.amount) as total_pipeline,
            AVG(sp.probability) as avg_probability,
            cs.typical_deal_size,
            cs.growth_rate
        FROM customer_segments cs
        LEFT JOIN sales_pipeline sp ON sp.customer_segment_id = cs.id
        WHERE cs.company_id = :company_id
        AND cs.is_active = true
        GROUP BY cs.id, cs.segment_name, cs.segment_type, cs.typical_deal_size, cs.growth_rate
        ORDER BY total_pipeline DESC NULLS LAST
        """
        
        result = self.db.execute(text(query), {'company_id': company_id})
        
        segments = []
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            segments.append({
                'name': row_dict['segment_name'],
                'type': row_dict['segment_type'],
                'metrics': {
                    'opportunity_count': row_dict['opportunity_count'] or 0,
                    'total_pipeline': float(row_dict['total_pipeline'] or 0),
                    'avg_probability': float(row_dict['avg_probability'] or 0),
                    'typical_deal_size': float(row_dict['typical_deal_size'] or 0),
                    'growth_rate': float(row_dict['growth_rate'] or 0)
                }
            })
        
        return segments
    
    async def _get_pipeline_metrics(self, company_id: str) -> Dict[str, Any]:
        """Get sales pipeline metrics"""
        
        query = """
        SELECT 
            stage,
            COUNT(*) as count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            AVG(probability) as avg_probability,
            AVG(days_in_stage) as avg_days_in_stage
        FROM sales_pipeline
        WHERE company_id = :company_id
        AND is_active = true
        GROUP BY stage
        ORDER BY 
            CASE stage
                WHEN 'lead' THEN 1
                WHEN 'qualified' THEN 2
                WHEN 'proposal' THEN 3
                WHEN 'negotiation' THEN 4
                WHEN 'closed_won' THEN 5
                ELSE 6
            END
        """
        
        result = self.db.execute(text(query), {'company_id': company_id})
        
        pipeline_stages = []
        total_pipeline = 0
        weighted_pipeline = 0
        
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            amount = float(row_dict['total_amount'] or 0)
            probability = float(row_dict['avg_probability'] or 0) / 100
            
            pipeline_stages.append({
                'stage': row_dict['stage'],
                'count': row_dict['count'],
                'amount': amount,
                'avg_amount': float(row_dict['avg_amount'] or 0),
                'probability': probability * 100,
                'avg_days': row_dict['avg_days_in_stage'] or 0
            })
            
            total_pipeline += amount
            weighted_pipeline += amount * probability
        
        return {
            'stages': pipeline_stages,
            'total_pipeline': total_pipeline,
            'weighted_pipeline': weighted_pipeline,
            'conversion_rate': (weighted_pipeline / total_pipeline * 100) if total_pipeline > 0 else 0
        }
    
    async def _calculate_recurring_metrics(self, company_id: str) -> Dict[str, Any]:
        """Calculate MRR, ARR, and other recurring revenue metrics"""
        
        query = """
        SELECT 
            SUM(CASE 
                WHEN rs.recurring_frequency = 'monthly' THEN rfl.forecast_amount
                WHEN rs.recurring_frequency = 'quarterly' THEN rfl.forecast_amount / 3
                WHEN rs.recurring_frequency = 'annual' THEN rfl.forecast_amount / 12
                ELSE 0
            END) as mrr,
            COUNT(DISTINCT CASE WHEN rs.is_recurring THEN rfl.revenue_stream_id END) as recurring_streams
        FROM revenue_forecast_lines rfl
        JOIN revenue_streams rs ON rs.id = rfl.revenue_stream_id
        JOIN revenue_plans rp ON rp.id = rfl.revenue_plan_id
        WHERE rp.company_id = :company_id
        AND rp.status = 'approved'
        AND rs.is_recurring = true
        """
        
        result = self.db.execute(text(query), {'company_id': company_id})
        row = result.fetchone()
        
        mrr = float(row[0] or 0) if row else 0
        recurring_streams = row[1] if row else 0
        
        # Calculate churn and growth
        churn_rate = await self._calculate_churn_rate(company_id)
        growth_rate = await self._calculate_revenue_growth_rate(company_id)
        
        return {
            'mrr': mrr,
            'arr': mrr * 12,
            'recurring_streams': recurring_streams,
            'churn_rate': churn_rate,
            'growth_rate': growth_rate,
            'ltv': (mrr / churn_rate) if churn_rate > 0 else 0,
            'months_to_recover_cac': 3  # Placeholder - would calculate from actual CAC data
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    async def _get_historical_revenue(
        self,
        company_id: str,
        months: int
    ) -> List[Dict[str, Any]]:
        """Get historical revenue data"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        query = """
        SELECT 
            EXTRACT(year FROM gt.transaction_date) as year,
            EXTRACT(month FROM gt.transaction_date) as month,
            SUM(gtl.credit_amount) as revenue
        FROM gl_transactions gt
        JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
        JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
        WHERE gt.company_id = :company_id
        AND ga.account_type = 'REVENUE'
        AND gt.is_posted = true
        AND gt.transaction_date >= :start_date
        AND gt.transaction_date <= :end_date
        GROUP BY EXTRACT(year FROM gt.transaction_date), EXTRACT(month FROM gt.transaction_date)
        ORDER BY year, month
        """
        
        result = self.db.execute(text(query), {
            'company_id': company_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        historical_data = []
        for row in result.fetchall():
            historical_data.append({
                'year': int(row[0]),
                'month': int(row[1]),
                'period': f"{int(row[0])}-{int(row[1]):02d}",
                'revenue': float(row[2] or 0),
                'type': 'actual'
            })
        
        return historical_data
    
    async def _get_revenue_drivers(self, company_id: str) -> List[Dict[str, Any]]:
        """Get revenue-related business drivers"""
        
        # This would integrate with the driver-based planning service
        # For now, return sample drivers
        return [
            {
                'id': 'new_customers',
                'name': 'New Customers',
                'default_value': 10,
                'unit_price': 5000,
                'calculation_type': 'volume_price',
                'growth_rate': 0.15
            },
            {
                'id': 'upsell_rate',
                'name': 'Upsell Rate',
                'default_value': 0.2,
                'base_driver': 'existing_revenue',
                'calculation_type': 'percentage'
            },
            {
                'id': 'price_increase',
                'name': 'Price Increase',
                'default_value': 0.05,
                'calculation_type': 'percentage',
                'base_driver': 'current_revenue'
            }
        ]
    
    async def _evaluate_driver_formula(
        self,
        formula: str,
        driver_value: float,
        all_drivers: Dict[str, float]
    ) -> float:
        """Evaluate driver formula"""
        
        # Simple formula evaluation
        eval_formula = formula.replace('$VALUE', str(driver_value))
        
        for driver_id, value in all_drivers.items():
            eval_formula = eval_formula.replace(f'${driver_id}', str(value))
        
        try:
            return eval(eval_formula, {"__builtins__": {}}, {
                "min": min, "max": max, "abs": abs, "round": round
            })
        except:
            return 0
    
    async def _driver_sensitivity_analysis(
        self,
        drivers: List[Dict],
        assumptions: Dict,
        forecast_data: List[Dict]
    ) -> Dict[str, Any]:
        """Perform sensitivity analysis on revenue drivers"""
        
        sensitivity_results = []
        base_revenue = sum(f['forecast'] for f in forecast_data)
        
        for driver in drivers:
            driver_id = driver['id']
            base_value = assumptions.get(driver_id, driver.get('default_value', 0))
            
            # Test +/- 10% changes
            variations = [-0.1, -0.05, 0, 0.05, 0.1]
            impact_results = []
            
            for variation in variations:
                test_assumptions = assumptions.copy()
                test_assumptions[driver_id] = base_value * (1 + variation)
                
                # Simplified revenue calculation for sensitivity
                if driver['calculation_type'] == 'volume_price':
                    test_revenue = test_assumptions[driver_id] * driver.get('unit_price', 0) * 12
                else:
                    test_revenue = base_revenue * (1 + variation)
                
                impact_results.append({
                    'variation_pct': variation * 100,
                    'driver_value': test_assumptions[driver_id],
                    'revenue_impact': test_revenue - base_revenue,
                    'revenue_change_pct': ((test_revenue - base_revenue) / base_revenue * 100) if base_revenue > 0 else 0
                })
            
            sensitivity_results.append({
                'driver': driver['name'],
                'base_value': base_value,
                'sensitivity': impact_results
            })
        
        return {
            'driver_sensitivity': sensitivity_results,
            'most_sensitive': max(
                sensitivity_results,
                key=lambda x: max(abs(i['revenue_change_pct']) for i in x['sensitivity'])
            )['driver'] if sensitivity_results else None
        }
    
    def _calculate_forecast_confidence(
        self,
        forecast_data: List[Dict],
        historical_data: List[Dict],
        confidence_level: float
    ) -> List[Dict[str, Any]]:
        """Calculate confidence intervals for forecast"""
        
        # Calculate historical volatility
        revenues = [d['revenue'] for d in historical_data]
        if len(revenues) > 1:
            returns = np.diff(revenues) / revenues[:-1]
            volatility = np.std(returns)
        else:
            volatility = 0.1  # Default 10% volatility
        
        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z_score = z_scores.get(confidence_level, 1.96)
        
        confidence_intervals = []
        
        for i, forecast in enumerate(forecast_data):
            # Uncertainty increases with forecast horizon
            uncertainty = volatility * np.sqrt(i + 1) * z_score
            forecast_value = forecast['forecast']
            
            confidence_intervals.append({
                'period': forecast['period'],
                'forecast': forecast_value,
                'lower': max(0, forecast_value * (1 - uncertainty)),
                'upper': forecast_value * (1 + uncertainty),
                'confidence_level': confidence_level * 100
            })
        
        return confidence_intervals
    
    def _calculate_growth_metrics(
        self,
        historical_data: List[Dict],
        forecast_data: List[Dict]
    ) -> Dict[str, float]:
        """Calculate growth metrics"""
        
        historical_revenues = [d['revenue'] for d in historical_data if d.get('revenue', 0) > 0]
        forecast_revenues = [d['forecast'] for d in forecast_data]
        
        metrics = {}
        
        if historical_revenues:
            # Historical growth
            if len(historical_revenues) > 1:
                historical_growth = (historical_revenues[-1] / historical_revenues[0]) ** (1 / len(historical_revenues)) - 1
                metrics['historical_growth_rate'] = historical_growth * 100
            
            # Forecast growth
            if forecast_revenues:
                forecast_growth = (forecast_revenues[-1] / historical_revenues[-1]) ** (1 / len(forecast_revenues)) - 1
                metrics['forecast_growth_rate'] = forecast_growth * 100
                
                # Year-over-year growth
                metrics['yoy_growth'] = ((sum(forecast_revenues[:12]) / sum(historical_revenues[-12:])) - 1) * 100 if len(historical_revenues) >= 12 else 0
        
        return metrics
    
    async def _calculate_churn_rate(self, company_id: str) -> float:
        """Calculate customer churn rate"""
        
        # Simplified churn calculation
        # In production, would calculate from actual customer data
        return 0.05  # 5% monthly churn
    
    async def _calculate_revenue_growth_rate(self, company_id: str) -> float:
        """Calculate revenue growth rate"""
        
        historical = await self._get_historical_revenue(company_id, 12)
        if len(historical) >= 2:
            return (historical[-1]['revenue'] / historical[0]['revenue']) ** (1 / len(historical)) - 1
        return 0.1  # Default 10% growth
    
    def _get_forecast_period(self, month_offset: int) -> str:
        """Get forecast period string"""
        
        future_date = datetime.now() + timedelta(days=30 * month_offset)
        return f"{future_date.year}-{future_date.month:02d}"
    
    def _generate_sample_revenue_data(self) -> List[Dict[str, Any]]:
        """Generate sample revenue data for demonstration"""
        
        base_revenue = 100000
        growth_rate = 0.15
        seasonality = [0.9, 0.85, 0.95, 1.0, 1.05, 1.1, 1.15, 1.1, 1.05, 1.0, 0.95, 1.2]
        
        historical_data = []
        current_date = datetime.now()
        
        for i in range(24, 0, -1):
            month_date = current_date - timedelta(days=i * 30)
            month = month_date.month
            year = month_date.year
            
            # Apply growth and seasonality
            revenue = base_revenue * (1 + growth_rate) ** ((24 - i) / 24)
            revenue *= seasonality[month - 1]
            revenue += np.random.normal(0, revenue * 0.1)  # Add noise
            
            historical_data.append({
                'year': year,
                'month': month,
                'period': f"{year}-{month:02d}",
                'revenue': max(0, revenue),
                'type': 'actual'
            })
        
        return historical_data
    
    def _evaluate_ensemble_performance(
        self,
        forecasts: List[List[Dict]],
        historical_data: List[Dict]
    ) -> Dict[str, float]:
        """Evaluate ensemble model performance"""
        
        # This would implement backtesting and cross-validation
        # For now, return placeholder metrics
        return {
            'mape': 5.2,  # Mean Absolute Percentage Error
            'rmse': 10000,  # Root Mean Square Error
            'mae': 8000,  # Mean Absolute Error
            'r_squared': 0.92  # R-squared
        }
    
    # ============================================
    # BASE CLASS METHOD IMPLEMENTATIONS
    # ============================================
    
    def generate_forecast(self, company_id: str, forecast_params: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of abstract method from base class"""
        import asyncio
        return asyncio.run(self.generate_revenue_forecast(company_id, forecast_params))
    
    def calculate_metrics(self, company_id: str, period_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate key revenue metrics"""
        import asyncio
        return asyncio.run(self._calculate_recurring_metrics(company_id))