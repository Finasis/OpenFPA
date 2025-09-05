'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { scenarioApi, companyApi } from '@/lib/api';
import { Scenario, Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import toast from 'react-hot-toast';

export default function ScenarioDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: scenario, isLoading, error } = useQuery({
    queryKey: ['scenario', id],
    queryFn: async () => {
      // Since there's no individual scenario endpoint, we need to get it from URL params or navigate back
      // For now, let's try to find it from sessionStorage or redirect back
      const scenario = sessionStorage.getItem(`scenario_${id}`);
      if (scenario) {
        return JSON.parse(scenario);
      }
      throw new Error('Scenario not found - please access from scenarios list');
    },
  });

  const { data: company } = useQuery({
    queryKey: ['company', scenario?.company_id],
    queryFn: async () => {
      if (!scenario?.company_id) return null;
      const company = await companyApi.getById(scenario.company_id);
      return company;
    },
    enabled: !!scenario?.company_id,
  });

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this scenario?')) return;
    
    try {
      await scenarioApi.delete(id);
      toast.success('Scenario deleted successfully');
      router.push('/scenarios');
    } catch (error) {
      toast.error('Failed to delete scenario');
    }
  };

  const handleApprove = async () => {
    if (!confirm('Are you sure you want to approve this scenario?')) return;
    
    try {
      await scenarioApi.approve(id, 'current-user-id'); // In production, use actual user ID
      toast.success('Scenario approved successfully');
      router.refresh();
    } catch (error) {
      toast.error('Failed to approve scenario');
    }
  };

  const getScenarioTypeColor = (type: string) => {
    switch (type) {
      case 'BUDGET': return 'bg-blue-100 text-blue-800';
      case 'FORECAST': return 'bg-green-100 text-green-800';
      case 'ACTUAL': return 'bg-gray-100 text-gray-800';
      case 'ROLLING_FORECAST': return 'bg-purple-100 text-purple-800';
      case 'STRATEGIC_PLAN': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading scenario</div>;
  if (!scenario) return <div>Scenario not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">
          {scenario.name}
        </h1>
        <div className="flex gap-2">
          <Link
            href={`/scenarios/${id}/budget-lines`}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            View Budget Lines
          </Link>
          {!scenario.is_approved && (
            <button
              onClick={handleApprove}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Approve
            </button>
          )}
          <Link
            href={`/scenarios/${id}/edit`}
            className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
          >
            Edit
          </Link>
          <button
            onClick={handleDelete}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Scenario Information
          </h3>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Scenario Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{scenario.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Scenario Type</dt>
              <dd className="mt-1">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getScenarioTypeColor(scenario.scenario_type)}`}>
                  {scenario.scenario_type}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Company</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {company ? (
                  <Link
                    href={`/companies/${company.id}`}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    {company.name} ({company.code})
                  </Link>
                ) : (
                  'Loading...'
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Fiscal Year</dt>
              <dd className="mt-1 text-sm text-gray-900">{scenario.fiscal_year}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Version</dt>
              <dd className="mt-1 text-sm text-gray-900">v{scenario.version}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1 flex gap-2">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  scenario.is_approved 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {scenario.is_approved ? 'Approved' : 'Draft'}
                </span>
                {scenario.is_locked && (
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                    Locked
                  </span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(scenario.created_at).toLocaleDateString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(scenario.updated_at).toLocaleDateString()}
              </dd>
            </div>
            {scenario.description && (
              <div className="sm:col-span-2">
                <dt className="text-sm font-medium text-gray-500">Description</dt>
                <dd className="mt-1 text-sm text-gray-900">{scenario.description}</dd>
              </div>
            )}
            {scenario.approved_at && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Approved Date</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(scenario.approved_at).toLocaleDateString()}
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href={`/scenarios/${id}/budget-lines`}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 text-sm font-medium">📊</span>
              </div>
            </div>
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-900">Budget Lines</div>
              <div className="text-sm text-gray-500">View and manage budget line items</div>
            </div>
          </Link>
          
          <Link
            href={`/analytics/variance-analysis?scenario_id=${id}`}
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-green-600 text-sm font-medium">📈</span>
              </div>
            </div>
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-900">Variance Analysis</div>
              <div className="text-sm text-gray-500">Compare with other scenarios</div>
            </div>
          </Link>

          <div className="flex items-center p-4 border border-gray-200 rounded-lg opacity-50">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                <span className="text-gray-600 text-sm font-medium">📋</span>
              </div>
            </div>
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Reports</div>
              <div className="text-sm text-gray-400">Generate scenario reports (Coming soon)</div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <Link
          href={`/scenarios?company_id=${scenario.company_id}`}
          className="text-blue-600 hover:text-blue-800"
        >
          ← Back to Scenarios
        </Link>
      </div>
    </div>
  );
}