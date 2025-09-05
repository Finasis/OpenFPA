'use client';

import Link from 'next/link';

const analyticsModules = [
  {
    id: 'executive-dashboard',
    title: 'Executive Dashboard',
    description: 'High-level financial performance overview with KPIs, variance analysis, and trends',
    icon: '📊',
    href: '/analytics/executive-dashboard',
    features: ['Financial Summary', 'KPI Performance', 'Variance Analysis', 'Trend Charts']
  },
  {
    id: 'variance-analysis', 
    title: 'Variance Analysis',
    description: 'Budget vs Actual analysis with drill-down capabilities and explanations',
    icon: '📈',
    href: '/analytics/variance-analysis',
    features: ['Budget vs Actual', 'Trend Analysis', 'Top Variances', 'Account Breakdown']
  },
  {
    id: 'kpi-management',
    title: 'KPI Management', 
    description: 'Key Performance Indicators tracking and performance monitoring',
    icon: '🎯',
    href: '/analytics/kpi-management',
    features: ['KPI Dashboard', 'Performance Tracking', 'Alerts', 'Custom KPIs']
  },
  {
    id: 'financial-reports',
    title: 'Financial Reports',
    description: 'Standard financial statements and custom reporting',
    icon: '📑',
    href: '/analytics/reports', 
    features: ['P&L Statement', 'Balance Sheet', 'Cash Flow', 'Custom Reports']
  },
  {
    id: 'profitability',
    title: 'Profitability Analysis',
    description: 'Product, customer, and segment profitability insights',
    icon: '💹',
    href: '/analytics/profitability',
    features: ['Margin Analysis', 'Segment Performance', 'Cost Allocation', 'ROI Tracking']
  }
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-8">
        <h1 className="text-3xl font-bold mb-4">📈 Analytics</h1>
        <p className="text-blue-100 text-lg max-w-3xl">
          Comprehensive financial analysis and reporting tools to drive data-driven decisions 
          and strategic insights for your organization.
        </p>
        
        <div className="flex items-center mt-6 space-x-6">
          <div className="text-center">
            <div className="text-2xl font-bold">5</div>
            <div className="text-blue-200 text-sm">Analytics Modules</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">Real-time</div>
            <div className="text-blue-200 text-sm">Data Analysis</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">Interactive</div>
            <div className="text-blue-200 text-sm">Dashboards</div>
          </div>
        </div>
      </div>

      {/* Analytics Modules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {analyticsModules.map((module) => (
          <div key={module.id} className="bg-gradient-to-br from-white to-gray-50 rounded-lg border-2 border-gray-300 shadow-lg hover:shadow-xl hover:border-blue-400 hover:from-blue-50 hover:to-white transform hover:-translate-y-1 hover:scale-105 transition-all duration-200">
            <div className="p-6">
              <div className="flex items-start space-x-4">
                <div className="text-4xl">{module.icon}</div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {module.title}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {module.description}
                  </p>
                  
                  <div className="space-y-2 mb-6">
                    <h4 className="text-sm font-medium text-gray-900">Key Features:</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {module.features.map((feature, index) => (
                        <div key={index} className="flex items-center text-sm text-gray-600">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                          {feature}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="flex space-x-3">
                    <Link
                      href={module.href}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                    >
                      Open Module
                    </Link>
                    <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium">
                      Learn More
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Start Notice */}
      <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <div className="text-2xl">💡</div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Need Sample Data?</h2>
            <p className="text-gray-600 mb-3">
              To explore analytics features with realistic data, visit the Setup page to generate comprehensive sample data.
            </p>
            <Link
              href="/setup"
              className="inline-flex px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Go to Setup →
            </Link>
          </div>
        </div>
      </div>

      {/* Getting Started Guide */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Getting Started with Analytics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">1️⃣</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">Set Up Data</h3>
            <p className="text-sm text-gray-600">
              Configure GL accounts, fiscal periods, and budgets, or use sample data from Setup.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">2️⃣</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">Explore Analytics</h3>
            <p className="text-sm text-gray-600">
              Access executive dashboards, variance analysis, KPI tracking, and reporting modules.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">3️⃣</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">Generate Reports</h3>
            <p className="text-sm text-gray-600">
              Create comprehensive financial reports, export insights, and share analytics with stakeholders.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}