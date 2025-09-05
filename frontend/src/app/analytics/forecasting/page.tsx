'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { companyApi } from '@/lib/api';
import { Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { LineChart } from '@/components/charts/LineChart';
import { BarChart } from '@/components/charts/BarChart';
import { GaugeChart } from '@/components/charts/GaugeChart';
import { KPICard } from '@/components/charts/KPICard';

export default function ForecastingPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [selectedModel, setSelectedModel] = useState<string>('linear-regression');
  const [forecastPeriod, setForecastPeriod] = useState<string>('6-months');
  const [selectedMetric, setSelectedMetric] = useState<string>('revenue');

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

  // Mock forecasting data for demonstration
  const mockHistoricalData = [
    { label: 'Jan 2024', value: 650000, forecast: null, confidence: null },
    { label: 'Feb 2024', value: 680000, forecast: null, confidence: null },
    { label: 'Mar 2024', value: 720000, forecast: null, confidence: null },
    { label: 'Apr 2024', value: 700000, forecast: null, confidence: null },
    { label: 'May 2024', value: 750000, forecast: null, confidence: null },
    { label: 'Jun 2024', value: 780000, forecast: null, confidence: null },
    { label: 'Jul 2024', value: 820000, forecast: null, confidence: null },
    { label: 'Aug 2024', value: 750000, forecast: null, confidence: null }
  ];

  const mockForecastData = [
    { label: 'Sep 2024', value: null, forecast: 785000, confidence: 0.85 },
    { label: 'Oct 2024', value: null, forecast: 810000, confidence: 0.82 },
    { label: 'Nov 2024', value: null, forecast: 835000, confidence: 0.78 },
    { label: 'Dec 2024', value: null, forecast: 860000, confidence: 0.75 },
    { label: 'Jan 2025', value: null, forecast: 890000, confidence: 0.72 },
    { label: 'Feb 2025', value: null, forecast: 920000, confidence: 0.68 }
  ];

  const combinedChartData = [...mockHistoricalData, ...mockForecastData].map(item => ({
    label: item.label,
    value: item.value || item.forecast || 0,
    target: item.forecast ? item.forecast * 1.1 : item.value ? item.value * 1.05 : 0,
    isForecast: item.forecast !== null
  }));

  const mockModelAccuracy = [
    { label: 'Linear Regression', value: 85, max: 100, color: 'blue' as const },
    { label: 'ARIMA', value: 78, max: 100, color: 'green' as const },
    { label: 'Random Forest', value: 82, max: 100, color: 'purple' as const },
    { label: 'Neural Network', value: 88, max: 100, color: 'yellow' as const }
  ];

  const mockScenarios = [
    {
      scenario: 'Optimistic',
      probability: 25,
      revenue: 950000,
      growth: 18.5,
      confidence: 0.65,
      color: 'bg-green-500'
    },
    {
      scenario: 'Most Likely',
      probability: 50,
      revenue: 820000,
      growth: 12.3,
      confidence: 0.85,
      color: 'bg-blue-500'
    },
    {
      scenario: 'Pessimistic',
      probability: 25,
      revenue: 680000,
      growth: 6.1,
      confidence: 0.75,
      color: 'bg-red-500'
    }
  ];

  const mockSeasonalityData = [
    { label: 'Q1', value: 15, target: 20, color: 'bg-blue-500' },
    { label: 'Q2', value: 25, target: 25, color: 'bg-green-500' },
    { label: 'Q3', value: 35, target: 30, color: 'bg-purple-500' },
    { label: 'Q4', value: 45, target: 40, color: 'bg-orange-500' }
  ];

  const mockDriversData = [
    { 
      driver: 'Market Expansion',
      impact: 15.2,
      confidence: 0.82,
      trend: 'up' as const,
      description: 'New market penetration driving growth'
    },
    {
      driver: 'Seasonal Trends', 
      impact: -8.7,
      confidence: 0.91,
      trend: 'down' as const,
      description: 'Holiday season revenue dip expected'
    },
    {
      driver: 'Product Launch',
      impact: 22.4,
      confidence: 0.76,
      trend: 'up' as const,
      description: 'New product line launch impact'
    },
    {
      driver: 'Economic Factors',
      impact: -5.1,
      confidence: 0.68,
      trend: 'down' as const,
      description: 'Economic headwinds affecting demand'
    }
  ];

  if (!companies) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Forecasting & Planning</h1>
          <p className="text-gray-600">Statistical forecasting and predictive analytics for strategic planning</p>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="linear-regression">Linear Regression</option>
              <option value="arima">ARIMA</option>
              <option value="random-forest">Random Forest</option>
              <option value="neural-network">Neural Network</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Forecast Period</label>
            <select
              value={forecastPeriod}
              onChange={(e) => setForecastPeriod(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="3-months">3 Months</option>
              <option value="6-months">6 Months</option>
              <option value="12-months">12 Months</option>
              <option value="24-months">24 Months</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Metric</label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="revenue">Revenue</option>
              <option value="expenses">Expenses</option>
              <option value="profit">Net Profit</option>
              <option value="cash-flow">Cash Flow</option>
            </select>
          </div>
        </div>
      </div>

      {/* Forecast Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <KPICard
          title="Forecast Accuracy"
          value={85}
          target={90}
          unit="%"
          trend="up"
          trendValue={3.2}
          status="good"
        />
        
        <KPICard
          title="Confidence Level"
          value={82}
          target={85}
          unit="%"
          trend="stable"
          trendValue={0.5}
          status="warning"
        />
        
        <KPICard
          title="Next Period Forecast"
          value={785000}
          target={800000}
          trend="up"
          trendValue={4.7}
          status="good"
          valueFormatter={(val) => `$${(val / 1000).toFixed(0)}K`}
        />
        
        <KPICard
          title="Forecast Error (MAPE)"
          value={12.3}
          target={10.0}
          unit="%"
          trend="down"
          trendValue={-1.8}
          status="warning"
        />
      </div>

      {/* Main Forecast Chart */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Historical Data & Forecast</h3>
        <div className="mb-4">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded mr-2"></div>
              <span>Historical Data</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
              <span>Forecast</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-300 rounded mr-2"></div>
              <span>Confidence Interval</span>
            </div>
          </div>
        </div>
        <LineChart
          title=""
          data={combinedChartData}
          valueFormatter={(val) => `$${(val / 1000).toFixed(0)}K`}
          height={400}
          color="rgb(59, 130, 246)"
          showTarget={true}
        />
      </div>

      {/* Model Performance & Scenarios */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Accuracy */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Accuracy</h3>
          <div className="grid grid-cols-2 gap-4">
            {mockModelAccuracy.map((model, index) => (
              <GaugeChart
                key={index}
                title={model.label}
                value={model.value}
                max={model.max}
                color={model.color}
                subtitle={`${model.value}% accuracy`}
                size="sm"
              />
            ))}
          </div>
        </div>

        {/* Scenario Analysis */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Scenario Analysis</h3>
          <div className="space-y-4">
            {mockScenarios.map((scenario, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 ${scenario.color} rounded-full mr-3`}></div>
                    <h4 className="font-medium text-gray-900">{scenario.scenario}</h4>
                  </div>
                  <span className="text-sm text-gray-500">{scenario.probability}% probability</span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Revenue: </span>
                    <span className="font-medium">${(scenario.revenue / 1000).toFixed(0)}K</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Growth: </span>
                    <span className="font-medium">{scenario.growth}%</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Confidence: </span>
                    <span className="font-medium">{(scenario.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Seasonality & Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChart
          title="Seasonal Patterns (% of Annual Revenue)"
          data={mockSeasonalityData}
          valueFormatter={(val) => `${val}%`}
          height={300}
          showTargets={true}
        />

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Forecast Drivers</h3>
          <div className="space-y-4">
            {mockDriversData.map((driver, index) => (
              <div key={index} className="border-l-4 border-blue-200 pl-4 py-2">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-medium text-gray-900">{driver.driver}</h4>
                  <div className="flex items-center space-x-2">
                    <span className={`text-sm font-medium ${
                      driver.impact > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {driver.impact > 0 ? '+' : ''}{driver.impact}%
                    </span>
                    <span className="text-sm text-gray-500">
                      ({(driver.confidence * 100).toFixed(0)}% conf.)
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-600">{driver.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Forecast Summary Table */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Detailed Forecast</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Period
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Forecast
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lower Bound
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Upper Bound
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Level
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mockForecastData.map((item, index) => {
                const lowerBound = item.forecast! * (1 - (1 - item.confidence!) * 0.3);
                const upperBound = item.forecast! * (1 + (1 - item.confidence!) * 0.3);
                const riskLevel = item.confidence! > 0.8 ? 'Low' : item.confidence! > 0.7 ? 'Medium' : 'High';
                const riskColor = item.confidence! > 0.8 ? 'text-green-600 bg-green-50 border-green-200' :
                                  item.confidence! > 0.7 ? 'text-yellow-600 bg-yellow-50 border-yellow-200' :
                                  'text-red-600 bg-red-50 border-red-200';
                
                return (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.label}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      ${item.forecast!.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                      ${lowerBound.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                      ${upperBound.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      {(item.confidence! * 100).toFixed(0)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full border ${riskColor}`}>
                        {riskLevel}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-purple-900 mb-4">Strategic Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-purple-800 mb-3">Model Insights</h4>
            <ul className="space-y-2 text-sm text-purple-700">
              <li className="flex items-start">
                <span className="w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                Linear regression shows strong correlation with market expansion
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                Seasonal patterns indicate Q4 revenue boost opportunity
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                Neural network model suggests product launch timing is critical
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-purple-800 mb-3">Action Items</h4>
            <ul className="space-y-2 text-sm text-purple-700">
              <li className="flex items-start">
                <span className="w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                Accelerate market expansion initiatives in Q1 2025
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                Prepare contingency plans for pessimistic scenario
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-3 flex-shrink-0"></span>
                Monitor economic indicators closely for model recalibration
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}