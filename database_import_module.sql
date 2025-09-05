-- ============================================
-- DATA IMPORT & MAPPING MODULE
-- For flexible data import from various sources
-- ============================================

-- Import Templates (Define reusable import configurations)
CREATE TABLE import_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) NOT NULL, -- 'csv', 'excel', 'json', 'api', 'database'
    target_entity VARCHAR(100) NOT NULL, -- 'gl_transactions', 'budget_lines', 'kpis', etc.
    file_format JSONB, -- Column definitions, data types, delimiters
    mapping_rules JSONB, -- Field mappings configuration
    transformation_rules JSONB, -- Data transformation rules
    validation_rules JSONB, -- Data quality checks
    default_values JSONB, -- Default values for missing fields
    is_active BOOLEAN DEFAULT true,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, name)
);

-- Field Mapping Definitions
CREATE TABLE field_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES import_templates(id) ON DELETE CASCADE,
    source_field VARCHAR(255) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_field VARCHAR(100) NOT NULL,
    field_order INTEGER,
    data_type VARCHAR(50), -- 'string', 'number', 'date', 'boolean'
    transformation_type VARCHAR(50), -- 'direct', 'lookup', 'formula', 'concatenate', 'split'
    transformation_config JSONB, -- Specific transformation parameters
    is_required BOOLEAN DEFAULT false,
    default_value TEXT,
    validation_regex TEXT,
    error_handling VARCHAR(50) DEFAULT 'reject', -- 'reject', 'skip', 'default'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lookup/Mapping Tables for code translations
CREATE TABLE mapping_lookups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    lookup_type VARCHAR(50) NOT NULL, -- 'account', 'cost_center', 'vendor', 'customer', 'project'
    external_code VARCHAR(255) NOT NULL,
    internal_id UUID,
    internal_code VARCHAR(255),
    description TEXT,
    metadata JSONB, -- Additional mapping information
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, lookup_type, external_code)
);

-- Import Jobs (Track import executions)
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES import_templates(id),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    job_name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'validating', 'processing', 'completed', 'failed', 'partial'
    source_file_path TEXT,
    source_file_size BIGINT,
    total_records INTEGER,
    processed_records INTEGER DEFAULT 0,
    successful_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    skipped_records INTEGER DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error_summary JSONB,
    import_config JSONB, -- Snapshot of template config at import time
    executed_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Import Job Details (Row-level import tracking)
CREATE TABLE import_job_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_job_id UUID REFERENCES import_jobs(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    source_data JSONB NOT NULL,
    transformed_data JSONB,
    status VARCHAR(50) NOT NULL, -- 'success', 'failed', 'skipped'
    error_message TEXT,
    warnings JSONB,
    created_entity_id UUID, -- ID of created record
    created_entity_type VARCHAR(100), -- Table name of created record
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Import Schedules (For automated imports)
CREATE TABLE import_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES import_templates(id) ON DELETE CASCADE,
    schedule_name VARCHAR(255) NOT NULL,
    schedule_type VARCHAR(50) NOT NULL, -- 'once', 'daily', 'weekly', 'monthly', 'custom'
    cron_expression VARCHAR(100), -- For custom schedules
    source_config JSONB, -- FTP/API connection details, file patterns
    is_active BOOLEAN DEFAULT true,
    last_run_time TIMESTAMP,
    next_run_time TIMESTAMP,
    retry_on_failure BOOLEAN DEFAULT true,
    max_retries INTEGER DEFAULT 3,
    notification_emails TEXT[],
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data Source Connections (Store connection details securely)
CREATE TABLE data_source_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    connection_name VARCHAR(255) NOT NULL,
    connection_type VARCHAR(50) NOT NULL, -- 'database', 'api', 'ftp', 'sftp', 's3'
    connection_config JSONB, -- Encrypted connection details
    test_query TEXT, -- Query to test connection
    is_active BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMP,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, connection_name)
);

-- Import Transformation Rules Library
CREATE TABLE transformation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'regex', 'formula', 'lookup', 'script'
    rule_definition TEXT NOT NULL,
    input_parameters JSONB,
    output_format VARCHAR(50),
    description TEXT,
    example_input TEXT,
    example_output TEXT,
    is_system_rule BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, rule_name)
);

