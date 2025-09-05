// ============================================
// BASE TYPES AND CONSTANTS
// ============================================

// Using const assertions for better type inference
export const AccountTypes = {
  ASSET: 'asset',
  LIABILITY: 'liability',
  EQUITY: 'equity',
  REVENUE: 'revenue',
  EXPENSE: 'expense',
} as const;

export const AccountSubtypes = {
  OPERATING: 'operating',
  NON_OPERATING: 'non_operating',
  CAPITAL: 'capital',
  OTHER: 'other',
} as const;

export const ScenarioTypes = {
  BUDGET: 'budget',
  FORECAST: 'forecast',
  ACTUAL: 'actual',
  SCENARIO: 'scenario',
} as const;

export const TransactionStatus = {
  DRAFT: 'draft',
  POSTED: 'posted',
  VOIDED: 'voided',
} as const;

// Type aliases from const objects
export type AccountType = typeof AccountTypes[keyof typeof AccountTypes];
export type AccountSubtype = typeof AccountSubtypes[keyof typeof AccountSubtypes];
export type ScenarioType = typeof ScenarioTypes[keyof typeof ScenarioTypes];
export type TransactionStatusType = typeof TransactionStatus[keyof typeof TransactionStatus];

// ============================================
// BRANDED TYPES FOR TYPE SAFETY
// ============================================

// Branded types prevent mixing up similar string types
type Brand<T, B> = T & { __brand: B };

export type UUID = Brand<string, 'UUID'>;
export type CurrencyCode = Brand<string, 'CurrencyCode'>;
export type AccountNumber = Brand<string, 'AccountNumber'>;
export type CompanyCode = Brand<string, 'CompanyCode'>;
export type ISODateString = Brand<string, 'ISODateString'>;

// ============================================
// BASE INTERFACES WITH READONLY PROPERTIES
// ============================================

// Common audit fields
interface AuditFields {
  readonly created_at: ISODateString;
  readonly updated_at: ISODateString;
  readonly created_by?: UUID;
  readonly updated_by?: UUID;
}

// Common active/inactive pattern
interface ActiveStatus {
  readonly is_active: boolean;
}

// ============================================
// DOMAIN MODELS
// ============================================

export interface Company extends AuditFields, ActiveStatus {
  readonly id: UUID;
  readonly code: CompanyCode;
  readonly name: string;
  readonly currency_code: CurrencyCode;
  readonly fiscal_year_start_month?: number;
}

export interface CostCenter extends AuditFields, ActiveStatus {
  readonly id: UUID;
  readonly company_id: UUID;
  readonly code: string;
  readonly name: string;
  readonly parent_id?: UUID | null;
  readonly manager_id?: UUID | null;
  readonly type?: 'operational' | 'administrative' | 'sales';
}

export interface GLAccount extends AuditFields, ActiveStatus {
  readonly id: UUID;
  readonly company_id: UUID;
  readonly account_number: AccountNumber;
  readonly name: string;
  readonly account_type: AccountType;
  readonly account_subtype?: AccountSubtype | null;
  readonly parent_id?: UUID | null;
  readonly is_summary: boolean;
  readonly normal_balance?: 'debit' | 'credit';
}

export interface FiscalPeriod extends AuditFields {
  readonly id: UUID;
  readonly company_id: UUID;
  readonly fiscal_year: number;
  readonly period_number: number;
  readonly period_name: string;
  readonly start_date: ISODateString;
  readonly end_date: ISODateString;
  readonly is_closed: boolean;
  readonly closed_at?: ISODateString | null;
  readonly closed_by?: UUID | null;
}

export interface Scenario extends AuditFields {
  readonly id: UUID;
  readonly company_id: UUID;
  readonly name: string;
  readonly scenario_type: ScenarioType;
  readonly fiscal_year: number;
  readonly version: number;
  readonly is_approved: boolean;
  readonly is_locked: boolean;
  readonly approved_by?: UUID | null;
  readonly approved_at?: ISODateString | null;
}

