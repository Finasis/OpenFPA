import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import type {
  Company,
  CompanyCreateRequest,
  CompanyUpdateRequest,
  CostCenter,
  CostCenterCreateRequest,
  CostCenterUpdateRequest,
  GLAccount,
  GLAccountCreateRequest,
  GLAccountUpdateRequest,
  FiscalPeriod,
  FiscalPeriodCreateRequest,
  FiscalPeriodUpdateRequest,
  Scenario,
  ScenarioCreateRequest,
  ScenarioUpdateRequest,
  BudgetLine,
  BudgetLineCreateRequest,
  BudgetLineUpdateRequest,
  GLTransaction,
  GLTransactionCreateRequest,
  UUID,
  ErrorResponse,
  CompanyFilters,
  GLAccountFilters,
  FiscalPeriodFilters,
  ScenarioFilters,
} from '@/types';

// ============================================
// CUSTOM ERROR CLASS
// ============================================

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly code?: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

// ============================================
// API CLIENT CONFIGURATION
// ============================================

const createApiClient = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || '/api/v1',
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 seconds
  });

  // Request interceptor for auth token
  instance.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling
  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ErrorResponse>) => {
      if (error.response) {
        const message = error.response.data?.detail || 'An error occurred';
        const status = error.response.status;
        const code = error.response.data?.type;
        
        throw new ApiError(message, status, code, error.response.data);
      } else if (error.request) {
        throw new ApiError('No response from server', undefined, 'NETWORK_ERROR');
      } else {
        throw new ApiError(error.message || 'Request failed', undefined, 'REQUEST_ERROR');
      }
    }
  );

  return instance;
};

export const api = createApiClient();

// ============================================
// GENERIC API METHODS
// ============================================

interface ApiClient<T, TCreate, TUpdate> {
  getAll(filters?: Record<string, unknown>): Promise<T[]>;
  getById(id: UUID): Promise<T>;
  create(data: TCreate): Promise<T>;
  update(id: UUID, data: TUpdate): Promise<T>;
  delete(id: UUID): Promise<void>;
}

const createCrudApi = <T, TCreate, TUpdate>(
  endpoint: string
): ApiClient<T, TCreate, TUpdate> => ({
  async getAll(filters?: Record<string, unknown>): Promise<T[]> {
    const response = await api.get<T[]>(endpoint, { params: filters });
    return response.data;
  },

  async getById(id: UUID): Promise<T> {
    const response = await api.get<T>(`${endpoint}/${id}`);
    return response.data;
  },

  async create(data: TCreate): Promise<T> {
    const response = await api.post<T>(endpoint, data);
    return response.data;
  },

  async update(id: UUID, data: TUpdate): Promise<T> {
    const response = await api.put<T>(`${endpoint}/${id}`, data);
    return response.data;
  },

  async delete(id: UUID): Promise<void> {
    await api.delete(`${endpoint}/${id}`);
  },
});

// ============================================
// COMPANY API
// ============================================

interface CompanyApi extends ApiClient<Company, CompanyCreateRequest, CompanyUpdateRequest> {
  getAll(filters?: CompanyFilters): Promise<Company[]>;
}

export const companyApi: CompanyApi = {
  ...createCrudApi<Company, CompanyCreateRequest, CompanyUpdateRequest>('/companies'),
  
  async getAll(filters?: CompanyFilters): Promise<Company[]> {
    const response = await api.get<Company[]>('/companies', { params: filters });
    return response.data;
  },
};

// ============================================
// COST CENTER API
// ============================================

interface CostCenterApi extends ApiClient<CostCenter, CostCenterCreateRequest, CostCenterUpdateRequest> {
  getByCompany(companyId: UUID): Promise<CostCenter[]>;
  getHierarchy(companyId: UUID): Promise<CostCenter[]>;
}

export const costCenterApi: CostCenterApi = {
  ...createCrudApi<CostCenter, CostCenterCreateRequest, CostCenterUpdateRequest>('/cost-centers'),
  
  async getByCompany(companyId: UUID): Promise<CostCenter[]> {
    const response = await api.get<CostCenter[]>(`/companies/${companyId}/cost-centers`);
    return response.data;
  },
  
  async getHierarchy(companyId: UUID): Promise<CostCenter[]> {
    const response = await api.get<CostCenter[]>(`/companies/${companyId}/cost-centers/hierarchy`);
    return response.data;
  },
};

// ============================================
// GL ACCOUNT API
// ============================================

