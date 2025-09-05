'use client';

import Link from 'next/link';

export default function PlanningPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">🎯 Planning</h1>
        <p className="mt-2 text-gray-600">
          Forecasting, scenario modeling, and strategic planning tools
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <PlanningCard
          title="Revenue Planning"
          description="Advanced revenue forecasting with multiple methods"
          href="/planning/revenue-planning"
          icon="📊"
          status="active"
        />
        <PlanningCard
          title="Expense Planning"
          description="Plan and model expense scenarios"
          href="/planning/expense-planning"
          icon="💵"
          status="active"
        />
        <PlanningCard
          title="Cash Flow Projection"
          description="Project cash flow and working capital needs"
          href="/planning/cash-flow"
          icon="💰"
          status="coming-soon"
        />
        <PlanningCard
          title="Scenario Modeling"
          description="Create what-if scenarios and sensitivity analysis"
          href="/planning/scenario-modeling"
          icon="🔄"
          status="coming-soon"
        />
        <PlanningCard
          title="Headcount Planning"
          description="Plan workforce and compensation budgets"
          href="/planning/headcount"
          icon="👥"
          status="coming-soon"
        />
        <PlanningCard
          title="Capital Planning"
          description="Plan capital expenditures and investments"
          href="/planning/capital"
          icon="🏗️"
          status="coming-soon"
        />
      </div>

      {/* Getting Started Guide */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Getting Started with Planning</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">1️⃣</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">Define Scenarios</h3>
            <p className="text-sm text-gray-600">
              Set up planning scenarios with assumptions, growth rates, and business drivers for modeling.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">2️⃣</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">Build Forecasts</h3>
            <p className="text-sm text-gray-600">
              Create revenue projections, expense plans, and cash flow forecasts based on your scenarios.
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-xl">3️⃣</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">Make Decisions</h3>
            <p className="text-sm text-gray-600">
              Use predictive insights to guide strategic planning, resource allocation, and investment decisions.
            </p>
          </div>
        </div>
      </div>

      {/* Key Benefits */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Why Use OpenFP&A Planning?</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start space-x-3">
            <div className="text-blue-600 mt-1">✓</div>
            <div>
              <h4 className="font-medium text-gray-900">Integrated Planning</h4>
              <p className="text-sm text-gray-600">Connect financial, operational, and strategic planning in one platform.</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="text-blue-600 mt-1">✓</div>
            <div>
              <h4 className="font-medium text-gray-900">Real-time Collaboration</h4>
              <p className="text-sm text-gray-600">Enable teams to work together on forecasts and scenarios.</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="text-blue-600 mt-1">✓</div>
            <div>
              <h4 className="font-medium text-gray-900">Scenario Comparison</h4>
              <p className="text-sm text-gray-600">Compare multiple scenarios side-by-side for better decision making.</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <div className="text-blue-600 mt-1">✓</div>
            <div>
              <h4 className="font-medium text-gray-900">Automated Workflows</h4>
              <p className="text-sm text-gray-600">Streamline planning cycles with automated data flows and calculations.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function PlanningCard({ 
  title, 
  description, 
  href, 
  icon,
  status = 'active'
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
  status?: 'active' | 'coming-soon';
}) {
  const isComingSoon = status === 'coming-soon';
  
  const cardContent = (
    <>
      <div className="flex items-start justify-between mb-4">
        <span className="text-3xl">{icon}</span>
        {isComingSoon && (
          <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
            Coming Soon
          </span>
        )}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </>
  );
  
  if (isComingSoon) {
    return (
      <div className="block p-6 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg border-2 border-gray-300 shadow-md opacity-75 cursor-not-allowed">
        {cardContent}
      </div>
    );
  }
  
  return (
    <Link
      href={href}
      className="block p-6 bg-gradient-to-br from-white to-gray-50 rounded-lg border-2 border-gray-300 shadow-lg hover:shadow-xl hover:border-blue-400 hover:from-blue-50 hover:to-white transform hover:-translate-y-1 hover:scale-105 transition-all duration-200"
    >
      {cardContent}
    </Link>
  );
}