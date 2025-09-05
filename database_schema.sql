-- Modern OpenFP&A Database Schema
-- Core tables for Financial Planning & Analysis Application

-- ============================================
-- 1. ORGANIZATIONAL STRUCTURE
-- ============================================

-- Companies/Entities (for multi-company support)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    currency_code CHAR(3) NOT NULL,
    fiscal_year_start_month INT CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost Centers / Departments
CREATE TABLE cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES cost_centers(id),
    manager_id UUID,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

-- ============================================
-- 2. CHART OF ACCOUNTS
-- ============================================

-- Account Types
CREATE TYPE account_type AS ENUM ('asset', 'liability', 'equity', 'revenue', 'expense');
CREATE TYPE account_subtype AS ENUM ('operating', 'non_operating', 'capital', 'other');

-- General Ledger Accounts
CREATE TABLE gl_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    account_number VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    account_type account_type NOT NULL,
    account_subtype account_subtype,
    parent_id UUID REFERENCES gl_accounts(id),
    is_summary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, account_number)
);

-- ============================================
-- 3. TIME DIMENSIONS
-- ============================================

-- Fiscal Periods
CREATE TABLE fiscal_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    fiscal_year INT NOT NULL,
    period_number INT NOT NULL CHECK (period_number BETWEEN 1 AND 12),
    period_name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, fiscal_year, period_number)
);

-- ============================================
-- 4. BUDGETS & FORECASTS
-- ============================================

-- Budget/Forecast Scenarios
CREATE TYPE scenario_type AS ENUM ('budget', 'forecast', 'actual', 'scenario');

CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    scenario_type scenario_type NOT NULL,
    fiscal_year INT NOT NULL,
    version INT DEFAULT 1,
    is_approved BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,
    created_by UUID,
    approved_by UUID,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, name, fiscal_year, version)
);

-- Budget/Forecast Line Items
CREATE TABLE budget_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    gl_account_id UUID REFERENCES gl_accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    amount DECIMAL(15, 2) NOT NULL,
    quantity DECIMAL(15, 4),
    rate DECIMAL(15, 4),
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scenario_id, gl_account_id, cost_center_id, fiscal_period_id)
);

-- ============================================
-- 5. ACTUALS
-- ============================================

-- General Ledger Transactions
CREATE TABLE gl_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    reference_number VARCHAR(100),
    description TEXT,
    source_system VARCHAR(100),
    external_id VARCHAR(255),
    is_posted BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- General Ledger Transaction Lines
CREATE TABLE gl_transaction_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gl_transaction_id UUID REFERENCES gl_transactions(id) ON DELETE CASCADE,
    gl_account_id UUID REFERENCES gl_accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    debit_amount DECIMAL(15, 2) DEFAULT 0,
    credit_amount DECIMAL(15, 2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (debit_amount >= 0 AND credit_amount >= 0),
    CHECK (debit_amount = 0 OR credit_amount = 0)
);

-- ============================================
-- 6. REPORTING & ANALYTICS
-- ============================================

-- KPI Definitions
CREATE TABLE kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    formula TEXT,
    unit_of_measure VARCHAR(50),
    target_value DECIMAL(15, 4),
    is_higher_better BOOLEAN DEFAULT true,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

-- KPI Actuals
CREATE TABLE kpi_actuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_id UUID REFERENCES kpis(id) ON DELETE CASCADE,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    actual_value DECIMAL(15, 4) NOT NULL,
    target_value DECIMAL(15, 4),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kpi_id, fiscal_period_id)
);

-- Report Templates
CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    template_config JSONB,
    is_public BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. VARIANCE ANALYSIS
-- ============================================

-- Variance Analysis
CREATE TABLE variance_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    gl_account_id UUID REFERENCES gl_accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    actual_amount DECIMAL(15, 2),
    budget_amount DECIMAL(15, 2),
    variance_amount DECIMAL(15, 2) GENERATED ALWAYS AS (actual_amount - budget_amount) STORED,
    variance_percentage DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE 
            WHEN budget_amount = 0 THEN NULL
            ELSE ((actual_amount - budget_amount) / ABS(budget_amount)) * 100
        END
    ) STORED,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, fiscal_period_id, gl_account_id, cost_center_id)
);

-- ============================================
-- 8. WORKFLOW & APPROVALS
-- ============================================

-- Approval Workflows
CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');

CREATE TABLE approval_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    object_type VARCHAR(100) NOT NULL,
    object_id UUID NOT NULL,
    status approval_status DEFAULT 'pending',
    requested_by UUID,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_approver_id UUID,
    final_approver_id UUID,
    approved_at TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 9. AUDIT & COMPLIANCE
-- ============================================

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 10. USER MANAGEMENT
-- ============================================

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Company Access
CREATE TABLE user_company_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, company_id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_gl_transactions_date ON gl_transactions(transaction_date);
CREATE INDEX idx_gl_transactions_period ON gl_transactions(fiscal_period_id);
CREATE INDEX idx_budget_lines_scenario ON budget_lines(scenario_id);
CREATE INDEX idx_budget_lines_account ON budget_lines(gl_account_id);
CREATE INDEX idx_variance_analysis_period ON variance_analysis(fiscal_period_id);
CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ============================================
-- VIEWS FOR REPORTING
-- ============================================

-- Actual vs Budget Summary View
CREATE VIEW v_actual_vs_budget AS
SELECT 
    fp.fiscal_year,
    fp.period_number,
    fp.period_name,
    cc.name AS cost_center,
    ga.account_number,
    ga.name AS account_name,
    ga.account_type,
    COALESCE(SUM(gtl.debit_amount - gtl.credit_amount), 0) AS actual_amount,
    COALESCE(bl.amount, 0) AS budget_amount,
    COALESCE(SUM(gtl.debit_amount - gtl.credit_amount), 0) - COALESCE(bl.amount, 0) AS variance
FROM fiscal_periods fp
CROSS JOIN gl_accounts ga
CROSS JOIN cost_centers cc
LEFT JOIN gl_transactions gt ON gt.fiscal_period_id = fp.id
LEFT JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id 
    AND gtl.gl_account_id = ga.id 
    AND gtl.cost_center_id = cc.id
LEFT JOIN scenarios s ON s.company_id = fp.company_id 
    AND s.fiscal_year = fp.fiscal_year 
    AND s.scenario_type = 'budget'
    AND s.is_approved = true
LEFT JOIN budget_lines bl ON bl.scenario_id = s.id 
    AND bl.fiscal_period_id = fp.id
    AND bl.gl_account_id = ga.id
    AND bl.cost_center_id = cc.id
WHERE gt.is_posted = true OR gt.is_posted IS NULL
GROUP BY fp.fiscal_year, fp.period_number, fp.period_name, 
         cc.name, ga.account_number, ga.name, ga.account_type, bl.amount;

-- P&L Summary View
CREATE VIEW v_profit_loss AS
SELECT 
    fp.fiscal_year,
    fp.period_number,
    ga.account_type,
    ga.account_subtype,
    SUM(CASE 
        WHEN ga.account_type IN ('revenue') THEN gtl.credit_amount - gtl.debit_amount
        WHEN ga.account_type IN ('expense') THEN gtl.debit_amount - gtl.credit_amount
        ELSE 0
    END) AS amount
FROM fiscal_periods fp
JOIN gl_transactions gt ON gt.fiscal_period_id = fp.id
JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id
JOIN gl_accounts ga ON ga.id = gtl.gl_account_id
WHERE gt.is_posted = true
    AND ga.account_type IN ('revenue', 'expense')
GROUP BY fp.fiscal_year, fp.period_number, ga.account_type, ga.account_subtype;