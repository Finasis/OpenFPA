'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { companyApi } from '@/lib/api';
import toast from 'react-hot-toast';

interface CompanyForm {
  code: string;
  name: string;
  currency_code: string;
  fiscal_year_start_month: number;
  is_active: boolean;
}

export default function NewCompanyPage() {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<CompanyForm>({
    defaultValues: {
      is_active: true,
      fiscal_year_start_month: 1,
    }
  });

  const onSubmit = async (data: CompanyForm) => {
    try {
      const company = await companyApi.create(data);
      toast.success('Company created successfully');
      router.push(`/companies/${company.id}`);
    } catch (error: any) {
      toast.error(error.message || 'Failed to create company');
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Company</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
        <div>
          <label htmlFor="code" className="block text-sm font-medium text-gray-700">
            Company Code
          </label>
          <input
            type="text"
            {...register('code', { 
              required: 'Code is required',
              pattern: {
                value: /^[A-Za-z0-9_-]+$/,
                message: 'Code must be alphanumeric (letters, numbers, _, or - only)'
              },
              maxLength: { value: 50, message: 'Code must be 50 characters or less' }
            })}
            placeholder="ACME_CORP"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
          <p className="mt-1 text-sm text-gray-500">
            Use letters, numbers, underscores, or hyphens only. No spaces allowed.
          </p>
          {errors.code && (
            <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Company Name
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
          <label htmlFor="currency_code" className="block text-sm font-medium text-gray-700">
            Currency Code
          </label>
          <input
            type="text"
            {...register('currency_code', { 
              required: 'Currency code is required',
              maxLength: { value: 3, message: 'Currency code must be 3 characters' },
              minLength: { value: 3, message: 'Currency code must be 3 characters' }
            })}
            placeholder="USD"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
          {errors.currency_code && (
            <p className="mt-1 text-sm text-red-600">{errors.currency_code.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="fiscal_year_start_month" className="block text-sm font-medium text-gray-700">
            Fiscal Year Start Month
          </label>
          <select
            {...register('fiscal_year_start_month', { valueAsNumber: true })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            {[...Array(12)].map((_, i) => (
              <option key={i + 1} value={i + 1}>
                {new Date(2000, i, 1).toLocaleDateString('en', { month: 'long' })}
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
            {isSubmitting ? 'Creating...' : 'Create Company'}
          </button>
        </div>
      </form>
    </div>
  );
}