interface GLAccountApi extends ApiClient<GLAccount, GLAccountCreateRequest, GLAccountUpdateRequest> {
  getByCompany(companyId: UUID, filters?: GLAccountFilters): Promise<GLAccount[]>;
  getByType(companyId: UUID, accountType: string): Promise<GLAccount[]>;
}

export const glAccountApi: GLAccountApi = {
  ...createCrudApi<GLAccount, GLAccountCreateRequest, GLAccountUpdateRequest>('/gl-accounts'),
  
  async getByCompany(companyId: UUID, filters?: GLAccountFilters): Promise<GLAccount[]> {
    const response = await api.get<GLAccount[]>(`/companies/${companyId}/gl-accounts`, { params: filters });
    return response.data;
  },
  
  async getByType(companyId: UUID, accountType: string): Promise<GLAccount[]> {
    const response = await api.get<GLAccount[]>(`/companies/${companyId}/gl-accounts`, {
      params: { account_type: accountType }
    });
    return response.data;
  },
};

// ============================================
// FISCAL PERIOD API
// ============================================

interface FiscalPeriodApi extends ApiClient<FiscalPeriod, FiscalPeriodCreateRequest, FiscalPeriodUpdateRequest> {
  getByCompany(companyId: UUID, filters?: FiscalPeriodFilters): Promise<FiscalPeriod[]>;
  close(id: UUID): Promise<FiscalPeriod>;
  reopen(id: UUID): Promise<FiscalPeriod>;
}

export const fiscalPeriodApi: FiscalPeriodApi = {
  ...createCrudApi<FiscalPeriod, FiscalPeriodCreateRequest, FiscalPeriodUpdateRequest>('/fiscal-periods'),
  
  async getByCompany(companyId: UUID, filters?: FiscalPeriodFilters): Promise<FiscalPeriod[]> {
    const response = await api.get<FiscalPeriod[]>(`/companies/${companyId}/fiscal-periods`, { params: filters });
    return response.data;
  },
  
  async close(id: UUID): Promise<FiscalPeriod> {
    const response = await api.post<FiscalPeriod>(`/fiscal-periods/${id}/close`);
    return response.data;
  },
  
  async reopen(id: UUID): Promise<FiscalPeriod> {
    const response = await api.post<FiscalPeriod>(`/fiscal-periods/${id}/reopen`);
    return response.data;
  },
};

// ============================================
// SCENARIO API
// ============================================

interface ScenarioApi extends ApiClient<Scenario, ScenarioCreateRequest, ScenarioUpdateRequest> {
  getByCompany(companyId: UUID, filters?: ScenarioFilters): Promise<Scenario[]>;
  approve(id: UUID, approvedBy: UUID): Promise<Scenario>;
  lock(id: UUID): Promise<Scenario>;
  unlock(id: UUID): Promise<Scenario>;
  duplicate(id: UUID, newName: string): Promise<Scenario>;
}

export const scenarioApi: ScenarioApi = {
  ...createCrudApi<Scenario, ScenarioCreateRequest, ScenarioUpdateRequest>('/scenarios'),
  
  async getByCompany(companyId: UUID, filters?: ScenarioFilters): Promise<Scenario[]> {
    const response = await api.get<Scenario[]>(`/companies/${companyId}/scenarios`, { params: filters });
    return response.data;
  },
  
  async approve(id: UUID, approvedBy: UUID): Promise<Scenario> {
    const scenario = await api.post<Scenario>(`/scenarios/${id}/approve`, null, {
      params: { approved_by: approvedBy }
    });
    return scenario;
  },
  
  async lock(id: UUID): Promise<Scenario> {
    const scenario = await api.post<Scenario>(`/scenarios/${id}/lock`);
    return scenario;
  },
  
  async unlock(id: UUID): Promise<Scenario> {
    const scenario = await api.post<Scenario>(`/scenarios/${id}/unlock`);
    return scenario;
  },
  
  async duplicate(id: UUID, newName: string): Promise<Scenario> {
    const scenario = await api.post<Scenario>(`/scenarios/${id}/duplicate`, { name: newName });
    return scenario;
  },
};

// ============================================
// BUDGET LINE API
// ============================================

interface BudgetLineApi extends ApiClient<BudgetLine, BudgetLineCreateRequest, BudgetLineUpdateRequest> {
  getByScenario(scenarioId: UUID): Promise<BudgetLine[]>;
  getByAccount(scenarioId: UUID, accountId: UUID): Promise<BudgetLine[]>;
  bulkCreate(data: BudgetLineCreateRequest[]): Promise<BudgetLine[]>;
  bulkUpdate(updates: Array<{ id: UUID; data: BudgetLineUpdateRequest }>): Promise<BudgetLine[]>;
}

