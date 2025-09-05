'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { glTransactionApi } from '@/lib/api';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useDateFormat } from '@/contexts/DateFormatContext';
import toast from 'react-hot-toast';

export default function TransactionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const transactionId = params.id as string;
  const { formatDate } = useDateFormat();

  const { data: transaction, isLoading, error } = useQuery({
    queryKey: ['transaction', transactionId],
    queryFn: () => glTransactionApi.getById(transactionId),
  });

  const postMutation = useMutation({
    mutationFn: () => glTransactionApi.post(transactionId),
    onSuccess: () => {
      toast.success('Transaction posted successfully');
      queryClient.invalidateQueries({ queryKey: ['transaction', transactionId] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to post transaction');
    },
  });

  const voidMutation = useMutation({
    mutationFn: (reason: string) => glTransactionApi.void(transactionId, reason),
    onSuccess: () => {
      toast.success('Transaction voided successfully');
      queryClient.invalidateQueries({ queryKey: ['transaction', transactionId] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to void transaction');
    },
  });

  const duplicateMutation = useMutation({
    mutationFn: () => glTransactionApi.duplicate(transactionId),
    onSuccess: (newTransaction) => {
      toast.success('Transaction duplicated successfully');
      router.push(`/transactions/${newTransaction.id}`);
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to duplicate transaction');
    },
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const handleVoid = () => {
    const reason = window.prompt('Please provide a reason for voiding this transaction:');
    if (reason) {
      voidMutation.mutate(reason);
    }
  };

  if (isLoading) return <LoadingSpinner />;

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">Error loading transaction</p>
        </div>
      </div>
    );
  }

  if (!transaction) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <p className="text-gray-600">Transaction not found</p>
        </div>
      </div>
    );
  }

  const totalDebits = transaction.transaction_lines?.reduce((sum, line) => sum + (Number(line.debit_amount) || 0), 0) || 0;
  const totalCredits = transaction.transaction_lines?.reduce((sum, line) => sum + (Number(line.credit_amount) || 0), 0) || 0;
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/transactions"
            className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
          >
            ← Back to Transactions
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            {transaction.reference_number || `Transaction #${transaction.id.slice(-8)}`}
          </h1>
        </div>
        <div className="flex space-x-2">
          {!transaction.is_posted && (
            <>
              <button
                onClick={() => postMutation.mutate()}
                disabled={!isBalanced || postMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {postMutation.isPending ? 'Posting...' : 'Post Transaction'}
              </button>
              <Link
                href={`/transactions/${transaction.id}/edit`}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Edit
              </Link>
            </>
          )}
          <button
            onClick={() => duplicateMutation.mutate()}
            disabled={duplicateMutation.isPending}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            {duplicateMutation.isPending ? 'Duplicating...' : 'Duplicate'}
          </button>
          {transaction.is_posted && (
            <button
              onClick={handleVoid}
              disabled={voidMutation.isPending}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              {voidMutation.isPending ? 'Voiding...' : 'Void'}
            </button>
          )}
        </div>
      </div>

      {/* Transaction Details */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Transaction Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Company</label>
            <p className="mt-1 text-sm text-gray-900">{transaction.company?.name}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Fiscal Period</label>
            <p className="mt-1 text-sm text-gray-900">
              {transaction.fiscal_period?.period_name} ({transaction.fiscal_period?.fiscal_year})
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Transaction Date</label>
            <p className="mt-1 text-sm text-gray-900">{formatDate(transaction.transaction_date)}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Reference Number</label>
            <p className="mt-1 text-sm text-gray-900">{transaction.reference_number || 'N/A'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Status</label>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              transaction.is_posted 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {transaction.is_posted ? 'Posted' : 'Draft'}
            </span>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Created</label>
            <p className="mt-1 text-sm text-gray-900">{formatDate(transaction.created_at)}</p>
          </div>
        </div>
        {transaction.description && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <p className="mt-1 text-sm text-gray-900">{transaction.description}</p>
          </div>
        )}
      </div>

      {/* Transaction Lines */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Transaction Lines</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-3 text-sm font-medium text-gray-700">Account</th>
                <th className="text-left p-3 text-sm font-medium text-gray-700">Cost Center</th>
                <th className="text-left p-3 text-sm font-medium text-gray-700">Description</th>
                <th className="text-right p-3 text-sm font-medium text-gray-700">Debit</th>
                <th className="text-right p-3 text-sm font-medium text-gray-700">Credit</th>
              </tr>
            </thead>
            <tbody>
              {transaction.transaction_lines?.map((line, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="p-3">
                    <div className="text-sm font-medium text-gray-900">
                      {line.gl_account?.account_number} - {line.gl_account?.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {line.gl_account?.account_type}
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="text-sm text-gray-900">
                      {line.cost_center?.code} - {line.cost_center?.name}
                    </div>
                  </td>
                  <td className="p-3 text-sm text-gray-900">
                    {line.description || 'N/A'}
                  </td>
                  <td className="p-3 text-right text-sm font-mono">
                    {line.debit_amount > 0 ? formatCurrency(line.debit_amount) : '—'}
                  </td>
                  <td className="p-3 text-right text-sm font-mono">
                    {line.credit_amount > 0 ? formatCurrency(line.credit_amount) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 font-medium bg-gray-50">
                <td colSpan={3} className="p-3 text-right text-sm font-medium">Totals:</td>
                <td className="p-3 text-right text-sm font-mono font-medium">
                  {formatCurrency(totalDebits)}
                </td>
                <td className="p-3 text-right text-sm font-mono font-medium">
                  {formatCurrency(totalCredits)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        {!isBalanced && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-sm text-red-600 font-medium">
              ⚠️ Transaction is not balanced. Difference: {formatCurrency(Math.abs(totalDebits - totalCredits))}
            </p>
          </div>
        )}
      </div>

      {/* Audit Trail */}
      {transaction.audit_trail && transaction.audit_trail.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Audit Trail</h2>
          <div className="space-y-2">
            {transaction.audit_trail.map((entry, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <div>
                  <span className="text-sm font-medium text-gray-900">{entry.action}</span>
                  {entry.reason && (
                    <span className="ml-2 text-sm text-gray-600">- {entry.reason}</span>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {formatDate(entry.timestamp)} by {entry.user_name}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}