'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { companyApi } from '@/lib/api';
import { expensePlanningApi, type ExpenseForecastRequest, type ExpenseForecastMethod } from '@/lib/expense-planning-api';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { LineChart } from '@/components/charts/LineChart';
import { BarChart } from '@/components/charts/BarChart';
import toast from 'react-hot-toast';

export default function ExpensePlanningPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [selectedMethod, setSelectedMethod] = useState<ExpenseForecastMethod['method']>('incremental');
  const [forecastMonths, setForecastMonths] = useState(12);
  const [growthRate, setGrowthRate] = useState(0.03);
  const [inflationRate, setInflationRate] = useState(0.02);
  const [costReductionTarget, setCostReductionTarget] = useState<number | undefined>();
  const [activeTab, setActiveTab] = useState<'forecast' | 'categories' | 'contracts' | 'variance'>('forecast');

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyApi.getAll(),
  });

  const { data: expenseMetrics } = useQuery({
    queryKey: ['expense-metrics', selectedCompanyId],
    queryFn: () => expensePlanningApi.getExpenseMetrics(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: categories } = useQuery({
    queryKey: ['expense-categories', selectedCompanyId],
    queryFn: () => expensePlanningApi.getCategories(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: contracts } = useQuery({
    queryKey: ['expense-contracts', selectedCompanyId],
    queryFn: () => expensePlanningApi.getContracts(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  // Set default company
  useEffect(() => {
    if (!selectedCompanyId && companies && companies.length > 0) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  const forecastMutation = useMutation({
    mutationFn: (params: ExpenseForecastRequest) => expensePlanningApi.generateForecast(params),
    onSuccess: () => {
      toast.success('Expense forecast generated successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to generate forecast');
    },
  });

  const handleGenerateForecast = () => {
    if (!selectedCompanyId) return;

    const request: ExpenseForecastRequest = {
      company_id: selectedCompanyId,
      forecast_months: forecastMonths,
      method: {
        method: selectedMethod,
        growth_rate: growthRate,
        inflation_rate: inflationRate,
        cost_reduction_target: costReductionTarget,
      },
      include_contracts: true,
      include_categories: true,
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
          <h1 className="text-2xl font-bold text-gray-900">💵 Expense Planning</h1>
          <p className="text-gray-600 mt-1">
            Plan and forecast expenses using various budgeting methods
          </p>
        </div>
      </div>

      {/* Company Selection & Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Company
          </label>
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a company...</option>
            {companies?.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name}
              </option>
            ))}
          </select>
        </div>

        {expenseMetrics && (
          <>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">Current Month</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(expenseMetrics.current_month_expense)}
                  </p>
                </div>
                <div className="text-2xl">📊</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">YTD Expenses</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(expenseMetrics.ytd_expense)}
                  </p>
                </div>
                <div className="text-2xl">📈</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-gray-600">Run Rate</p>
                  <p className="text-lg font-bold text-gray-900">
                    {formatCurrency(expenseMetrics.expense_run_rate)}
                  </p>
                </div>
                <div className="text-2xl">🎯</div>
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
            { id: 'categories', label: 'Categories', icon: '📁' },
            { id: 'contracts', label: 'Contracts', icon: '📄' },
            { id: 'variance', label: 'Variance', icon: '📉' },
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
              <span className="mr-1">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'forecast' && (
        <div className="space-y-6">
          {/* Forecasting Controls */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Configuration</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Budgeting Method
                </label>
                <select
                  value={selectedMethod}
                  onChange={(e) => setSelectedMethod(e.target.value as any)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="incremental">Incremental</option>
                  <option value="zero_based">Zero-Based</option>
                  <option value="driver_based">Driver-Based</option>
                  <option value="activity_based">Activity-Based</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Forecast Months
                </label>
                <input
                  type="number"
                  value={forecastMonths}
                  onChange={(e) => setForecastMonths(parseInt(e.target.value))}
                  min="1"
                  max="36"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>

              {selectedMethod === 'incremental' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Growth Rate (%)
                    </label>
                    <input
                      type="number"
                      value={growthRate * 100}
                      onChange={(e) => setGrowthRate(parseFloat(e.target.value) / 100)}
                      step="0.1"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Inflation Rate (%)
                    </label>
                    <input
                      type="number"
                      value={inflationRate * 100}
                      onChange={(e) => setInflationRate(parseFloat(e.target.value) / 100)}
                      step="0.1"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cost Reduction Target (% - Optional)
              </label>
              <input
                type="number"
                value={costReductionTarget ? costReductionTarget * 100 : ''}
                onChange={(e) => setCostReductionTarget(e.target.value ? parseFloat(e.target.value) / 100 : undefined)}
                placeholder="Enter percentage (e.g., 5 for 5% reduction)"
                step="0.1"
                className="w-full max-w-xs border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
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
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg shadow-sm border p-4">
                  <h4 className="text-sm font-medium text-gray-600 mb-2">Total Forecast</h4>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(forecastData.total_forecast)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {forecastData.forecast_data.length} month projection
                  </p>
                </div>

                <div className="bg-white rounded-lg shadow-sm border p-4">
                  <h4 className="text-sm font-medium text-gray-600 mb-2">Method Used</h4>
                  <p className="text-lg font-semibold text-gray-900 capitalize">
                    {forecastData.method.replace('_', ' ')}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Budgeting approach
                  </p>
                </div>

                {forecastData.contract_obligations && (
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">Contract Obligations</h4>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(forecastData.contract_obligations.total_obligation)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {forecastData.contract_obligations.contract_count} active contracts
                    </p>
                  </div>
                )}
              </div>

              {/* Forecast Chart */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Expense Forecast Trend</h3>
                <LineChart
                  data={forecastData.forecast_data.map(d => ({
                    label: d.period,
                    value: d.forecast_amount || d.total_cost || 0,
                  }))}
                  height={300}
                  color="#ef4444"
                />
              </div>

              {/* Category Breakdown */}
              {forecastData.category_breakdown && forecastData.category_breakdown.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h3>
                  <BarChart
                    data={forecastData.category_breakdown.map(c => ({
                      label: c.category,
                      value: c.total,
                    }))}
                    height={300}
                    color="#f59e0b"
                  />
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'categories' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Expense Categories</h3>
          
          {categories && categories.length > 0 ? (
            <div className="space-y-2">
              {categories.map((category) => (
                <div
                  key={category.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                  style={{ marginLeft: `${(category.level || 0) * 20}px` }}
                >
                  <div>
                    <span className="font-medium text-gray-900">{category.category_name}</span>
                    <span className="ml-2 text-sm text-gray-500">({category.category_code})</span>
                    <div className="flex gap-4 mt-1">
                      <span className="text-xs text-gray-600">Type: {category.category_type}</span>
                      {category.is_controllable && (
                        <span className="text-xs text-green-600">Controllable</span>
                      )}
                      {category.is_discretionary && (
                        <span className="text-xs text-yellow-600">Discretionary</span>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    Typical Variance: ±{category.typical_variance_pct}%
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No categories defined yet.</p>
          )}
        </div>
      )}

      {activeTab === 'contracts' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Vendor Contracts</h3>
          
          {contracts && contracts.contracts && contracts.contracts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Contract</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Monthly</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {contracts.contracts.map((contract: any) => (
                    <tr key={contract.id}>
                      <td className="px-4 py-2 text-sm text-gray-900">{contract.contract_name}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">{contract.vendor_name}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">{contract.contract_type}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{formatCurrency(contract.monthly_amount)}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          contract.contract_status === 'active' ? 'bg-green-100 text-green-800' :
                          contract.contract_status === 'expiring_soon' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {contract.contract_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500">No contracts found.</p>
          )}
        </div>
      )}

      {activeTab === 'variance' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Variance Analysis</h3>
          <p className="text-gray-500">Variance analysis will show actual vs planned expenses once data is available.</p>
        </div>
      )}
    </div>
  );
}