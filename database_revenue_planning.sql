-- ============================================
-- REVENUE PLANNING MODULE
-- Comprehensive revenue forecasting and planning
-- ============================================

-- Revenue Streams/Products
CREATE TABLE revenue_streams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    stream_code VARCHAR(50) NOT NULL,
    stream_name VARCHAR(255) NOT NULL,
    stream_type VARCHAR(50) NOT NULL, -- 'product', 'service', 'subscription', 'licensing', 'other'
    parent_stream_id UUID REFERENCES revenue_streams(id),
    gl_account_id UUID REFERENCES gl_accounts(id),
    recognition_method VARCHAR(50), -- 'point_in_time', 'over_time', 'milestone'
    typical_payment_terms INTEGER, -- Days
    is_recurring BOOLEAN DEFAULT false,
    recurring_frequency VARCHAR(50), -- 'monthly', 'quarterly', 'annual'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, stream_code)
);

-- Customer Segments
CREATE TABLE customer_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    segment_code VARCHAR(50) NOT NULL,
    segment_name VARCHAR(255) NOT NULL,
    segment_type VARCHAR(50), -- 'enterprise', 'mid_market', 'smb', 'consumer', 'government'
    typical_deal_size DECIMAL(15,2),
    typical_sales_cycle_days INTEGER,
    churn_rate DECIMAL(5,4), -- Monthly churn rate (0-1)
    growth_rate DECIMAL(5,4), -- Expected growth rate
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, segment_code)
);

-- Revenue Plans/Forecasts
CREATE TABLE revenue_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    scenario_id UUID REFERENCES scenarios(id),
    plan_name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50) NOT NULL, -- 'baseline', 'optimistic', 'pessimistic', 'target'
    fiscal_year INTEGER NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'review', 'approved', 'rejected'
    total_planned_revenue DECIMAL(15,2),
    confidence_level DECIMAL(5,2) DEFAULT 80.0, -- Confidence percentage
    notes TEXT,
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, plan_name, fiscal_year, version)
);

-- Revenue Forecast Details
CREATE TABLE revenue_forecast_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revenue_plan_id UUID REFERENCES revenue_plans(id) ON DELETE CASCADE,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    revenue_stream_id UUID REFERENCES revenue_streams(id),
    customer_segment_id UUID REFERENCES customer_segments(id),
    forecast_amount DECIMAL(15,2) NOT NULL,
    forecast_quantity INTEGER,
    average_price DECIMAL(15,2),
    probability DECIMAL(5,2) DEFAULT 100.0, -- Probability of closure (0-100)
    weighted_amount DECIMAL(15,2) GENERATED ALWAYS AS (forecast_amount * probability / 100) STORED,
    driver_id UUID REFERENCES business_drivers(id),
    driver_formula TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(revenue_plan_id, fiscal_period_id, revenue_stream_id, customer_segment_id)
);

-- Sales Pipeline (for pipeline-based forecasting)
CREATE TABLE sales_pipeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    opportunity_name VARCHAR(255) NOT NULL,
    customer_segment_id UUID REFERENCES customer_segments(id),
    revenue_stream_id UUID REFERENCES revenue_streams(id),
    stage VARCHAR(50) NOT NULL, -- 'lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost'
    probability DECIMAL(5,2), -- Stage probability
    amount DECIMAL(15,2),
    expected_close_date DATE,
    sales_rep_id UUID,
    created_date DATE,
    last_activity_date DATE,
    days_in_stage INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue Recognition Schedule
CREATE TABLE revenue_recognition_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    source_type VARCHAR(50), -- 'contract', 'invoice', 'forecast'
    source_id UUID, -- Reference to contract/invoice
    revenue_stream_id UUID REFERENCES revenue_streams(id),
    total_amount DECIMAL(15,2) NOT NULL,
    recognized_amount DECIMAL(15,2) DEFAULT 0,
    remaining_amount DECIMAL(15,2) GENERATED ALWAYS AS (total_amount - recognized_amount) STORED,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    recognition_method VARCHAR(50), -- 'straight_line', 'percentage_complete', 'milestone'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue Recognition Entries
CREATE TABLE revenue_recognition_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES revenue_recognition_schedule(id) ON DELETE CASCADE,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    recognition_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    is_recognized BOOLEAN DEFAULT false,
    gl_transaction_id UUID REFERENCES gl_transactions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pricing Models
CREATE TABLE pricing_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    revenue_stream_id UUID REFERENCES revenue_streams(id),
    model_name VARCHAR(255) NOT NULL,
    pricing_type VARCHAR(50), -- 'fixed', 'tiered', 'usage', 'value', 'dynamic'
    base_price DECIMAL(15,2),
    pricing_tiers JSONB, -- Tiered pricing configuration
    discount_rules JSONB, -- Volume discounts, etc.
    effective_date DATE,
    expiration_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue Metrics/KPIs
CREATE TABLE revenue_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    metric_type VARCHAR(50) NOT NULL, -- 'mrr', 'arr', 'arpu', 'ltv', 'cac', 'churn'
    metric_value DECIMAL(15,2) NOT NULL,
    segment_id UUID REFERENCES customer_segments(id),
    stream_id UUID REFERENCES revenue_streams(id),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, fiscal_period_id, metric_type, segment_id, stream_id)
);

