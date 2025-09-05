import { api } from './api';

export interface RevenueGrowthModel {
  method: 'linear' | 'exponential' | 'seasonal';
  base_growth_rate: number;
  seasonality_factors?: number[];
  confidence_level: number;
}

export interface RevenueForecastRequest {
  company_id: string;
  forecast_months: number;
  growth_model: RevenueGrowthModel;
  include_segments: boolean;
  scenario_id?: string;
}

export interface HistoricalDataPoint {
  year: number;
  month: number;
  period: string;
  revenue: number;
  type: 'actual';
}

export interface ForecastDataPoint {
  year: number;
  month: number;
  period: string;
  revenue: number;
  type: 'forecast';
}

export interface RevenueSegment {
  name: string;
  revenue: number;
  percentage: number;
}

export interface ConfidenceInterval {
  period: string;
  lower: number;
  upper: number;
  forecast: number;
}

export interface RevenueForecastResponse {
  company_id: string;
  forecast_period: {
    start: string;
    end: string;
  };
  historical_data: HistoricalDataPoint[];
  forecast_data: ForecastDataPoint[];
  growth_metrics: {
    historical_avg_monthly: number;
    historical_total: number;
    historical_cagr: number;
    forecast_avg_monthly: number;
    forecast_total: number;
    forecast_growth_rate: number;
  };
  accuracy_metrics: {
    mape: number;
    rmse: number;
    r_squared: number;
  };
  segments: RevenueSegment[] | null;
  confidence_intervals: ConfidenceInterval[];
}

export interface RevenueMetrics {
  current_month_revenue: number;
  ytd_revenue: number;
  last_year_revenue: number;
  yoy_growth_percent: number;
  average_monthly_revenue: number;
  revenue_run_rate: number;
}

export const planningApi = {
  async generateRevenueForecast(request: RevenueForecastRequest): Promise<RevenueForecastResponse> {
    const response = await api.post<RevenueForecastResponse>('/planning/revenue-forecast', request);
    return response.data;
  },

  async getRevenueMetrics(companyId: string): Promise<RevenueMetrics> {
    const response = await api.get<RevenueMetrics>(`/planning/revenue-forecast/${companyId}/metrics`);
    return response.data;
  },
};