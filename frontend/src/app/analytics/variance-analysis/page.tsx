'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { companyApi } from '@/lib/api';
import { analyticsApi } from '@/lib/analytics-api';
import { Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { BarChart } from '@/components/charts/BarChart';
import { LineChart } from '@/components/charts/LineChart';

export default function VarianceAnalysisPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('2024-08');
  const [viewType, setViewType] = useState<'summary' | 'detailed'>('summary');
  const [filterType, setFilterType] = useState<string>('all');

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const companies = await companyApi.getAll();
      return companies;
    },
  });

  useEffect(() => {
    if (!selectedCompanyId && companies && companies.length > 0) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);

  // Fetch real variance data from backend
  const { data: varianceData, isLoading: varianceLoading } = useQuery({
    queryKey: ['variance', selectedCompanyId],
    queryFn: () => analyticsApi.getVarianceAnalysis(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const hasVarianceData = varianceData && varianceData.variances && varianceData.variances.length > 0;

  // Calculate summary statistics from variance data
  const summary = hasVarianceData ? {
    total_budget: varianceData.total_budget || varianceData.variances.reduce((sum, v) => sum + v.budget, 0),
    total_actual: varianceData.total_actual || varianceData.variances.reduce((sum, v) => sum + v.actual, 0),
    total_variance: varianceData.total_variance || varianceData.variances.reduce((sum, v) => sum + v.variance, 0),
    favorable_count: varianceData.variances.filter(v => v.status === 'favorable').length,
    unfavorable_count: varianceData.variances.filter(v => v.status === 'unfavorable').length,
    largest_variance: varianceData.variances.reduce((max, v) => 
      Math.abs(v.variance) > Math.abs(max?.variance || 0) ? v : max, null)
  } : null;

  if (!companies) return <LoadingSpinner />;

  const filteredData = hasVarianceData 
    ? (filterType === 'all' 
        ? varianceData.variances 
        : varianceData.variances.filter(item => item.account_type === filterType))
    : [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'favorable': return 'text-green-600 bg-green-50 border-green-200';
      case 'unfavorable': return 'text-red-600 bg-red-50 border-red-200';
      case 'neutral': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Variance Analysis</h1>
          <p className="text-gray-600">Budget vs Actual analysis with detailed insights</p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Company</label>
            <select
              value={selectedCompanyId}
              onChange={(e) => setSelectedCompanyId(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select Company</option>
              {companies?.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Period</label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="2024-08">August 2024</option>
              <option value="2024-07">July 2024</option>
              <option value="2024-06">June 2024</option>
              <option value="2024-05">May 2024</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Account Type</label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="revenue">Revenue</option>
              <option value="expense">Expense</option>
              <option value="asset">Asset</option>
              <option value="liability">Liability</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">View</label>
            <div className="flex space-x-2">
              <button
                onClick={() => setViewType('summary')}
                className={`px-3 py-2 text-sm rounded-md ${
                  viewType === 'summary'
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'bg-gray-100 text-gray-700 border border-gray-300'
                }`}
              >
                Summary
              </button>
              <button
                onClick={() => setViewType('detailed')}
                className={`px-3 py-2 text-sm rounded-md ${
                  viewType === 'detailed'
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'bg-gray-100 text-gray-700 border border-gray-300'
                }`}
              >
                Detailed
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Variance</h3>
          {hasVarianceData ? (
            <>
              <div className={`text-2xl font-bold ${(summary?.total_variance || 0) < 0 ? 'text-red-600' : 'text-green-600'}`}>
                {(summary?.total_variance || 0) < 0 ? '-' : '+'}$
                {Math.abs(summary?.total_variance || 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {summary?.total_budget ? 
                  Math.abs(((summary?.total_variance || 0) / summary.total_budget) * 100).toFixed(1) : 
                  0}% 
                {(summary?.total_variance || 0) < 0 ? ' unfavorable' : ' favorable'}
              </div>
            </>
          ) : (
            <>
              <div className="text-2xl font-bold text-gray-400">No data</div>
              <div className="text-sm text-gray-400 mt-1">Budget data needed</div>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Favorable Variances</h3>
          {hasVarianceData ? (
            <>
              <div className="text-2xl font-bold text-green-600">{summary?.favorable_count || 0}</div>
              <div className="text-sm text-gray-600 mt-1">
                {filteredData.length > 0 ? Math.round(((summary?.favorable_count || 0) / filteredData.length) * 100) : 0}% of accounts
              </div>
            </>
          ) : (
            <>
              <div className="text-2xl font-bold text-gray-400">No data</div>
              <div className="text-sm text-gray-400 mt-1">Variance analysis needed</div>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Largest Variance</h3>
          {hasVarianceData && summary?.largest_variance ? (
            <>
              <div className={`text-2xl font-bold ${summary.largest_variance.variance < 0 ? 'text-red-600' : 'text-green-600'}`}>
                {summary.largest_variance.variance < 0 ? '-' : '+'}$
                {Math.abs(summary.largest_variance.variance).toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mt-1">{summary.largest_variance.account_name}</div>
            </>
          ) : (
            <>
              <div className="text-2xl font-bold text-gray-400">No data</div>
              <div className="text-sm text-gray-400 mt-1">Account data needed</div>
            </>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Variance Trend</h3>
          <div className="text-2xl font-bold text-gray-400">No data</div>
          <div className="text-sm text-gray-400 mt-1">Historical data needed</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {hasVarianceData ? (
          <BarChart
            title="Variance by Account Type"
            data={varianceData.by_account_type || []}
            valueFormatter={(val) => `$${(val / 1000).toFixed(1)}K`}
            height={300}
          />
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Variance by Account Type</h3>
            <div className="flex items-center justify-center h-64 text-gray-500">
              <div className="text-center">
                <div className="text-4xl mb-2">📊</div>
                <p>No variance data available</p>
                <p className="text-sm">Budget and actual data needed</p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Variance Trend (YTD)</h3>
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <div className="text-4xl mb-2">📈</div>
              <p>No trend data available</p>
              <p className="text-sm">Historical data needed</p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {viewType === 'summary' ? 'Variance Summary' : 'Detailed Variance Analysis'}
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actual
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Budget
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Variance
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Variance %
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                {viewType === 'detailed' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Explanation
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredData.length > 0 ? (
                filteredData.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{item.account_name || item.account}</div>
                      <div className="text-sm text-gray-500 capitalize">{item.account_type || item.accountType}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      ${(item.actual || 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      ${(item.budget || 0).toLocaleString()}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${
                      (item.variance || 0) < 0 
                        ? ((item.account_type || item.accountType) === 'expense' ? 'text-green-600' : 'text-red-600')
                        : ((item.account_type || item.accountType) === 'expense' ? 'text-red-600' : 'text-green-600')
                    }`}>
                      {(item.variance || 0) < 0 ? '-' : '+'}${Math.abs(item.variance || 0).toLocaleString()}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${
                      (item.variance || 0) < 0 
                        ? ((item.account_type || item.accountType) === 'expense' ? 'text-green-600' : 'text-red-600')
                        : ((item.account_type || item.accountType) === 'expense' ? 'text-red-600' : 'text-green-600')
                    }`}>
                      {Math.abs(item.variance_percent || item.variancePercent || 0).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${getStatusColor(item.status || 'neutral')}`}>
                        {item.status || 'neutral'}
                      </span>
                    </td>
                    {viewType === 'detailed' && (
                      <td className="px-6 py-4 text-sm text-gray-600 max-w-xs">
                        {item.explanation || 'No explanation available'}
                      </td>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={viewType === 'detailed' ? 7 : 6} className="px-6 py-12 text-center">
                    <div className="text-gray-500">
                      <div className="text-4xl mb-4">📊</div>
                      <h4 className="text-lg font-medium text-gray-900 mb-2">No variance data available</h4>
                      <p className="text-gray-600 mb-4">
                        To see variance analysis, you need budget and actual transaction data for the selected period.
                      </p>
                      <div className="text-sm text-gray-500 space-y-1">
                        <p>• Set up budget lines for accounts</p>
                        <p>• Record actual transactions</p>
                        <p>• Generate sample data using the main analytics page</p>
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Items */}
      {hasVarianceData ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Analysis Insights & Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-blue-800 mb-3">Key Findings</h4>
              <ul className="space-y-2 text-sm text-blue-700">
                {varianceData.insights?.key_findings?.map((finding, index) => (
                  <li key={index} className="flex items-start">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                    {finding}
                  </li>
                )) || (
                  <li className="flex items-start">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                    Analysis results will appear here when variance data is available
                  </li>
                )}
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-blue-800 mb-3">Recommended Actions</h4>
              <ul className="space-y-2 text-sm text-blue-700">
                {varianceData.insights?.recommended_actions?.map((action, index) => (
                  <li key={index} className="flex items-start">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                    {action}
                  </li>
                )) || (
                  <li className="flex items-start">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                    Actionable insights will be generated based on your variance analysis
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">💡 Get Started with Variance Analysis</h3>
          <div className="text-sm text-gray-600 space-y-3">
            <p>Variance analysis helps you understand the differences between your budgeted and actual performance:</p>
            <ul className="space-y-2 ml-4">
              <li className="flex items-start">
                <span className="w-2 h-2 bg-gray-400 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                <strong>Set up budgets:</strong> Create budget lines for your accounts
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-gray-400 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                <strong>Record transactions:</strong> Enter actual financial transactions
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-gray-400 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                <strong>Generate insights:</strong> The system will automatically analyze variances and provide actionable insights
              </li>
            </ul>
            <p className="pt-2">
              <strong>Quick start:</strong> Use the sample data generator on the main Analytics page to populate your system with realistic data.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}