-- Import Validation Rules Library
CREATE TABLE validation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'required', 'format', 'range', 'lookup', 'custom'
    field_type VARCHAR(50), -- 'account', 'amount', 'date', 'code'
    validation_logic TEXT NOT NULL,
    error_message TEXT,
    severity VARCHAR(20) DEFAULT 'error', -- 'error', 'warning', 'info'
    is_system_rule BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, rule_name)
);

-- ============================================
-- CONSOLIDATION MODULE
-- For multi-entity consolidation
-- ============================================

-- Consolidation Groups
CREATE TABLE consolidation_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_company_id UUID REFERENCES companies(id),
    group_name VARCHAR(255) NOT NULL,
    consolidation_method VARCHAR(50), -- 'full', 'proportional', 'equity'
    reporting_currency CHAR(3) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Consolidation Group Members
CREATE TABLE consolidation_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consolidation_group_id UUID REFERENCES consolidation_groups(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id),
    ownership_percentage DECIMAL(5,2) NOT NULL CHECK (ownership_percentage > 0 AND ownership_percentage <= 100),
    consolidation_method VARCHAR(50), -- 'full', 'proportional', 'equity'
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Intercompany Elimination Rules
CREATE TABLE elimination_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consolidation_group_id UUID REFERENCES consolidation_groups(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'balance', 'transaction', 'investment'
    source_company_id UUID REFERENCES companies(id),
    target_company_id UUID REFERENCES companies(id),
    source_account_id UUID REFERENCES gl_accounts(id),
    target_account_id UUID REFERENCES gl_accounts(id),
    elimination_percentage DECIMAL(5,2) DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Currency Exchange Rates
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_currency CHAR(3) NOT NULL,
    to_currency CHAR(3) NOT NULL,
    rate_date DATE NOT NULL,
    rate_type VARCHAR(50) NOT NULL, -- 'spot', 'average', 'closing'
    exchange_rate DECIMAL(15,6) NOT NULL,
    source VARCHAR(100), -- 'manual', 'ecb', 'custom_api'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency, rate_date, rate_type)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_import_templates_company ON import_templates(company_id);
CREATE INDEX idx_import_jobs_template ON import_jobs(template_id);
CREATE INDEX idx_import_jobs_status ON import_jobs(status);
CREATE INDEX idx_import_job_details_job ON import_job_details(import_job_id);
CREATE INDEX idx_mapping_lookups_lookup ON mapping_lookups(company_id, lookup_type, external_code);
CREATE INDEX idx_field_mappings_template ON field_mappings(template_id);
CREATE INDEX idx_exchange_rates_lookup ON exchange_rates(from_currency, to_currency, rate_date);
CREATE INDEX idx_consolidation_members_group ON consolidation_members(consolidation_group_id);

-- ============================================
-- VIEWS FOR IMPORT MONITORING
-- ============================================

-- Import Job Summary View
CREATE VIEW v_import_job_summary AS
SELECT 
    ij.id,
    ij.job_name,
    c.name as company_name,
    it.name as template_name,
    ij.status,
    ij.total_records,
    ij.successful_records,
    ij.failed_records,
    ij.skipped_records,
    ROUND((ij.successful_records::NUMERIC / NULLIF(ij.total_records, 0)) * 100, 2) as success_rate,
    ij.start_time,
    ij.end_time,
    EXTRACT(EPOCH FROM (ij.end_time - ij.start_time)) as duration_seconds,
    u.email as executed_by_email
FROM import_jobs ij
JOIN companies c ON c.id = ij.company_id
LEFT JOIN import_templates it ON it.id = ij.template_id
LEFT JOIN users u ON u.id = ij.executed_by
ORDER BY ij.created_at DESC;

-- Active Import Schedules View
CREATE VIEW v_active_import_schedules AS
SELECT 
    s.id,
    s.schedule_name,
    t.name as template_name,
    c.name as company_name,
    s.schedule_type,
    s.cron_expression,
    s.last_run_time,
    s.next_run_time,
    s.is_active,
    CASE 
        WHEN s.next_run_time < CURRENT_TIMESTAMP THEN 'overdue'
        WHEN s.next_run_time < CURRENT_TIMESTAMP + INTERVAL '1 day' THEN 'upcoming'
        ELSE 'scheduled'
    END as schedule_status
FROM import_schedules s
JOIN import_templates t ON t.id = s.template_id
JOIN companies c ON c.id = t.company_id
WHERE s.is_active = true
ORDER BY s.next_run_time;