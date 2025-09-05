-- Analytics & Planning Extensions
-- Additional tables for advanced FP&A functionality

-- ============================================
-- FORECASTING & PREDICTIONS
-- ============================================

-- Forecast Models
CREATE TABLE forecast_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'linear_regression', 'moving_average', 'seasonal', 'driver_based'
    gl_account_id UUID REFERENCES gl_accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    configuration JSONB, -- Model-specific parameters
    is_active BOOLEAN DEFAULT true,
    accuracy_score DECIMAL(5,4), -- R-squared or similar metric
    last_trained_at TIMESTAMP,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, name)
);

-- Forecast Results
CREATE TABLE forecast_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_model_id UUID REFERENCES forecast_models(id) ON DELETE CASCADE,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    forecasted_amount DECIMAL(15, 2) NOT NULL,
    confidence_interval_low DECIMAL(15, 2),
    confidence_interval_high DECIMAL(15, 2),
    confidence_score DECIMAL(5,4), -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(forecast_model_id, fiscal_period_id)
);

-- Business Drivers for driver-based planning
CREATE TABLE business_drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    unit_of_measure VARCHAR(50),
    category VARCHAR(100), -- 'volume', 'price', 'efficiency', 'external'
    is_external BOOLEAN DEFAULT false, -- External factors like inflation, currency rates
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

-- Driver Values (actuals and plans)
CREATE TABLE driver_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_driver_id UUID REFERENCES business_drivers(id) ON DELETE CASCADE,
    fiscal_period_id UUID REFERENCES fiscal_periods(id),
    scenario_id UUID REFERENCES scenarios(id), -- NULL for actuals
    actual_value DECIMAL(15, 4),
    planned_value DECIMAL(15, 4),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_driver_id, fiscal_period_id, scenario_id)
);

-- Driver Relationships (how drivers affect GL accounts)
CREATE TABLE driver_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_driver_id UUID REFERENCES business_drivers(id) ON DELETE CASCADE,
    gl_account_id UUID REFERENCES gl_accounts(id) ON DELETE CASCADE,
    cost_center_id UUID REFERENCES cost_centers(id),
    relationship_type VARCHAR(50) NOT NULL, -- 'linear', 'percentage', 'step_function', 'custom_formula'
    coefficient DECIMAL(15, 6), -- Multiplier for linear relationships
    formula TEXT, -- Custom formula for complex relationships
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DASHBOARD & ANALYTICS
-- ============================================

-- Dashboard Definitions
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    dashboard_type VARCHAR(50) NOT NULL, -- 'executive', 'operational', 'variance', 'kpi'
    layout_config JSONB, -- Widget positions, sizes, etc.
    filters_config JSONB, -- Default filters
    is_public BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard Widgets
CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(50) NOT NULL, -- 'kpi_card', 'chart', 'table', 'variance_analysis'
    title VARCHAR(255) NOT NULL,
    configuration JSONB, -- Widget-specific config (chart type, data source, etc.)
    position_x INT,
    position_y INT,
    width INT,
    height INT,
    refresh_interval INT, -- Minutes
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Widget Data Sources
CREATE TABLE widget_data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_widget_id UUID REFERENCES dashboard_widgets(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL, -- 'kpi', 'gl_account', 'variance', 'forecast', 'custom_query'
    source_id UUID, -- ID of the source object
    configuration JSONB, -- Source-specific config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- VARIANCE ANALYSIS EXTENSIONS
-- ============================================

-- Variance Explanations & Comments
CREATE TABLE variance_explanations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variance_analysis_id UUID REFERENCES variance_analysis(id) ON DELETE CASCADE,
    explanation_text TEXT NOT NULL,
    impact_category VARCHAR(50), -- 'volume', 'price', 'efficiency', 'timing', 'one_time'
    corrective_action TEXT,
    responsible_person UUID,
    due_date DATE,
    status VARCHAR(50) DEFAULT 'open', -- 'open', 'in_progress', 'resolved'
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Variance Thresholds for automatic alerts
CREATE TABLE variance_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    gl_account_id UUID REFERENCES gl_accounts(id),
    cost_center_id UUID REFERENCES cost_centers(id),
    threshold_type VARCHAR(50) NOT NULL, -- 'percentage', 'absolute'
    warning_threshold DECIMAL(15, 2) NOT NULL,
    critical_threshold DECIMAL(15, 2) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SCENARIO ANALYSIS & WHAT-IF
-- ============================================

-- Scenario Assumptions
CREATE TABLE scenario_assumptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    assumption_type VARCHAR(50) NOT NULL, -- 'growth_rate', 'inflation', 'headcount', 'custom'
    name VARCHAR(255) NOT NULL,
    base_value DECIMAL(15, 4),
    adjusted_value DECIMAL(15, 4),
    unit_of_measure VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scenario Comparisons
CREATE TABLE scenario_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    base_scenario_id UUID REFERENCES scenarios(id),
    comparison_scenarios UUID[], -- Array of scenario IDs
    comparison_config JSONB,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_forecast_results_period ON forecast_results(fiscal_period_id);
CREATE INDEX idx_forecast_results_model ON forecast_results(forecast_model_id);
CREATE INDEX idx_driver_values_period ON driver_values(fiscal_period_id);
CREATE INDEX idx_driver_values_driver ON driver_values(business_driver_id);
CREATE INDEX idx_dashboard_widgets_dashboard ON dashboard_widgets(dashboard_id);
CREATE INDEX idx_variance_explanations_analysis ON variance_explanations(variance_analysis_id);
CREATE INDEX idx_scenario_assumptions_scenario ON scenario_assumptions(scenario_id);

-- ============================================
-- ADVANCED VIEWS
-- ============================================

-- Executive KPI Summary
CREATE VIEW v_executive_kpis AS
SELECT 
    k.company_id,
    k.name,
    k.category,
    ka.fiscal_period_id,
    fp.period_name,
    fp.fiscal_year,
    ka.actual_value,
    ka.target_value,
    CASE 
        WHEN ka.target_value = 0 THEN NULL
        WHEN k.is_higher_better THEN 
            CASE WHEN ka.actual_value >= ka.target_value THEN 'on_target' ELSE 'below_target' END
        ELSE 
            CASE WHEN ka.actual_value <= ka.target_value THEN 'on_target' ELSE 'above_target' END
    END as performance_status,
    CASE 
        WHEN ka.target_value = 0 THEN NULL
        ELSE ((ka.actual_value - ka.target_value) / ABS(ka.target_value)) * 100
    END as variance_percentage
FROM kpis k
JOIN kpi_actuals ka ON ka.kpi_id = k.id
JOIN fiscal_periods fp ON fp.id = ka.fiscal_period_id
WHERE k.is_active = true;

-- Forecast Accuracy View
CREATE VIEW v_forecast_accuracy AS
SELECT 
    fm.company_id,
    fm.name as model_name,
    fm.model_type,
    fp.fiscal_year,
    fp.period_number,
    fr.forecasted_amount,
    COALESCE(SUM(gtl.debit_amount - gtl.credit_amount), 0) AS actual_amount,
    ABS(fr.forecasted_amount - COALESCE(SUM(gtl.debit_amount - gtl.credit_amount), 0)) AS absolute_error,
    CASE 
        WHEN COALESCE(SUM(gtl.debit_amount - gtl.credit_amount), 0) = 0 THEN NULL
        ELSE ABS(fr.forecasted_amount - COALESCE(SUM(gtl.debit_amount - gtl.credit_amount), 0)) / 
             ABS(COALESCE(SUM(gtl.debit_amount - gtl.credit_amount), 0)) * 100
    END as mape_error
FROM forecast_models fm
JOIN forecast_results fr ON fr.forecast_model_id = fm.id
JOIN fiscal_periods fp ON fp.id = fr.fiscal_period_id
LEFT JOIN gl_transactions gt ON gt.fiscal_period_id = fp.id
LEFT JOIN gl_transaction_lines gtl ON gtl.gl_transaction_id = gt.id 
    AND gtl.gl_account_id = fm.gl_account_id
    AND (gtl.cost_center_id = fm.cost_center_id OR fm.cost_center_id IS NULL)
WHERE gt.is_posted = true OR gt.is_posted IS NULL
GROUP BY fm.company_id, fm.name, fm.model_type, fp.fiscal_year, fp.period_number, 
         fr.forecasted_amount;