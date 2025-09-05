'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { companyApi } from '@/lib/api';
import { Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { KPICard } from '@/components/charts/KPICard';
import { GaugeChart } from '@/components/charts/GaugeChart';
import { LineChart } from '@/components/charts/LineChart';
import { BarChart } from '@/components/charts/BarChart';

export default function KPIManagementPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('ytd');

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

  // Mock KPI data for demonstration
  const mockKPIs = [
    {
      id: '1',
      name: 'Monthly Revenue',
      category: 'Financial',
      current: 750000,
      target: 800000,
      unit: '',
      trend: 'up' as const,
      trendValue: 12.5,
      status: 'warning' as const,
      description: 'Total monthly revenue across all streams',
      formula: 'Sum of all revenue accounts',
      lastUpdated: '2024-09-01',
      trend_data: [
        { label: 'Jan', value: 650000 },
        { label: 'Feb', value: 680000 },
        { label: 'Mar', value: 720000 },
        { label: 'Apr', value: 700000 },
        { label: 'May', value: 750000 },
        { label: 'Jun', value: 780000 },
        { label: 'Jul', value: 820000 },
        { label: 'Aug', value: 750000 }
      ]
    },
    {
      id: '2',
      name: 'Gross Margin',
      category: 'Financial',
      current: 36.8,
      target: 40.0,
      unit: '%',
      trend: 'stable' as const,
      trendValue: 0.2,
      status: 'warning' as const,
      description: 'Gross profit as percentage of revenue',
      formula: '(Revenue - COGS) / Revenue * 100',
      lastUpdated: '2024-09-01',
      trend_data: [
        { label: 'Jan', value: 35.2 },
        { label: 'Feb', value: 36.1 },
        { label: 'Mar', value: 37.5 },
        { label: 'Apr', value: 36.8 },
        { label: 'May', value: 38.2 },
        { label: 'Jun', value: 37.9 },
        { label: 'Jul', value: 38.5 },
        { label: 'Aug', value: 36.8 }
      ]
    },
    {
      id: '3',
      name: 'Customer Acquisition Cost',
      category: 'Marketing',
      current: 85,
      target: 75,
      unit: '',
      trend: 'down' as const,
      trendValue: -5.8,
      status: 'danger' as const,
      description: 'Average cost to acquire a new customer',
      formula: 'Marketing Spend / New Customers',
      lastUpdated: '2024-09-01',
      trend_data: [
        { label: 'Jan', value: 90 },
        { label: 'Feb', value: 88 },
        { label: 'Mar', value: 82 },
        { label: 'Apr', value: 86 },
        { label: 'May', value: 79 },
        { label: 'Jun', value: 83 },
        { label: 'Jul', value: 87 },
        { label: 'Aug', value: 85 }
      ]
    },
    {
      id: '4',
      name: 'Employee Productivity',
      category: 'Operations',
      current: 92.3,
      target: 90.0,
      unit: '%',
      trend: 'up' as const,
      trendValue: 8.5,
      status: 'good' as const,
      description: 'Overall employee productivity index',
      formula: 'Output / Target Output * 100',
      lastUpdated: '2024-09-01',
      trend_data: [
        { label: 'Jan', value: 88.5 },
        { label: 'Feb', value: 89.2 },
        { label: 'Mar', value: 91.1 },
        { label: 'Apr', value: 90.8 },
        { label: 'May', value: 92.5 },
        { label: 'Jun', value: 91.9 },
        { label: 'Jul', value: 93.2 },
        { label: 'Aug', value: 92.3 }
      ]
    },
    {
      id: '5',
      name: 'Cash Flow Ratio',
      category: 'Financial',
      current: 1.85,
      target: 2.0,
      unit: 'x',
      trend: 'stable' as const,
      trendValue: 1.2,
      status: 'warning' as const,
      description: 'Current cash flow to obligations ratio',
      formula: 'Operating Cash Flow / Current Liabilities',
      lastUpdated: '2024-09-01',
      trend_data: [
        { label: 'Jan', value: 1.65 },
        { label: 'Feb', value: 1.72 },
        { label: 'Mar', value: 1.88 },
        { label: 'Apr', value: 1.79 },
        { label: 'May', value: 1.92 },
        { label: 'Jun', value: 1.86 },
        { label: 'Jul', value: 1.91 },
        { label: 'Aug', value: 1.85 }
      ]
    },
    {
      id: '6',
      name: 'Customer Satisfaction',
      category: 'Customer',
      current: 4.3,
      target: 4.5,
      unit: '/5',
      trend: 'up' as const,
      trendValue: 2.4,
      status: 'warning' as const,
      description: 'Average customer satisfaction score',
      formula: 'Average of customer survey ratings',
      lastUpdated: '2024-09-01',
      trend_data: [
        { label: 'Jan', value: 4.1 },
        { label: 'Feb', value: 4.2 },
        { label: 'Mar', value: 4.4 },
        { label: 'Apr', value: 4.2 },
        { label: 'May', value: 4.5 },
        { label: 'Jun', value: 4.3 },
        { label: 'Jul', value: 4.4 },
        { label: 'Aug', value: 4.3 }
      ]
    }
  ];

  const categories = ['all', 'Financial', 'Marketing', 'Operations', 'Customer'];
  
  const filteredKPIs = selectedCategory === 'all' 
    ? mockKPIs 
    : mockKPIs.filter(kpi => kpi.category === selectedCategory);

  // Performance summary
  const performanceSummary = {
    onTarget: mockKPIs.filter(kpi => kpi.status === 'good').length,
    warning: mockKPIs.filter(kpi => kpi.status === 'warning').length,
    danger: mockKPIs.filter(kpi => kpi.status === 'danger').length,
    total: mockKPIs.length
  };

  const categoryPerformance = categories.slice(1).map(category => {
    const categoryKPIs = mockKPIs.filter(kpi => kpi.category === category);
    const onTarget = categoryKPIs.filter(kpi => kpi.status === 'good').length;
    return {
      label: category,
      value: categoryKPIs.length > 0 ? (onTarget / categoryKPIs.length) * 100 : 0,
      target: 85,
      color: onTarget / categoryKPIs.length >= 0.8 ? 'bg-green-500' : 
             onTarget / categoryKPIs.length >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
    };
  });

  if (!companies) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">KPI Management</h1>
          <p className="text-gray-600">Monitor and track key performance indicators</p>
        </div>
        
        <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          Add New KPI
        </button>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Time Range</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="mtd">Month to Date</option>
              <option value="qtd">Quarter to Date</option>
              <option value="ytd">Year to Date</option>
              <option value="12m">Last 12 Months</option>
            </select>
          </div>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-500">Total KPIs</h3>
              <div className="text-2xl font-bold text-gray-900">{performanceSummary.total}</div>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600">📊</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-500">On Target</h3>
              <div className="text-2xl font-bold text-green-600">{performanceSummary.onTarget}</div>
              <div className="text-xs text-gray-500 mt-1">
                {((performanceSummary.onTarget / performanceSummary.total) * 100).toFixed(0)}%
              </div>
            </div>
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-green-600">✅</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-500">Warning</h3>
              <div className="text-2xl font-bold text-yellow-600">{performanceSummary.warning}</div>
              <div className="text-xs text-gray-500 mt-1">
                {((performanceSummary.warning / performanceSummary.total) * 100).toFixed(0)}%
              </div>
            </div>
            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
              <span className="text-yellow-600">⚠️</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-500">Critical</h3>
              <div className="text-2xl font-bold text-red-600">{performanceSummary.danger}</div>
              <div className="text-xs text-gray-500 mt-1">
                {((performanceSummary.danger / performanceSummary.total) * 100).toFixed(0)}%
              </div>
            </div>
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <span className="text-red-600">🚨</span>
            </div>
          </div>
        </div>
      </div>

      {/* Category Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChart
          title="Performance by Category"
          data={categoryPerformance}
          valueFormatter={(val) => `${val.toFixed(0)}%`}
          height={300}
          showTargets={true}
        />

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Gauges</h3>
          <div className="grid grid-cols-2 gap-4">
            {categoryPerformance.map((category, index) => (
              <GaugeChart
                key={index}
                title={category.label}
                value={category.value}
                max={100}
                color={category.value >= 80 ? 'green' : category.value >= 60 ? 'yellow' : 'red'}
                subtitle={`${category.value.toFixed(0)}%`}
                size="sm"
              />
            ))}
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredKPIs.map((kpi) => (
          <KPICard
            key={kpi.id}
            title={kpi.name}
            value={kpi.current}
            target={kpi.target}
            unit={kpi.unit}
            trend={kpi.trend}
            trendValue={kpi.trendValue}
            status={kpi.status}
            valueFormatter={kpi.unit === '%' ? (val) => val.toFixed(1) : 
                           kpi.unit === '' && kpi.current >= 1000 ? (val) => `$${(val/1000).toFixed(0)}K` :
                           (val) => val.toFixed(kpi.unit === 'x' || kpi.unit === '/5' ? 2 : 0)}
          />
        ))}
      </div>

      {/* Detailed KPI Table */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">KPI Details</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  KPI Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Target
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trend
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Updated
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredKPIs.map((kpi) => (
                <tr key={kpi.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{kpi.name}</div>
                    <div className="text-sm text-gray-500">{kpi.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {kpi.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {kpi.unit === '%' ? kpi.current.toFixed(1) : 
                     kpi.unit === '' && kpi.current >= 1000 ? `$${(kpi.current/1000).toFixed(0)}K` :
                     kpi.current.toFixed(kpi.unit === 'x' || kpi.unit === '/5' ? 2 : 0)}{kpi.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {kpi.unit === '%' ? kpi.target.toFixed(1) : 
                     kpi.unit === '' && kpi.target >= 1000 ? `$${(kpi.target/1000).toFixed(0)}K` :
                     kpi.target.toFixed(kpi.unit === 'x' || kpi.unit === '/5' ? 2 : 0)}{kpi.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      kpi.status === 'good' ? 'bg-green-100 text-green-800' :
                      kpi.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {kpi.status === 'good' ? 'On Target' : 
                       kpi.status === 'warning' ? 'Warning' : 'Critical'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className={`flex items-center ${
                      kpi.trend === 'up' ? 'text-green-600' :
                      kpi.trend === 'down' ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      <span className="mr-1">
                        {kpi.trend === 'up' ? '↗' : kpi.trend === 'down' ? '↘' : '→'}
                      </span>
                      {Math.abs(kpi.trendValue).toFixed(1)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(kpi.lastUpdated).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trends for Selected KPIs */}
      {filteredKPIs.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredKPIs.slice(0, 2).map((kpi) => (
            <LineChart
              key={kpi.id}
              title={`${kpi.name} Trend`}
              data={kpi.trend_data}
              showTarget={false}
              valueFormatter={(val) => 
                kpi.unit === '%' ? `${val.toFixed(1)}%` :
                kpi.unit === '' && val >= 1000 ? `$${(val/1000).toFixed(0)}K` :
                `${val.toFixed(kpi.unit === 'x' || kpi.unit === '/5' ? 2 : 0)}${kpi.unit}`
              }
              height={250}
              color={kpi.status === 'good' ? 'rgb(34, 197, 94)' : 
                     kpi.status === 'warning' ? 'rgb(234, 179, 8)' : 
                     'rgb(239, 68, 68)'}
            />
          ))}
        </div>
      )}
    </div>
  );
}