-- Revenue Cohorts (for cohort analysis)
CREATE TABLE revenue_cohorts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    cohort_name VARCHAR(255) NOT NULL,
    cohort_date DATE NOT NULL,
    customer_segment_id UUID REFERENCES customer_segments(id),
    initial_customers INTEGER,
    initial_revenue DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, cohort_name)
);

-- Cohort Retention Data
CREATE TABLE cohort_retention (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID REFERENCES revenue_cohorts(id) ON DELETE CASCADE,
    period_offset INTEGER NOT NULL, -- Months since cohort start
    retained_customers INTEGER,
    retained_revenue DECIMAL(15,2),
    retention_rate DECIMAL(5,4), -- Percentage (0-1)
    revenue_retention_rate DECIMAL(5,4), -- Net revenue retention
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cohort_id, period_offset)
);

-- Revenue Seasonality Patterns
CREATE TABLE revenue_seasonality (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    revenue_stream_id UUID REFERENCES revenue_streams(id),
    month_number INTEGER CHECK (month_number BETWEEN 1 AND 12),
    seasonality_index DECIMAL(5,4), -- 1.0 = average, >1 = above average
    historical_avg DECIMAL(15,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, revenue_stream_id, month_number)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_revenue_streams_company ON revenue_streams(company_id);
CREATE INDEX idx_revenue_streams_parent ON revenue_streams(parent_stream_id);
CREATE INDEX idx_customer_segments_company ON customer_segments(company_id);
CREATE INDEX idx_revenue_plans_company_year ON revenue_plans(company_id, fiscal_year);
CREATE INDEX idx_revenue_forecast_lines_plan ON revenue_forecast_lines(revenue_plan_id);
CREATE INDEX idx_sales_pipeline_company_stage ON sales_pipeline(company_id, stage);
CREATE INDEX idx_sales_pipeline_close_date ON sales_pipeline(expected_close_date);
CREATE INDEX idx_recognition_schedule_dates ON revenue_recognition_schedule(start_date, end_date);
CREATE INDEX idx_revenue_metrics_period ON revenue_metrics(fiscal_period_id);
CREATE INDEX idx_cohort_retention_cohort ON cohort_retention(cohort_id);

-- ============================================
-- VIEWS FOR REPORTING
-- ============================================

-- Revenue Summary by Stream View
CREATE VIEW v_revenue_summary_by_stream AS
SELECT 
    rp.company_id,
    rp.fiscal_year,
    rs.stream_name,
    rs.stream_type,
    SUM(rfl.forecast_amount) as total_forecast,
    SUM(rfl.weighted_amount) as weighted_forecast,
    AVG(rfl.probability) as avg_probability,
    COUNT(DISTINCT rfl.customer_segment_id) as num_segments
FROM revenue_plans rp
JOIN revenue_forecast_lines rfl ON rfl.revenue_plan_id = rp.id
JOIN revenue_streams rs ON rs.id = rfl.revenue_stream_id
WHERE rp.status = 'approved'
GROUP BY rp.company_id, rp.fiscal_year, rs.stream_name, rs.stream_type;

-- Pipeline Summary View
CREATE VIEW v_pipeline_summary AS
SELECT 
    company_id,
    stage,
    COUNT(*) as opportunity_count,
    SUM(amount) as total_amount,
    SUM(amount * probability / 100) as weighted_amount,
    AVG(probability) as avg_probability,
    AVG(days_in_stage) as avg_days_in_stage
FROM sales_pipeline
WHERE is_active = true
GROUP BY company_id, stage;

-- MRR/ARR Calculation View
CREATE VIEW v_recurring_revenue AS
SELECT 
    c.id as company_id,
    c.name as company_name,
    fp.fiscal_year,
    fp.period_number,
    SUM(CASE 
        WHEN rs.recurring_frequency = 'monthly' THEN rfl.forecast_amount
        WHEN rs.recurring_frequency = 'quarterly' THEN rfl.forecast_amount / 3
        WHEN rs.recurring_frequency = 'annual' THEN rfl.forecast_amount / 12
        ELSE 0
    END) as mrr,
    SUM(CASE 
        WHEN rs.recurring_frequency = 'monthly' THEN rfl.forecast_amount * 12
        WHEN rs.recurring_frequency = 'quarterly' THEN rfl.forecast_amount * 4
        WHEN rs.recurring_frequency = 'annual' THEN rfl.forecast_amount
        ELSE 0
    END) as arr
FROM companies c
JOIN revenue_plans rp ON rp.company_id = c.id
JOIN revenue_forecast_lines rfl ON rfl.revenue_plan_id = rp.id
JOIN revenue_streams rs ON rs.id = rfl.revenue_stream_id
JOIN fiscal_periods fp ON fp.id = rfl.fiscal_period_id
WHERE rs.is_recurring = true
AND rp.status = 'approved'
GROUP BY c.id, c.name, fp.fiscal_year, fp.period_number;