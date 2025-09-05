-- ============================================
-- EXPENSE PLANNING MODULE
-- Comprehensive expense planning and budgeting
-- ============================================

-- Expense Categories with hierarchical structure
CREATE TABLE expense_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    category_code VARCHAR(50) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    category_type VARCHAR(50) NOT NULL, -- 'personnel', 'operating', 'capital', 'marketing', 'travel', 'facilities'
    parent_category_id UUID REFERENCES expense_categories(id),
    allocation_driver_id UUID REFERENCES business_drivers(id),
    is_controllable BOOLEAN DEFAULT true, -- Can be directly controlled/reduced
    is_discretionary BOOLEAN DEFAULT false, -- Optional vs mandatory expense
    typical_variance_pct DECIMAL(5,2) DEFAULT 5.0, -- Expected variance percentage
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, category_code)
);

-- Expense Planning Scenarios
CREATE TABLE expense_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    scenario_id UUID REFERENCES scenarios(id),
    plan_name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50) NOT NULL, -- 'zero_based', 'incremental', 'activity_based', 'driver_based'
    fiscal_year INTEGER NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'review', 'approved', 'rejected'
    total_planned_amount DECIMAL(15,2),
    notes TEXT,
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, plan_name, fiscal_year, version)
);

-- Detailed Expense Line Items
CREATE TABLE expense_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_plan_id UUID REFERENCES expense_plans(id) ON DELETE CASCADE,
    gl_account_id UUID REFERENCES gl_accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    category_id UUID REFERENCES expense_categories(id),
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    vendor_id UUID, -- Reference to vendors table if exists
    planned_amount DECIMAL(15,2) NOT NULL,
    driver_id UUID REFERENCES business_drivers(id), -- For driver-based planning
    driver_formula TEXT, -- Formula for driver-based calculation
    headcount_impact INTEGER, -- Number of headcount if personnel expense
    justification TEXT,
    is_recurring BOOLEAN DEFAULT true,
    frequency VARCHAR(50), -- 'monthly', 'quarterly', 'annual', 'one_time'
    confidence_level DECIMAL(5,2) DEFAULT 90.0, -- Confidence in estimate (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(expense_plan_id, gl_account_id, cost_center_id, fiscal_period_id)
);

-- Vendor Management for Expense Planning
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    vendor_code VARCHAR(50) NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_type VARCHAR(50), -- 'supplier', 'contractor', 'service_provider', 'consultant'
    primary_category_id UUID REFERENCES expense_categories(id),
    payment_terms VARCHAR(50), -- 'net30', 'net60', 'immediate'
    annual_spend_limit DECIMAL(15,2),
    is_preferred BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, vendor_code)
);

-- Contract Management for Recurring Expenses
CREATE TABLE expense_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    vendor_id UUID REFERENCES vendors(id),
    contract_number VARCHAR(100) NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    contract_type VARCHAR(50), -- 'subscription', 'lease', 'service', 'maintenance'
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_amount DECIMAL(15,2),
    annual_amount DECIMAL(15,2),
    escalation_rate DECIMAL(5,2), -- Annual increase percentage
    auto_renew BOOLEAN DEFAULT false,
    notice_period_days INTEGER,
    gl_account_id UUID REFERENCES gl_accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, contract_number)
);

-- Headcount Planning (for personnel expenses)
CREATE TABLE headcount_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_plan_id UUID REFERENCES expense_plans(id) ON DELETE CASCADE,
    cost_center_id UUID REFERENCES cost_centers(id),
    position_title VARCHAR(255) NOT NULL,
    position_level VARCHAR(50), -- 'junior', 'mid', 'senior', 'manager', 'director', 'executive'
    headcount_start INTEGER NOT NULL,
    headcount_end INTEGER NOT NULL,
    average_salary DECIMAL(15,2),
    benefits_multiplier DECIMAL(5,4) DEFAULT 1.3, -- Salary * multiplier for total cost
    hire_date DATE,
    is_replacement BOOLEAN DEFAULT false,
    justification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expense Allocation Rules
