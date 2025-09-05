'use client';

import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { scenarioApi, companyApi } from '@/lib/api';
import { Scenario, Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

export default function ScenariosPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const [filters, setFilters] = useState({
    fiscal_year: new Date().getFullYear(),
    scenario_type: '',
  });

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
    queryKey: ['scenarios', selectedCompanyId, filters],
    queryFn: async () => {
      if (!selectedCompanyId) return [];
      const scenarios = await scenarioApi.getByCompany(selectedCompanyId, filters);
      return scenarios;
    },
    enabled: !!selectedCompanyId,
  });

  const handleApprove = async (scenarioId: string) => {
    if (!confirm('Are you sure you want to approve this scenario?')) return;
    
    try {
      // In production, this would use the actual user ID
      await scenarioApi.approve(scenarioId, 'current-user-id');
      toast.success('Scenario approved successfully');
      refetch();
    } catch (error) {
      toast.error('Failed to approve scenario');
    }
  };

  const getScenarioTypeColor = (type: string) => {
    switch (type) {
      case 'BUDGET': return 'bg-blue-100 text-blue-800';
      case 'FORECAST': return 'bg-purple-100 text-purple-800';
      case 'ACTUAL': return 'bg-green-100 text-green-800';
      case 'SCENARIO': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading scenarios</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">💰 Budgets & Scenarios</h1>
        <Link
          href={`/scenarios/new${selectedCompanyId ? `?company_id=${selectedCompanyId}` : ''}`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Create Scenario
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">
              Fiscal Year
            </label>
            <select
              id="year"
              value={filters.fiscal_year}
              onChange={(e) => setFilters({ ...filters, fiscal_year: Number(e.target.value) })}
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

          <div>
            <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-2">
              Scenario Type
            </label>
            <select
              id="type"
              value={filters.scenario_type}
              onChange={(e) => setFilters({ ...filters, scenario_type: e.target.value })}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="BUDGET">Budget</option>
              <option value="FORECAST">Forecast</option>
              <option value="ACTUAL">Actual</option>
              <option value="SCENARIO">Scenario</option>
            </select>
          </div>
        </div>
      </div>

      {selectedCompanyId && (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {data?.length === 0 && (
              <li className="px-4 py-8 text-center text-gray-500">
                No scenarios found
              </li>
            )}
            {Array.isArray(data) ? data.map((scenario) => (
              <li key={scenario.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <Link
                        href={`/scenarios/${scenario.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        onClick={() => {
                          // Store scenario data for the detail page
                          sessionStorage.setItem(`scenario_${scenario.id}`, JSON.stringify(scenario));
                        }}
                      >
                        {scenario.name}
                      </Link>
                      <div className="mt-1 flex items-center gap-3">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getScenarioTypeColor(scenario.scenario_type)}`}>
                          {scenario.scenario_type}
                        </span>
                        <span className="text-xs text-gray-500">
                          FY {scenario.fiscal_year} | Version {scenario.version}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {scenario.is_approved ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          Approved
                        </span>
                      ) : (
                        <button
                          onClick={() => handleApprove(scenario.id)}
                          className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                        >
                          Approve
                        </button>
                      )}
                      {scenario.is_locked && (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                          Locked
                        </span>
                      )}
                      <Link
                        href={`/scenarios/${scenario.id}/budget-lines`}
                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        Budget Lines
                      </Link>
                    </div>
                  </div>
                </div>
              </li>
            )) : (
              <li className="px-4 py-8 text-center text-gray-500">
                {data ? 'Invalid data format received' : 'Loading scenarios...'}
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}