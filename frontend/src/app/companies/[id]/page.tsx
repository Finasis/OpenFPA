'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { companyApi } from '@/lib/api';
import { Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useDateFormat } from '@/contexts/DateFormatContext';
import toast from 'react-hot-toast';

export default function CompanyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { formatDate } = useDateFormat();

  const { data, isLoading, error } = useQuery({
    queryKey: ['company', id],
    queryFn: async () => {
      const company = await companyApi.getById(id);
      return company;
    },
  });

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this company?')) return;
    
    try {
      await companyApi.delete(id);
      toast.success('Company deleted successfully');
      router.push('/companies');
    } catch (error) {
      toast.error('Failed to delete company');
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading company</div>;
  if (!data) return <div>Company not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
        <div className="flex gap-2">
          <Link
            href={`/analytics?company_id=${id}`}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            📊 Generate Sample Data
          </Link>
          <Link
            href={`/companies/${id}/edit`}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
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
            Company Information
          </h3>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Company Code</dt>
              <dd className="mt-1 text-sm text-gray-900">{data.code}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Company Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{data.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Currency</dt>
              <dd className="mt-1 text-sm text-gray-900">{data.currency_code}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Fiscal Year Start</dt>
              <dd className="mt-1 text-sm text-gray-900">
                Month {data.fiscal_year_start_month || 1}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  data.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {data.is_active ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDate(data.created_at)}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="flex gap-4">
        <Link
          href={`/cost-centers?company_id=${id}`}
          className="text-blue-600 hover:text-blue-800"
        >
          View Cost Centers →
        </Link>
        <Link
          href={`/gl-accounts?company_id=${id}`}
          className="text-blue-600 hover:text-blue-800"
        >
          View GL Accounts →
        </Link>
        <Link
          href={`/fiscal-periods?company_id=${id}`}
          className="text-blue-600 hover:text-blue-800"
        >
          View Fiscal Periods →
        </Link>
      </div>
    </div>
  );
}