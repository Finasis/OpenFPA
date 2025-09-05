'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { scenarioApi, companyApi } from '@/lib/api';
import { Company } from '@/types';
import toast from 'react-hot-toast';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface ScenarioForm {
  company_id: string;
  name: string;
  scenario_type: string;
  fiscal_year: number;
  version: number;
  description?: string;
  is_approved: boolean;
  is_locked: boolean;
}

export default function NewScenarioPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const companyId = searchParams.get('company_id');
  
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm<ScenarioForm>({
    defaultValues: {
      company_id: companyId || '',
      fiscal_year: new Date().getFullYear(),
      version: 1,
      is_approved: false,
      is_locked: false,
    }
  });

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const companies = await companyApi.getAll();
      return companies;
    },
  });

  const onSubmit = async (data: ScenarioForm) => {
    try {
      // Add created_by field as null for now
      const scenarioData = { ...data, created_by: null };
      const scenario = await scenarioApi.create(scenarioData);
      toast.success('Scenario created successfully');
      // Store the scenario data for the detail page
      sessionStorage.setItem(`scenario_${scenario.id}`, JSON.stringify(scenario));
      router.push(`/scenarios/${scenario.id}`);
    } catch (error: any) {
      console.error('Scenario creation error:', error);
      toast.error(error.message || 'Failed to create scenario - there may be a backend configuration issue. Please check the server logs.');
    }
  };

  if (!companies) return <LoadingSpinner />;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Scenario</h1>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
          <div className="md:grid md:grid-cols-3 md:gap-6">
            <div className="md:col-span-1">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Basic Information</h3>
              <p className="mt-1 text-sm text-gray-500">
                General information about the scenario.
              </p>
            </div>
            <div className="mt-5 md:mt-0 md:col-span-2">
              <div className="space-y-6">
                <div>
                  <label htmlFor="company_id" className="block text-sm font-medium text-gray-700">
                    Company *
                  </label>
                  <select
                    {...register('company_id', { required: 'Company is required' })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select a company...</option>
                    {companies?.map((company) => (
                      <option key={company.id} value={company.id}>
                        {company.name} ({company.code})
                      </option>
                    ))}
                  </select>
                  {errors.company_id && (
                    <p className="mt-1 text-sm text-red-600">{errors.company_id.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Scenario Name *
                  </label>
                  <input
                    type="text"
                    {...register('name', { required: 'Scenario name is required' })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., 2024 Annual Budget"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="scenario_type" className="block text-sm font-medium text-gray-700">
                    Scenario Type *
                  </label>
                  <select
                    {...register('scenario_type', { required: 'Scenario type is required' })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select scenario type...</option>
                    <option value="BUDGET">Budget</option>
                    <option value="FORECAST">Forecast</option>
                    <option value="ACTUAL">Actual</option>
                    <option value="SCENARIO">Scenario</option>
                  </select>
                  {errors.scenario_type && (
                    <p className="mt-1 text-sm text-red-600">{errors.scenario_type.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="fiscal_year" className="block text-sm font-medium text-gray-700">
                      Fiscal Year *
                    </label>
                    <input
                      type="number"
                      {...register('fiscal_year', { 
                        required: 'Fiscal year is required',
                        min: { value: 2020, message: 'Year must be 2020 or later' },
                        max: { value: 2030, message: 'Year must be 2030 or earlier' }
                      })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                    {errors.fiscal_year && (
                      <p className="mt-1 text-sm text-red-600">{errors.fiscal_year.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="version" className="block text-sm font-medium text-gray-700">
                      Version *
                    </label>
                    <input
                      type="number"
                      {...register('version', { 
                        required: 'Version is required',
                        min: { value: 1, message: 'Version must be 1 or higher' }
                      })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                    {errors.version && (
                      <p className="mt-1 text-sm text-red-600">{errors.version.message}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    {...register('description')}
                    rows={3}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Optional description of the scenario..."
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
          <div className="md:grid md:grid-cols-3 md:gap-6">
            <div className="md:col-span-1">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Status Options</h3>
              <p className="mt-1 text-sm text-gray-500">
                Control the approval and lock status of the scenario.
              </p>
            </div>
            <div className="mt-5 md:mt-0 md:col-span-2">
              <div className="space-y-6">
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      type="checkbox"
                      {...register('is_approved')}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="is_approved" className="font-medium text-gray-700">
                      Pre-approved
                    </label>
                    <p className="text-gray-500">
                      Create this scenario in an approved state (can be changed later).
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      type="checkbox"
                      {...register('is_locked')}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="is_locked" className="font-medium text-gray-700">
                      Locked
                    </label>
                    <p className="text-gray-500">
                      Prevent further modifications to this scenario.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isSubmitting ? 'Creating...' : 'Create Scenario'}
          </button>
        </div>
      </form>
    </div>
  );
}