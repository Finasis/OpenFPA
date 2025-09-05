'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useForm, useFieldArray } from 'react-hook-form';
import { companyApi, glAccountApi, costCenterApi, fiscalPeriodApi, glTransactionApi } from '@/lib/api';
import { Company, GLAccount, CostCenter, FiscalPeriod } from '@/types';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import toast from 'react-hot-toast';

interface TransactionLine {
  gl_account_id: string;
  cost_center_id: string;
  debit_amount: number;
  credit_amount: number;
  description: string;
}

interface TransactionForm {
  company_id: string;
  fiscal_period_id: string;
  transaction_date: string;
  reference_number: string;
  description: string;
  lines: TransactionLine[];
}

export default function NewTransactionPage() {
  const router = useRouter();
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');

  const { register, control, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm<TransactionForm>({
    defaultValues: {
      transaction_date: new Date().toISOString().split('T')[0],
      lines: [
        { gl_account_id: '', cost_center_id: '', debit_amount: 0, credit_amount: 0, description: '' },
        { gl_account_id: '', cost_center_id: '', debit_amount: 0, credit_amount: 0, description: '' }
      ]
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'lines'
  });

  const watchedLines = watch('lines');
  const watchedCompanyId = watch('company_id');

  // Update selected company when form changes
  useEffect(() => {
    if (watchedCompanyId && watchedCompanyId !== selectedCompanyId) {
      setSelectedCompanyId(watchedCompanyId);
    }
  }, [watchedCompanyId, selectedCompanyId]);

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyApi.getAll(),
  });

  const { data: glAccounts } = useQuery({
    queryKey: ['gl-accounts', selectedCompanyId],
    queryFn: () => glAccountApi.getByCompany(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: costCenters } = useQuery({
    queryKey: ['cost-centers', selectedCompanyId],
    queryFn: () => costCenterApi.getByCompany(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  const { data: fiscalPeriods } = useQuery({
    queryKey: ['fiscal-periods', selectedCompanyId],
    queryFn: () => fiscalPeriodApi.getByCompany(selectedCompanyId),
    enabled: !!selectedCompanyId,
  });

  // Set default company
  useEffect(() => {
    if (!watchedCompanyId && companies && companies.length > 0) {
      setValue('company_id', companies[0].id);
    }
  }, [companies, watchedCompanyId, setValue]);

  // Calculate totals
  const totalDebits = watchedLines?.reduce((sum, line) => sum + (Number(line.debit_amount) || 0), 0) || 0;
  const totalCredits = watchedLines?.reduce((sum, line) => sum + (Number(line.credit_amount) || 0), 0) || 0;
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;

  const onSubmit = async (data: TransactionForm) => {
    if (!isBalanced) {
      toast.error('Transaction must be balanced (debits must equal credits)');
      return;
    }

    try {
      const transactionData = {
        ...data,
        lines: data.lines.map(line => ({
          ...line,
          debit_amount: Number(line.debit_amount) || 0,
          credit_amount: Number(line.credit_amount) || 0
        }))
      };

      const transaction = await glTransactionApi.create(transactionData);
      toast.success('Transaction created successfully');
      router.push('/transactions');
    } catch (error: any) {
      console.error('Transaction creation error:', error);
      toast.error(error.message || 'Failed to create transaction');
    }
  };

  if (!companies) return <LoadingSpinner />;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Create GL Transaction</h1>
        <button
          type="button"
          onClick={() => router.back()}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
        >
          Cancel
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Header Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Transaction Details</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company *
              </label>
              <select
                {...register('company_id', { required: 'Company is required' })}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select Company</option>
                {companies?.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>
              {errors.company_id && (
                <p className="mt-1 text-sm text-red-600">{errors.company_id.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fiscal Period *
              </label>
              <select
                {...register('fiscal_period_id', { required: 'Fiscal period is required' })}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select Period</option>
                {fiscalPeriods?.map((period) => (
                  <option key={period.id} value={period.id}>
                    {period.period_name} ({period.fiscal_year})
                  </option>
                ))}
              </select>
              {errors.fiscal_period_id && (
                <p className="mt-1 text-sm text-red-600">{errors.fiscal_period_id.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Transaction Date *
              </label>
              <input
                type="date"
                {...register('transaction_date', { required: 'Date is required' })}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
              {errors.transaction_date && (
                <p className="mt-1 text-sm text-red-600">{errors.transaction_date.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reference Number
              </label>
              <input
                type="text"
                {...register('reference_number')}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., INV-2024-001"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <input
              type="text"
              {...register('description')}
              className="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="Transaction description"
            />
          </div>
        </div>

        {/* Transaction Lines */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Transaction Lines</h2>
            <button
              type="button"
              onClick={() => append({ gl_account_id: '', cost_center_id: '', debit_amount: 0, credit_amount: 0, description: '' })}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Add Line
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2 text-sm font-medium text-gray-700">Account</th>
                  <th className="text-left p-2 text-sm font-medium text-gray-700">Cost Center</th>
                  <th className="text-left p-2 text-sm font-medium text-gray-700">Description</th>
                  <th className="text-right p-2 text-sm font-medium text-gray-700">Debit</th>
                  <th className="text-right p-2 text-sm font-medium text-gray-700">Credit</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field, index) => (
                  <tr key={field.id} className="border-b">
                    <td className="p-2">
                      <select
                        {...register(`lines.${index}.gl_account_id`, { required: 'Account required' })}
                        className="w-full text-sm border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Select Account</option>
                        {glAccounts?.map((account) => (
                          <option key={account.id} value={account.id}>
                            {account.account_number} - {account.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-2">
                      <select
                        {...register(`lines.${index}.cost_center_id`, { required: 'Cost center required' })}
                        className="w-full text-sm border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Select Cost Center</option>
                        {costCenters?.map((cc) => (
                          <option key={cc.id} value={cc.id}>
                            {cc.code} - {cc.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-2">
                      <input
                        type="text"
                        {...register(`lines.${index}.description`)}
                        className="w-full text-sm border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Line description"
                      />
                    </td>
                    <td className="p-2">
                      <input
                        type="number"
                        step="0.01"
                        {...register(`lines.${index}.debit_amount`, { 
                          valueAsNumber: true,
                          validate: (value, formValues) => {
                            const line = formValues.lines[index];
                            if (!value && !line.credit_amount) {
                              return 'Either debit or credit amount required';
                            }
                            if (value && line.credit_amount) {
                              return 'Cannot have both debit and credit on same line';
                            }
                            return true;
                          }
                        })}
                        className="w-full text-sm border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-right"
                        placeholder="0.00"
                      />
                    </td>
                    <td className="p-2">
                      <input
                        type="number"
                        step="0.01"
                        {...register(`lines.${index}.credit_amount`, { 
                          valueAsNumber: true,
                          validate: (value, formValues) => {
                            const line = formValues.lines[index];
                            if (!value && !line.debit_amount) {
                              return 'Either debit or credit amount required';
                            }
                            if (value && line.debit_amount) {
                              return 'Cannot have both debit and credit on same line';
                            }
                            return true;
                          }
                        })}
                        className="w-full text-sm border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 text-right"
                        placeholder="0.00"
                      />
                    </td>
                    <td className="p-2">
                      {fields.length > 2 && (
                        <button
                          type="button"
                          onClick={() => remove(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          ×
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 font-medium">
                  <td colSpan={3} className="p-2 text-right">Totals:</td>
                  <td className="p-2 text-right">${totalDebits.toFixed(2)}</td>
                  <td className="p-2 text-right">${totalCredits.toFixed(2)}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>

          {!isBalanced && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
              <p className="text-sm text-red-600">
                Transaction is not balanced. Difference: ${Math.abs(totalDebits - totalCredits).toFixed(2)}
              </p>
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !isBalanced}
            className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Creating...' : 'Create Transaction'}
          </button>
        </div>
      </form>
    </div>
  );
}