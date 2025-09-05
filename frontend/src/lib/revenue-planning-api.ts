import { api } from './api';

// ============================================
// TYPE DEFINITIONS
// ============================================

export interface RevenueForecastRequest {
  company_id: string;
  forecast_months: number;
  method: string;
  lookback_months?: number;
  trend_type?: string;
  growth_rate?: number;
  polynomial_degree?: number;
  confidence_level?: number;
  driver_assumptions?: Record<string, number>;
  new_cohort_size?: number;
  cohort_growth_rate?: number;
  ensemble_weights?: number[];
  stage_conversion?: Record<string, number>;
  include_segments?: boolean;
  include_pipeline?: boolean;
  include_seasonality?: boolean;
  include_cyclical?: boolean;
  cycle_period?: number;
  cycle_amplitude?: number;
  external_factors?: Array<{
    name: string;
    values: number[];
    projection: number;
  }>;
}

export interface RevenueForecastResponse {
  forecast_data: Array<{
    month: number;
    period: string;
    forecast: number;
    method: string;
    trend?: number;
    seasonal_factor?: number;
    pipeline_value?: number;
    opportunity_count?: number;
    new_revenue?: number;
    recurring_revenue?: number;
    driver_breakdown?: Record<string, number>;
  }>;
  method: string;
  total_forecast: number;
  confidence_intervals?: Array<{
    period: string;
    forecast: number;
    lower: number;
    upper: number;
    confidence_level: number;
  }>;
  segments?: Array<{
    name: string;
    type: string;
    metrics: {
      opportunity_count: number;
      total_pipeline: number;
      avg_probability: number;
      typical_deal_size: number;
      growth_rate: number;
    };
  }>;
  pipeline?: {
    stages: Array<{
      stage: string;
      count: number;
      amount: number;
      avg_amount: number;
      probability: number;
      avg_days: number;
    }>;
    total_pipeline: number;
    weighted_pipeline: number;
    conversion_rate: number;
  };
  recurring_metrics?: {
    mrr: number;
    arr: number;
    recurring_streams: number;
    churn_rate: number;
    growth_rate: number;
    ltv: number;
    months_to_recover_cac: number;
  };
  sensitivity_analysis?: {
    driver_sensitivity: Array<{
      driver: string;
      base_value: number;
      sensitivity: Array<{
        variation_pct: number;
        driver_value: number;
        revenue_impact: number;
        revenue_change_pct: number;
      }>;
    }>;
    most_sensitive: string;
  };
  growth_metrics?: {
    historical_growth_rate?: number;
    forecast_growth_rate?: number;
    yoy_growth?: number;
  };
  model_metrics?: {
    r_squared?: number;
    coefficients?: number[];
    intercept?: number;
    mape?: number;
    rmse?: number;
    mae?: number;
  };
}

