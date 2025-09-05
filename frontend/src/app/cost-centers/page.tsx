'use client';

import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { costCenterApi, companyApi } from '@/lib/api';
import { CostCenter, Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useState, useEffect } from 'react';

export default function CostCentersPage() {
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

  const { data, isLoading, error } = useQuery({
    queryKey: ['cost-centers', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return [];
      const costCenters = await costCenterApi.getByCompany(selectedCompanyId);
      return costCenters;
    },
    enabled: !!selectedCompanyId,
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading cost centers</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">💻 Cost Centers</h1>
        <Link
          href={`/cost-centers/new${selectedCompanyId ? `?company_id=${selectedCompanyId}` : ''}`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Cost Center
        </Link>
      </div>

      <div className="bg-white p-4 rounded-md shadow">
        <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
          Select Company
        </label>
        <select
          id="company"
          value={selectedCompanyId}
          onChange={(e) => setSelectedCompanyId(e.target.value)}
          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select a company...</option>
          {companies?.map((company) => (
            <option key={company.id} value={company.id}>
              {company.name} ({company.code})
            </option>
          ))}
        </select>
      </div>

      {selectedCompanyId && (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {data?.length === 0 && (
              <li className="px-4 py-8 text-center text-gray-500">
                No cost centers found for this company
              </li>
            )}
            {data?.map((costCenter) => (
              <li key={costCenter.id}>
                <Link
                  href={`/cost-centers/${costCenter.id}`}
                  className="block hover:bg-gray-50 px-4 py-4 sm:px-6"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-600 truncate">
                        {costCenter.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        Code: {costCenter.code}
                      </p>
                    </div>
                    <div className="flex items-center">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        costCenter.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {costCenter.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}