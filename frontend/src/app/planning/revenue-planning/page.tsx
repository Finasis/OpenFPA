'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { companyApi } from '@/lib/api';
import { revenuePlanningApi, type RevenueForecastRequest } from '@/lib/revenue-planning-api';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { LineChart } from '@/components/charts/LineChart';
import { BarChart } from '@/components/charts/BarChart';
import toast from 'react-hot-toast';

export default function RevenuePlanningPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [selectedMethod, setSelectedMethod] = useState<string>('trend');
  const [forecastMonths, setForecastMonths] = useState(12);
  const [lookbackMonths, setLookbackMonths] = useState(24);
  const [trendType, setTrendType] = useState('linear');
  const [growthRate, setGrowthRate] = useState(0.15);
  const [confidenceLevel, setConfidenceLevel] = useState(0.95);
  const [includeSegments, setIncludeSegments] = useState(true);
  const [includePipeline, setIncludePipeline] = useState(true);
  const [activeTab, setActiveTab] = useState<'forecast' | 'streams' | 'segments' | 'pipeline' | 'analysis'>('forecast');

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyApi.getAll(),
  });

  const { data: revenueMetrics } = useQuery({
    queryKey: ['revenue-metrics', selectedCompanyId],
    queryFn: () => revenuePlanningApi.getRevenueMetrics(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: revenueStreams } = useQuery({
    queryKey: ['revenue-streams', selectedCompanyId],
    queryFn: () => revenuePlanningApi.getRevenueStreams(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: customerSegments } = useQuery({
    queryKey: ['customer-segments', selectedCompanyId],
    queryFn: () => revenuePlanningApi.getCustomerSegments(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: pipelineOpportunities } = useQuery({
    queryKey: ['pipeline-opportunities', selectedCompanyId],
    queryFn: () => revenuePlanningApi.getPipelineOpportunities(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const forecastMutation = useMutation({
    mutationFn: (params: RevenueForecastRequest) => revenuePlanningApi.generateForecast(params),
    onSuccess: () => {
      toast.success('Revenue forecast generated successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to generate forecast');
    },
  });

  const handleGenerateForecast = () => {
    if (!selectedCompanyId) return;

    const request: RevenueForecastRequest = {
      company_id: selectedCompanyId,
      forecast_months: forecastMonths,
      method: selectedMethod,
      lookback_months: lookbackMonths,
      trend_type: trendType,
      growth_rate: growthRate,
      confidence_level: confidenceLevel,
      include_segments: includeSegments,
      include_pipeline: includePipeline,
    };

    forecastMutation.mutate(request);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const forecastData = forecastMutation.data;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Revenue Planning & Forecasting</h1>
        <p className="text-gray-600">Advanced revenue forecasting with multiple methods</p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {revenueMetrics && (
          <>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">MRR</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(revenueMetrics.recurring_metrics?.mrr || 0)}
                  </p>
                </div>
                <div className="text-2xl">📊</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">ARR</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(revenueMetrics.recurring_metrics?.arr || 0)}
                  </p>
                </div>
                <div className="text-2xl">💰</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">Pipeline</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(revenueMetrics.pipeline?.total_pipeline || 0)}
                  </p>
                </div>
                <div className="text-2xl">🎯</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">Growth Rate</p>
                  <p className="text-lg font-bold text-gray-900">
                    {((revenueMetrics.recurring_metrics?.growth_rate || 0) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="text-2xl">📈</div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'forecast', label: 'Forecast', icon: '📊' },
            { id: 'streams', label: 'Revenue Streams', icon: '💵' },
            { id: 'segments', label: 'Segments', icon: '👥' },
            { id: 'pipeline', label: 'Pipeline', icon: '🚀' },
            { id: 'analysis', label: 'Analysis', icon: '📉' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`
                py-2 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="mt-6">
        {activeTab === 'forecast' && (
          <div className="space-y-6">
            {/* Forecast Configuration */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold mb-4">Configure Revenue Forecast</h2>
              
              {/* Company Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company
                </label>
                <select
                  value={selectedCompanyId}
                  onChange={(e) => setSelectedCompanyId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a company</option>
                  {companies?.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Forecasting Method
                  </label>
                  <select
                    value={selectedMethod}
                    onChange={(e) => setSelectedMethod(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="trend">Trend Analysis</option>
                    <option value="seasonal">Seasonal Decomposition</option>
                    <option value="regression">Multiple Regression</option>
                    <option value="pipeline">Pipeline-Based</option>
                    <option value="driver_based">Driver-Based</option>
                    <option value="cohort">Cohort Analysis</option>
                    <option value="ml_ensemble">ML Ensemble</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Forecast Months
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={forecastMonths}
                    onChange={(e) => setForecastMonths(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Historical Months
                  </label>
                  <input
                    type="number"
                    min="6"
                    max="60"
                    value={lookbackMonths}
                    onChange={(e) => setLookbackMonths(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {selectedMethod === 'trend' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Trend Type
                    </label>
                    <select
                      value={trendType}
                      onChange={(e) => setTrendType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="linear">Linear</option>
                      <option value="exponential">Exponential</option>
                      <option value="polynomial">Polynomial</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Growth Rate ({(growthRate * 100).toFixed(0)}%)
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={growthRate * 100}
                      onChange={(e) => setGrowthRate(parseInt(e.target.value) / 100)}
                      className="w-full"
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-4 mt-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includeSegments}
                    onChange={(e) => setIncludeSegments(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm">Include Segments</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={includePipeline}
                    onChange={(e) => setIncludePipeline(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm">Include Pipeline</span>
                </label>
              </div>

              <button
                onClick={handleGenerateForecast}
                disabled={!selectedCompanyId || forecastMutation.isPending}
                className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {forecastMutation.isPending ? 'Generating...' : 'Generate Forecast'}
              </button>
            </div>

            {/* Forecast Results */}
            {forecastData && (
              <>
                {/* Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">Total Forecast</h4>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(forecastData.total_forecast)}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">Method</h4>
                    <p className="text-lg font-semibold text-gray-900">
                      {forecastData.method}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">Confidence</h4>
                    <p className="text-lg font-semibold text-gray-900">
                      {(confidenceLevel * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                {/* Forecast Chart */}
                {forecastData.forecast_data && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold mb-4">Revenue Forecast</h3>
                    <LineChart
                      data={{
                        labels: forecastData.forecast_data.map((d: any) => d.period),
                        datasets: [{
                          label: 'Forecast',
                          data: forecastData.forecast_data.map((d: any) => d.forecast),
                          borderColor: 'rgb(75, 192, 192)',
                          backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        }]
                      }}
                      options={{
                        responsive: true,
                        plugins: {
                          legend: {
                            position: 'top' as const,
                          },
                        },
                      }}
                    />
                  </div>
                )}

                {/* Segments Analysis */}
                {forecastData.segments && forecastData.segments.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold mb-4">Customer Segments</h3>
                    <div className="space-y-3">
                      {forecastData.segments.map((segment: any) => (
                        <div key={segment.name} className="p-3 border rounded">
                          <div className="flex justify-between items-center">
                            <div>
                              <span className="font-medium">{segment.name}</span>
                              <span className="ml-2 text-sm text-gray-500">({segment.type})</span>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold">
                                {formatCurrency(segment.metrics.total_pipeline)}
                              </p>
                              <p className="text-sm text-gray-600">
                                Growth: {(segment.metrics.growth_rate * 100).toFixed(1)}%
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Pipeline Summary */}
                {forecastData.pipeline && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold mb-4">Pipeline Summary</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Total Pipeline</p>
                        <p className="text-xl font-bold">
                          {formatCurrency(forecastData.pipeline.total_pipeline)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Weighted Pipeline</p>
                        <p className="text-xl font-bold">
                          {formatCurrency(forecastData.pipeline.weighted_pipeline)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Conversion Rate</p>
                        <p className="text-xl font-bold">
                          {forecastData.pipeline.conversion_rate.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'streams' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Revenue Streams</h2>
            <div className="space-y-3">
              {revenueStreams?.map((stream) => (
                <div key={stream.id} className="p-4 border rounded">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold">{stream.stream_name}</h3>
                      <p className="text-sm text-gray-600">Code: {stream.stream_code}</p>
                    </div>
                    <div className="flex space-x-2">
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {stream.stream_type}
                      </span>
                      {stream.is_recurring && (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                          {stream.recurring_frequency}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'segments' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Customer Segments</h2>
            <div className="space-y-3">
              {customerSegments?.map((segment) => (
                <div key={segment.id} className="p-4 border rounded">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold">{segment.segment_name}</h3>
                      <p className="text-sm text-gray-600">Type: {segment.segment_type}</p>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Deal Size: </span>
                        {formatCurrency(segment.typical_deal_size || 0)}
                      </div>
                      <div>
                        <span className="text-gray-600">Churn: </span>
                        {((segment.churn_rate || 0) * 100).toFixed(1)}%
                      </div>
                      <div>
                        <span className="text-gray-600">Growth: </span>
                        {((segment.growth_rate || 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'pipeline' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Sales Pipeline</h2>
            <div className="space-y-3">
              {pipelineOpportunities?.map((opp) => (
                <div key={opp.id} className="p-4 border rounded">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-medium">{opp.opportunity_name}</h4>
                      <p className="text-sm text-gray-600">
                        Close Date: {new Date(opp.expected_close_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{formatCurrency(opp.amount)}</p>
                      <p className="text-sm text-gray-600">
                        Weighted: {formatCurrency(opp.weighted_amount)}
                      </p>
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {opp.probability}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Revenue Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Key Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Customer Churn Rate</span>
                    <span className="font-medium">
                      {((revenueMetrics?.recurring_metrics?.churn_rate || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">LTV</span>
                    <span className="font-medium">
                      {formatCurrency(revenueMetrics?.recurring_metrics?.ltv || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Pipeline Conversion</span>
                    <span className="font-medium">
                      {revenueMetrics?.pipeline?.conversion_rate?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Recurring Streams</span>
                    <span className="font-medium">
                      {revenueMetrics?.recurring_metrics?.recurring_streams}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Growth Analysis</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">MoM Growth</span>
                    <span className="font-medium text-green-600">+12.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">QoQ Growth</span>
                    <span className="font-medium text-green-600">+38.2%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">YoY Growth</span>
                    <span className="font-medium text-green-600">+156.4%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">CAGR</span>
                    <span className="font-medium">45.2%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}