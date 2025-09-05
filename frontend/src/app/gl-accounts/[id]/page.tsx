'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { glAccountApi, companyApi } from '@/lib/api';
import { GLAccount, Company } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import toast from 'react-hot-toast';

export default function GLAccountDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: account, isLoading, error } = useQuery({
    queryKey: ['gl-account', id],
    queryFn: async () => {
      const account = await glAccountApi.getById(id);
      return account;
    },
  });

  const { data: company } = useQuery({
    queryKey: ['company', account?.company_id],
    queryFn: async () => {
      if (!account?.company_id) return null;
      const company = await companyApi.getById(account.company_id);
      return company;
    },
    enabled: !!account?.company_id,
  });

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this GL account?')) return;
    
    try {
      await glAccountApi.delete(id);
      toast.success('GL account deleted successfully');
      router.push('/gl-accounts');
    } catch (error) {
      toast.error('Failed to delete GL account');
    }
  };

  const getAccountTypeColor = (type: string) => {
    switch (type) {
      case 'ASSET': return 'bg-blue-100 text-blue-800';
      case 'LIABILITY': return 'bg-orange-100 text-orange-800';
      case 'EQUITY': return 'bg-purple-100 text-purple-800';
      case 'REVENUE': return 'bg-green-100 text-green-800';
      case 'EXPENSE': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading GL account</div>;
  if (!account) return <div>GL account not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">
          {account.account_number} - {account.name}
        </h1>
        <div className="flex gap-2">
          <Link
            href={`/gl-accounts/${id}/edit`}
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
            GL Account Information
          </h3>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Account Number</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.account_number}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Account Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{account.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Account Type</dt>
              <dd className="mt-1">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getAccountTypeColor(account.account_type)}`}>
                  {account.account_type}
                </span>
              </dd>
            </div>
            {account.account_subtype && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Account Subtype</dt>
                <dd className="mt-1 text-sm text-gray-900">{account.account_subtype}</dd>
              </div>
            )}
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
              <dt className="text-sm font-medium text-gray-500">Summary Account</dt>
              <dd className="mt-1">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  account.is_summary 
                    ? 'bg-purple-100 text-purple-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {account.is_summary ? 'Summary' : 'Detail'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status</dt>
              <dd className="mt-1">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  account.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {account.is_active ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Created</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(account.created_at).toLocaleDateString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(account.updated_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="flex gap-4">
        <Link
          href={`/gl-accounts?company_id=${account.company_id}`}
          className="text-blue-600 hover:text-blue-800"
        >
          ← Back to GL Accounts
        </Link>
      </div>
    </div>
  );
}