'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { companyApi } from '@/lib/api';
import { planningApi, type RevenueForecastRequest, type RevenueGrowthModel } from '@/lib/planning-api';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useDateFormat } from '@/contexts/DateFormatContext';
import toast from 'react-hot-toast';

export default function RevenueForecastPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [forecastParams, setForecastParams] = useState<RevenueForecastRequest>({
    company_id: '',
    forecast_months: 12,
    growth_model: {
      method: 'exponential',
      base_growth_rate: 0.15,
      confidence_level: 0.95
    },
    include_segments: true
  });
  const { formatDate } = useDateFormat();

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyApi.getAll(),
  });

  // Set default company
  useEffect(() => {
    if (!selectedCompanyId && companies && companies.length > 0) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  // Update forecast params when company changes
  useEffect(() => {
    if (selectedCompanyId) {
      setForecastParams(prev => ({ ...prev, company_id: selectedCompanyId }));
    }
  }, [selectedCompanyId]);

  const { data: revenueMetrics } = useQuery({
    queryKey: ['revenue-metrics', selectedCompanyId],
    queryFn: () => planningApi.getRevenueMetrics(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const forecastMutation = useMutation({
    mutationFn: (params: RevenueForecastRequest) => planningApi.generateRevenueForecast(params),
    onError: (error: any) => {
      toast.error(error.message || 'Failed to generate forecast');
    },
  });

  const handleGenerateForecast = () => {
    if (selectedCompanyId) {
      forecastMutation.mutate(forecastParams);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const forecastData = forecastMutation.data;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/planning" className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block">
            ← Back to Planning
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">📊 Revenue Forecasting</h1>
          <p className="text-gray-600 mt-1">
            Predict future revenue using historical data and statistical models
          </p>
        </div>
      </div>

      {/* Company Selection & Current Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Company
          </label>
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a company...</option>
            {companies?.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name} ({company.code})
              </option>
            ))}
          </select>
        </div>

        {revenueMetrics && (
          <>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Current Month Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(revenueMetrics.current_month_revenue)}
                  </p>
                </div>
                <div className="text-3xl">💰</div>
              </div>
              <div className="mt-2">
                <span className={`text-sm ${revenueMetrics.yoy_growth_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercentage(revenueMetrics.yoy_growth_percent)} YoY
                </span>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Revenue Run Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(revenueMetrics.revenue_run_rate)}
                  </p>
                </div>
                <div className="text-3xl">📈</div>
              </div>
              <div className="mt-2">
                <span className="text-sm text-gray-500">
                  Avg: {formatCurrency(revenueMetrics.average_monthly_revenue)}/month
                </span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Forecast Configuration */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Forecast Period
              <div className="group relative inline-block ml-1">
                <span className="text-blue-500 cursor-help">ℹ️</span>
                <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 left-full ml-2">
                  Number of months to forecast ahead. Longer periods have higher uncertainty.
                </div>
              </div>
            </label>
            <select
              value={forecastParams.forecast_months}
              onChange={(e) => setForecastParams(prev => ({ 
                ...prev, 
                forecast_months: parseInt(e.target.value) 
              }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value={6}>6 months</option>
              <option value={12}>12 months</option>
              <option value={18}>18 months</option>
              <option value={24}>24 months</option>
              <option value={36}>36 months</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Growth Model
              <div className="group relative inline-block ml-1">
                <span className="text-blue-500 cursor-help">ℹ️</span>
                <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 left-full ml-2">
                  <div><strong>Linear:</strong> Constant growth amount</div>
                  <div><strong>Exponential:</strong> Compound growth rate</div>
                  <div><strong>Seasonal:</strong> Accounts for monthly patterns</div>
                </div>
              </div>
            </label>
            <select
              value={forecastParams.growth_model.method}
              onChange={(e) => setForecastParams(prev => ({
                ...prev,
                growth_model: {
                  ...prev.growth_model,
                  method: e.target.value as 'linear' | 'exponential' | 'seasonal'
                }
              }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="exponential">Exponential Growth</option>
              <option value="linear">Linear Growth</option>
              <option value="seasonal">Seasonal Model</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Growth Rate (Annual)
              <div className="group relative inline-block ml-1">
                <span className="text-blue-500 cursor-help">ℹ️</span>
                <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 left-full ml-2">
                  Expected annual growth rate. For example, 0.15 = 15% growth per year.
                </div>
              </div>
            </label>
            <input
              type="number"
              step="0.01"
              min="-0.5"
              max="2.0"
              value={forecastParams.growth_model.base_growth_rate}
              onChange={(e) => setForecastParams(prev => ({
                ...prev,
                growth_model: {
                  ...prev.growth_model,
                  base_growth_rate: parseFloat(e.target.value)
                }
              }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="0.15"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confidence Level
              <div className="group relative inline-block ml-1">
                <span className="text-blue-500 cursor-help">ℹ️</span>
                <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 left-full ml-2">
                  Statistical confidence level for prediction intervals. 95% means the actual values should fall within the range 95% of the time.
                </div>
              </div>
            </label>
            <select
              value={forecastParams.growth_model.confidence_level}
              onChange={(e) => setForecastParams(prev => ({
                ...prev,
                growth_model: {
                  ...prev.growth_model,
                  confidence_level: parseFloat(e.target.value)
                }
              }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value={0.90}>90%</option>
              <option value={0.95}>95%</option>
              <option value={0.99}>99%</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex items-center space-x-4">
          <button
            onClick={handleGenerateForecast}
            disabled={!selectedCompanyId || forecastMutation.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {forecastMutation.isPending ? 'Generating...' : 'Generate Forecast'}
          </button>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={forecastParams.include_segments}
              onChange={(e) => setForecastParams(prev => ({
                ...prev,
                include_segments: e.target.checked
              }))}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">Include revenue segments</span>
          </label>
        </div>
      </div>

      {/* Forecast Results */}
      {forecastMutation.isPending && (
        <div className="text-center py-8">
          <LoadingSpinner />
          <p className="text-gray-600 mt-2">Analyzing historical data and generating forecast...</p>
        </div>
      )}

      {forecastData && (
        <div className="space-y-8">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-600">Forecast Total</h4>
                <div className="group relative">
                  <span className="text-blue-500 cursor-help">ℹ️</span>
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 right-0">
                    Total revenue expected over the forecast period
                  </div>
                </div>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(forecastData.growth_metrics.forecast_total)}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-600">Growth Rate</h4>
                <div className="group relative">
                  <span className="text-blue-500 cursor-help">ℹ️</span>
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 right-0">
                    Expected growth rate from current levels to end of forecast period
                  </div>
                </div>
              </div>
              <p className={`text-2xl font-bold ${forecastData.growth_metrics.forecast_growth_rate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercentage(forecastData.growth_metrics.forecast_growth_rate)}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-600">Forecast Accuracy</h4>
                <div className="group relative">
                  <span className="text-blue-500 cursor-help">ℹ️</span>
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 right-0">
                    R² shows how well the model explains historical data (higher is better, max 1.0)
                  </div>
                </div>
              </div>
              <p className="text-2xl font-bold text-purple-600">
                {(forecastData.accuracy_metrics.r_squared * 100).toFixed(1)}%
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-600">Avg Monthly</h4>
                <div className="group relative">
                  <span className="text-blue-500 cursor-help">ℹ️</span>
                  <div className="invisible group-hover:visible absolute z-10 w-48 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 right-0">
                    Average monthly revenue expected during forecast period
                  </div>
                </div>
              </div>
              <p className="text-2xl font-bold text-orange-600">
                {formatCurrency(forecastData.growth_metrics.forecast_avg_monthly)}
              </p>
            </div>
          </div>

          {/* Revenue Trend Table */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Revenue Trend & Forecast</h3>
              <div className="group relative">
                <span className="text-blue-500 cursor-help">ℹ️</span>
                <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 right-0">
                  Historical revenue vs forecasted revenue. Look for consistent trends and reasonable forecast projections.
                </div>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Period</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Historical</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Forecast</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {forecastData.historical_data.map((item, idx) => (
                    <tr key={`hist-${idx}`} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm text-gray-900">{item.period}</td>
                      <td className="px-4 py-2 text-sm text-right text-gray-900 font-medium">{formatCurrency(item.revenue)}</td>
                      <td className="px-4 py-2 text-sm text-right text-gray-400">-</td>
                      <td className="px-4 py-2 text-sm text-right">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          Actual
                        </span>
                      </td>
                    </tr>
                  ))}
                  {forecastData.forecast_data.map((item, idx) => (
                    <tr key={`forecast-${idx}`} className="hover:bg-green-50 bg-green-25">
                      <td className="px-4 py-2 text-sm text-gray-900">{item.period}</td>
                      <td className="px-4 py-2 text-sm text-right text-gray-400">-</td>
                      <td className="px-4 py-2 text-sm text-right text-green-600 font-medium">{formatCurrency(item.revenue)}</td>
                      <td className="px-4 py-2 text-sm text-right">
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          Forecast
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Confidence Intervals Table */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Forecast Confidence Intervals</h3>
              <div className="group relative">
                <span className="text-blue-500 cursor-help">ℹ️</span>
                <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 right-0">
                  The range where actual revenue is likely to fall. Wider intervals indicate higher uncertainty.
                </div>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Period</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Lower Bound</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Forecast</th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Upper Bound</th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Range</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {forecastData.confidence_intervals.map((interval, idx) => {
                    const range = ((interval.upper - interval.lower) / interval.forecast * 100);
                    return (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-4 py-2 text-sm text-gray-900">{interval.period}</td>
                        <td className="px-4 py-2 text-sm text-right text-red-600">{formatCurrency(interval.lower)}</td>
                        <td className="px-4 py-2 text-sm text-right text-green-600 font-medium">{formatCurrency(interval.forecast)}</td>
                        <td className="px-4 py-2 text-sm text-right text-blue-600">{formatCurrency(interval.upper)}</td>
                        <td className="px-4 py-2 text-sm text-center">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            range < 20 ? 'bg-green-100 text-green-800' : 
                            range < 40 ? 'bg-yellow-100 text-yellow-800' : 
                            'bg-red-100 text-red-800'
                          }`}>
                            ±{range.toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Revenue Segments */}
          {forecastData.segments && forecastData.segments.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Revenue by Segment</h3>
                <div className="group relative">
                  <span className="text-blue-500 cursor-help">ℹ️</span>
                  <div className="invisible group-hover:visible absolute z-10 w-64 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 right-0">
                    Historical revenue breakdown by product/service categories. Helps identify key revenue drivers.
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {forecastData.segments.map((segment, index) => {
                  const colors = [
                    'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-purple-500', 'bg-pink-500'
                  ];
                  const bgColors = [
                    'bg-blue-50', 'bg-green-50', 'bg-yellow-50', 'bg-red-50', 'bg-purple-50', 'bg-pink-50'
                  ];
                  return (
                    <div key={segment.name} className={`${bgColors[index % 6]} border-2 border-gray-200 rounded-lg p-4`}>
                      <div className="flex items-center mb-2">
                        <div className={`w-4 h-4 ${colors[index % 6]} rounded-full mr-2`} />
                        <h4 className="font-medium text-gray-900 text-sm">{segment.name}</h4>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-gray-900 mb-1">{formatCurrency(segment.revenue)}</div>
                        <div className="text-sm text-gray-600">{Number(segment.percentage || 0).toFixed(1)}% of total</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Model Performance */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Performance</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-blue-600">
                  {forecastData.accuracy_metrics.mape.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  MAPE
                  <div className="group relative inline-block ml-1">
                    <span className="text-blue-500 cursor-help">ℹ️</span>
                    <div className="invisible group-hover:visible absolute z-10 w-48 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 left-full ml-2">
                      Mean Absolute Percentage Error. Lower is better. &lt;10% is excellent, &lt;20% is good.
                    </div>
                  </div>
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(forecastData.accuracy_metrics.rmse)}
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  RMSE
                  <div className="group relative inline-block ml-1">
                    <span className="text-blue-500 cursor-help">ℹ️</span>
                    <div className="invisible group-hover:visible absolute z-10 w-48 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 left-full ml-2">
                      Root Mean Square Error. Shows average forecast error in dollar terms.
                    </div>
                  </div>
                </div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-purple-600">
                  {(forecastData.accuracy_metrics.r_squared * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  R-Squared
                  <div className="group relative inline-block ml-1">
                    <span className="text-blue-500 cursor-help">ℹ️</span>
                    <div className="invisible group-hover:visible absolute z-10 w-48 p-2 text-xs bg-gray-800 text-white rounded shadow-lg -top-2 left-full ml-2">
                      Coefficient of determination. Shows how well the model explains the data. Higher is better.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Interpretation Guide */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">💡 How to Interpret Results</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-blue-800">
              <div>
                <h4 className="font-semibold mb-2">Forecast Reliability</h4>
                <ul className="space-y-1">
                  <li>• Higher R² values (&gt;70%) indicate more reliable forecasts</li>
                  <li>• Wider confidence intervals suggest higher uncertainty</li>
                  <li>• MAPE &lt;10% is excellent, &lt;20% is good forecasting accuracy</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Business Insights</h4>
                <ul className="space-y-1">
                  <li>• Identify seasonal patterns for resource planning</li>
                  <li>• Use growth rate to set realistic targets</li>
                  <li>• Review top revenue segments for strategic focus</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}