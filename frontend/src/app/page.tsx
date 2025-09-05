import Link from 'next/link';
import OpenFPALogo from '@/components/OpenFPALogo';
import OpenFPAIcon from '@/components/OpenFPAIcon';

export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center">
        <OpenFPAIcon size={32} className="mr-2" />
        Dashboard
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <DashboardCard
          title="Companies"
          description="Manage companies and organizational structure"
          href="/companies"
          icon="🏢"
        />
        <DashboardCard
          title="Cost Centers"
          description="Define and organize cost centers"
          href="/cost-centers"
          icon="💻"
        />
        <DashboardCard
          title="GL Accounts"
          description="Chart of accounts management"
          href="/gl-accounts"
          icon="📋"
        />
        <DashboardCard
          title="Fiscal Periods"
          description="Configure fiscal calendar"
          href="/fiscal-periods"
          icon="📅"
        />
        <DashboardCard
          title="Budgets & Scenarios"
          description="Create and manage budgets"
          href="/scenarios"
          icon="💰"
        />
        <DashboardCard
          title="Transactions"
          description="Record and post GL transactions"
          href="/transactions"
          icon="💳"
        />
        <DashboardCard
          title="Analytics"
          description="Financial analytics and reporting"
          href="/analytics"
          icon="📈"
        />
        <DashboardCard
          title="Planning"
          description="Forecasting and planning tools"
          href="/planning"
          icon="🎯"
        />
        <DashboardCard
          title="Setup"
          description="System configuration and sample data"
          href="/setup"
          icon="⚙️"
        />
      </div>
      
      <div className="flex items-center justify-center gap-8 mt-12 pt-8 border-t border-gray-200">
        <div className="text-right">
          <h2 className="text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Empower Your Financial Intelligence
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Open-Source FP&A Platform • Built for Modern Finance Teams
          </p>
        </div>
        <OpenFPALogo size="lg" />
      </div>
    </div>
  );
}

function DashboardCard({ title, description, href, icon }: {
  title: string;
  description: string;
  href: string;
  icon: string;
}) {
  return (
    <Link
      href={href}
      className="block p-6 bg-gradient-to-br from-white to-gray-50 rounded-lg border-2 border-gray-300 shadow-lg hover:shadow-xl hover:border-blue-400 hover:from-blue-50 hover:to-white transform hover:-translate-y-1 hover:scale-105 transition-all duration-200 group"
    >
      <div className="flex items-center mb-4">
        <span className="text-3xl mr-3 group-hover:scale-110 transition-transform">{icon}</span>
        <h2 className="text-xl font-semibold text-gray-900 group-hover:text-blue-700">{title}</h2>
      </div>
      <p className="text-gray-600 text-sm">{description}</p>
    </Link>
  );
}