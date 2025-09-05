'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { companyApi } from '@/lib/api';
import { analyticsApi } from '@/lib/analytics-api';
import { Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { GaugeChart } from '@/components/charts/GaugeChart';
import { KPICard } from '@/components/charts/KPICard';
import { BarChart } from '@/components/charts/BarChart';
import { LineChart } from '@/components/charts/LineChart';

export default function ExecutiveDashboardPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');

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

  // Fetch real analytics data from backend
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard', selectedCompanyId],
    queryFn: () => analyticsApi.getDashboardData(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: kpiData, isLoading: kpiLoading } = useQuery({
    queryKey: ['kpis', selectedCompanyId],
    queryFn: () => analyticsApi.getKPISummary(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: varianceData, isLoading: varianceLoading } = useQuery({
    queryKey: ['variance', selectedCompanyId],
    queryFn: () => analyticsApi.getVarianceAnalysis(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  // Helper function to check if data is empty
  const hasFinancialData = dashboardData && dashboardData.financial_summary && (
    dashboardData.financial_summary.revenue > 0 ||
    dashboardData.financial_summary.expenses > 0
  );
  
  const hasKpiData = kpiData && kpiData.kpis && kpiData.kpis.length > 0;
  const hasVarianceData = varianceData && varianceData.variances && varianceData.variances.length > 0;
  const hasTrendData = dashboardData && dashboardData.trends && dashboardData.trends.length > 0;

  // Debug logging
  console.log('Debug Dashboard Data:', {
    dashboardData,
    hasFinancialData,
    hasKpiData,
    hasVarianceData,
    hasTrendData,
    kpiCount: kpiData?.kpis?.length,
    varianceCount: varianceData?.variances?.length,
    trendCount: dashboardData?.trends?.length,
    varianceDataStructure: varianceData,
    varianceDataType: typeof varianceData,
    varianceHasVariances: !!varianceData?.variances,
    varianceIsArray: Array.isArray(varianceData?.variances)
  });

  if (!companies || dashboardLoading || kpiLoading || varianceLoading) return <LoadingSpinner />;

  const selectedCompany = companies.find(c => c.id === selectedCompanyId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dir</h1>
          <p className="text-gray-600">Financial performance overview and key metrics</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={selectedCompanyId}
            onChange={(e) => setSelectedCompanyId(e.target.value)}
            className="block border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select Company</option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name}
              </option>
            ))}
          </select>
          
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            Export Report
          </button>
        </div>
      </div>

      {selectedCompany && (
        <>
          {/* Company Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-blue-900">{selectedCompany.name}</h2>
                <p className="text-blue-700">
                  {selectedCompany.code} • {selectedCompany.currency_code} • 
                  Fiscal Year Start: Month {selectedCompany.fiscal_year_start_month}
                </p>
              </div>
              <div className="text-sm text-blue-600">
                Last Updated: {new Date().toLocaleString()}
              </div>
            </div>
          </div>

          {/* Debug Info */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="font-semibold text-yellow-800 mb-2">Debug Info</h3>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div className="font-medium">Financial Data</div>
                <div className={hasFinancialData ? 'text-green-600' : 'text-red-600'}>
                  {hasFinancialData ? '✅ Available' : '❌ Missing'}
                </div>
                {dashboardData?.financial_summary && (
                  <div className="text-xs mt-1">
                    Rev: ${dashboardData.financial_summary.revenue.toFixed(0)}<br/>
                    Exp: ${dashboardData.financial_summary.expenses.toFixed(0)}
                  </div>
                )}
              </div>
              <div>
                <div className="font-medium">KPI Data</div>
                <div className={hasKpiData ? 'text-green-600' : 'text-red-600'}>
                  {hasKpiData ? `✅ ${kpiData?.kpis?.length} KPIs` : '❌ No KPIs'}
                </div>
              </div>
              <div>
                <div className="font-medium">Variance Data</div>
                <div className={hasVarianceData ? 'text-green-600' : 'text-red-600'}>
                  {hasVarianceData ? `✅ ${varianceData?.variances?.length} items` : '❌ No variances'}
                </div>
                <div className="text-xs mt-1">
                  Data: {varianceData ? 'exists' : 'null'}<br/>
                  Array: {Array.isArray(varianceData?.variances) ? 'yes' : 'no'}<br/>
                  Count: {varianceData?.variances?.length || 0}
                </div>
              </div>
              <div>
                <div className="font-medium">Trend Data</div>
                <div className={hasTrendData ? 'text-green-600' : 'text-red-600'}>
                  {hasTrendData ? `✅ ${dashboardData?.trends?.length} periods` : '❌ No trends'}
                </div>
              </div>
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {hasFinancialData ? (
              <>
                <KPICard
                  title="Revenue"
                  value={dashboardData.financial_summary.revenue}
                  target={dashboardData.financial_summary.revenue * 1.1}
                  unit=""
                  trend="up"
                  trendValue={12.5}
                  status={dashboardData.financial_summary.revenue > 500000 ? 'good' : 'warning'}
                  valueFormatter={(val) => `$${(val / 1000).toFixed(0)}K`}
                />
                
                <KPICard
                  title="Expenses"
                  value={dashboardData.financial_summary.expenses}
                  target={dashboardData.financial_summary.expenses * 1.05}
                  unit=""
                  trend="down"
                  trendValue={-5.2}
                  status={dashboardData.financial_summary.expenses < dashboardData.financial_summary.revenue * 0.8 ? 'good' : 'warning'}
                  valueFormatter={(val) => `$${(val / 1000).toFixed(0)}K`}
                />
                
                <KPICard
                  title="Net Profit"
                  value={dashboardData.financial_summary.profit}
                  target={dashboardData.financial_summary.profit * 1.15}
                  unit=""
                  trend="up"
                  trendValue={18.3}
                  status={dashboardData.financial_summary.profit > 150000 ? 'good' : 'warning'}
                  valueFormatter={(val) => `$${(val / 1000).toFixed(0)}K`}
                />
                
                <KPICard
                  title="Profit Margin"
                  value={dashboardData.financial_summary.margin}
                  target={40.0}
                  unit="%"
                  trend="stable"
                  trendValue={2.1}
                  status={dashboardData.financial_summary.margin >= 30 ? 'good' : 'warning'}
                />
              </>
            ) : (
              <>
                <KPICard
                  title="Revenue"
                  value={0}
                  target={0}
                  unit=""
                  trend="stable"
                  trendValue={0}
                  status="warning"
                  valueFormatter={() => "No data"}
                />
                
                <KPICard
                  title="Expenses"
                  value={0}
                  target={0}
                  unit=""
                  trend="stable"
                  trendValue={0}
                  status="warning"
                  valueFormatter={() => "No data"}
                />
                
                <KPICard
                  title="Net Profit"
                  value={0}
                  target={0}
                  unit=""
                  trend="stable"
                  trendValue={0}
                  status="warning"
                  valueFormatter={() => "No data"}
                />
                
                <KPICard
                  title="Profit Margin"
                  value={0}
                  target={0}
                  unit="%"
                  trend="stable"
                  trendValue={0}
                  status="warning"
                />
              </>
            )}
          </div>

          {/* Gauge Charts Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {hasKpiData ? (
              kpiData.kpis.slice(0, 4).map((kpi, index) => (
                <GaugeChart
                  key={index}
                  title={kpi.name}
                  value={kpi.value}
                  max={kpi.target > 100 ? kpi.target : 100}
                  color={
                    kpi.status === 'good' ? 'green' : 
                    kpi.status === 'warning' ? 'yellow' : 
                    kpi.status === 'danger' ? 'red' :
                    kpi.status === 'critical' ? 'red' :
                    'blue'
                  }
                  subtitle={`${kpi.value}${kpi.unit || ''} / ${kpi.target}${kpi.unit || ''}`}
                  size="md"
                />
              ))
            ) : (
              // Show empty gauges when no KPI data
              Array.from({ length: 4 }, (_, index) => (
                <GaugeChart
                  key={index}
                  title={`KPI ${index + 1}`}
                  value={0}
                  max={100}
                  color="gray"
                  subtitle="No data available"
                  size="md"
                />
              ))
            )}
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Variance Chart */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Variance by Category</h3>
              {hasVarianceData ? (
                <BarChart
                  title=""
                  data={varianceData.variances.slice(0, 6).map(v => ({
                    label: v.account_name,
                    value: v.variance,
                    target: 0,
                    color: v.status === 'favorable' ? 'bg-green-500' : 'bg-red-500'
                  }))}
                  valueFormatter={(val) => `$${(val / 1000).toFixed(0)}K`}
                  height={250}
                />
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📊</div>
                    <p>No variance data available</p>
                    <p className="text-sm">Budget and actual data needed</p>
                  </div>
                </div>
              )}
            </div>
            
            {/* Trend Chart */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Trend (YTD)</h3>
              {hasTrendData ? (
                <LineChart
                  title=""
                  data={dashboardData.trends.map(t => ({
                    label: t.month || 'N/A',
                    value: t.revenue || 0,
                    target: (t.revenue || 0) * 1.1 // 10% target above actual
                  }))}
                  showTarget={true}
                  valueFormatter={(val) => `$${(val / 1000).toFixed(0)}K`}
                  height={250}
                  color="rgb(34, 197, 94)" // green-500
                />
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  <div className="text-center">
                    <div className="text-4xl mb-2">📈</div>
                    <p>No trend data available</p>
                    <p className="text-sm">Transaction history needed</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Summary Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Variances */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Variances</h3>
              {hasVarianceData ? (
                <div className="space-y-3">
                  {varianceData.variances
                    .sort((a, b) => Math.abs(b.variance) - Math.abs(a.variance))
                    .slice(0, 5)
                    .map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium text-gray-900">{item.account_name}</div>
                        <div className="text-sm text-gray-600">{item.account_code} • Budget vs Actual</div>
                      </div>
                      <div className={`text-right ${
                        item.status === 'favorable' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        <div className="font-bold">
                          ${Math.abs(item.variance / 1000).toFixed(0)}K
                        </div>
                        <div className="text-xs capitalize">
                          {item.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <div className="text-center">
                    <div className="text-2xl mb-2">📋</div>
                    <p>No variance data available</p>
                    <p className="text-sm">Set up budgets to see variances</p>
                  </div>
                </div>
              )}
            </div>

            {/* Key Insights */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h3>
              {hasFinancialData || hasKpiData || hasVarianceData ? (
                <div className="space-y-4">
                  {hasFinancialData && (
                    <div className="flex items-start space-x-3">
                      <div className={`w-2 h-2 rounded-full mt-2 ${
                        dashboardData.financial_summary.profit > 0 ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                      <div>
                        <div className="font-medium text-gray-900">Financial Performance</div>
                        <div className="text-sm text-gray-600">
                          {dashboardData.financial_summary.profit > 0 
                            ? `Profitable operations with ${dashboardData.financial_summary.margin.toFixed(1)}% margin`
                            : 'Loss-making operations, review cost structure'
                          }
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {hasKpiData && (
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                      <div>
                        <div className="font-medium text-gray-900">KPI Performance</div>
                        <div className="text-sm text-gray-600">
                          {kpiData.kpis.length} KPIs being tracked for performance measurement
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {hasVarianceData && (
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                      <div>
                        <div className="font-medium text-gray-900">Budget Management</div>
                        <div className="text-sm text-gray-600">
                          {varianceData?.variances?.length || 0} account variances available for analysis
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {!hasFinancialData && !hasKpiData && !hasVarianceData && (
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-gray-400 rounded-full mt-2"></div>
                      <div>
                        <div className="font-medium text-gray-900">Getting Started</div>
                        <div className="text-sm text-gray-600">
                          Add transaction data and budgets to generate insights
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-gray-500">
                  <div className="text-center">
                    <div className="text-2xl mb-2">💡</div>
                    <p>No insights available</p>
                    <p className="text-sm">Add financial data to generate insights</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action Items */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-4">Recommended Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Revenue Recovery</h4>
                <p className="text-sm text-gray-600 mb-3">
                  Implement targeted sales initiatives to close $50K revenue gap
                </p>
                <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">High Priority</span>
              </div>
              
              <div className="bg-white p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Cost Optimization</h4>
                <p className="text-sm text-gray-600 mb-3">
                  Reallocate cost savings to growth initiatives and marketing
                </p>
                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">Medium Priority</span>
              </div>
              
              <div className="bg-white p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Forecasting</h4>
                <p className="text-sm text-gray-600 mb-3">
                  Update Q4 forecasts based on current performance trends
                </p>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Low Priority</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