export interface BudgetLine extends AuditFields {
  readonly id: UUID;
  readonly scenario_id: UUID;
  readonly gl_account_id: UUID;
  readonly cost_center_id: UUID;
  readonly fiscal_period_id: UUID;
  readonly amount: number;
  readonly quantity?: number | null;
  readonly rate?: number | null;
  readonly notes?: string | null;
}

export interface GLTransactionLine {
  readonly id: UUID;
  readonly gl_account_id: UUID;
  readonly cost_center_id: UUID;
  readonly debit_amount: number;
  readonly credit_amount: number;
  readonly description?: string | null;
  readonly created_at: ISODateString;
}

export interface GLTransaction extends AuditFields {
  readonly id: UUID;
  readonly company_id: UUID;
  readonly transaction_date: ISODateString;
  readonly fiscal_period_id: UUID;
  readonly reference_number?: string | null;
  readonly description?: string | null;
  readonly source_system?: string | null;
  readonly external_id?: string | null;
  readonly status: TransactionStatusType;
  readonly is_posted: boolean;
  readonly posted_at?: ISODateString | null;
  readonly posted_by?: UUID | null;
  readonly transaction_lines: readonly GLTransactionLine[];
}

// ============================================
// API REQUEST/RESPONSE TYPES
// ============================================

// Request types - use Partial and Pick for flexibility
export type CompanyCreateRequest = Pick<Company, 'code' | 'name' | 'currency_code'> & 
  Partial<Pick<Company, 'fiscal_year_start_month' | 'is_active'>>;

export type CompanyUpdateRequest = Partial<Omit<Company, 'id' | 'created_at' | 'updated_at'>>;

export type CostCenterCreateRequest = Pick<CostCenter, 'company_id' | 'code' | 'name'> & 
  Partial<Pick<CostCenter, 'parent_id' | 'manager_id' | 'type' | 'is_active'>>;

export type CostCenterUpdateRequest = Partial<Omit<CostCenter, 'id' | 'company_id' | 'created_at' | 'updated_at'>>;

export type GLAccountCreateRequest = Pick<GLAccount, 'company_id' | 'account_number' | 'name' | 'account_type'> & 
  Partial<Pick<GLAccount, 'account_subtype' | 'parent_id' | 'is_summary' | 'is_active' | 'normal_balance'>>;

export type GLAccountUpdateRequest = Partial<Omit<GLAccount, 'id' | 'company_id' | 'created_at' | 'updated_at'>>;

export type FiscalPeriodCreateRequest = Pick<FiscalPeriod, 'company_id' | 'fiscal_year' | 'period_number' | 'period_name' | 'start_date' | 'end_date'>;

export type FiscalPeriodUpdateRequest = Partial<Pick<FiscalPeriod, 'period_name' | 'start_date' | 'end_date' | 'is_closed'>>;

export type ScenarioCreateRequest = Pick<Scenario, 'company_id' | 'name' | 'scenario_type' | 'fiscal_year'> & 
  Partial<Pick<Scenario, 'version'>>;

export type ScenarioUpdateRequest = Partial<Pick<Scenario, 'name' | 'is_approved' | 'is_locked'>>;

export type BudgetLineCreateRequest = Pick<BudgetLine, 'scenario_id' | 'gl_account_id' | 'cost_center_id' | 'fiscal_period_id' | 'amount'> & 
  Partial<Pick<BudgetLine, 'quantity' | 'rate' | 'notes'>>;

export type BudgetLineUpdateRequest = Partial<Pick<BudgetLine, 'amount' | 'quantity' | 'rate' | 'notes'>>;

// Transaction line for creation (without id and timestamps)
export interface GLTransactionLineCreateRequest {
  gl_account_id: UUID;
  cost_center_id: UUID;
  debit_amount: number;
  credit_amount: number;
  description?: string | null;
}

export type GLTransactionCreateRequest = Pick<GLTransaction, 'company_id' | 'transaction_date' | 'fiscal_period_id'> & 
  Partial<Pick<GLTransaction, 'reference_number' | 'description' | 'source_system' | 'external_id'>> & {
  transaction_lines: GLTransactionLineCreateRequest[];
};

