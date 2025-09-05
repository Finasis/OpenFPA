'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { companyApi } from '@/lib/api';
import { analyticsApi } from '@/lib/analytics-api';
import { useDateFormat, type DateFormat } from '@/contexts/DateFormatContext';
import toast from 'react-hot-toast';

export default function SetupPage() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<any>(null);
  const queryClient = useQueryClient();
  const { dateFormat, setDateFormat, formatDate } = useDateFormat();

  const generateSampleDataMutation = useMutation({
    mutationFn: async () => {
      let company;
      
      // Try to get existing ACME company first
      try {
        const companies = await companyApi.getAll();
        company = companies.find(c => c.code === 'ACME');
      } catch (error) {
        console.log('No existing companies found');
      }

      // If ACME doesn't exist, create it
      if (!company) {
        company = await companyApi.create({
          code: 'ACME',
          name: 'Acme Company',
          currency_code: 'USD',
          fiscal_year_start_month: 1,
          is_active: true
        });
      }

      // Generate sample data for ACME
      const data = await analyticsApi.generateSampleData(company.id, 24); // 24 months of data
      
      return { company, data };
    },
    onSuccess: (result) => {
      setGenerationResult(result);
      // Invalidate all queries to refresh data
      queryClient.invalidateQueries();
      toast.success('Sample data generated successfully!');
    },
    onError: (error: any) => {
      console.error('Sample data generation error:', error);
      toast.error(error.message || 'Failed to generate sample data');
    },
    onSettled: () => {
      setIsGenerating(false);
    }
  });

  const handleGenerateSampleData = () => {
    setIsGenerating(true);
    generateSampleDataMutation.mutate();
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">⚙️ Setup</h1>
        <p className="mt-2 text-gray-600">
          System configuration, initial setup, and sample data generation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Sample Data Generation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start space-x-4">
            <div className="text-4xl">🚀</div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Quick Start with Sample Data
              </h3>
              <p className="text-gray-600 mb-4">
                Generate comprehensive sample data to explore all features immediately. Creates ACME company with:
              </p>
              
              <ul className="space-y-2 mb-6 text-sm text-gray-600">
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Complete chart of accounts (40+ GL accounts)
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  8 cost centers across departments
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  24 months of GL transactions
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Budget scenarios with variance analysis
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  KPIs and business drivers
                </li>
              </ul>
              
              <button
                onClick={handleGenerateSampleData}
                disabled={isGenerating}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isGenerating ? 'Generating...' : 'Generate Sample Data'}
              </button>
              
              {generationResult && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h4 className="font-medium text-green-800 mb-2">✅ Generation Complete!</h4>
                  <div className="text-sm text-green-700 space-y-1">
                    <div>• Company: {generationResult.company?.name} ({generationResult.company?.code})</div>
                    <div>• Transactions: {generationResult.data?.details?.transactions_created || 0}</div>
                    <div>• Budget Lines: {generationResult.data?.details?.budget_lines_created || 0}</div>
                    <div>• KPIs: {generationResult.data?.details?.kpis_created || 0}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* System Preferences */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start space-x-4">
            <div className="text-4xl">🎨</div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                System Preferences
              </h3>
              <p className="text-gray-600 mb-4">
                Configure global system settings and preferences
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Default Currency
                  </label>
                  <select className="w-full border border-gray-300 rounded-md px-3 py-2" disabled>
                    <option>USD - US Dollar</option>
                    <option>EUR - Euro</option>
                    <option>GBP - British Pound</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date Format
                  </label>
                  <select 
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                    value={dateFormat}
                    onChange={(e) => setDateFormat(e.target.value as DateFormat)}
                  >
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Example: {formatDate(new Date())}
                  </p>
                </div>
                
                <div className="pt-2 border-t border-gray-200">
                  <p className="text-sm text-green-600">✓ Date format preference saved</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Data Import/Export */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start space-x-4">
            <div className="text-4xl">📤</div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Data Import/Export
              </h3>
              <p className="text-gray-600 mb-4">
                Import data from spreadsheets or export for backup
              </p>
              
              <div className="space-y-3">
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Import from CSV
                </button>
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Export to Excel
                </button>
                <p className="text-xs text-gray-500 text-center">Coming Soon</p>
              </div>
            </div>
          </div>
        </div>

        {/* User Management */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start space-x-4">
            <div className="text-4xl">👥</div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                User Management
              </h3>
              <p className="text-gray-600 mb-4">
                Manage users, roles, and permissions
              </p>
              
              <div className="space-y-3">
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Manage Users
                </button>
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Configure Roles
                </button>
                <p className="text-xs text-gray-500 text-center">Coming Soon</p>
              </div>
            </div>
          </div>
        </div>

        {/* Database Maintenance */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start space-x-4">
            <div className="text-4xl">🗄️</div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Database Maintenance
              </h3>
              <p className="text-gray-600 mb-4">
                Database backup, restore, and maintenance tasks
              </p>
              
              <div className="space-y-3">
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Backup Database
                </button>
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Restore Database
                </button>
                <p className="text-xs text-gray-500 text-center">Coming Soon</p>
              </div>
            </div>
          </div>
        </div>

        {/* API Configuration */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start space-x-4">
            <div className="text-4xl">🔌</div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                API & Integrations
              </h3>
              <p className="text-gray-600 mb-4">
                Configure API access and third-party integrations
              </p>
              
              <div className="space-y-3">
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  API Keys
                </button>
                <button className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                  Webhooks
                </button>
                <p className="text-xs text-gray-500 text-center">Coming Soon</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}