export interface RevenuePlan {
  id: string;
  company_id: string;
  scenario_id?: string;
  plan_name: string;
  plan_type: string;
  fiscal_year: number;
  version: number;
  status: 'draft' | 'review' | 'approved' | 'rejected';
  total_planned_revenue?: number;
  confidence_level?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface RevenueStream {
  id: string;
  stream_code: string;
  stream_name: string;
  stream_type: string;
  parent_stream_id?: string;
  parent_stream_name?: string;
  gl_account_name?: string;
  recognition_method?: string;
  is_recurring: boolean;
  recurring_frequency?: string;
}

export interface CustomerSegment {
  id: string;
  segment_code: string;
  segment_name: string;
  segment_type?: string;
  typical_deal_size?: number;
  typical_sales_cycle_days?: number;
  churn_rate?: number;
  growth_rate?: number;
  pipeline_opportunities?: number;
  pipeline_value?: number;
}

export interface PipelineOpportunity {
  id: string;
  opportunity_name: string;
  segment_name?: string;
  stream_name?: string;
  stage: string;
  probability: number;
  amount: number;
  weighted_amount: number;
  expected_close_date: string;
  days_in_stage?: number;
}

export interface PricingModel {
  id: string;
  stream_name: string;
  model_name: string;
  pricing_type: string;
  base_price?: number;
  effective_date: string;
  expiration_date?: string;
  is_active: boolean;
}

export interface RevenueVariance {
  period_id: string;
  actual_revenue: number;
  planned_revenue: number;
  variance: number;
  variance_pct: number;
  status: 'over_target' | 'under_target' | 'no_data';
}

export interface CohortAnalysis {
  cohort_name: string;
  cohort_date: string;
  initial_customers: number;
  initial_revenue: number;
  retention_curve: Array<{
    month: number;
    retained_customers: number;
    retained_revenue: number;
    retention_rate: number;
    revenue_retention_rate: number;
  }>;
}

export interface SeasonalityPattern {
  stream: string;
  monthly_indices: Record<number, {
    index: number;
    historical_avg: number;
  }>;
}

// ============================================
// API FUNCTIONS
// ============================================

export const revenuePlanningApi = {
  // Revenue Forecasting
  async generateForecast(request: RevenueForecastRequest): Promise<RevenueForecastResponse> {
    const response = await api.post<RevenueForecastResponse>('/planning/revenue/forecast', request);
    return response.data;
  },

  // Revenue Plans
  async createRevenuePlan(data: {
    company_id: string;
    plan_name: string;
    plan_type: string;
    fiscal_year: number;
    scenario_id?: string;
    confidence_level?: number;
    notes?: string;
  }): Promise<{ plan_id: string; status: string; message: string }> {
    const response = await api.post('/planning/revenue/plans', data);
    return response.data;
  },

  async getRevenuePlans(companyId: string, fiscalYear?: number, status?: string): Promise<RevenuePlan[]> {
    const params = new URLSearchParams();
    if (fiscalYear) params.append('fiscal_year', fiscalYear.toString());
    if (status) params.append('status', status);
    
    const response = await api.get<RevenuePlan[]>(`/planning/revenue/plans/${companyId}?${params}`);
    return response.data;
  },

  // Revenue Streams
  async createRevenueStream(data: {
    company_id: string;
    stream_code: string;
    stream_name: string;
    stream_type: string;
    parent_stream_id?: string;
    gl_account_id?: string;
    recognition_method?: string;
    typical_payment_terms?: number;
    is_recurring: boolean;
    recurring_frequency?: string;
  }): Promise<{ stream_id: string; status: string; message: string }> {
    const response = await api.post('/planning/revenue/streams', data);
    return response.data;
  },

  async getRevenueStreams(companyId: string, streamType?: string, isRecurring?: boolean): Promise<RevenueStream[]> {
    const params = new URLSearchParams();
    if (streamType) params.append('stream_type', streamType);
    if (isRecurring !== undefined) params.append('is_recurring', isRecurring.toString());
    
    const response = await api.get<RevenueStream[]>(`/planning/revenue/streams/${companyId}?${params}`);
    return response.data;
  },

  // Customer Segments
  async createCustomerSegment(data: {
    company_id: string;
    segment_code: string;
    segment_name: string;
    segment_type?: string;
    typical_deal_size?: number;
    typical_sales_cycle_days?: number;
    churn_rate?: number;
    growth_rate?: number;
  }): Promise<{ segment_id: string; status: string; message: string }> {
    const response = await api.post('/planning/revenue/segments', data);
    return response.data;
  },

  async getCustomerSegments(companyId: string, segmentType?: string): Promise<CustomerSegment[]> {
    const params = segmentType ? `?segment_type=${segmentType}` : '';
    const response = await api.get<CustomerSegment[]>(`/planning/revenue/segments/${companyId}${params}`);
    return response.data;
  },

  // Sales Pipeline
  async createPipelineOpportunity(data: {
    company_id: string;
    opportunity_name: string;
    customer_segment_id?: string;
    revenue_stream_id?: string;
    stage: string;
    probability: number;
    amount: number;
    expected_close_date: string;
    sales_rep_id?: string;
  }): Promise<{ opportunity_id: string; status: string; message: string }> {
    const response = await api.post('/planning/revenue/pipeline', data);
    return response.data;
  },

  async getPipelineOpportunities(
    companyId: string,
    stage?: string,
    segmentId?: string,
    streamId?: string
  ): Promise<PipelineOpportunity[]> {
    const params = new URLSearchParams();
    if (stage) params.append('stage', stage);
    if (segmentId) params.append('segment_id', segmentId);
    if (streamId) params.append('stream_id', streamId);
    
    const response = await api.get<PipelineOpportunity[]>(`/planning/revenue/pipeline/${companyId}?${params}`);
    return response.data;
  },

  async getPipelineSummary(companyId: string): Promise<any> {
    const response = await api.get(`/planning/revenue/pipeline/summary/${companyId}`);
    return response.data;
  },

  // Pricing Models
  async createPricingModel(data: {
    company_id: string;
    revenue_stream_id: string;
    model_name: string;
    pricing_type: string;
    base_price?: number;
    pricing_tiers?: any;
    discount_rules?: any;
    effective_date: string;
    expiration_date?: string;
  }): Promise<{ model_id: string; status: string; message: string }> {
    const response = await api.post('/planning/revenue/pricing', data);
    return response.data;
  },

  async getPricingModels(companyId: string, streamId?: string, activeOnly: boolean = true): Promise<PricingModel[]> {
    const params = new URLSearchParams();
    if (streamId) params.append('stream_id', streamId);
    params.append('active_only', activeOnly.toString());
    
    const response = await api.get<PricingModel[]>(`/planning/revenue/pricing/${companyId}?${params}`);
    return response.data;
  },

  // Metrics and Analysis
  async getRevenueMetrics(companyId: string): Promise<any> {
    const response = await api.get(`/planning/revenue/metrics/${companyId}`);
    return response.data;
  },

  async analyzeVariance(data: {
    company_id: string;
    period_id: string;
    revenue_plan_id?: string;
    stream_filter?: string;
    segment_filter?: string;
  }): Promise<RevenueVariance> {
    const response = await api.post<RevenueVariance>('/planning/revenue/variance-analysis', data);
    return response.data;
  },

  async getCohortAnalysis(companyId: string, segmentId?: string): Promise<CohortAnalysis[]> {
    const params = segmentId ? `?segment_id=${segmentId}` : '';
    const response = await api.get<CohortAnalysis[]>(`/planning/revenue/cohorts/${companyId}${params}`);
    return response.data;
  },

  async getSeasonalityPatterns(companyId: string, streamId?: string): Promise<SeasonalityPattern[]> {
    const params = streamId ? `?stream_id=${streamId}` : '';
    const response = await api.get<SeasonalityPattern[]>(`/planning/revenue/seasonality/${companyId}${params}`);
    return response.data;
  },
};