from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from datetime import datetime, date, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd
import uuid

from .planning_base import PlanningBaseService
from ..analytics.driver_based_planning import DriverBasedPlanningService

class ExpensePlanningService(PlanningBaseService):
    """
    Service for expense planning, budgeting, and forecasting
    Supports multiple budgeting methods and driver-based planning
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.driver_service = DriverBasedPlanningService(db)
    
    async def create_expense_plan(
        self,
        company_id: str,
        plan_name: str,
        plan_type: str,
        fiscal_year: int,
        scenario_id: Optional[str] = None
    ) -> str:
        """Create a new expense plan"""
        
        plan_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO expense_plans (
            id, company_id, scenario_id, plan_name, plan_type,
            fiscal_year, version, status, created_at
        ) VALUES (
            :id, :company_id, :scenario_id, :plan_name, :plan_type,
            :fiscal_year, 1, 'draft', :created_at
        ) RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'id': plan_id,
            'company_id': company_id,
            'scenario_id': scenario_id,
            'plan_name': plan_name,
            'plan_type': plan_type,
            'fiscal_year': fiscal_year,
            'created_at': datetime.utcnow()
        })
        
        self.db.commit()
        return plan_id
    
    async def generate_expense_forecast(
        self,
        company_id: str,
        forecast_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate expense forecast based on selected method"""
        
        method = forecast_params.get('method', 'incremental')
        forecast_months = forecast_params.get('forecast_months', 12)
        
        if method == 'zero_based':
            return await self._zero_based_forecast(company_id, forecast_params)
        elif method == 'incremental':
            return await self._incremental_forecast(company_id, forecast_params)
        elif method == 'driver_based':
            return await self._driver_based_forecast(company_id, forecast_params)
        elif method == 'activity_based':
            return await self._activity_based_forecast(company_id, forecast_params)
        else:
            # Default to incremental
            return await self._incremental_forecast(company_id, forecast_params)
    
    async def _incremental_forecast(
        self,
        company_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate incremental budget forecast"""
        
        # Get expense accounts
        expense_accounts = await self._get_expense_accounts(company_id)
        account_ids = [acc['id'] for acc in expense_accounts]
        
        # Get historical expenses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        historical_data = self.get_historical_actuals(
            company_id,
            account_ids,
            start_date.date(),
            end_date.date(),
            'month'
        )
        
        if historical_data.empty:
            # Generate sample data if no historicals
            historical_data = self._generate_sample_expense_data()
        
        # Calculate base expenses and growth
        base_expenses = historical_data.groupby('month')['amount'].mean()
        growth_rate = params.get('growth_rate', 0.03)  # Default 3% growth
        inflation_rate = params.get('inflation_rate', 0.02)  # Default 2% inflation
        
        # Generate forecast
        forecast_months = params.get('forecast_months', 12)
        forecast_data = []
        
        for month in range(1, forecast_months + 1):
            base_month = (month - 1) % 12 + 1
            base_amount = base_expenses.get(base_month, base_expenses.mean())
            
            # Apply growth and inflation
            forecast_amount = base_amount * (1 + growth_rate / 12) ** month
            forecast_amount *= (1 + inflation_rate / 12) ** month
            
            # Apply cost reduction targets if specified
            if 'cost_reduction_target' in params:
                reduction = params['cost_reduction_target']
                forecast_amount *= (1 - reduction)
            
            forecast_data.append({
                'month': month,
                'period': f"{datetime.now().year}-{month:02d}",
                'forecast_amount': forecast_amount,
                'type': 'forecast'
            })
        
        # Break down by category
        categories = await self._get_expense_categories(company_id)
        category_breakdown = await self._allocate_to_categories(
            forecast_data,
            categories,
            historical_data
        )
        
        return {
            'company_id': company_id,
            'method': 'incremental',
            'forecast_data': forecast_data,
            'category_breakdown': category_breakdown,
            'total_forecast': sum(f['forecast_amount'] for f in forecast_data),
            'assumptions': {
                'growth_rate': growth_rate,
                'inflation_rate': inflation_rate,
                'cost_reduction': params.get('cost_reduction_target', 0)
            }
        }
    
    async def _zero_based_forecast(
        self,
        company_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate zero-based budget forecast"""
        
        # Get cost centers and categories
        cost_centers = await self._get_cost_centers(company_id)
        categories = await self._get_expense_categories(company_id)
        
        # Build up expenses from zero
        forecast_data = []
        forecast_months = params.get('forecast_months', 12)
        
        # Personnel costs (usually largest expense)
        headcount_plan = params.get('headcount_plan', {})
        personnel_costs = await self._calculate_personnel_costs(
            company_id,
            headcount_plan,
            forecast_months
        )
        
        # Operating expenses by category
        operating_expenses = []
        for category in categories:
            if category['category_type'] != 'personnel':
                # Estimate based on business needs
                monthly_need = await self._estimate_category_need(
                    company_id,
                    category,
                    params
                )
                operating_expenses.append({
                    'category': category['category_name'],
                    'monthly_amount': monthly_need,
                    'annual_amount': monthly_need * 12
                })
        
        # Combine all expenses
        for month in range(1, forecast_months + 1):
            total_personnel = sum(p['monthly_cost'] for p in personnel_costs)
            total_operating = sum(o['monthly_amount'] for o in operating_expenses)
            
            forecast_data.append({
                'month': month,
                'period': f"{datetime.now().year}-{month:02d}",
                'personnel_cost': total_personnel,
                'operating_cost': total_operating,
                'total_cost': total_personnel + total_operating,
                'type': 'forecast'
            })
        
        return {
            'company_id': company_id,
            'method': 'zero_based',
            'forecast_data': forecast_data,
            'personnel_costs': personnel_costs,
            'operating_expenses': operating_expenses,
            'total_forecast': sum(f['total_cost'] for f in forecast_data),
            'cost_centers': cost_centers
        }
    
    async def _driver_based_forecast(
        self,
        company_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate driver-based expense forecast"""
        
        # Get business drivers
        drivers = await self._get_expense_drivers(company_id)
        
        # Get driver assumptions
        driver_assumptions = params.get('driver_assumptions') if params else {}
        if not driver_assumptions:
            driver_assumptions = {}
        
        # Calculate expenses based on drivers
        forecast_months = params.get('forecast_months', 12)
        forecast_data = []
        
        for month in range(1, forecast_months + 1):
            month_expenses = {}
            
            for driver in drivers:
                driver_id = driver['id']
                driver_value = driver_assumptions.get(driver_id, driver['default_value'])
                
                # Calculate expense based on driver relationship
                expense = await self._calculate_driver_expense(
                    driver,
                    driver_value,
                    month
                )
                
                month_expenses[driver['name']] = expense
            
            forecast_data.append({
                'month': month,
                'period': f"{datetime.now().year}-{month:02d}",
                'driver_expenses': month_expenses,
                'total_expense': sum(month_expenses.values()),
                'type': 'forecast'
            })
        
        # Perform sensitivity analysis
        sensitivity = await self._driver_sensitivity_analysis(
            drivers,
            driver_assumptions,
            forecast_data
        )
        
        return {
            'company_id': company_id,
            'method': 'driver_based',
            'forecast_data': forecast_data,
            'drivers': drivers,
            'driver_assumptions': driver_assumptions,
            'sensitivity_analysis': sensitivity,
            'total_forecast': sum(f['total_expense'] for f in forecast_data)
        }
    
    async def _activity_based_forecast(
        self,
        company_id: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate activity-based expense forecast"""
        
        # Define activities and cost pools
        activities = params.get('activities', [])
        if not activities:
            activities = await self._get_default_activities(company_id)
        
        forecast_months = params.get('forecast_months', 12)
        forecast_data = []
        
        for month in range(1, forecast_months + 1):
            month_costs = []
            
            for activity in activities:
                # Calculate cost based on activity volume and rate
                volume = activity.get('monthly_volume', 0)
                rate = activity.get('cost_per_unit', 0)
                
                # Apply complexity factors
                complexity = activity.get('complexity_factor', 1.0)
                cost = volume * rate * complexity
                
                month_costs.append({
                    'activity': activity['name'],
                    'volume': volume,
                    'rate': rate,
                    'cost': cost
                })
            
            forecast_data.append({
                'month': month,
                'period': f"{datetime.now().year}-{month:02d}",
                'activity_costs': month_costs,
                'total_cost': sum(c['cost'] for c in month_costs),
                'type': 'forecast'
            })
        
        return {
            'company_id': company_id,
            'method': 'activity_based',
            'forecast_data': forecast_data,
            'activities': activities,
            'total_forecast': sum(f['total_cost'] for f in forecast_data)
        }
    
    async def create_vendor_contract(
        self,
        company_id: str,
        vendor_id: str,
        contract_details: Dict[str, Any]
    ) -> str:
        """Create a vendor contract for expense planning"""
        
        contract_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO expense_contracts (
            id, company_id, vendor_id, contract_number, contract_name,
            contract_type, start_date, end_date, monthly_amount,
            annual_amount, escalation_rate, auto_renew, 
            gl_account_id, cost_center_id, created_at
        ) VALUES (
            :id, :company_id, :vendor_id, :contract_number, :contract_name,
            :contract_type, :start_date, :end_date, :monthly_amount,
            :annual_amount, :escalation_rate, :auto_renew,
            :gl_account_id, :cost_center_id, :created_at
        ) RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'id': contract_id,
            'company_id': company_id,
            'vendor_id': vendor_id,
            'contract_number': contract_details['contract_number'],
            'contract_name': contract_details['contract_name'],
            'contract_type': contract_details.get('contract_type', 'service'),
            'start_date': contract_details['start_date'],
            'end_date': contract_details.get('end_date'),
            'monthly_amount': contract_details.get('monthly_amount', 0),
            'annual_amount': contract_details.get('annual_amount', 0),
            'escalation_rate': contract_details.get('escalation_rate', 0),
            'auto_renew': contract_details.get('auto_renew', False),
            'gl_account_id': contract_details.get('gl_account_id'),
            'cost_center_id': contract_details.get('cost_center_id'),
            'created_at': datetime.utcnow()
        })
        
        self.db.commit()
        return contract_id
    
    async def get_contract_obligations(
        self,
        company_id: str,
        forecast_period: int = 12
    ) -> Dict[str, Any]:
        """Get contractual expense obligations"""
        
        query = """
        SELECT 
            ec.*,
            v.vendor_name,
            ga.name as account_name,
            cc.name as cost_center_name
        FROM expense_contracts ec
        LEFT JOIN vendors v ON v.id = ec.vendor_id
        LEFT JOIN gl_accounts ga ON ga.id = ec.gl_account_id
        LEFT JOIN cost_centers cc ON cc.id = ec.cost_center_id
        WHERE ec.company_id = :company_id
        AND ec.is_active = true
        AND (ec.end_date IS NULL OR ec.end_date >= CURRENT_DATE)
        """
        
        result = self.db.execute(text(query), {'company_id': company_id})
        contracts = [dict(row._mapping) for row in result.fetchall()]
        
        # Calculate obligations by period
        monthly_obligations = []
        total_obligation = 0
        
        for month in range(1, forecast_period + 1):
            month_total = 0
            month_date = datetime.now() + timedelta(days=30 * month)
            
            for contract in contracts:
                # Check if contract is active in this month
                start = contract['start_date']
                end = contract.get('end_date')
                
                if start <= month_date.date():
                    if not end or end >= month_date.date():
                        # Apply escalation
                        months_elapsed = month
                        escalation = contract.get('escalation_rate', 0) / 100
                        monthly_amount = contract['monthly_amount']
                        
                        if escalation > 0 and months_elapsed > 12:
                            years = months_elapsed // 12
                            monthly_amount *= (1 + escalation) ** years
                        
                        month_total += monthly_amount
            
            monthly_obligations.append({
                'month': month,
                'period': f"{month_date.year}-{month_date.month:02d}",
                'obligation': month_total
            })
            total_obligation += month_total
        
        return {
            'contracts': contracts,
            'monthly_obligations': monthly_obligations,
            'total_obligation': total_obligation,
            'contract_count': len(contracts)
        }
    
    async def analyze_expense_variance(
        self,
        company_id: str,
        period_id: str,
        expense_plan_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze expense variance vs plan"""
        
        # Get actual expenses
        query = """
        SELECT 
            ga.id as account_id,
            ga.name as account_name,
            ec.category_name,
            SUM(gtl.debit_amount - gtl.credit_amount) as actual_amount
        FROM gl_transactions gt
        JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
        JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
        LEFT JOIN expense_categories ec ON ec.id = ga.expense_category_id
        WHERE gt.company_id = :company_id
        AND gt.fiscal_period_id = :period_id
        AND gt.is_posted = true
        AND ga.account_type = 'EXPENSE'
        GROUP BY ga.id, ga.name, ec.category_name
        """
        
        actual_result = self.db.execute(text(query), {
            'company_id': company_id,
            'period_id': period_id
        })
        
        actuals = [dict(row._mapping) for row in actual_result.fetchall()]
        
        # Get planned expenses
        planned = []
        if expense_plan_id:
            plan_query = """
            SELECT 
                eli.gl_account_id as account_id,
                ga.name as account_name,
                ec.category_name,
                eli.planned_amount
            FROM expense_line_items eli
            JOIN gl_accounts ga ON ga.id = eli.gl_account_id
            LEFT JOIN expense_categories ec ON ec.id = eli.category_id
            WHERE eli.expense_plan_id = :plan_id
            AND eli.fiscal_period_id = :period_id
            """
            
            plan_result = self.db.execute(text(plan_query), {
                'plan_id': expense_plan_id,
                'period_id': period_id
            })
            
            planned = [dict(row._mapping) for row in plan_result.fetchall()]
        
        # Calculate variances
        variance_analysis = []
        
        for actual in actuals:
            account_id = actual['account_id']
            actual_amount = float(actual['actual_amount'])
            
            # Find matching plan
            plan_amount = 0
            for plan in planned:
                if plan['account_id'] == account_id:
                    plan_amount = float(plan['planned_amount'])
                    break
            
            variance = actual_amount - plan_amount
            variance_pct = (variance / plan_amount * 100) if plan_amount != 0 else 0
            
            variance_analysis.append({
                'account_id': account_id,
                'account_name': actual['account_name'],
                'category': actual.get('category_name', 'Uncategorized'),
                'actual': actual_amount,
                'planned': plan_amount,
                'variance': variance,
                'variance_pct': variance_pct,
                'status': 'over' if variance > 0 else 'under' if variance < 0 else 'on_target'
            })
        
        # Sort by variance magnitude
        variance_analysis.sort(key=lambda x: abs(x['variance']), reverse=True)
        
        return {
            'period_id': period_id,
            'variance_details': variance_analysis,
            'total_actual': sum(v['actual'] for v in variance_analysis),
            'total_planned': sum(v['planned'] for v in variance_analysis),
            'total_variance': sum(v['variance'] for v in variance_analysis),
            'over_budget_items': [v for v in variance_analysis if v['variance'] > 0],
            'under_budget_items': [v for v in variance_analysis if v['variance'] < 0]
        }
    
    # Helper methods
    
    async def _get_expense_accounts(self, company_id: str) -> List[Dict]:
        """Get expense accounts for company"""
        query = """
        SELECT id, account_number, name 
        FROM gl_accounts 
        WHERE company_id = :company_id 
        AND account_type = 'EXPENSE'
        AND is_active = true
        """
        result = self.db.execute(text(query), {'company_id': company_id})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _get_expense_categories(self, company_id: str) -> List[Dict]:
        """Get expense categories"""
        query = """
        SELECT * FROM expense_categories 
        WHERE company_id = :company_id 
        AND is_active = true
        ORDER BY category_type, category_name
        """
        result = self.db.execute(text(query), {'company_id': company_id})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _get_cost_centers(self, company_id: str) -> List[Dict]:
        """Get cost centers"""
        query = """
        SELECT id, code, name 
        FROM cost_centers 
        WHERE company_id = :company_id 
        AND is_active = true
        """
        result = self.db.execute(text(query), {'company_id': company_id})
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _calculate_personnel_costs(
        self,
        company_id: str,
        headcount_plan: Dict,
        months: int
    ) -> List[Dict]:
        """Calculate personnel costs based on headcount plan"""
        
        personnel_costs = []
        
        # If no headcount plan provided, use default departments
        if not headcount_plan:
            headcount_plan = {
                'Engineering': {'headcount': 10, 'avg_salary': 120000, 'benefits_rate': 0.3},
                'Sales': {'headcount': 5, 'avg_salary': 80000, 'benefits_rate': 0.3},
                'Marketing': {'headcount': 3, 'avg_salary': 70000, 'benefits_rate': 0.3},
                'Operations': {'headcount': 4, 'avg_salary': 60000, 'benefits_rate': 0.3},
                'Finance': {'headcount': 2, 'avg_salary': 90000, 'benefits_rate': 0.3}
            }
        
        for dept, plan in headcount_plan.items():
            headcount = plan.get('headcount', 0)
            avg_salary = plan.get('avg_salary', 60000)
            benefits_rate = plan.get('benefits_rate', 0.3)
            
            monthly_salary = (avg_salary * headcount) / 12
            monthly_benefits = monthly_salary * benefits_rate
            monthly_cost = monthly_salary + monthly_benefits
            
            personnel_costs.append({
                'department': dept,
                'headcount': headcount,
                'monthly_salary': monthly_salary,
                'monthly_benefits': monthly_benefits,
                'monthly_cost': monthly_cost,
                'annual_cost': monthly_cost * 12
            })
        
        return personnel_costs
    
    async def _estimate_category_need(
        self,
        company_id: str,
        category: Dict,
        params: Dict
    ) -> float:
        """Estimate expense need for a category"""
        
        # Base estimation logic
        base_amounts = {
            'facilities': 10000,  # Rent, utilities
            'marketing': 5000,     # Marketing spend
            'travel': 3000,        # Travel expenses
            'technology': 8000,    # Software, IT
            'professional': 4000,  # Legal, accounting
            'supplies': 2000,      # Office supplies
            'other': 1000
        }
        
        category_type = category.get('category_type', 'other')
        base = base_amounts.get(category_type, 1000)
        
        # Apply company size factor
        company_size = params.get('company_size', 'small')
        size_factors = {'small': 1.0, 'medium': 2.5, 'large': 5.0}
        size_factor = size_factors.get(company_size, 1.0)
        
        return base * size_factor
    
    def _generate_sample_expense_data(self) -> pd.DataFrame:
        """Generate sample expense data for demonstration"""
        
        months = []
        amounts = []
        
        base_expense = 50000
        for month in range(1, 13):
            # Add some variability
            variation = np.random.normal(0, 0.1)
            amount = base_expense * (1 + variation)
            
            months.append(month)
            amounts.append(amount)
        
        return pd.DataFrame({
            'month': months,
            'amount': amounts,
            'account_type': 'expense'
        })
    
    async def _allocate_to_categories(
        self,
        forecast_data: List[Dict],
        categories: List[Dict],
        historical_data: pd.DataFrame
    ) -> List[Dict]:
        """Allocate forecast to expense categories"""
        
        # Default category allocation percentages
        default_allocations = {
            'personnel': 0.50,
            'operating': 0.25,
            'marketing': 0.10,
            'technology': 0.08,
            'facilities': 0.05,
            'other': 0.02
        }
        
        category_breakdown = []
        
        for category in categories:
            category_type = category.get('category_type', 'other')
            allocation_pct = default_allocations.get(category_type, 0.01)
            
            category_forecast = []
            for period in forecast_data:
                amount = period['forecast_amount'] * allocation_pct
                category_forecast.append({
                    'period': period['period'],
                    'amount': amount
                })
            
            category_breakdown.append({
                'category': category.get('category_name', category_type),
                'category_type': category_type,
                'forecast': category_forecast,
                'total': sum(f['amount'] for f in category_forecast),
                'percentage': allocation_pct * 100
            })
        
        return category_breakdown
    
    async def _get_expense_drivers(self, company_id: str) -> List[Dict]:
        """Get expense-related business drivers"""
        
        # This would integrate with the driver-based planning service
        # For now, return sample drivers
        return [
            {
                'id': 'headcount',
                'name': 'Headcount',
                'default_value': 100,
                'unit': 'employees',
                'expense_per_unit': 8000  # Monthly cost per employee
            },
            {
                'id': 'revenue',
                'name': 'Revenue',
                'default_value': 1000000,
                'unit': 'dollars',
                'expense_ratio': 0.15  # Expense as % of revenue
            },
            {
                'id': 'transactions',
                'name': 'Transaction Volume',
                'default_value': 10000,
                'unit': 'transactions',
                'expense_per_unit': 2.5  # Cost per transaction
            }
        ]
    
    async def _calculate_driver_expense(
        self,
        driver: Dict,
        driver_value: float,
        month: int
    ) -> float:
        """Calculate expense based on driver value"""
        
        if 'expense_per_unit' in driver:
            return driver_value * driver['expense_per_unit']
        elif 'expense_ratio' in driver:
            return driver_value * driver['expense_ratio']
        else:
            return 0
    
    async def _driver_sensitivity_analysis(
        self,
        drivers: List[Dict],
        assumptions: Dict,
        forecast_data: List[Dict]
    ) -> Dict[str, Any]:
        """Perform sensitivity analysis on expense drivers"""
        
        sensitivity_results = []
        
        for driver in drivers:
            driver_id = driver['id']
            base_value = assumptions.get(driver_id, driver['default_value'])
            
            # Test +/- 10% changes
            variations = [-0.1, -0.05, 0, 0.05, 0.1]
            impact_results = []
            
            for variation in variations:
                test_value = base_value * (1 + variation)
                test_expense = await self._calculate_driver_expense(
                    driver,
                    test_value,
                    1  # First month
                )
                
                impact_results.append({
                    'variation_pct': variation * 100,
                    'driver_value': test_value,
                    'expense_impact': test_expense
                })
            
            sensitivity_results.append({
                'driver': driver['name'],
                'base_value': base_value,
                'sensitivity': impact_results
            })
        
        return {
            'driver_sensitivity': sensitivity_results,
            'most_sensitive': max(sensitivity_results, 
                                 key=lambda x: max(abs(i['expense_impact']) 
                                                 for i in x['sensitivity']))['driver']
        }
    
    async def _get_default_activities(self, company_id: str) -> List[Dict]:
        """Get default activities for activity-based costing"""
        
        return [
            {
                'name': 'Customer Service',
                'monthly_volume': 1000,
                'cost_per_unit': 25,
                'complexity_factor': 1.0
            },
            {
                'name': 'Order Processing',
                'monthly_volume': 500,
                'cost_per_unit': 15,
                'complexity_factor': 1.2
            },
            {
                'name': 'Product Development',
                'monthly_volume': 10,
                'cost_per_unit': 5000,
                'complexity_factor': 1.5
            },
            {
                'name': 'Quality Control',
                'monthly_volume': 100,
                'cost_per_unit': 50,
                'complexity_factor': 1.1
            }
        ]
    
    def generate_forecast(self, company_id: str, forecast_params: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of abstract method from base class"""
        # Synchronous wrapper for async method
        import asyncio
        return asyncio.run(self.generate_expense_forecast(company_id, forecast_params))
    
    def calculate_metrics(self, company_id: str, period_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate key expense metrics"""
        
        query = """
        SELECT 
            COUNT(DISTINCT ga.id) as num_expense_accounts,
            COUNT(DISTINCT cc.id) as num_cost_centers,
            SUM(gtl.debit_amount) as total_expenses
        FROM gl_accounts ga
        LEFT JOIN gl_transaction_lines gtl ON gtl.gl_account_id = ga.id
        LEFT JOIN gl_transactions gt ON gt.id = gtl.gl_transaction_id
        LEFT JOIN cost_centers cc ON cc.company_id = ga.company_id
        WHERE ga.company_id = :company_id
        AND ga.account_type = 'EXPENSE'
        """
        
        params = {'company_id': company_id}
        if period_id:
            query += " AND gt.fiscal_period_id = :period_id"
            params['period_id'] = period_id
        
        result = self.db.execute(text(query), params)
        row = result.fetchone()
        
        return {
            'num_expense_accounts': row[0] or 0,
            'num_cost_centers': row[1] or 0,
            'total_expenses': float(row[2] or 0)
        }