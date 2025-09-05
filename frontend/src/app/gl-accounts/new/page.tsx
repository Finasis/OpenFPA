'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { glAccountApi, companyApi } from '@/lib/api';
import { Company } from '@/types';
import toast from 'react-hot-toast';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface GLAccountForm {
  company_id: string;
  account_number: string;
  name: string;
  account_type: string;
  account_subtype?: string;
  parent_id?: string;
  is_summary: boolean;
  is_active: boolean;
}

export default function NewGLAccountPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const companyId = searchParams.get('company_id');
  
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm<GLAccountForm>({
    defaultValues: {
      company_id: companyId || '',
      is_active: true,
      is_summary: false,
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

  const { data: parentAccounts } = useQuery({
    queryKey: ['gl-accounts', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return [];
      const parentAccounts = await glAccountApi.getByCompany(selectedCompanyId);
      return parentAccounts;
    },
    enabled: !!selectedCompanyId,
  });

  const onSubmit = async (data: GLAccountForm) => {
    try {
      const glAccount = await glAccountApi.create(data);
      toast.success('GL account created successfully');
      router.push(`/gl-accounts/${glAccount.id}`);
    } catch (error: any) {
      toast.error(error.message || 'Failed to create GL account');
    }
  };

  if (!companies) return <LoadingSpinner />;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New GL Account</h1>

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
          <label htmlFor="account_number" className="block text-sm font-medium text-gray-700">
            Account Number
          </label>
          <input
            type="text"
            {...register('account_number', { required: 'Account number is required' })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
          {errors.account_number && (
            <p className="mt-1 text-sm text-red-600">{errors.account_number.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Account Name
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
          <label htmlFor="account_type" className="block text-sm font-medium text-gray-700">
            Account Type
          </label>
          <select
            {...register('account_type', { required: 'Account type is required' })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">Select type...</option>
            <option value="ASSET">Asset</option>
            <option value="LIABILITY">Liability</option>
            <option value="EQUITY">Equity</option>
            <option value="REVENUE">Revenue</option>
            <option value="EXPENSE">Expense</option>
          </select>
          {errors.account_type && (
            <p className="mt-1 text-sm text-red-600">{errors.account_type.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="account_subtype" className="block text-sm font-medium text-gray-700">
            Account Subtype (Optional)
          </label>
          <select
            {...register('account_subtype')}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">None</option>
            <option value="OPERATING">Operating</option>
            <option value="NON_OPERATING">Non-Operating</option>
            <option value="CAPITAL">Capital</option>
            <option value="OTHER">Other</option>
          </select>
        </div>

        <div>
          <label htmlFor="parent_id" className="block text-sm font-medium text-gray-700">
            Parent Account (Optional)
          </label>
          <select
            {...register('parent_id')}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">None</option>
            {parentAccounts?.filter((acc: any) => acc.is_summary).map((acc: any) => (
              <option key={acc.id} value={acc.id}>
                {acc.account_number} - {acc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <div className="flex items-center">
            <input
              type="checkbox"
              {...register('is_summary')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_summary" className="ml-2 block text-sm text-gray-900">
              Summary Account (can have child accounts)
            </label>
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
            {isSubmitting ? 'Creating...' : 'Create GL Account'}
          </button>
        </div>
      </form>
    </div>
  );
}