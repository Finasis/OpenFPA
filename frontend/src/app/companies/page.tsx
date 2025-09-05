'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { companyApi } from '@/lib/api';
import { Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export default function CompaniesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const companies = await companyApi.getAll();
      return companies;
    },
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) {
    console.error('Companies page error:', error);
    console.error('Error message:', error?.message);
    console.error('Error response:', error?.response);
    console.error('Error status:', error?.response?.status);
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-sm border p-8 text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Problem</h2>
          <p className="text-gray-600 mb-4">
            Unable to connect to the server. Please check that the backend service is running and try again.
          </p>
          <div className="text-sm text-gray-500 mb-4 p-2 bg-gray-100 rounded">
            Error: {error?.message || 'Unknown error'}
          </div>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">🏢 Companies</h1>
        <Link
          href="/companies/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Company
        </Link>
      </div>

      {data && data.length > 0 ? (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {data.map((company) => (
            <li key={company.id}>
              <Link
                href={`/companies/${company.id}`}
                className="block hover:bg-gray-50 px-4 py-4 sm:px-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div>
                      <p className="text-sm font-medium text-blue-600 truncate">
                        {company.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        Code: {company.code} | Currency: {company.currency_code}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      company.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {company.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </Link>
            </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="bg-white shadow sm:rounded-md p-8">
          <div className="text-center">
            <div className="text-4xl mb-4">🏢</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No companies yet</h3>
            <p className="text-gray-600 mb-6">
              Get started by creating your first company to manage financial data.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/companies/new"
                className="inline-flex px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Create First Company
              </Link>
              <Link
                href="/analytics"
                className="inline-flex px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                📊 Generate Sample Data
              </Link>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Or use the sample data generator to create a company with realistic financial data for testing
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
