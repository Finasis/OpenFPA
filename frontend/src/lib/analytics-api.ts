import { api, ApiError, handleApiError } from './api';
import type { UUID, KPIMetric, DashboardMetrics, VarianceAnalysis } from '@/types';

// ============================================
// ANALYTICS API TYPES
// ============================================

export interface FinancialSummary {
  readonly revenue: number;
  readonly expenses: number;
  readonly profit: number;
  readonly margin: number;
}

export interface TrendDataPoint {
  readonly month: string;
  readonly revenue: number;
  readonly expenses: number;
  readonly profit?: number;
}

export interface DashboardData {
  readonly company_id: UUID;
  readonly financial_summary: FinancialSummary;
  readonly kpis: readonly KPIMetric[];
  readonly trends: readonly TrendDataPoint[];
  readonly status: 'success' | 'error';
  readonly data_source?: 'database';
  readonly message?: string;
}

export interface VarianceData {
  readonly company_id: UUID;
  readonly variances: readonly VarianceAnalysis[];
  readonly total_budget?: number;
  readonly total_actual?: number;
  readonly total_variance?: number;
  readonly status: 'success' | 'error';
  readonly data_source?: 'database';
  readonly message?: string;
}

export interface KPIData {
  readonly company_id: UUID;
  readonly kpis: readonly KPIMetric[];
  readonly overall_health?: 'excellent' | 'good' | 'warning' | 'critical';
  readonly status: 'success' | 'error';
  readonly data_source?: 'database';
  readonly message?: string;
}

export interface TimeSeriesData {
  readonly period?: string;
  readonly date?: string;
  readonly value?: number;
  readonly revenue?: number;
  readonly expenses?: number;
  readonly label?: string;
}

export interface ForecastData {
  readonly company_id: UUID;
  readonly account_id?: UUID;
  readonly historical: readonly TimeSeriesData[];
  readonly forecast: readonly TimeSeriesData[];
  readonly confidence_interval?: {
    readonly lower: readonly number[];
    readonly upper: readonly number[];
  };
  readonly method?: 'linear' | 'seasonal' | 'moving_average' | 'ml';
  readonly accuracy?: number;
  readonly message?: string;
}

// ============================================
// ANALYTICS FILTERS
// ============================================

export interface AnalyticsFilters {
  readonly fiscal_period_id?: UUID;
  readonly fiscal_year?: number;
  readonly cost_center_id?: UUID;
  readonly scenario_id?: UUID;
  readonly compare_to?: UUID; // Another period or scenario for comparison
}

export interface ForecastOptions {
  readonly method?: 'linear' | 'seasonal' | 'moving_average';
  readonly periods?: number;
  readonly confidence?: number;
  readonly seasonality?: 'monthly' | 'quarterly' | 'yearly';
}

// ============================================
// ANALYTICS API CLIENT
// ============================================

class AnalyticsApiClient {
  private readonly basePath = '/analytics';

