'use client';

import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { fiscalPeriodApi, companyApi } from '@/lib/api';
import { FiscalPeriod, Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

export default function FiscalPeriodsPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());

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

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['fiscal-periods', selectedCompanyId, selectedYear],
    queryFn: async () => {
      if (!selectedCompanyId) return [];
      const fiscalPeriods = await fiscalPeriodApi.getByCompany(selectedCompanyId, { fiscal_year: selectedYear });
      return fiscalPeriods;
    },
    enabled: !!selectedCompanyId,
  });

  const handleClosePeriod = async (periodId: string) => {
    if (!confirm('Are you sure you want to close this period? This action cannot be undone.')) return;
    
    try {
      await fiscalPeriodApi.close(periodId);
      toast.success('Period closed successfully');
      refetch();
    } catch (error) {
      toast.error('Failed to close period');
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading fiscal periods</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">📅 Fiscal Periods</h1>
        <Link
          href={`/fiscal-periods/new${selectedCompanyId ? `?company_id=${selectedCompanyId}` : ''}`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Fiscal Period
        </Link>
      </div>

      <div className="bg-white p-4 rounded-md shadow space-y-4">
        <div>
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

        <div>
          <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">
            Fiscal Year
          </label>
          <select
            id="year"
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            {[...Array(5)].map((_, i) => {
              const year = new Date().getFullYear() - 2 + i;
              return (
                <option key={year} value={year}>{year}</option>
              );
            })}
          </select>
        </div>
      </div>

      {selectedCompanyId && (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {data?.length === 0 && (
              <li className="px-4 py-8 text-center text-gray-500">
                No fiscal periods found for {selectedYear}
              </li>
            )}
            {data?.sort((a, b) => a.period_number - b.period_number).map((period) => (
              <li key={period.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <Link
                        href={`/fiscal-periods/${period.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {period.period_name}
                      </Link>
                      <p className="text-sm text-gray-500">
                        Period {period.period_number} | 
                        {' '}{new Date(period.start_date).toLocaleDateString()} - 
                        {' '}{new Date(period.end_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {period.is_closed ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                          Closed
                        </span>
                      ) : (
                        <>
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            Open
                          </span>
                          <button
                            onClick={() => handleClosePeriod(period.id)}
                            className="px-3 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700"
                          >
                            Close Period
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}