CREATE TABLE expense_allocation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    source_category_id UUID REFERENCES expense_categories(id),
    source_cost_center_id UUID REFERENCES cost_centers(id),
    allocation_method VARCHAR(50) NOT NULL, -- 'percentage', 'headcount', 'revenue', 'custom_driver'
    allocation_driver_id UUID REFERENCES business_drivers(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Allocation Targets
CREATE TABLE expense_allocation_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    allocation_rule_id UUID REFERENCES expense_allocation_rules(id) ON DELETE CASCADE,
    target_cost_center_id UUID REFERENCES cost_centers(id),
    target_gl_account_id UUID REFERENCES gl_accounts(id),
    allocation_percentage DECIMAL(5,2), -- For percentage method
    allocation_formula TEXT, -- For custom formulas
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expense Benchmarks (for comparison)
CREATE TABLE expense_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    category_id UUID REFERENCES expense_categories(id),
    benchmark_type VARCHAR(50), -- 'industry_average', 'best_in_class', 'historical', 'target'
    fiscal_year INTEGER,
    benchmark_value DECIMAL(15,2),
    benchmark_percentage DECIMAL(5,2), -- As % of revenue
    source VARCHAR(255), -- Source of benchmark data
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expense Approval Workflow
CREATE TABLE expense_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_plan_id UUID REFERENCES expense_plans(id),
    approval_level INTEGER NOT NULL, -- 1, 2, 3 for multi-level approval
    approver_id UUID REFERENCES users(id),
    approval_status VARCHAR(50), -- 'pending', 'approved', 'rejected', 'requested_changes'
    approval_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_expense_categories_company ON expense_categories(company_id);
CREATE INDEX idx_expense_categories_parent ON expense_categories(parent_category_id);
CREATE INDEX idx_expense_plans_company_year ON expense_plans(company_id, fiscal_year);
CREATE INDEX idx_expense_line_items_plan ON expense_line_items(expense_plan_id);
CREATE INDEX idx_expense_line_items_period ON expense_line_items(fiscal_period_id);
CREATE INDEX idx_vendors_company ON vendors(company_id);
CREATE INDEX idx_contracts_vendor ON expense_contracts(vendor_id);
CREATE INDEX idx_contracts_dates ON expense_contracts(start_date, end_date);
CREATE INDEX idx_headcount_plans_expense ON headcount_plans(expense_plan_id);
CREATE INDEX idx_allocation_rules_company ON expense_allocation_rules(company_id);

-- ============================================
-- VIEWS FOR REPORTING
-- ============================================

-- Expense Summary by Category View
CREATE VIEW v_expense_summary_by_category AS
SELECT 
    ep.company_id,
    ep.fiscal_year,
    ec.category_name,
    ec.category_type,
    SUM(eli.planned_amount) as total_planned,
    COUNT(DISTINCT eli.cost_center_id) as num_cost_centers,
    COUNT(DISTINCT eli.vendor_id) as num_vendors,
    AVG(eli.confidence_level) as avg_confidence
FROM expense_plans ep
JOIN expense_line_items eli ON eli.expense_plan_id = ep.id
LEFT JOIN expense_categories ec ON ec.id = eli.category_id
WHERE ep.status = 'approved'
GROUP BY ep.company_id, ep.fiscal_year, ec.category_name, ec.category_type;

-- Contract Obligations View
CREATE VIEW v_contract_obligations AS
SELECT 
    c.name as company_name,
    ec.contract_number,
    ec.contract_name,
    v.vendor_name,
    ec.contract_type,
    ec.start_date,
    ec.end_date,
    ec.monthly_amount,
    ec.annual_amount,
    CASE 
        WHEN ec.end_date < CURRENT_DATE THEN 'expired'
        WHEN ec.end_date < CURRENT_DATE + INTERVAL '90 days' THEN 'expiring_soon'
        ELSE 'active'
    END as contract_status,
    cc.name as cost_center_name,
    ga.name as gl_account_name
FROM expense_contracts ec
JOIN companies c ON c.id = ec.company_id
LEFT JOIN vendors v ON v.id = ec.vendor_id
LEFT JOIN cost_centers cc ON cc.id = ec.cost_center_id
LEFT JOIN gl_accounts ga ON ga.id = ec.gl_account_id
WHERE ec.is_active = true;

-- Headcount Cost Summary View
CREATE VIEW v_headcount_cost_summary AS
SELECT 
    hp.expense_plan_id,
    cc.name as cost_center_name,
    SUM(hp.headcount_end - hp.headcount_start) as net_headcount_change,
    SUM(hp.headcount_end * hp.average_salary * hp.benefits_multiplier) as total_personnel_cost,
    AVG(hp.average_salary) as avg_salary,
    COUNT(DISTINCT hp.position_title) as num_positions
FROM headcount_plans hp
JOIN cost_centers cc ON cc.id = hp.cost_center_id
GROUP BY hp.expense_plan_id, cc.name;