  /**
   * Get dashboard data for a company
   */
  async getDashboardData(
    companyId: UUID,
    filters?: AnalyticsFilters
  ): Promise<DashboardData> {
    try {
      const response = await api.get<DashboardData>(
        `${this.basePath}/dashboard/${companyId}`,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      throw new ApiError(
        handleApiError(error, 'Failed to fetch dashboard data'),
        undefined,
        'DASHBOARD_FETCH_ERROR'
      );
    }
  }

  /**
   * Get variance analysis comparing budget vs actual
   */
  async getVarianceAnalysis(
    companyId: UUID,
    filters?: AnalyticsFilters
  ): Promise<VarianceData> {
    try {
      const response = await api.get<VarianceData>(
        `${this.basePath}/variance/${companyId}`,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      throw new ApiError(
        handleApiError(error, 'Failed to fetch variance analysis'),
        undefined,
        'VARIANCE_FETCH_ERROR'
      );
    }
  }

  /**
   * Get KPI summary with trends
   */
  async getKPISummary(
    companyId: UUID,
    filters?: AnalyticsFilters
  ): Promise<KPIData> {
    try {
      const response = await api.get<KPIData>(
        `${this.basePath}/kpis/${companyId}`,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      throw new ApiError(
        handleApiError(error, 'Failed to fetch KPI summary'),
        undefined,
        'KPI_FETCH_ERROR'
      );
    }
  }

  /**
   * Get forecast for an account
   */
  async getForecast(
    companyId: UUID,
    accountId: UUID,
    options?: ForecastOptions
  ): Promise<ForecastData> {
    try {
      const response = await api.get<ForecastData>(
        `${this.basePath}/forecast/${companyId}/${accountId}`,
        { params: options }
      );
      return response.data;
    } catch (error) {
      throw new ApiError(
        handleApiError(error, 'Failed to generate forecast'),
        undefined,
        'FORECAST_ERROR'
      );
    }
  }

  /**
   * Generate sample analytics data for testing
   */
  async generateSampleData(
    companyId: UUID,
    months = 12
  ): Promise<{ success: boolean; message: string; details?: unknown }> {
    try {
      const response = await api.post<{ success: boolean; message: string; details?: unknown }>(
        `${this.basePath}/generate-sample-data/${companyId}`,
        null,
        { params: { months } }
      );
      return response.data;
    } catch (error) {
      throw new ApiError(
        handleApiError(error, 'Failed to generate sample data'),
        undefined,
        'SAMPLE_DATA_ERROR'
      );
    }
  }

  /**
   * Export analytics data to various formats
   */
  async exportData(
    companyId: UUID,
    format: 'csv' | 'excel' | 'pdf',
    reportType: 'dashboard' | 'variance' | 'kpi' | 'forecast',
    filters?: AnalyticsFilters
  ): Promise<Blob> {
    try {
      const response = await api.get<Blob>(
        `${this.basePath}/export/${companyId}`,
        {
          params: {
            format,
            report_type: reportType,
            ...filters,
          },
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error) {
      throw new ApiError(
        handleApiError(error, 'Failed to export analytics data'),
        undefined,
        'EXPORT_ERROR'
      );
    }
  }

  /**
   * Get comparison between two periods or scenarios
   */
  async getComparison(
    companyId: UUID,
    baseId: UUID,
    compareToId: UUID,
    comparisonType: 'period' | 'scenario'
  ): Promise<{
    base: DashboardData;
    comparison: DashboardData;
    differences: Record<string, number>;
  }> {
    try {
      const response = await api.get<{
        base: DashboardData;
        comparison: DashboardData;
        differences: Record<string, number>;
      }>(`${this.basePath}/compare/${companyId}`, {
        params: {
          base_id: baseId,
          compare_to_id: compareToId,
          comparison_type: comparisonType,
        },
      });
      return response.data;
    } catch (error) {
      throw new ApiError(
        handleApiError(error, 'Failed to fetch comparison data'),
        undefined,
        'COMPARISON_ERROR'
      );
    }
  }
}

// Export singleton instance
export const analyticsApi = new AnalyticsApiClient();

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Calculate percentage change between two values
 */
export const calculatePercentageChange = (
  oldValue: number,
  newValue: number
): number => {
  if (oldValue === 0) return newValue === 0 ? 0 : 100;
  return ((newValue - oldValue) / Math.abs(oldValue)) * 100;
};

/**
 * Format variance status based on account type
 */
export const getVarianceStatus = (
  variance: number,
  accountType: 'revenue' | 'expense'
): 'favorable' | 'unfavorable' | 'neutral' => {
  if (variance === 0) return 'neutral';
  
  if (accountType === 'revenue') {
    return variance > 0 ? 'favorable' : 'unfavorable';
  } else {
    return variance < 0 ? 'favorable' : 'unfavorable';
  }
};

/**
 * Calculate overall KPI health score
 */
export const calculateKPIHealth = (
  kpis: readonly KPIMetric[]
): 'excellent' | 'good' | 'warning' | 'critical' => {
  if (kpis.length === 0) return 'warning';
  
  const scores = kpis.map((kpi) => {
    const percentage = (kpi.value / kpi.target) * 100;
    if (percentage >= 100) return 4;
    if (percentage >= 80) return 3;
    if (percentage >= 60) return 2;
    return 1;
  });
  
  const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
  
  if (avgScore >= 3.5) return 'excellent';
  if (avgScore >= 2.5) return 'good';
  if (avgScore >= 1.5) return 'warning';
  return 'critical';
};