export const budgetLineApi: BudgetLineApi = {
  ...createCrudApi<BudgetLine, BudgetLineCreateRequest, BudgetLineUpdateRequest>('/budget-lines'),
  
  async getByScenario(scenarioId: UUID): Promise<BudgetLine[]> {
    const response = await api.get<BudgetLine[]>(`/scenarios/${scenarioId}/budget-lines`);
    return response.data;
  },
  
  async getByAccount(scenarioId: UUID, accountId: UUID): Promise<BudgetLine[]> {
    const response = await api.get<BudgetLine[]>(`/scenarios/${scenarioId}/budget-lines`, {
      params: { gl_account_id: accountId }
    });
    return response.data;
  },
  
  async bulkCreate(data: BudgetLineCreateRequest[]): Promise<BudgetLine[]> {
    const response = await api.post<BudgetLine[]>('/budget-lines/bulk', data);
    return response.data;
  },
  
  async bulkUpdate(updates: Array<{ id: UUID; data: BudgetLineUpdateRequest }>): Promise<BudgetLine[]> {
    const response = await api.put<BudgetLine[]>('/budget-lines/bulk', updates);
    return response.data;
  },
};

// ============================================
// GL TRANSACTION API
// ============================================

interface GLTransactionApi {
  getById(id: UUID): Promise<GLTransaction>;
  getByCompany(companyId: UUID, filters?: Record<string, unknown>): Promise<GLTransaction[]>;
  getByPeriod(companyId: UUID, periodId: UUID): Promise<GLTransaction[]>;
  create(data: GLTransactionCreateRequest): Promise<GLTransaction>;
  post(id: UUID): Promise<GLTransaction>;
  void(id: UUID, reason: string): Promise<GLTransaction>;
  duplicate(id: UUID): Promise<GLTransaction>;
  validate(data: GLTransactionCreateRequest): Promise<{ valid: boolean; errors?: string[] }>;
}

export const glTransactionApi: GLTransactionApi = {
  async getById(id: UUID): Promise<GLTransaction> {
    const response = await api.get<GLTransaction>(`/gl-transactions/${id}`);
    return response.data;
  },
  
  async getByCompany(companyId: UUID, filters?: Record<string, unknown>): Promise<GLTransaction[]> {
    const response = await api.get<GLTransaction[]>(`/companies/${companyId}/gl-transactions`, { params: filters });
    return response.data;
  },
  
  async getByPeriod(companyId: UUID, periodId: UUID): Promise<GLTransaction[]> {
    const response = await api.get<GLTransaction[]>(`/companies/${companyId}/gl-transactions`, {
      params: { fiscal_period_id: periodId }
    });
    return response.data;
  },
  
  async create(data: GLTransactionCreateRequest): Promise<GLTransaction> {
    const response = await api.post<GLTransaction>('/gl-transactions', data);
    return response.data;
  },
  
  async post(id: UUID): Promise<GLTransaction> {
    const response = await api.post<GLTransaction>(`/gl-transactions/${id}/post`);
    return response.data;
  },
  
  async void(id: UUID, reason: string): Promise<GLTransaction> {
    const response = await api.post<GLTransaction>(`/gl-transactions/${id}/void`, { reason });
    return response.data;
  },
  
  async duplicate(id: UUID): Promise<GLTransaction> {
    const response = await api.post<GLTransaction>(`/gl-transactions/${id}/duplicate`);
    return response.data;
  },
  
  async validate(data: GLTransactionCreateRequest): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await api.post<{ valid: boolean; errors?: string[] }>('/gl-transactions/validate', data);
    return response.data;
  },
};

// ============================================
// UTILITY FUNCTIONS
// ============================================

export const isApiError = (error: unknown): error is ApiError => {
  return error instanceof ApiError;
};

export const getErrorMessage = (error: unknown): string => {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const handleApiError = (error: unknown, fallbackMessage = 'Operation failed'): string => {
  console.error('API Error:', error);
  
  if (isApiError(error)) {
    switch (error.status) {
      case 400:
        return error.message || 'Invalid request';
      case 401:
        return 'Authentication required';
      case 403:
        return 'Permission denied';
      case 404:
        return 'Resource not found';
      case 409:
        return error.message || 'Conflict with existing data';
      case 422:
        return error.message || 'Validation failed';
      case 500:
        return 'Server error - please try again later';
      default:
        return error.message || fallbackMessage;
    }
  }
  
  return getErrorMessage(error) || fallbackMessage;
};