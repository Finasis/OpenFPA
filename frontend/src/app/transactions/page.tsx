'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { companyApi, glTransactionApi } from '@/lib/api';
import { Company, GLTransaction } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useDateFormat } from '@/contexts/DateFormatContext';

export default function TransactionsPage() {
  const searchParams = useSearchParams();
  const companyIdParam = searchParams.get('company_id');
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyIdParam || '');
  const { formatDate } = useDateFormat();

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyApi.getAll(),
  });

  const { data: transactions, isLoading, error } = useQuery({
    queryKey: ['transactions', selectedCompanyId],
    queryFn: () => glTransactionApi.getByCompany(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  useEffect(() => {
    if (!selectedCompanyId && companies && companies.length > 0) {
      setSelectedCompanyId(companies[0].id);
    }
  }, [companies, selectedCompanyId]);


  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (isLoading || !companies) return <LoadingSpinner />;

  const selectedCompany = companies.find(c => c.id === selectedCompanyId);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">💳 GL Transactions</h1>
        <Link
          href={`/transactions/new${selectedCompanyId ? `?company_id=${selectedCompanyId}` : ''}`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Create Transaction
        </Link>
      </div>

      {/* Company Selection */}
      <div className="bg-white p-4 rounded-md shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Company
        </label>
        <select
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

      {selectedCompany && (
        <>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-600">Error loading transactions</p>
            </div>
          )}

          {transactions && transactions.length > 0 ? (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {transactions.map((transaction) => {
                  // Calculate total debits from transaction lines
                  const totalDebits = transaction.transaction_lines?.reduce(
                    (sum, line) => sum + (Number(line.debit_amount) || 0), 0
                  ) || 0;

                  return (
                    <li key={transaction.id}>
                      <Link
                        href={`/transactions/${transaction.id}`}
                        className="block hover:bg-gray-50 px-4 py-4 sm:px-6"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium text-blue-600">
                                  {transaction.reference_number || `Transaction #${transaction.id.slice(-8)}`}
                                </p>
                                <p className="text-sm text-gray-500">
                                  {transaction.description || 'No description'}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-sm font-medium text-gray-900">
                                  {formatCurrency(totalDebits)}
                                </p>
                                <p className="text-sm text-gray-500">
                                  {transaction.transaction_lines?.length || 0} line(s)
                                </p>
                              </div>
                            </div>
                            <div className="mt-2 flex items-center text-sm text-gray-500">
                              <span>
                                {formatDate(transaction.transaction_date)}
                              </span>
                              <span className="mx-2">•</span>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                transaction.is_posted 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {transaction.is_posted ? 'Posted' : 'Draft'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : (
            <div className="bg-white shadow sm:rounded-lg p-6">
              <div className="text-center py-12">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  No transactions found
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating your first GL transaction
                </p>
                <div className="mt-6">
                  <Link
                    href={`/transactions/new${selectedCompanyId ? `?company_id=${selectedCompanyId}` : ''}`}
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Create Transaction
                  </Link>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}