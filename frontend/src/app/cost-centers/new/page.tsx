'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { costCenterApi, companyApi } from '@/lib/api';
import { Company, CostCenter } from '@/types';
import toast from 'react-hot-toast';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface CostCenterForm {
  company_id: string;
  code: string;
  name: string;
  parent_id?: string;
  is_active: boolean;
}

export default function NewCostCenterPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const companyId = searchParams.get('company_id');
  
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm<CostCenterForm>({
    defaultValues: {
      company_id: companyId || '',
      is_active: true,
    }
  });

  const selectedCompanyId = watch('company_id');

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: async () => {
      const companies = await companyApi.getAll();
      return companies;
    },
  });

  const { data: costCenters } = useQuery({
    queryKey: ['cost-centers', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return [];
      const costCenters = await costCenterApi.getByCompany(selectedCompanyId);
      return costCenters;
    },
    enabled: !!selectedCompanyId,
  });

  const onSubmit = async (data: CostCenterForm) => {
    try {
      // Transform empty parent_id to null
      const submitData = {
        ...data,
        parent_id: data.parent_id === '' ? null : data.parent_id
      };
      const response = await costCenterApi.create(submitData);
      toast.success('Cost center created successfully');
      router.push(`/cost-centers/${response.id}`);
    } catch (error: any) {
      toast.error(error.message || 'Failed to create cost center');
    }
  };

  if (!companies) return <LoadingSpinner />;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Cost Center</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
        <div>
          <label htmlFor="company_id" className="block text-sm font-medium text-gray-700">
            Company
          </label>
          <select
            {...register('company_id', { required: 'Company is required' })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
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
          <label htmlFor="code" className="block text-sm font-medium text-gray-700">
            Cost Center Code
          </label>
          <input
            type="text"
            {...register('code', { required: 'Code is required' })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
          {errors.code && (
            <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Cost Center Name
          </label>
          <input
            type="text"
            {...register('name', { required: 'Name is required' })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="parent_id" className="block text-sm font-medium text-gray-700">
            Parent Cost Center (Optional)
          </label>
          <select
            {...register('parent_id')}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">None</option>
            {costCenters?.map((cc) => (
              <option key={cc.id} value={cc.id}>
                {cc.name} ({cc.code})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            {...register('is_active')}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
            Active
          </label>
        </div>

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Creating...' : 'Create Cost Center'}
          </button>
        </div>
      </form>
    </div>
  );
}