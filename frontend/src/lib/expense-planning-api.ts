import { api } from './api';

// ============================================
// TYPE DEFINITIONS
// ============================================

export interface ExpenseForecastMethod {
  method: 'incremental' | 'zero_based' | 'driver_based' | 'activity_based';
  growth_rate?: number;
  inflation_rate?: number;
  cost_reduction_target?: number;
}

export interface HeadcountPlan {
  department: string;
  headcount: number;
  avg_salary: number;
  benefits_rate: number;
}

export interface ExpenseForecastRequest {
  company_id: string;
  forecast_months: number;
  method: ExpenseForecastMethod;
  headcount_plan?: Record<string, HeadcountPlan>;
  driver_assumptions?: Record<string, number>;
  activities?: Array<{
    name: string;
    monthly_volume: number;
    cost_per_unit: number;
    complexity_factor: number;
  }>;
  include_contracts: boolean;
  include_categories: boolean;
}

export interface ExpenseForecastResponse {
  company_id: string;
  method: string;
  forecast_data: Array<{
    month: number;
    period: string;
    forecast_amount?: number;
    total_cost?: number;
    personnel_cost?: number;
    operating_cost?: number;
    type: string;
  }>;
  category_breakdown?: Array<{
    category: string;
    category_type: string;
    forecast: Array<{
      period: string;
      amount: number;
    }>;
    total: number;
    percentage: number;
  }>;
  total_forecast: number;
  assumptions: Record<string, any>;
  contract_obligations?: {
    contracts: any[];
    monthly_obligations: Array<{
      month: number;
      period: string;
      obligation: number;
    }>;
    total_obligation: number;
    contract_count: number;
  };
  sensitivity_analysis?: any;
}

export interface ExpensePlan {
  id: string;
  company_id: string;
  plan_name: string;
  plan_type: string;
  fiscal_year: number;
  version: number;
  status: 'draft' | 'review' | 'approved' | 'rejected';
  total_planned_amount?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCategory {
  id: string;
  company_id: string;
  category_code: string;
  category_name: string;
  category_type: string;
  parent_category_id?: string;
  is_controllable: boolean;
  is_discretionary: boolean;
  typical_variance_pct: number;
  level?: number;
  path?: string[];
}

export interface VendorContract {
  id: string;
  company_id: string;
  vendor_id: string;
  vendor_name?: string;
  contract_number: string;
  contract_name: string;
  contract_type: string;
  start_date: string;
  end_date?: string;
  monthly_amount: number;
  annual_amount?: number;
  escalation_rate?: number;
  auto_renew: boolean;
  contract_status?: string;
}

export interface ExpenseMetrics {
  current_month_expense: number;
  ytd_expense: number;
  avg_transaction_expense: number;
  num_expense_accounts: number;
  num_cost_centers: number;
  active_contracts: number;
  monthly_contract_obligations: number;
  expense_run_rate: number;
}

export interface ExpenseVariance {
  period_id: string;
  variance_details: Array<{
    account_id: string;
    account_name: string;
    category: string;
    actual: number;
    planned: number;
    variance: number;
    variance_pct: number;
    status: 'over' | 'under' | 'on_target';
  }>;
  total_actual: number;
  total_planned: number;
  total_variance: number;
  over_budget_items: any[];
  under_budget_items: any[];
}

// ============================================
// API FUNCTIONS
// ============================================

export const expensePlanningApi = {
  // Expense Forecasting
  async generateForecast(request: ExpenseForecastRequest): Promise<ExpenseForecastResponse> {
    const response = await api.post<ExpenseForecastResponse>('/planning/expense/forecast', request);
    return response.data;
  },

  // Expense Plans
  async createExpensePlan(data: {
    company_id: string;
    plan_name: string;
    plan_type: string;
    fiscal_year: number;
    scenario_id?: string;
    notes?: string;
  }): Promise<{ plan_id: string; status: string }> {
    const response = await api.post('/planning/expense/plans', data);
    return response.data;
  },

  async getExpensePlans(companyId: string, fiscalYear?: number, status?: string): Promise<ExpensePlan[]> {
    const params = new URLSearchParams();
    if (fiscalYear) params.append('fiscal_year', fiscalYear.toString());
    if (status) params.append('status', status);
    
    const response = await api.get<ExpensePlan[]>(`/planning/expense/plans/${companyId}?${params}`);
    return response.data;
  },

  // Expense Categories
  async getCategories(companyId: string, categoryType?: string): Promise<ExpenseCategory[]> {
    const params = categoryType ? `?category_type=${categoryType}` : '';
    const response = await api.get<ExpenseCategory[]>(`/planning/expense/categories/${companyId}${params}`);
    return response.data;
  },

  async createCategory(data: {
    company_id: string;
    category_code: string;
    category_name: string;
    category_type: string;
    parent_category_id?: string;
    is_controllable?: boolean;
    is_discretionary?: boolean;
    typical_variance_pct?: number;
  }): Promise<{ category_id: string; status: string }> {
    const response = await api.post('/planning/expense/categories', data);
    return response.data;
  },

  // Vendor Contracts
  async getContracts(companyId: string, activeOnly: boolean = true): Promise<any> {
    const params = `?active_only=${activeOnly}`;
    const response = await api.get(`/planning/expense/contracts/${companyId}${params}`);
    return response.data;
  },

  async createContract(data: {
    company_id: string;
    vendor_id: string;
    contract_number: string;
    contract_name: string;
    contract_type: string;
    start_date: string;
    end_date?: string;
    monthly_amount: number;
    annual_amount?: number;
    escalation_rate?: number;
    auto_renew?: boolean;
    gl_account_id?: string;
    cost_center_id?: string;
  }): Promise<{ contract_id: string; status: string }> {
    const response = await api.post('/planning/expense/contracts', data);
    return response.data;
  },

  // Metrics and Analysis
  async getExpenseMetrics(companyId: string): Promise<ExpenseMetrics> {
    const response = await api.get<ExpenseMetrics>(`/planning/expense/metrics/${companyId}`);
    return response.data;
  },

  async analyzeVariance(data: {
    company_id: string;
    period_id: string;
    expense_plan_id?: string;
    category_filter?: string;
  }): Promise<ExpenseVariance> {
    const response = await api.post<ExpenseVariance>('/planning/expense/variance-analysis', data);
    return response.data;
  },

  async getBenchmarks(companyId: string, categoryId?: string, fiscalYear?: number): Promise<any[]> {
    const params = new URLSearchParams();
    if (categoryId) params.append('category_id', categoryId);
    if (fiscalYear) params.append('fiscal_year', fiscalYear.toString());
    
    const response = await api.get(`/planning/expense/benchmarks/${companyId}?${params}`);
    return response.data;
  },

  async getExpenseDrivers(companyId: string): Promise<any[]> {
    const response = await api.get(`/planning/expense/cost-drivers/${companyId}`);
    return response.data;
  },
};