// ============================================
// API RESPONSE TYPES
// ============================================

export interface ApiResponse<T> {
  readonly data: T;
  readonly status: 'success' | 'error';
  readonly message?: string;
}

export interface PaginatedResponse<T> {
  readonly items: readonly T[];
  readonly total: number;
  readonly page: number;
  readonly limit: number;
  readonly has_next: boolean;
  readonly has_prev: boolean;
}

export interface ErrorResponse {
  readonly detail: string;
  readonly status_code: number;
  readonly type?: string;
}

// ============================================
// FILTER AND QUERY TYPES
// ============================================

export interface CompanyFilters {
  readonly is_active?: boolean;
  readonly currency_code?: CurrencyCode;
  readonly search?: string;
}

export interface GLAccountFilters {
  readonly account_type?: AccountType;
  readonly is_active?: boolean;
  readonly is_summary?: boolean;
  readonly search?: string;
}

export interface FiscalPeriodFilters {
  readonly fiscal_year?: number;
  readonly is_closed?: boolean;
}

export interface ScenarioFilters {
  readonly scenario_type?: ScenarioType;
  readonly fiscal_year?: number;
  readonly is_approved?: boolean;
  readonly is_locked?: boolean;
}

// ============================================
// TYPE GUARDS
// ============================================

export const isUUID = (value: unknown): value is UUID => {
  return typeof value === 'string' && 
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
};

export const isCurrencyCode = (value: unknown): value is CurrencyCode => {
  return typeof value === 'string' && /^[A-Z]{3}$/.test(value);
};

export const isISODateString = (value: unknown): value is ISODateString => {
  if (typeof value !== 'string') return false;
  const date = new Date(value);
  return !isNaN(date.getTime()) && date.toISOString() === value;
};

export const isAccountType = (value: unknown): value is AccountType => {
  return typeof value === 'string' && Object.values(AccountTypes).includes(value as AccountType);
};

export const isScenarioType = (value: unknown): value is ScenarioType => {
  return typeof value === 'string' && Object.values(ScenarioTypes).includes(value as ScenarioType);
};

// ============================================
// UTILITY TYPES
// ============================================

// Make all properties mutable (remove readonly)
export type Mutable<T> = {
  -readonly [K in keyof T]: T[K];
};

// Make all properties optional and remove readonly
export type PartialMutable<T> = {
  -readonly [K in keyof T]?: T[K];
};

// Extract only the keys that are not readonly
export type WritableKeys<T> = {
  [K in keyof T]-?: IfEquals<
    { [Q in K]: T[K] },
    { -readonly [Q in K]: T[K] },
    K
  >
}[keyof T];

// Helper type for checking equality
type IfEquals<X, Y, A = X, B = never> =
  (<T>() => T extends X ? 1 : 2) extends
  (<T>() => T extends Y ? 1 : 2) ? A : B;

// ============================================
// VALIDATION HELPERS
// ============================================

export interface ValidationError {
  readonly field: string;
  readonly message: string;
  readonly code?: string;
}

export interface ValidationResult<T> {
  readonly success: boolean;
  readonly data?: T;
  readonly errors?: readonly ValidationError[];
}

// ============================================
// ANALYTICS TYPES
// ============================================

export interface DashboardMetrics {
  readonly revenue: number;
  readonly expenses: number;
  readonly profit: number;
  readonly margin: number;
  readonly period: string;
}

export interface KPIMetric {
  readonly name: string;
  readonly value: number;
  readonly target: number;
  readonly unit?: string;
  readonly status: 'good' | 'warning' | 'danger';
  readonly trend?: 'up' | 'down' | 'stable';
}

export interface VarianceAnalysis {
  readonly account_code: string;
  readonly account_name: string;
  readonly account_type: string;
  readonly budget: number;
  readonly actual: number;
  readonly variance: number;
  readonly variance_percentage: number;
  readonly status: 'favorable' | 'unfavorable' | 'neutral';
}