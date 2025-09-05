from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
from decimal import Decimal
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import json

class DriverBasedPlanningService:
    """
    Service for driver-based planning and scenario modeling
    Allows FP&A analysts to model business outcomes based on key drivers
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def create_business_driver(
        self,
        company_id: str,
        code: str,
        name: str,
        unit_of_measure: str,
        category: str,
        is_external: bool = False
    ) -> str:
        """Create a new business driver"""
        
        import uuid
        driver_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO business_drivers (
            id, company_id, code, name, unit_of_measure,
            category, is_external, is_active, created_at
        ) VALUES (
            :id, :company_id, :code, :name, :unit_of_measure,
            :category, :is_external, true, :created_at
        ) RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'id': driver_id,
            'company_id': company_id,
            'code': code,
            'name': name,
            'unit_of_measure': unit_of_measure,
            'category': category,
            'is_external': is_external,
            'created_at': datetime.utcnow()
        })
        
        self.db.commit()
        return result.fetchone()[0]
    
    async def create_driver_relationship(
        self,
        driver_id: str,
        gl_account_id: str,
        relationship_type: str,
        coefficient: float = 1.0,
        formula: Optional[str] = None,
        cost_center_id: Optional[str] = None
    ) -> str:
        """Create relationship between driver and GL account"""
        
        import uuid
        relationship_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO driver_relationships (
            id, business_driver_id, gl_account_id, cost_center_id,
            relationship_type, coefficient, formula, is_active, created_at
        ) VALUES (
            :id, :driver_id, :gl_account_id, :cost_center_id,
            :relationship_type, :coefficient, :formula, true, :created_at
        ) RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'id': relationship_id,
            'driver_id': driver_id,
            'gl_account_id': gl_account_id,
            'cost_center_id': cost_center_id,
            'relationship_type': relationship_type,
            'coefficient': coefficient,
            'formula': formula,
            'created_at': datetime.utcnow()
        })
        
        self.db.commit()
        return result.fetchone()[0]
    
    async def calculate_driver_based_forecast(
        self,
        company_id: str,
        scenario_id: str,
        fiscal_periods: List[str],
        driver_assumptions: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Calculate forecast based on driver assumptions
        
        driver_assumptions format:
        {
            'driver_id': {
                'period_id': value
            }
        }
        """
        
        results = []
        
        for period_id in fiscal_periods:
            period_results = await self._calculate_period_forecast(
                company_id,
                scenario_id,
                period_id,
                driver_assumptions
            )
            results.append(period_results)
        
        # Aggregate results
        total_revenue = sum(r.get('total_revenue', 0) for r in results)
        total_expenses = sum(r.get('total_expenses', 0) for r in results)
        total_ebitda = sum(r.get('ebitda', 0) for r in results)
        
        return {
            'scenario_id': scenario_id,
            'periods': results,
            'summary': {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'ebitda': total_ebitda,
                'ebitda_margin': (total_ebitda / total_revenue * 100) if total_revenue else 0
            }
        }
    
    async def _calculate_period_forecast(
        self,
        company_id: str,
        scenario_id: str,
        period_id: str,
        driver_assumptions: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Calculate forecast for a single period"""
        
        # Get all driver relationships
        query = """
        SELECT 
            dr.*,
            bd.code as driver_code,
            bd.name as driver_name,
            bd.category as driver_category,
            ga.account_number,
            ga.name as account_name,
            ga.account_type
        FROM driver_relationships dr
        JOIN business_drivers bd ON bd.id = dr.business_driver_id
        JOIN gl_accounts ga ON ga.id = dr.gl_account_id
        WHERE bd.company_id = :company_id
        AND dr.is_active = true
        AND bd.is_active = true
        """
        
        result = self.db.execute(text(query), {'company_id': company_id})
        relationships = [dict(row._mapping) for row in result.fetchall()]
        
        # Calculate GL account values based on drivers
        account_values = {}
        
        for rel in relationships:
            driver_id = str(rel['business_driver_id'])
            account_id = str(rel['gl_account_id'])
            
            # Get driver value for this period
            driver_value = driver_assumptions.get(driver_id, {}).get(period_id, 0)
            
            if driver_value:
                # Calculate account value based on relationship type
                if rel['relationship_type'] == 'linear':
                    account_value = driver_value * float(rel['coefficient'])
                elif rel['relationship_type'] == 'percentage':
                    base_value = account_values.get(account_id, 0)
                    account_value = base_value * (float(rel['coefficient']) / 100)
                elif rel['relationship_type'] == 'step_function':
                    account_value = await self._calculate_step_function(
                        driver_value, rel['formula']
                    )
                elif rel['relationship_type'] == 'custom_formula':
                    account_value = await self._evaluate_formula(
                        rel['formula'], driver_value, driver_assumptions, period_id
                    )
                else:
                    account_value = driver_value
                
                # Aggregate by account
                if account_id not in account_values:
                    account_values[account_id] = 0
                account_values[account_id] += account_value
        
        # Store calculated values as budget lines
        for account_id, amount in account_values.items():
            await self._create_budget_line(
                scenario_id, account_id, period_id, amount
            )
        
        # Calculate summary metrics
        revenue = sum(v for k, v in account_values.items() 
                     if self._is_revenue_account(k))
        expenses = sum(v for k, v in account_values.items() 
                      if self._is_expense_account(k))
        ebitda = revenue - expenses
        
        return {
            'period_id': period_id,
            'account_values': account_values,
            'total_revenue': revenue,
            'total_expenses': expenses,
            'ebitda': ebitda,
            'ebitda_margin': (ebitda / revenue * 100) if revenue else 0
        }
    
    async def perform_sensitivity_analysis(
        self,
        company_id: str,
        base_scenario_id: str,
        driver_id: str,
        variation_range: Tuple[float, float],
        steps: int = 10
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on a driver
        Shows how changes in driver affect key metrics
        """
        
        # Get base driver values
        base_values = await self._get_driver_values(base_scenario_id)
        
        # Generate variation scenarios
        min_pct, max_pct = variation_range
        variations = np.linspace(min_pct, max_pct, steps)
        
        results = []
        
        for variation in variations:
            # Adjust driver value
            adjusted_values = base_values.copy()
            for period in adjusted_values.get(driver_id, {}):
                original = adjusted_values[driver_id][period]
                adjusted_values[driver_id][period] = original * (1 + variation / 100)
            
            # Calculate forecast with adjusted driver
            forecast = await self.calculate_driver_based_forecast(
                company_id,
                base_scenario_id,
                list(base_values[driver_id].keys()),
                adjusted_values
            )
            
            results.append({
                'variation_pct': variation,
                'revenue': forecast['summary']['total_revenue'],
                'expenses': forecast['summary']['total_expenses'],
                'ebitda': forecast['summary']['ebitda'],
                'ebitda_margin': forecast['summary']['ebitda_margin']
            })
        
        return {
            'driver_id': driver_id,
            'base_scenario_id': base_scenario_id,
            'sensitivity_results': results,
            'impact_summary': self._calculate_impact_summary(results)
        }
    
    async def optimize_drivers_for_target(
        self,
        company_id: str,
        scenario_id: str,
        target_metric: str,
        target_value: float,
        controllable_drivers: List[str],
        constraints: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Any]:
        """
        Optimize driver values to achieve target metric
        Uses linear programming to find optimal driver combination
        """
        
        from scipy.optimize import minimize
        
        # Define objective function
        def objective(driver_values):
            # Convert array to driver dict
            driver_dict = {}
            for i, driver_id in enumerate(controllable_drivers):
                driver_dict[driver_id] = driver_values[i]
            
            # Calculate forecast (simplified for optimization)
            forecast = self._quick_forecast(company_id, driver_dict)
            
            # Return distance from target
            if target_metric == 'revenue':
                return abs(forecast['revenue'] - target_value)
            elif target_metric == 'ebitda':
                return abs(forecast['ebitda'] - target_value)
            elif target_metric == 'ebitda_margin':
                return abs(forecast['ebitda_margin'] - target_value)
            else:
                return float('inf')
        
        # Set up constraints
        bounds = []
        for driver_id in controllable_drivers:
            if driver_id in constraints:
                bounds.append(constraints[driver_id])
            else:
                bounds.append((0, None))  # Default: non-negative
        
        # Initial guess (midpoint of constraints)
        x0 = []
        for driver_id in controllable_drivers:
            if driver_id in constraints:
                min_val, max_val = constraints[driver_id]
                x0.append((min_val + max_val) / 2)
            else:
                x0.append(100)  # Default starting value
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='L-BFGS-B',
            bounds=bounds
        )
        
        # Format results
        optimal_drivers = {}
        for i, driver_id in enumerate(controllable_drivers):
            optimal_drivers[driver_id] = result.x[i]
        
        # Calculate final forecast with optimal drivers
        final_forecast = await self.calculate_driver_based_forecast(
            company_id,
            scenario_id,
            ['current_period'],  # Simplified
            optimal_drivers
        )
        
        return {
            'target_metric': target_metric,
            'target_value': target_value,
            'optimal_drivers': optimal_drivers,
            'achieved_metrics': final_forecast['summary'],
            'optimization_success': result.success,
            'iterations': result.nit
        }
    
    async def analyze_driver_correlations(
        self,
        company_id: str,
        lookback_periods: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze historical correlations between drivers and financial outcomes
        Helps identify which drivers have strongest predictive power
        """
        
        # Get historical driver values
        driver_query = """
        SELECT 
            dv.business_driver_id,
            dv.fiscal_period_id,
            dv.actual_value,
            bd.name as driver_name,
            fp.fiscal_year,
            fp.period_number
        FROM driver_values dv
        JOIN business_drivers bd ON bd.id = dv.business_driver_id
        JOIN fiscal_periods fp ON fp.id = dv.fiscal_period_id
        WHERE bd.company_id = :company_id
        AND dv.actual_value IS NOT NULL
        ORDER BY fp.fiscal_year DESC, fp.period_number DESC
        LIMIT :limit
        """
        
        driver_result = self.db.execute(text(driver_query), {
            'company_id': company_id,
            'limit': lookback_periods * 10  # Get more data
        })
        
        driver_data = pd.DataFrame([dict(row._mapping) for row in driver_result.fetchall()])
        
        if driver_data.empty:
            return {'error': 'No historical driver data available'}
        
        # Get historical financial outcomes
        financial_query = """
        SELECT 
            fp.id as fiscal_period_id,
            fp.fiscal_year,
            fp.period_number,
            SUM(CASE 
                WHEN ga.account_type = 'revenue' THEN gtl.credit_amount - gtl.debit_amount
                ELSE 0
            END) as revenue,
            SUM(CASE 
                WHEN ga.account_type = 'expense' THEN gtl.debit_amount - gtl.credit_amount
                ELSE 0
            END) as expenses
        FROM fiscal_periods fp
        JOIN gl_transactions gt ON gt.fiscal_period_id = fp.id
        JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
        JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
        WHERE fp.company_id = :company_id
        AND gt.is_posted = true
        GROUP BY fp.id, fp.fiscal_year, fp.period_number
        ORDER BY fp.fiscal_year DESC, fp.period_number DESC
        LIMIT :limit
        """
        
        financial_result = self.db.execute(text(financial_query), {
            'company_id': company_id,
            'limit': lookback_periods
        })
        
        financial_data = pd.DataFrame([dict(row._mapping) for row in financial_result.fetchall()])
        
        if financial_data.empty:
            return {'error': 'No historical financial data available'}
        
        # Calculate EBITDA
        financial_data['ebitda'] = financial_data['revenue'] - financial_data['expenses']
        
        # Merge driver and financial data
        merged_data = pd.merge(
            driver_data,
            financial_data,
            on='fiscal_period_id',
            suffixes=('_driver', '_financial')
        )
        
        # Calculate correlations
        correlations = []
        
        for driver_id in merged_data['business_driver_id'].unique():
            driver_subset = merged_data[merged_data['business_driver_id'] == driver_id]
            
            if len(driver_subset) < 3:  # Need at least 3 data points
                continue
            
            # Calculate correlation with revenue
            revenue_corr = driver_subset['actual_value'].corr(driver_subset['revenue'])
            
            # Calculate correlation with EBITDA
            ebitda_corr = driver_subset['actual_value'].corr(driver_subset['ebitda'])
            
            # Perform regression to get coefficient
            X = driver_subset[['actual_value']].values
            y_revenue = driver_subset['revenue'].values
            
            model = LinearRegression()
            model.fit(X, y_revenue)
            
            correlations.append({
                'driver_id': str(driver_id),
                'driver_name': driver_subset['driver_name'].iloc[0],
                'revenue_correlation': revenue_corr,
                'ebitda_correlation': ebitda_corr,
                'revenue_coefficient': model.coef_[0],
                'r_squared': model.score(X, y_revenue),
                'data_points': len(driver_subset)
            })
        
        # Sort by strongest correlation
        correlations.sort(key=lambda x: abs(x['revenue_correlation']), reverse=True)
        
        return {
            'driver_correlations': correlations,
            'top_revenue_drivers': correlations[:5],
            'analysis_period': f"Last {lookback_periods} periods",
            'recommendations': self._generate_driver_recommendations(correlations)
        }
    
    async def create_waterfall_analysis(
        self,
        company_id: str,
        base_period_id: str,
        comparison_period_id: str,
        metric: str = 'ebitda'
    ) -> Dict[str, Any]:
        """
        Create waterfall analysis showing driver impact on metric changes
        """
        
        # Get driver values for both periods
        driver_query = """
        SELECT 
            dv.business_driver_id,
            dv.fiscal_period_id,
            dv.actual_value,
            bd.name as driver_name,
            bd.category
        FROM driver_values dv
        JOIN business_drivers bd ON bd.id = dv.business_driver_id
        WHERE bd.company_id = :company_id
        AND dv.fiscal_period_id IN (:base_period, :comp_period)
        """
        
        result = self.db.execute(text(driver_query), {
            'company_id': company_id,
            'base_period': base_period_id,
            'comp_period': comparison_period_id
        })
        
        driver_data = [dict(row._mapping) for row in result.fetchall()]
        
        # Calculate driver changes
        driver_changes = {}
        for row in driver_data:
            driver_id = str(row['business_driver_id'])
            if driver_id not in driver_changes:
                driver_changes[driver_id] = {
                    'name': row['driver_name'],
                    'category': row['category'],
                    'base_value': 0,
                    'comp_value': 0
                }
            
            if row['fiscal_period_id'] == base_period_id:
                driver_changes[driver_id]['base_value'] = row['actual_value']
            else:
                driver_changes[driver_id]['comp_value'] = row['actual_value']
        
        # Calculate impact of each driver change
        waterfall_components = []
        
        for driver_id, changes in driver_changes.items():
            change_value = changes['comp_value'] - changes['base_value']
            if change_value != 0:
                # Get driver relationships to calculate impact
                impact = await self._calculate_driver_impact(
                    driver_id, change_value, metric
                )
                
                waterfall_components.append({
                    'driver': changes['name'],
                    'category': changes['category'],
                    'base_value': changes['base_value'],
                    'new_value': changes['comp_value'],
                    'change': change_value,
                    'impact': impact,
                    'impact_pct': (impact / abs(impact)) * 100 if impact else 0
                })
        
        # Sort by impact magnitude
        waterfall_components.sort(key=lambda x: abs(x['impact']), reverse=True)
        
        return {
            'base_period': base_period_id,
            'comparison_period': comparison_period_id,
            'metric': metric,
            'waterfall_components': waterfall_components,
            'total_impact': sum(c['impact'] for c in waterfall_components)
        }
    
    def _calculate_impact_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary of sensitivity analysis impact"""
        
        if not results:
            return {}
        
        base_result = results[len(results) // 2]  # Assume middle is base
        
        return {
            'revenue_sensitivity': max(r['revenue'] for r in results) - min(r['revenue'] for r in results),
            'ebitda_sensitivity': max(r['ebitda'] for r in results) - min(r['ebitda'] for r in results),
            'max_ebitda_margin': max(r['ebitda_margin'] for r in results),
            'min_ebitda_margin': min(r['ebitda_margin'] for r in results),
            'breakeven_point': next((r['variation_pct'] for r in results if r['ebitda'] <= 0), None)
        }
    
    def _generate_driver_recommendations(self, correlations: List[Dict]) -> List[str]:
        """Generate recommendations based on driver analysis"""
        
        recommendations = []
        
        # Identify high-impact drivers
        high_impact = [d for d in correlations if abs(d['revenue_correlation']) > 0.7]
        if high_impact:
            recommendations.append(
                f"Focus on {', '.join(d['driver_name'] for d in high_impact[:3])} "
                f"as they show strong correlation with revenue"
            )
        
        # Identify weak drivers
        weak_drivers = [d for d in correlations if abs(d['revenue_correlation']) < 0.3]
        if weak_drivers:
            recommendations.append(
                f"Consider reviewing relationships for {weak_drivers[0]['driver_name']} "
                f"as it shows weak correlation with financial outcomes"
            )
        
        # Identify predictive drivers
        predictive = [d for d in correlations if d['r_squared'] > 0.8]
        if predictive:
            recommendations.append(
                f"{predictive[0]['driver_name']} shows high predictive power "
                f"(R² = {predictive[0]['r_squared']:.2f}) and should be closely monitored"
            )
        
        return recommendations
    
    async def _calculate_step_function(self, driver_value: float, formula: str) -> float:
        """Calculate value based on step function formula"""
        
        # Parse step function (simplified example)
        # Format: "0-100:1000;101-200:2000;201+:3000"
        steps = formula.split(';')
        
        for step in steps:
            range_part, value_part = step.split(':')
            
            if '-' in range_part:
                min_val, max_val = range_part.split('-')
                if max_val == '+':
                    if driver_value >= float(min_val):
                        return float(value_part)
                else:
                    if float(min_val) <= driver_value <= float(max_val):
                        return float(value_part)
        
        return 0
    
    async def _evaluate_formula(
        self,
        formula: str,
        driver_value: float,
        all_drivers: Dict[str, Dict[str, float]],
        period_id: str
    ) -> float:
        """Evaluate custom formula"""
        
        # Simple formula evaluation (would need more robust implementation)
        # Replace driver references with values
        eval_formula = formula
        
        # Replace current driver reference
        eval_formula = eval_formula.replace('$DRIVER', str(driver_value))
        
        # Replace other driver references
        for driver_id, values in all_drivers.items():
            if period_id in values:
                eval_formula = eval_formula.replace(f'${driver_id}', str(values[period_id]))
        
        try:
            # Safe evaluation with limited scope
            return eval(eval_formula, {"__builtins__": {}}, {
                "min": min, "max": max, "abs": abs, "round": round
            })
        except:
            return 0
    
    def _is_revenue_account(self, account_id: str) -> bool:
        """Check if account is revenue type"""
        query = "SELECT account_type FROM gl_accounts WHERE id = :account_id"
        result = self.db.execute(text(query), {'account_id': account_id})
        row = result.fetchone()
        return row and row[0] == 'revenue'
    
    def _is_expense_account(self, account_id: str) -> bool:
        """Check if account is expense type"""
        query = "SELECT account_type FROM gl_accounts WHERE id = :account_id"
        result = self.db.execute(text(query), {'account_id': account_id})
        row = result.fetchone()
        return row and row[0] == 'expense'